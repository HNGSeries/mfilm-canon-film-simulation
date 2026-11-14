"""Does a frame developed with no film stock match a standard RAW developer? (#98)

    python darkroomraw.py <sim/out dir> <out.json> CONFIG=frame.CR2 [CONFIG=frame.CR2 ...]

For each frame, the picture the darkroom has just before the scanner's
exposure and the film stock's table (scene-linear sRGB, 720 x 480) is set
beside LibRaw's linear sRGB of the same RAW at the same white balance.

  D  the darkroom's own code: sim/out/devtest-CONFIG, built from fos_dev.c
     with dump.patch, writes the picture where stage_key() begins
  L  LibRaw (rawpy): daylight balance from the camera's matrix, sRGB
     primaries, no tone curve, no automatic brightness, highlights clipped,
     AHD demosaic, then the camera's crop boxed down to 720 x 480
  P  the darkroom's steps again in floating point here, to take them apart
     (white level, the two clips)

CONFIG is the camera the darkroom was built for (EOSM, 5D3, 600D, ...).
Needs numpy, rawpy and Pillow.
"""

import json
import os
import re
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import rawpy
from PIL import Image

W, H = 720, 480
M_XYZ = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]], np.float64)          # fos_dev.c RGB_XYZ
LUMA = np.array([871, 2929, 296], np.float64) / 4096                       # stage_key()'s


# ---------------------------------------------------------------- colour maths (as lut-input/lutinput.py)

def lin_to_srgb(x):
    x = np.clip(np.asarray(x, np.float64), 0, 1)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def lab(lin):
    xyz = np.clip(lin, 0, 1).astype(np.float64) @ M_XYZ.T / M_XYZ.sum(1)
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


def cct_rgb(t):
    """fos_dev.c cct_rgb(): linear sRGB of a blackbody at t kelvin."""
    if t <= 4000:
        x = -0.2661239e9 / t ** 3 - 0.2343589e6 / t ** 2 + 0.8776956e3 / t + 0.179910
    else:
        x = -3.0258469e9 / t ** 3 + 2.1070379e6 / t ** 2 + 0.2226347e3 / t + 0.240390
    if t <= 2222:
        y = -1.1063814 * x ** 3 - 1.34811020 * x ** 2 + 2.18555832 * x - 0.20219683
    elif t <= 4000:
        y = -0.9549476 * x ** 3 - 1.37418593 * x ** 2 + 2.09137015 * x - 0.16748867
    else:
        y = 3.0817580 * x ** 3 - 5.87338670 * x ** 2 + 3.75112997 * x - 0.37001483
    X, Y, Z = x / y, 1.0, (1 - x - y) / y
    return np.array([3.2406 * X - 1.5372 * Y - 0.4986 * Z, -0.9689 * X + 1.8758 * Y + 0.0415 * Z,
                     0.0557 * X - 0.2040 * Y + 1.0570 * Z])


# ---------------------------------------------------------------- the CR2's own notes

def canon_notes(path):
    """ISO, and the white balances Canon wrote into the frame (maker note
    0x4001): {kelvin or 'as shot': (r, g, b) multipliers}."""
    b = Path(path).read_bytes()[:4 << 20]
    if b[:2] != b"II":
        return {}

    def ifd(off):
        n = struct.unpack_from("<H", b, off)[0]
        return {struct.unpack_from("<H", b, off + 2 + 12 * i)[0]: struct.unpack_from("<HIi", b, off + 4 + 12 * i)
                for i in range(n)}
    out = {}
    try:
        exif = ifd(ifd(struct.unpack_from("<I", b, 4)[0])[0x8769][2])
        if 0x8827 in exif:
            out["iso"] = exif[0x8827][2] & 0xFFFF
        maker = ifd(exif[0x927C][2])
        typ, count, off = maker[0x4001]
        v = struct.unpack_from("<%dH" % count, b, off)
        wb = {}
        for i in range(count - 4):
            if v[i + 1] == v[i + 2] and 900 < v[i + 1] < 1200 and v[i + 4] in (5200, 7000, 6000, 3200) and v[i] > 300 and v[i + 3] > 300:
                wb.setdefault(v[i + 4], (v[i] / v[i + 1], 1.0, v[i + 3] / v[i + 1]))
        out["canon_wb"] = wb
    except (KeyError, struct.error):
        pass
    return out


# ---------------------------------------------------------------- the pictures

