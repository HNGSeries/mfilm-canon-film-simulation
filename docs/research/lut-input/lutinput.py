"""Do the Film-Luts tables get the input they were made for? (#97)

    python lutinput.py <ml-dev> <out-dir> [--cam-dir DIR]

Develops ml-dev/films/sample/SAMPLE.CR2 two ways for every Film-Luts film
stock whose table expects a finished sRGB photo (59 of the 63; the 4 print
tables are #107):

  A  as the build does it today: scene-linear sRGB, the scanner's exposure,
     the Cineon grid, the table baked by genfilms.bake() (sRGB curve and a
     highlight roll-off, then the .cube)
  B  a finished 8-bit sRGB photo first, then the .cube straight on it:
       canon  the camera's own JPEG, as stored inside the CR2
       apple  macOS's RAW engine (--apple: sips, converted to sRGB)
       dcraw  LibRaw with dcraw's defaults (BT.709 curve, automatic brightness)

A and B share a white balance in each pair (as shot for canon and apple,
daylight for dcraw), and vignette, halation and grain are left out of both, so the two
differ only in what the table is fed. Needs numpy, rawpy and Pillow, and
the tables fetched by films/getluts.py.

--cam-dir: prints made by filmos/sim/out/devtest (FOS_JPEG) as <key>.jpg,
to check that A here is what the camera's code makes.
"""

import argparse
import io
import json
import sys
from pathlib import Path

import numpy as np
import rawpy
from PIL import Image

W, H, GRID = 720, 480, 33
WHITE_LEVEL = 13600                      # fos_dev.c, the EOS M's
LUMA = np.array([871, 2929, 296], np.float32) / 4096      # stage_key()'s


# ---------------------------------------------------------------- colour maths

def srgb_to_lin(v):
    v = np.asarray(v, np.float32)
    return np.where(v <= 0.04045, v / 12.92, np.power((v + 0.055) / 1.055, 2.4))


def lin_to_srgb(x):
    x = np.clip(np.asarray(x, np.float32), 0, 1)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)


M_XYZ = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]], np.float64)
WHITE = M_XYZ.sum(1)


def lab(srgb):
    """Display sRGB 0..1 -> CIELAB (D65)."""
    xyz = srgb_to_lin(srgb).astype(np.float64) @ M_XYZ.T / WHITE
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def de2000(l1, l2):
    L1, a1, b1 = l1[..., 0], l1[..., 1], l1[..., 2]
    L2, a2, b2 = l2[..., 0], l2[..., 1], l2[..., 2]
    cb = (np.hypot(a1, b1) + np.hypot(a2, b2)) / 2
    g = 0.5 * (1 - np.sqrt(cb ** 7 / (cb ** 7 + 25.0 ** 7)))
    a1, a2 = (1 + g) * a1, (1 + g) * a2
    c1, c2 = np.hypot(a1, b1), np.hypot(a2, b2)
    h1, h2 = np.degrees(np.arctan2(b1, a1)) % 360, np.degrees(np.arctan2(b2, a2)) % 360
    dl, dc = L2 - L1, c2 - c1
    dh = h2 - h1
    dh = np.where(dh > 180, dh - 360, np.where(dh < -180, dh + 360, dh))
    dh = np.where(c1 * c2 == 0, 0, dh)
    dH = 2 * np.sqrt(c1 * c2) * np.sin(np.radians(dh) / 2)
    lm, cm = (L1 + L2) / 2, (c1 + c2) / 2
    hs = h1 + h2
    hm = np.where(np.abs(h1 - h2) > 180, np.where(hs < 360, hs + 360, hs - 360), hs) / 2
    hm = np.where(c1 * c2 == 0, hs, hm)
    t = (1 - 0.17 * np.cos(np.radians(hm - 30)) + 0.24 * np.cos(np.radians(2 * hm))
         + 0.32 * np.cos(np.radians(3 * hm + 6)) - 0.20 * np.cos(np.radians(4 * hm - 63)))
    sl = 1 + 0.015 * (lm - 50) ** 2 / np.sqrt(20 + (lm - 50) ** 2)
    sc, sh = 1 + 0.045 * cm, 1 + 0.015 * cm * t
    rt = (-2 * np.sqrt(cm ** 7 / (cm ** 7 + 25.0 ** 7))
          * np.sin(np.radians(60 * np.exp(-((hm - 275) / 25) ** 2))))
    return np.sqrt((dl / sl) ** 2 + (dc / sc) ** 2 + (dH / sh) ** 2 + rt * (dc / sc) * (dH / sh))


