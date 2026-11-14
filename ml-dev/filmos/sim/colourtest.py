#!/usr/bin/env python3
"""The darkroom's picture before the film stock, against a RAW developer's.

    make out/devtest && python3 colourtest.py [--raw frame.CR2] [--devtest out/devtest]

Develops the frame with the camera's own code (devtest, FOS_DUMP_LIN: the
picture where stage_key() begins, before the scanner's exposure and any film
stock) and with LibRaw at the same white level and the same daylight
balance: sRGB primaries, no tone curve, no automatic brightness, highlights
clipped. Fails if the two are not the same picture.

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
LIMITS = {"ev": 0.02, "de_mean": 1.0}   # brightness in stops, mean dE2000
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


def darkroom(devtest, cr2):
    """The darkroom's picture (H x W x 3, 1.0 = white) and the black and white
    levels it scaled the frame by."""
    with tempfile.TemporaryDirectory() as tmp:
        # beside a link to the frame: the darkroom keeps paths short, as on a card
        os.symlink(Path(cr2).resolve(), os.path.join(tmp, "frame.CR2"))
        r = subprocess.run([str(Path(devtest).resolve()), "frame.CR2", "o.fop"], cwd=tmp, capture_output=True, text=True,
                           env=dict(os.environ, FOS_DUMP_LIN="lin.i32"))
        dump = os.path.join(tmp, "lin.i32")
        if r.returncode or not os.path.exists(dump):
            sys.exit(f"FAIL  devtest did not develop {cr2}:\n{r.stderr.strip()}")
        pic = np.fromfile(dump, np.int32).reshape(H, W, 3) / 4096.0
    m = re.search(r"dump: black (\d+)/16, white (\d+)", r.stderr)
    if not m:
        sys.exit("FAIL  devtest wrote no 'dump:' line (built without FOS_DEV_TEST?)")
    if re.search(r"orientation [5-8]", r.stderr):
        sys.exit("FAIL  a portrait frame: the test lays the two pictures over each other and needs a landscape one")
    return pic, int(m.group(1)) / 16, int(m.group(2))


def shrink(img):
    """(h, w, 3) -> the print's 720 x 480, a box filter."""
    return np.stack([np.asarray(Image.fromarray(np.ascontiguousarray(img[..., c], np.float32), "F").resize((W, H), Image.BOX))
                     for c in range(3)], -1).astype(np.float64)


def libraw(cr2, black, white):
    """LibRaw's linear sRGB of the camera's crop, at the darkroom's white level."""
    with rawpy.imread(str(cr2)) as raw:
        z = raw.sizes
        img = raw.postprocess(gamma=(1, 1), no_auto_bright=True, output_bps=16, use_camera_wb=False, use_auto_wb=False,
                              output_color=rawpy.ColorSpace.sRGB, highlight_mode=rawpy.HighlightMode.Clip, user_flip=0,
                              user_sat=int(round(white - black)))            # user_sat counts from black
        x0, y0 = z.crop_left_margin - z.left_margin, z.crop_top_margin - z.top_margin
        return shrink(img[y0:y0 + z.crop_height, x0:x0 + z.crop_width] / 65535.0)


def blocks(a):
    return a.reshape(H // 8, 8, W // 8, 8, 3).mean((1, 3))


def compare(a, b):
    """a against b: stops between their brightness (over blocks well inside
    both pictures' range), and dE2000 over every block."""
    a, b = blocks(a), blocks(b)
    ok = (a.max(-1) < 0.9) & (b.max(-1) < 0.9) & (a.min(-1) > 0.005) & (b.min(-1) > 0.005) & (b @ LUMA > 0.02)
    if ok.sum() < 200:
        sys.exit(f"FAIL  only {int(ok.sum())} blocks are inside both pictures' range: not a frame to test with")
    de = de2000(lab(a), lab(b))
    return {"ev": float(np.log2(np.median((a[ok] @ LUMA) / (b[ok] @ LUMA)))), "de_mean": float(de.mean()),
            "de_p95": float(np.percentile(de, 95))}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--raw", default=HERE.parents[1] / "films/sample/SAMPLE.CR2")
    ap.add_argument("--devtest", default=HERE / "out/devtest")
    a = ap.parse_args()
    pic, black, white = darkroom(a.devtest, a.raw)
    got = compare(pic, libraw(a.raw, black, white))
    fail = 0
    for what, key, unit in (("brightness", "ev", "EV"), ("colour", "de_mean", "mean dE2000")):
        bad = abs(got[key]) > LIMITS[key]
        fail |= bad
        value = f"{got[key]:+.3f}" if key == "ev" else f"{got[key]:.2f}"
        print(f"{'FAIL ' if bad else 'ok   '} {what} against LibRaw: {value} {unit} (limit {LIMITS[key]})")
    print(f"      95 % of the print within dE2000 {got['de_p95']:.2f}; white level {white}, black {black:.1f}")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
