#!/usr/bin/env python3
"""What the Film-Luts tables are fed: a finished photo's tone.

    make out/devtest && python3 tonetest.py [--raw frame.CR2] [--devtest out/devtest]

The Film-Luts tables were made by eye on finished photos. The build fed them
the plain sRGB curve, which is flatter than any camera's own JPEG: 80 to
88 % of its contrast (#97). lut.py's "photo" input space is the tone curve
of Canon's Standard picture style, with mid grey where sRGB has it (#125).

This checks it on the frame's own camera JPEG, a frame the curve was not
fitted on: the picture a table is fed, brought to the JPEG's brightness, has
the JPEG's contrast (the spread of L*, over 8 x 8 blocks) within LIMIT. It
also holds the curve's shape: sRGB's value at the pivot, rising everywhere,
darker shadows and brighter upper tones than sRGB, and back through
decode(). Needs numpy, rawpy and Pillow.
"""

import argparse
import io
import sys
from pathlib import Path

import numpy as np
import rawpy
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "films"))
import colourtest as ct  # noqa: E402
import lut  # noqa: E402

LIMIT = 0.03        # how far the contrast may be from the camera JPEG's
WAS = 0.92          # the plain sRGB curve has to be below this, or the test has stopped showing the fault


def srgb_to_lin(v):
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def lightness(display):
    """L* of a display picture's 8 x 8 blocks."""
    y = np.clip(ct.blocks(srgb_to_lin(np.asarray(display, np.float64))) @ ct.LUMA, 0, 1)
    f = np.where(y > 216 / 24389, np.cbrt(y), (24389 / 27 * y + 16) / 116)
    return 116 * f - 16


def contrast(lin, space, photo):
    """The spread of L* of lin through the curve, over the photo's, with lin's
    exposure moved until its mean L* is the photo's."""
    lo, hi = -6.0, 8.0
    for _ in range(40):
        ev = (lo + hi) / 2
        L = lightness(lut.encode(lin * 2.0 ** ev, space))
        lo, hi = (ev, hi) if L.mean() < photo.mean() else (lo, ev)
    return float(L.std() / photo.std())


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--raw", default=HERE.parents[1] / "films/sample/SAMPLE.CR2")
    ap.add_argument("--devtest", default=HERE / "out/devtest")
    a = ap.parse_args()
    fail = 0

    def check(ok, what):
        nonlocal fail
        fail |= not ok
        print(f"{'ok   ' if ok else 'FAIL '} {what}")

    # the curve
    p = lut.PHOTO_PIVOT
    x = p * 2.0 ** np.linspace(-14, 7, 2101)
    y, plain = lut.encode(x, "photo").astype(np.float64), lut.encode(np.minimum(x, 0.8), "srgb").astype(np.float64)
    at = float(lut.encode(np.array([p]), "photo")[0])
    check(abs(at - float(lut.encode(np.array([p]), "srgb")[0])) < 1e-4, f"mid grey is where sRGB has it: {at:.4f} at {p}")
    check(bool(np.all(np.diff(y) > 0)) and y[0] < 1e-3 and y[-1] > 0.995, "the curve rises everywhere, from black to white")
    shadows, upper = (x < p / 2) & (x > p / 64), (x > p * 1.5) & (x < p * 4)
    check(bool(np.all(y[shadows] < plain[shadows])) and bool(np.all(y[upper] > plain[upper])),
          "shadows are darker and the upper tones brighter than the plain sRGB curve")
    back = lut.decode(lut.encode(x[400:1900], "photo"), "photo")
    check(float(np.max(np.abs(back / x[400:1900] - 1))) < 0.01, "decode() takes it back")
    check(float(lut.encode(np.array([0.0, -1.0]), "photo").max()) == 0.0, "nothing and less than nothing are black")

    # against the camera's own JPEG
    d = ct.darkroom(a.devtest, a.raw)
    with rawpy.imread(str(a.raw)) as raw:
        jpeg = Image.open(io.BytesIO(raw.extract_thumb().data)).convert("RGB")
    photo = lightness(np.asarray(jpeg.resize((ct.W, ct.H), Image.BOX), np.float64) / 255)
    new, was = contrast(d.pic, "photo", photo), contrast(d.pic, "srgb", photo)
    check(abs(new - 1) <= LIMIT, f"a table is fed the camera JPEG's contrast: {new:.2f} of it (limit 1 ± {LIMIT})")
    check(was < WAS, f"the plain sRGB curve gave {was:.2f} of it (the fault this fixes: under {WAS})")

    # the films that use it
    from filmluts import FILMS
    spaces = {f["lut_space"] for f in FILMS.values()}
    check(spaces == {"photo"}, f"all {len(FILMS)} Film-Luts films are fed it (input spaces: {', '.join(sorted(spaces))})")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