# ---------------------------------------------------------------- the RAW

def shrink(img):
    """(h, w, 3) float, the camera's crop -> the 720 x 480 print, a box filter."""
    out = [np.asarray(Image.fromarray(np.ascontiguousarray(img[..., c]), "F").resize((W, H), Image.BOX))
           for c in range(3)]
    return np.stack(out, -1)


def crop(img, sizes):
    """LibRaw's picture -> the camera's crop (CR2 sensor info, as fos_dev.c)."""
    x0, y0 = sizes.crop_left_margin - sizes.left_margin, sizes.crop_top_margin - sizes.top_margin
    return img[y0:y0 + sizes.crop_height, x0:x0 + sizes.crop_width]


XYZ_CAM = np.array([[0.6602, -0.0841, -0.0939], [-0.4472, 1.2458, 0.2247], [-0.0975, 0.2039, 0.6148]])   # fos_dev.c, EOS M


def camera_linear(raw, wb):
    """Scene-linear sRGB as fos_dev.c makes it: the samples boxed into the print,
    less black, to WHITE_LEVEL, balanced, clipped, the camera's matrix, clipped.
    wb: None for the daylight balance of the matrix, or multipliers (r, g, b)."""
    z = raw.sizes
    full = raw.raw_image.astype(np.float32)
    c = full[z.crop_top_margin:z.crop_top_margin + z.crop_height, z.crop_left_margin:z.crop_left_margin + z.crop_width]
    col = raw.raw_colors[z.crop_top_margin:z.crop_top_margin + 2, z.crop_left_margin:z.crop_left_margin + 2]
    black = float(np.mean(raw.black_level_per_channel))
    planes = [[], [], []]
    for dy in (0, 1):
        for dx in (0, 1):
            planes[1 if col[dy, dx] == 3 else int(col[dy, dx])].append(shrink(c[dy::2, dx::2, None].repeat(3, -1))[..., 0])
    mosaic = np.stack([np.mean(p, 0) for p in planes], -1)
    cam_rgb = XYZ_CAM @ M_XYZ
    rows = cam_rgb.sum(1)
    pre = (1 / rows) / (1 / rows)[1] if wb is None else np.asarray(wb, np.float64) / wb[1]
    cam = np.clip((mosaic - black) / (WHITE_LEVEL - black) * pre, 0, 1)
    return np.clip(cam @ np.linalg.inv(cam_rgb / rows[:, None]).T, 0, 1).astype(np.float32)


def develop(path, apple=None):
    """The pictures the two ways start from, all 720 x 480 x 3 float."""
    pics = {}
    with rawpy.imread(str(path)) as raw:
        sizes = raw.sizes
        pics["lin_daylight"] = camera_linear(raw, None)
        pics["lin_asshot"] = camera_linear(raw, raw.camera_whitebalance[:3])
        # dcraw's defaults: daylight, BT.709 curve, brightness set so 1 % of pixels clip
        dc = raw.postprocess(output_bps=8, use_camera_wb=False, use_auto_wb=False)
        pics["photo_dcraw"] = lin_to_srgb(shrink(srgb_to_lin(crop(dc.astype(np.float32) / 255, sizes))))
        dc = raw.postprocess(output_bps=8, use_camera_wb=True)      # the same as shot, to set beside the other photos
        pics["photo_dcraw_asshot"] = lin_to_srgb(shrink(srgb_to_lin(crop(dc.astype(np.float32) / 255, sizes))))
        jpg = np.asarray(Image.open(io.BytesIO(raw.extract_thumb().data)).convert("RGB"), np.float32) / 255
        assert jpg.shape[:2] == (sizes.crop_height, sizes.crop_width), jpg.shape
        pics["photo_canon"] = lin_to_srgb(shrink(srgb_to_lin(jpg)))
        if apple:
            ap = np.asarray(Image.open(apple).convert("RGB"), np.float32) / 255
            assert ap.shape[:2] == (sizes.crop_height, sizes.crop_width), ap.shape
            pics["photo_apple"] = lin_to_srgb(shrink(srgb_to_lin(ap)))
    for k in [k for k in pics if k.startswith("photo_")]:          # a finished photo is 8 bits
        pics[k] = np.round(pics[k] * 255) / 255
    return pics