def shrink(img):
    """(h, w) or (h, w, 3) float -> 720 x 480, a box filter."""
    img = np.asarray(img, np.float32)
    if img.ndim == 2:
        return np.asarray(Image.fromarray(np.ascontiguousarray(img), "F").resize((W, H), Image.BOX))
    return np.stack([shrink(img[..., c]) for c in range(3)], -1)


def darkroom(devtest, cr2):
    """D, and what the darkroom printed about the frame."""
    with tempfile.TemporaryDirectory() as tmp:
        dump = os.path.join(tmp, "lin.i32")
        # run beside the frame: the darkroom keeps paths short, as on a camera's card
        cr2 = Path(cr2).resolve()
        r = subprocess.run([os.path.abspath(devtest), cr2.name, "o.fop"], capture_output=True, text=True, cwd=cr2.parent,
                           env=dict(os.environ, FOS_DUMP_LIN=dump))
        if os.path.exists(cr2.parent / "o.fop"):
            os.remove(cr2.parent / "o.fop")
        log = r.stderr
        if r.returncode or not os.path.exists(dump):
            return None, {"error": (log.strip().splitlines() or ["devtest failed"])[-1]}
        d = np.fromfile(dump, np.int32).reshape(H, W, 3) / 4096.0
    m = re.search(r"dump: black (\d+)/16, pre (\d+) (\d+) (\d+), mat ([-\d /]+), white (\d+)", log)
    info = {"black": int(m.group(1)) / 16, "pre": [int(m.group(i)) / int(m.group(3)) for i in (2, 3, 4)],
            "mat": [int(x) / 4096 for x in m.group(5).replace("/", " ").split()], "white": int(m.group(6))}
    o = re.search(r"orientation (\d+)", log)
    info["orientation"] = int(o.group(1)) if o else 1
    return d, info


def mosaic_planes(raw):
    """The camera's crop as three 720 x 480 planes of mean raw value (the
    darkroom's box filter: every sample into the print pixel it falls in)."""
    z = raw.sizes
    y0, x0 = z.crop_top_margin, z.crop_left_margin
    c = raw.raw_image[y0:y0 + z.crop_height, x0:x0 + z.crop_width].astype(np.float32)
    col = raw.raw_colors[y0:y0 + 2, x0:x0 + 2]
    planes = [[], [], []]
    for dy in (0, 1):
        for dx in (0, 1):
            planes[1 if col[dy, dx] == 3 else int(col[dy, dx])].append(shrink(c[dy::2, dx::2]))
    return np.stack([np.mean(p, 0) for p in planes], -1)


def steps(mosaic, xyz_cam, black, white, clip=True):
    """fos_dev.c in floating point: less black, to the white level, balanced
    for the matrix's daylight, [clipped,] the matrix, [clipped]. Returns the
    picture, and the two unclipped stages for counting what the clips cut."""
    cam_rgb = xyz_cam @ M_XYZ
    rows = cam_rgb.sum(1)
    pre = (1 / rows) / (1 / rows)[1]
    inv = np.linalg.inv(cam_rgb / rows[:, None])
    cam = np.maximum(mosaic - black, 0) / (white - black) * pre
    lin_open = np.minimum(cam, 1) @ inv.T
    if not clip:
        return cam @ inv.T, cam, lin_open
    return np.clip(lin_open, 0, 1), cam, lin_open


def libraw_linear(raw, **kw):
    z = raw.sizes
    img = raw.postprocess(gamma=(1, 1), no_auto_bright=True, output_bps=16, use_camera_wb=False, use_auto_wb=False,
                          output_color=rawpy.ColorSpace.sRGB, highlight_mode=rawpy.HighlightMode.Clip, user_flip=0, **kw)
    x0, y0 = z.crop_left_margin - z.left_margin, z.crop_top_margin - z.top_margin
    return shrink(img[y0:y0 + z.crop_height, x0:x0 + z.crop_width].astype(np.float32) / 65535).astype(np.float64)


