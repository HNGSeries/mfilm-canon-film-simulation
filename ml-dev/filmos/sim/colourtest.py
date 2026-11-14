#!/usr/bin/env python3
"""The darkroom's picture before the film stock, against a RAW developer's.

    make out/devtest out/mkcr2 && python3 colourtest.py [--raw frame.CR2] [--devtest out/devtest] [--mkcr2 out/mkcr2]

Develops the frame with the camera's own code (devtest, FOS_DUMP_LIN: the
picture where stage_key() begins, before the scanner's exposure and any film
stock) and with LibRaw at the white balance the camera wrote into the frame:
sRGB primaries, no tone curve, no automatic brightness, highlights clipped.
Fails if the two are not the same picture, if the darkroom did not read the
balance LibRaw reads, or if its blown highlights are not neutral.

The darkroom scales a frame by its camera's white level and clips it where
that frame's own samples clip (white_clip() in fos_dev.c, #114). LibRaw is
given the frame's clip as its white level and its picture is put back on
the darkroom's scale, so the two clip at the same raw value.

Whether the darkroom finds the clip is tested on made-up frames (mkcr2
--white): a chart three stops over, its samples clipping below the camera's
white level, where a blown patch used to come out pink, and above it, where
highlights used to be cut off early.

The white balance is tested on a made-up frame too (mkcr2 --wb): a chart
under tungsten light with the camera on 3200 K and CineStill 800T loaded has
to come out as the same chart in daylight does, and the film stock must not
shift it a second time (#115, #123). The other made-up frames carry no
balance, and have to be developed as daylight and say so.

The limits are in LIMITS below. The two pictures are compared as 8 x 8 block
means: the darkroom puts each raw sample whole into one print pixel and a
box filter splits samples between pixels, which at one pixel is a few per
cent of noise and says nothing about colour.

Needs numpy, rawpy and Pillow. Measured for #98 (docs/research/darkroom-raw.md
on the research/darkroom-raw branch): 29 frames of 16 cameras were within
0.013 EV and a mean dE2000 of 0.66.
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import rawpy
from PIL import Image

HERE = Path(__file__).resolve().parent
W, H = 720, 480                         # FOS_PRINT_W, FOS_PRINT_H
# stops; mean dE2000; a blown pixel's colours, as a share of the clip; a chart in two lights, 1.0 = white
LIMITS = {"ev": 0.02, "de_mean": 1.0, "blown": 0.02, "light": 0.01}
M_XYZ = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])                       # fos_dev.c RGB_XYZ
LUMA = np.array([871, 2929, 296]) / 4096                                    # stage_key()'s


def lab(lin):
    """Scene-linear sRGB (clipped to 0..1) -> CIELAB, D65."""
    xyz = np.clip(lin, 0, 1) @ M_XYZ.T / M_XYZ.sum(1)
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


class Developed:
    """What the darkroom made of a frame: pic, the picture (H x W x 3, 1.0 =
    the camera's white level); black and white, the levels it scaled the
    frame by; clip, where it clipped it, on the picture's scale; balance, the
    white balance it read from the frame (red, green, blue), or None; mul,
    what the film stock then multiplies the three colours by; log."""


def darkroom(devtest, cr2, film=None):
    with tempfile.TemporaryDirectory() as tmp:
        # beside a link to the frame: the darkroom keeps paths short, as on a card
        os.symlink(Path(cr2).resolve(), os.path.join(tmp, "frame.CR2"))
        r = subprocess.run([str(Path(devtest).resolve())] + (["-f", film] if film else []) + ["frame.CR2", "o.fop"], cwd=tmp,
                           capture_output=True, text=True, env=dict(os.environ, FOS_DUMP_LIN="lin.i32"))
        dump = os.path.join(tmp, "lin.i32")
        if r.returncode or not os.path.exists(dump):
            sys.exit(f"FAIL  devtest did not develop {cr2}:\n{r.stderr.strip()}")
        d = Developed()
        d.pic = np.fromfile(dump, np.int32).reshape(H, W, 3) / 4096.0
    d.log = r.stderr
    m = re.search(r"dump: black (\d+)/16, white (\d+), clip (\d+), pre [\d ]+, balance (\d+) (\d+) (\d+)", d.log)
    mul = re.search(r"film: \w+, mul (\d+) (\d+) (\d+)", d.log)
    if not m or not mul:
        sys.exit("FAIL  devtest wrote no 'dump:' or 'film:' line (built without FOS_DEV_TEST?)")
    if re.search(r"orientation [5-8]", d.log):
        sys.exit("FAIL  a portrait frame: the test lays the two pictures over each other and needs a landscape one")
    d.black, d.white, d.clip = int(m.group(1)) / 16, int(m.group(2)), int(m.group(3)) / 4096
    d.balance = tuple(int(m.group(i)) for i in (4, 5, 6)) if int(m.group(5)) else None
    d.mul = tuple(int(mul.group(i)) for i in (1, 2, 3))
    return d


def shrink(img):
    """(h, w, 3) -> the print's 720 x 480, a box filter."""
    return np.stack([np.asarray(Image.fromarray(np.ascontiguousarray(img[..., c], np.float32), "F").resize((W, H), Image.BOX))
                     for c in range(3)], -1).astype(np.float64)


def libraw(cr2, d):
    """LibRaw's linear sRGB of the camera's crop, at the camera's white
    balance (the matrix's daylight if the darkroom found none), clipped where
    the darkroom clips and on its scale. Also the balance LibRaw read."""
    with rawpy.imread(str(cr2)) as raw:
        z = raw.sizes
        img = raw.postprocess(gamma=(1, 1), no_auto_bright=True, output_bps=16, use_camera_wb=d.balance is not None,
                              use_auto_wb=False, output_color=rawpy.ColorSpace.sRGB, highlight_mode=rawpy.HighlightMode.Clip,
                              user_flip=0, user_sat=int(round((d.white - d.black) * d.clip)))   # user_sat counts from black
        x0, y0 = z.crop_left_margin - z.left_margin, z.crop_top_margin - z.top_margin
        wb = raw.camera_whitebalance
        return shrink(img[y0:y0 + z.crop_height, x0:x0 + z.crop_width] / 65535.0) * d.clip, (int(wb[0]), int(wb[1]), int(wb[2]))


def blocks(a):
    return a.reshape(H // 8, 8, W // 8, 8, 3).mean((1, 3))


def make(mkcr2, cr2, *args):
    r = subprocess.run([str(Path(mkcr2).resolve()), str(cr2), "--half", "--scene", "chart"] + [str(a) for a in args],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"FAIL  mkcr2 did not make a frame:\n{r.stderr.strip()}")


def made_up(devtest, mkcr2, white):
    """A made-up frame whose samples clip at the raw value white: where the
    darkroom clipped it, where it should have, how many print pixels are
    blown through and through, how far the worst of them is from the clip in
    any colour (as a share of the clip), and whether the darkroom said the
    frame has no white balance."""
    with tempfile.TemporaryDirectory() as tmp:
        cr2 = os.path.join(tmp, "blown.CR2")
        make(mkcr2, cr2, "--ev", 3, "--white", white)
        d = darkroom(devtest, cr2)
        with rawpy.imread(cr2) as raw:
            z = raw.sizes
            at = raw.raw_image[z.crop_top_margin:z.crop_top_margin + z.crop_height,
                               z.crop_left_margin:z.crop_left_margin + z.crop_width] >= white
        share = np.asarray(Image.fromarray(at.astype(np.float32), "F").resize((W, H), Image.BOX))
    blown = share > 0.999
    worst = float(np.abs(d.pic[blown] - d.clip).max() / d.clip) if blown.any() else 0.0
    said = d.balance is None and "no white balance in the frame" in d.log
    return d.clip, (white - d.black) / (d.white - d.black), int(blown.sum()), worst, said


TUNGSTEN = (1.39, 2.36)     # red and blue multipliers of a Canon on 3200 K, green 1


def tungsten(devtest, mkcr2):
    """The chart under tungsten light with the camera on 3200 K and CineStill
    800T loaded, against the same chart in daylight: the balance the darkroom
    read; how far the two pictures are apart (the median over 8 x 8 blocks of
    the largest difference in any colour, 1.0 = white); and what the film
    stock multiplies the colours by."""
    with tempfile.TemporaryDirectory() as tmp:
        day, lamp = os.path.join(tmp, "day.CR2"), os.path.join(tmp, "lamp.CR2")
        make(mkcr2, day)
        make(mkcr2, lamp, "--wb", "%g,%g" % TUNGSTEN)
        a, b = darkroom(devtest, day, "cinestill800t"), darkroom(devtest, lamp, "cinestill800t")
    apart = float(np.median(np.abs(blocks(a.pic) - blocks(b.pic)).max(-1)))
    return b.balance, apart, b.mul


def compare(a, b, clip=1.0):
    """a against b: stops between their brightness (over blocks well inside
    both pictures' range), and dE2000 over every block."""
    a, b = blocks(a), blocks(b)
    top = 0.9 * min(clip, 1.0)
    ok = (a.max(-1) < top) & (b.max(-1) < top) & (a.min(-1) > 0.005) & (b.min(-1) > 0.005) & (b @ LUMA > 0.02)
    if ok.sum() < 200:
        sys.exit(f"FAIL  only {int(ok.sum())} blocks are inside both pictures' range: not a frame to test with")
    de = de2000(lab(a), lab(b))
    return {"ev": float(np.log2(np.median((a[ok] @ LUMA) / (b[ok] @ LUMA)))), "de_mean": float(de.mean()),
            "de_p95": float(np.percentile(de, 95))}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--raw", default=HERE.parents[1] / "films/sample/SAMPLE.CR2")
    ap.add_argument("--devtest", default=HERE / "out/devtest")
    ap.add_argument("--mkcr2", default=HERE / "out/mkcr2")
    a = ap.parse_args()
    d = darkroom(a.devtest, a.raw)
    theirs, wb = libraw(a.raw, d)
    got = compare(d.pic, theirs, d.clip)
    fail = 0
    for what, key, unit in (("brightness", "ev", "EV"), ("colour", "de_mean", "mean dE2000")):
        bad = abs(got[key]) > LIMITS[key]
        fail |= bad
        value = f"{got[key]:+.3f}" if key == "ev" else f"{got[key]:.2f}"
        print(f"{'FAIL ' if bad else 'ok   '} {what} against LibRaw: {value} {unit} (limit {LIMITS[key]})")
    print(f"      95 % of the print within dE2000 {got['de_p95']:.2f}; white level {d.white}, black {d.black:.1f}, "
          f"this frame clips at {d.black + (d.white - d.black) * d.clip:.0f}")
    bad = d.balance != wb
    fail |= bad
    print(f"{'FAIL ' if bad else 'ok   '} the frame's white balance: the darkroom read {d.balance}, LibRaw {wb}")

    for white, was in ((12000, "used to come out pink"), (15300, "used to be cut off early")):
        clip, want, n, worst, said = made_up(a.devtest, a.mkcr2, white)
        bad = abs(clip / want - 1) > 0.005 or n < 100 or worst > LIMITS["blown"]
        fail |= bad
        print(f"{'FAIL ' if bad else 'ok   '} a made-up frame clipping at {white} ({was}): the darkroom clips it at "
              f"{clip:.3f} (should: {want:.3f}), {n} blown pixels within {worst:.3f} of neutral (limit {LIMITS['blown']})")
    fail |= not said
    print(f"{'ok   ' if said else 'FAIL '} a frame with no white balance in it is developed as daylight, and the darkroom says so")

    balance, apart, mul = tungsten(a.devtest, a.mkcr2)
    want = (round(TUNGSTEN[0] * 1024), 1024, round(TUNGSTEN[1] * 1024))
    bad = balance != want or apart > LIMITS["light"]
    fail |= bad
    print(f"{'FAIL ' if bad else 'ok   '} a chart under tungsten with the camera on 3200 K: balance read {balance} "
          f"(written: {want}), {apart:.4f} from the same chart in daylight (limit {LIMITS['light']})")
    bad = len(set(mul)) != 1
    fail |= bad
    print(f"{'FAIL ' if bad else 'ok   '} CineStill 800T does not shift the colours a second time: it multiplies them by {mul}")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