# ---------------------------------------------------------------- way A: the build's

def scanner_ev(lin, slide):
    """stage_key() of fos_dev.c: the log-average luminance to 0.11, or +1 EV for slides."""
    if slide:
        return 1.0
    y = np.floor((np.round(lin[::4, ::4] * 4096) @ (LUMA * 4096)) / 4096)
    key = np.exp(np.mean(np.log(y / 4096 + 1e-4)))
    return float(np.clip(np.log2(0.11 / key), -2, 3.5))


def baked(luts, table):
    """genfilms.bake(): the camera's grid of Cineon codes -> the 8-bit table."""
    g = np.arange(GRID, dtype=np.float32) / (GRID - 1)
    b, gg, r = np.meshgrid(g, g, g, indexing="ij")
    lin = luts.decode(np.stack([r, gg, b], -1).reshape(-1, 3), "cineon")
    rgb = np.clip(table.apply(lin), 0, 1)
    return (rgb * 255 + 0.5).astype(np.uint8).reshape(GRID, GRID, GRID, 3).astype(np.float32) / 255


def exposed(lin, ev, vignette=False):
    """The light the camera puts on the film's table: exposed, at most 16."""
    x = np.minimum(np.clip(lin, 0, 1) * 2 ** ev, 16)
    if vignette:
        ty, tx = np.linspace(-1, 1, H)[:, None], np.linspace(-1, 1, W)[None, :]
        x = x * (1 - 0.06 * ty ** 2 - 0.06 * tx ** 2)[..., None]
    return x


def way_a(luts, grid, x):
    pos = np.clip(luts.encode(x, "cineon"), 0, 1) * (GRID - 1)
    return luts._trilinear(grid, pos.reshape(-1, 3).astype(np.float32)).reshape(x.shape)


def way_b(table, photo):
    return np.clip(table.apply_encoded(photo.reshape(-1, 3)), 0, 1).reshape(photo.shape)


# ---------------------------------------------------------------- measuring

def compare(a, b, mono):
    """How far picture a is from picture b (the one the table was made for)."""
    la, lb = lab(a), lab(b)
    de = de2000(la, lb)
    out = dict(de_mean=de.mean(), de_median=np.median(de), de_p95=np.percentile(de, 95),
               dL=np.mean(la[..., 0] - lb[..., 0]),
               mid_a=np.median(la[..., 0]), mid_b=np.median(lb[..., 0]),
               contrast=np.std(la[..., 0]) / np.std(lb[..., 0]))
    if not mono:
        ca, cb = np.hypot(la[..., 1], la[..., 2]), np.hypot(lb[..., 1], lb[..., 2])
        out["chroma"] = ca.mean() / cb.mean()
        m = (ca > 10) & (cb > 10)
        dh = np.degrees(np.arctan2(la[..., 2], la[..., 1]) - np.arctan2(lb[..., 2], lb[..., 1]))[m]
        dh = (dh + 180) % 360 - 180
        out["hue"] = np.average(dh, weights=np.minimum(ca, cb)[m])
        out["hue_abs"] = np.average(np.abs(dh), weights=np.minimum(ca, cb)[m])
    return {k: float(v) for k, v in out.items()}