def blocks(a):
    """8 x 8 means, 90 x 60: the two pictures put a sample in a print pixel in
    slightly different ways (the darkroom whole, a box filter by fractions),
    which at one print pixel is noise of a few per cent and is nothing to do
    with colour."""
    return a.reshape(H // 8, 8, W // 8, 8, 3).mean((1, 3))


def compare(a, b):
    """a against b, both scene-linear sRGB, as 8 x 8 block means. Ratios are
    over blocks well inside both pictures' range (no channel near a clip, not
    near black); the dE2000 figures are over every block."""
    a, b = blocks(a), blocks(b)
    la, lb = a @ LUMA, b @ LUMA
    ok = (a.max(-1) < 0.9) & (b.max(-1) < 0.9) & (a.min(-1) > 0.005) & (b.min(-1) > 0.005) & (lb > 0.02)
    if ok.sum() < 200:
        return {"blocks": int(ok.sum())}
    ratio = a[ok] / b[ok]
    lum = la[ok] / lb[ok]
    k = float(np.median(lum))
    de = de2000(lab(a), lab(b))
    de_lev = de2000(lab(a / k), lab(b))
    return {
        "blocks": int(ok.sum()),
        "luminance_ratio_median": k,
        "ev": float(np.log2(k)),
        "channel_ratio_median": [float(x) for x in np.median(ratio, 0)],
        "channel_ratio_after_levelling": [float(x) for x in np.median(ratio, 0) / k],
        "ratio_p05_p95": [float(x) for x in np.percentile(lum / k, [5, 95])],
        "mean_abs_percent_after_levelling": float(np.mean(np.abs(ratio / k - 1)) * 100),
        "de2000_mean": float(de.mean()), "de2000_p95": float(np.percentile(de, 95)),
        "de2000_mean_after_levelling": float(de_lev.mean()), "de2000_p95_after_levelling": float(np.percentile(de_lev, 95)),
    }


def saturation(raw):
    """The raw value the frame's brightest pixels pile up at, if any do:
    the highest value inside the picture that at least 200 samples share."""
    z = raw.sizes
    c = raw.raw_image[z.crop_top_margin:z.crop_top_margin + z.crop_height, z.crop_left_margin:z.crop_left_margin + z.crop_width]
    h = np.bincount(c.ravel(), minlength=16384)
    top = np.nonzero(h)[0][-1]
    # a pile: many samples within 8 of one value, far more than just below it
    for v in range(int(top), 4000, -1):
        pile = int(h[max(v - 8, 0):v + 1].sum())
        if pile >= 200 and pile > 6 * int(h[max(v - 60, 0):v - 20].sum() / 5 + 1):
            return {"value": int(max(v - 8, 0) + np.argmax(h[max(v - 8, 0):v + 1])), "samples": pile, "max": int(top)}
    return {"value": None, "samples": 0, "max": int(top)}


def frame(devtest_dir, config, cr2):
    out = {"config": config, "file": str(cr2)}
    out.update(canon_notes(cr2))
    d, info = darkroom(os.path.join(devtest_dir, "devtest-" + config), cr2)
    out["darkroom"] = info
    with rawpy.imread(str(cr2)) as raw:
        z = raw.sizes
        black_l = float(np.mean(raw.black_level_per_channel))
        xyz_cam = np.array(raw.rgb_xyz_matrix[:3], np.float64)
        out["libraw"] = {"black": black_l, "white": int(raw.white_level),
                         "canon_white": [int(x) for x in raw.camera_white_level_per_channel] if raw.camera_white_level_per_channel is not None else None,
                         "daylight_wb": [float(x) / float(raw.daylight_whitebalance[1]) for x in raw.daylight_whitebalance[:3]],
                         "as_shot_wb": [float(x) / float(raw.camera_whitebalance[1]) for x in raw.camera_whitebalance[:3]],
                         "xyz_cam": xyz_cam.round(4).tolist(), "crop": [z.crop_width, z.crop_height]}
        out["saturation"] = sat = saturation(raw)
        if d is None:
            return out
        white, black = info["white"], info["black"]
        # the build's matrix, back out of the dump line (camera -> sRGB, rows summing to 1)
        build_inv = np.array(info["mat"]).reshape(3, 3)
        lib_cam_rgb = xyz_cam @ M_XYZ
        lib_inv = np.linalg.inv(lib_cam_rgb / lib_cam_rgb.sum(1)[:, None])
        out["matrix_max_abs_diff"] = float(np.abs(build_inv - lib_inv).max())
        out["pre_vs_libraw_daylight"] = [info["pre"][c] / out["libraw"]["daylight_wb"][c] for c in range(3)]

        # the frame's own white level: where its brightest samples pile up, if any do;
        # Canon's note in the file (LibRaw reads it) otherwise, which is a little lower
        note = (out["libraw"]["canon_white"] or [None])[0]
        real_white = sat["value"] or note
        out["white_level"] = {"build": white, "pile": sat["value"], "canon_note": note,
                              "ev": float(np.log2((sat["value"] - black) / (white - black))) if sat["value"] else None}
        if info["orientation"] != 1:
            out["skipped"] = "portrait frame: the pictures are not laid over each other here"
            return out

        mosaic = mosaic_planes(raw)
        p, cam, lin_open = steps(mosaic, xyz_cam, black, white)
        out["check_P_against_D"] = compare(d, p)
        out["check_P_against_D"]["max_abs_block"] = float(np.abs(blocks(d) - blocks(p)).max())

        lib = libraw_linear(raw)
        out["D_vs_libraw"] = compare(d, lib)
        # LibRaw told to use the build's white level, to see what is left
        lib_w = libraw_linear(raw, user_sat=int(round(white - black)))     # user_sat counts from black
        out["D_vs_libraw_same_white"] = compare(d, lib_w)
        # the darkroom's steps with the frame's own white level against LibRaw as it comes
        out["libraw_white_used"] = float(black + (white - black) * out["D_vs_libraw"].get("luminance_ratio_median", float("nan")))

        # what the two clips cut, in the darkroom's own picture
        n = W * H
        lum_open = lin_open @ LUMA
        out["clips"] = {
            "camera_channel_over_1_percent": float((cam.max(-1) > 1).sum() / n * 100),
            "all_three_over_1_percent": float((cam.min(-1) > 1).sum() / n * 100),
            "srgb_below_0_percent": float((lin_open.min(-1) < 0).sum() / n * 100),
            "srgb_below_minus_0.01_percent": float((lin_open.min(-1) < -0.01).sum() / n * 100),
            "srgb_over_1_percent": float(((lin_open.max(-1) > 1) & (cam.max(-1) <= 1)).sum() / n * 100),
            "light_cut_by_clip_at_1_percent": float(100 - (np.clip(lin_open, None, 1) @ LUMA).sum() / lum_open.sum() * 100),
            "light_added_by_clip_at_0_percent": float((np.clip(lin_open, 0, None) @ LUMA).sum() / lum_open.sum() * 100 - 100),
        }
        if sat["value"]:
            _, cam_real, _ = steps(mosaic, xyz_cam, black, sat["value"])
            out["clips"]["camera_channel_over_1_percent_at_frame_white"] = float((cam_real.max(-1) > 1).sum() / n * 100)
        # a grey that one of Canon's own balances calls neutral, through the build's fixed balance
        out["grey_under_canon_balance"] = {}
        wbs = dict(out.get("canon_wb", {}))
        wbs["as shot"] = out["libraw"]["as_shot_wb"]
        for name, wb in wbs.items():
            g = (np.array(info["pre"]) / np.array(wb)) @ build_inv.T
            g = g / (g @ LUMA)
            out["grey_under_canon_balance"][str(name)] = {
                "linear_srgb": [float(x) for x in g],
                "de2000_at_mid_grey": float(de2000(lab((0.18 * g)[None, None]), lab(np.full((1, 1, 3), 0.18)))[0, 0])}
        # a fully saturated pixel through the build's white level: grey only if the level is right
        # (only where the frame's blown samples say what its white level is)
        real_white = sat["value"]
        if real_white:
            cam_rgb = xyz_cam @ M_XYZ
            pre = (1 / cam_rgb.sum(1)) / (1 / cam_rgb.sum(1))[1]
            s = np.minimum((real_white - black) / (white - black) * pre, 1)
            out["saturated_pixel_linear_srgb"] = [float(x) for x in np.clip(s @ build_inv.T, 0, 1)]
    return out


def balance():
    """The darkroom's neutral (the matrix's: D65) against the film stocks' (5500 K)."""
    d65 = np.linalg.solve(M_XYZ, np.array([0.95047, 1.0, 1.08883]))          # = (1, 1, 1)
    out = {"d65_linear_srgb": d65.tolist()}
    for t in (5000, 5200, 5500, 6000, 6504):
        c = cct_rgb(t)
        c = c / c[1]
        grey = 0.18 * c
        out[str(t)] = {"linear_srgb_g1": c.tolist(), "percent": ((c - 1) * 100).tolist(),
                       "de2000_at_mid_grey": float(de2000(lab(grey[None, None]), lab(np.full((1, 1, 3), 0.18)))[0, 0])}
    return out


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    devdir, dest = sys.argv[1], sys.argv[2]
    res = {"balance": balance(), "frames": []}
    for arg in sys.argv[3:]:
        config, path = arg.split("=", 1)
        print(config, path, file=sys.stderr)
        try:
            res["frames"].append(frame(devdir, config, path))
        except Exception as e:                      # a file LibRaw can't read: say so and go on
            res["frames"].append({"config": config, "file": path, "failed": repr(e)})
    Path(dest).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