def match_ev(lin, photo):
    """The exposure at which the sRGB curve alone puts the picture's median where the photo has it."""
    target = np.median(photo @ LUMA)
    lo, hi = -4.0, 6.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if np.median(lin_to_srgb(exposed(lin, mid)) @ LUMA) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mldev")
    ap.add_argument("out")
    ap.add_argument("--cam-dir")
    ap.add_argument("--apple", help="the RAW developed by macOS (sips), converted to sRGB")
    ap.add_argument("--cam-lin", help="the camera code's own linear picture (int32, 4096 = 1.0), to check lin_daylight")
    a = ap.parse_args()
    films_dir = Path(a.mldev) / "films"
    sys.path.insert(0, str(films_dir))
    import lut as luts
    from filmluts import DIR, FILMS, STOCKS
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    pics = develop(films_dir / "sample" / "SAMPLE.CR2", a.apple)
    pairs = {"canon": ("lin_asshot", "photo_canon"), "dcraw": ("lin_daylight", "photo_dcraw")}
    if a.apple:
        pairs["apple"] = ("lin_asshot", "photo_apple")
    if a.cam_lin:
        theirs = np.fromfile(a.cam_lin, np.int32).reshape(H, W, 3) / 4096
        r = (theirs.sum(-1) + 1e-4) / (pics["lin_daylight"].sum(-1) + 1e-4)
        print(f"the camera code's linear picture against the one rebuilt here: ratio median {np.median(r):.4f}, "
              f"5th to 95th percentile {np.percentile(r, 5):.3f} to {np.percentile(r, 95):.3f}\n")

    # ---- what the table is fed, whatever the film: its 8-bit codes
    feed = {}
    for kind, slide, look_ev in (("neg", False, 0.2), ("slide", True, 0.0)):
        for name, (lk, pk) in pairs.items():
            ev = scanner_ev(pics["lin_daylight"], slide) + look_ev
            fed = luts.encode(exposed(pics[lk], ev), "srgb")
            y_fed, y_photo = fed @ LUMA, pics[pk] @ LUMA
            pct = lambda v: [round(float(np.percentile(v, p)) * 255, 1) for p in (5, 25, 50, 75, 95)]  # noqa: E731
            # the tone curve of each, from the same pixels: scene level (stops about the
            # picture's log-average) -> the code the table sees
            y_lin = pics[lk] @ LUMA
            stops = np.log2(np.maximum(y_lin, 1e-5) / np.exp(np.mean(np.log(np.maximum(y_lin, 1e-5)))))
            curve = {}
            for s in (-3, -2, -1, 0, 1, 2, 3):
                m = np.abs(stops - s) < 0.1
                if m.sum() > 200:
                    curve[s] = (round(float(np.median(y_fed[m])) * 255, 1), round(float(np.median(y_photo[m])) * 255, 1))
            feed[f"{kind}/{name}"] = dict(ev=round(ev, 3), fed=pct(y_fed), photo=pct(y_photo), curve=curve,
                                          nofilm=compare(np.clip(fed, 0, 1), pics[pk], False),
                                          clipped_fed=round(float((fed.max(-1) > 0.995).mean()) * 100, 2),
                                          clipped_photo=round(float((pics[pk].max(-1) > 0.995).mean()) * 100, 2),
                                          match_ev=round(match_ev(pics[lk], pics[pk]), 3))

    # ---- every film stock, both ways
    rows, check = [], {}
    mev = {p: match_ev(pics[lk], pics[pk]) for p, (lk, pk) in pairs.items()}
    photos = [k for k in ("photo_canon", "photo_apple", "photo_dcraw_asshot") if k in pics]
    between = [(x, y) for i, x in enumerate(photos) for y in photos[i + 1:]]
    block = lambda p: p.reshape(H // 8, 8, W // 8, 8, 3).mean((1, 3))      # noqa: E731  (grain averaged away)
    for key, path, brand, name, iso, kind in STOCKS:
        if kind == "print":
            continue
        f = FILMS[key]
        table = luts.load(str(films_dir / "luts" / DIR / f"{path}.cube"), "srgb")
        grid = baked(luts, table)
        ev = scanner_ev(pics["lin_daylight"], bool(f.get("slide"))) + f["ev"]
        row = dict(key=key, name=f["name"], kind=kind, ev=round(ev, 3))
        for pname, (lk, pk) in pairs.items():
            pa, pb = way_a(luts, grid, exposed(pics[lk], ev)), way_b(table, pics[pk])
            row[pname] = compare(pa, pb, kind == "bw")
            # the same with the exposure moved so only the curve's shape differs
            pm = way_a(luts, grid, exposed(pics[lk], mev[pname]))
            row[pname + "_matched"] = compare(pm, pb, kind == "bw")
            if key in ("pro400h", "velvia100", "tmax400", "portra160", "kodachrome64"):
                sheet = np.concatenate([pa, pb], 1)
                Image.fromarray((sheet * 255 + 0.5).astype(np.uint8)).save(out / f"{key}_{pname}_A-left_B-right.jpg", quality=92)
        # two finished photos of the same RAW through the same table: how far apart are they?
        for x, y in between:
            row[f"{x[6:]}~{y[6:]}"] = compare(way_b(table, pics[x]), way_b(table, pics[y]), kind == "bw")
        rows.append(row)
        cam = Path(a.cam_dir) / f"{key}.jpg" if a.cam_dir else None
        if cam and cam.is_file():
            mine = way_a(luts, grid, exposed(pics["lin_daylight"], ev, vignette=True))
            theirs = np.asarray(Image.open(cam).convert("RGB"), np.float32) / 255
            check[key] = compare(mine, theirs, kind == "bw")
            check[key]["de_block"] = compare(block(mine), block(theirs), kind == "bw")["de_mean"]

    (out / "results.json").write_text(json.dumps(dict(feed=feed, films=rows, check=check), indent=1))

    # ---- report
    print("what the table is fed (8-bit luminance codes at the 5/25/50/75/95th percentile)")
    for k, v in feed.items():
        print(f"  {k:12s} exposure {v['ev']:+.2f} EV  today {v['fed']}  photo {v['photo']}  "
              f"clipped {v['clipped_fed']} % / {v['clipped_photo']} %  exposure that matches the median {v['match_ev']:+.2f} EV")
        print("     scene stops -> code today / photo: " + "  ".join(f"{s:+d}: {c[0]:.0f}/{c[1]:.0f}" for s, c in v["curve"].items()))
        n = v["nofilm"]
        print(f"     with no table at all, fed against photo: dE {n['de_mean']:.2f}, L* {n['dL']:+.1f}, contrast {n['contrast']:.2f}, "
              f"chroma {n['chroma']:.2f}, hue {n['hue']:+.1f} (|{n['hue_abs']:.1f}|)")
    cols = ("de_mean", "de_p95", "dL", "contrast", "chroma", "hue", "hue_abs")
    for pname in [p + m for p in pairs for m in ("", "_matched")] + [f"{x[6:]}~{y[6:]}" for x, y in between]:
        print(f"\nA against B ({pname}): dE2000 mean, p95; L* A-B; contrast A/B; chroma A/B; hue A-B deg, |hue|")
        for kind in ("neg", "slide", "xpro", "bw"):
            sel = [r[pname] for r in rows if r["kind"] == kind]
            line = "  ".join(f"{c} {np.mean([s[c] for s in sel]):6.2f}" for c in cols if c in sel[0])
            de = [s["de_mean"] for s in sel]
            print(f"  {kind:5s} n={len(sel):2d}  {line}   (dE mean from {min(de):.1f} to {max(de):.1f})")
    print("\nnamed film stocks, A against B (" + " | ".join(pairs) + "): dE mean, L* A-B, contrast, chroma, hue")
    for r in rows:
        if r["key"] in ("pro400h", "portra160", "superia200", "velvia100", "provia100f", "kodachrome64", "elite100xpro", "tmax400", "delta400"):
            cell = lambda d: f"{d['de_mean']:5.1f} {d['dL']:+6.1f} {d['contrast']:5.2f} " + (f"{d['chroma']:5.2f} {d['hue']:+5.1f}" if "chroma" in d else "    -     -")  # noqa: E731
            print(f"  {r['name']:26s} " + " | ".join(cell(r[p]) for p in pairs))
    if check:
        print("\nA here against the camera code's own print (with its vignette; the print also has halation, grain and JPEG):")
        for k, v in check.items():
            print(f"  {k:12s} dE mean {v['de_mean']:.2f}, median {v['de_median']:.2f}, L* {v['dL']:+.2f}; "
                  f"in 8 x 8 blocks (grain averaged away) dE mean {v['de_block']:.2f}")


if __name__ == "__main__":
    main()
