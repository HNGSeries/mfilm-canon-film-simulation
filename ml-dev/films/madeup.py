#!/usr/bin/env python3
"""A made-up paired shot's pictures: what stands in for a roll until one is shot.

    python3 madeup.py OUT [--record ../references/made-up/record.txt] [--raw [--mkcr2 PATH]]

No film has been shot (#121), so the measuring command is tested on a paired
shot that is drawn. For every frame of the record that shows the chart, at
that frame's exposure and with the chart where the record says it is, this
writes

    OUT/canon/NN.jpg     the chart printed plainly: a finished photo's tone
                         (lut.py's "photo" curve), no colour of its own. An
                         8-bit JPEG, as a developer saves
    OUT/locked/NN.tif    the same chart through a made-up film (LOOK), which
                         stands in for the locked scan. A 16-bit TIFF, as a
                         lab hands over

    OUT/automatic/NN.jpg the made-up film again with every frame brought back
                         to a normal exposure, as a lab's everyday scan does

With --raw, OUT/canon/NN.CR2 instead: the chart as a Canon's RAW frames
(filmos/sim/tools/mkcr2.c), for the measuring command to develop. The
made-up film is also a table file (table()), so the darkroom can print
with it and has to come out where the "scan" is.

The made-up film has the shape a measured film stock's look has (#119):
a mix of the three colours, a tone curve for each with a toe and a shoulder,
a second mix, then sRGB; for a black-and-white film stock, one mix to grey
and one curve (LOOK_BW). Its numbers are nobody's film. They are only known,
so a test knows what the measuring command has to print.

    python3 measure.py compare ../references/made-up/record.txt canon=OUT/canon locked=OUT/locked

The frames in open shade are drawn in bluer light (SHADE), which neither
picture corrects: a frame keeps the white balance the camera was on (#115).

Needs numpy and Pillow.
"""

import argparse
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "filmos/tools"))
import lut  # noqa: E402
import measure  # noqa: E402
from measure import Bad, Reading, Record  # noqa: E402

RECORD = HERE.parent / "references/made-up/record.txt"
MKCR2 = HERE.parent / "filmos/sim/out/mkcr2"
SIZE = (1200, 800)
RAW_SIZE = (2592, 1728)                 # mkcr2 --half: enough samples of every colour for each pixel of a print

# the chart's 24 patches as sRGB, the values tools/mkcr2.c draws
CHECKER = np.array([
    [115, 82, 68], [194, 150, 130], [98, 122, 157], [87, 108, 67], [133, 128, 177], [103, 189, 170],
    [214, 126, 44], [80, 91, 166], [193, 90, 99], [94, 60, 108], [157, 188, 64], [224, 163, 46],
    [56, 61, 150], [70, 148, 73], [175, 54, 60], [231, 199, 31], [187, 86, 149], [8, 133, 161],
    [243, 243, 242], [200, 200, 200], [160, 160, 160], [122, 122, 121], [85, 85, 85], [52, 52, 52]], np.float64) / 255
CARD, EDGE = 0.18, 0.035                # the grey card the chart stands on, and the chart's black frame, as light
OUTLINE = 0.62                          # how far the chart's frame reaches past its corner patches' centres, in patches
SHADE = np.array([0.80, 1.00, 1.30])    # open shade under blue sky, against the main light

# The made-up film. mix: scene light to the film's three layers. curve, per
# layer: the print's value, lo + (hi - lo) / (1 + exp(-(c0 + a s + b s^2 + c s^3))),
# s the stops from mid grey (0.18) and c0 where "mid" puts mid grey; b bends
# the toe against the shoulder (b^2 < 3 a c keeps it rising). out: the print's
# three colours to sRGB's, as light. Each row of a mix adds up to 1, so grey stays grey.
LOOK = dict(
    mix=[[0.92, 0.06, 0.02], [0.05, 0.90, 0.05], [0.02, 0.10, 0.88]],
    curve=[dict(mid=0.47, a=0.62, b=0.012, c=0.006, lo=0.030, hi=0.97),
           dict(mid=0.46, a=0.60, b=0.010, c=0.006, lo=0.025, hi=0.96),
           dict(mid=0.43, a=0.56, b=0.008, c=0.005, lo=0.020, hi=0.93)],
    out=[[1.10, -0.07, -0.03], [-0.04, 1.08, -0.04], [-0.02, -0.08, 1.10]],
)
LOOK_BW = dict(
    mix=[[0.30, 0.55, 0.15]],
    curve=[dict(mid=0.45, a=0.66, b=0.012, c=0.007, lo=0.02, hi=0.97)],
)


def film(lin, look):
    """Scene light (0.18 = mid grey) through a film-shaped look -> sRGB, 0..1."""
    m = np.maximum(np.asarray(lin, np.float64) @ np.array(look["mix"], np.float64).T, 1e-9)
    s = np.log2(m / 0.18)
    v = np.zeros_like(m)
    for i, c in enumerate(look["curve"]):
        mid = (c["mid"] - c["lo"]) / (c["hi"] - c["lo"])
        z = np.log(mid / (1 - mid)) + c["a"] * s[..., i] + c["b"] * s[..., i] ** 2 + c["c"] * s[..., i] ** 3
        v[..., i] = c["lo"] + (c["hi"] - c["lo"]) / (1 + np.exp(-z))
    if "out" not in look:
        return np.repeat(v, 3, -1)
    return measure.to_srgb(measure.to_lin(v) @ np.array(look["out"], np.float64).T)


def plain(lin):
    """Scene light printed plainly: a finished photo's tone, the same for the three colours."""
    return lut.encode(np.asarray(lin, np.float64), "photo").astype(np.float64)


def look_of(record):
    return LOOK_BW if record.tone_only else LOOK


def scene(frame):
    """A chart frame's light: the 24 patches, the card and the chart's frame, at the frame's exposure and in its light."""
    light = 2.0 ** frame.ev * (SHADE if "shade" in frame.shows else np.ones(3))
    return measure.to_lin(CHECKER) * light, CARD * light, EDGE * light


def printed(record, name, frame):
    """What a set's picture of a chart frame has as sRGB: the 24 patches, the card, the chart's frame."""
    if name == "canon":
        return [plain(x) for x in scene(frame)]
    back = 2.0 ** -frame.ev if name == "automatic" else 1      # an everyday scan levels every frame
    return [film(x * back, look_of(record)) for x in scene(frame)]


def reading(record, name, frame):
    """What the measuring command should read in that picture, worked out with no picture."""
    return Reading.of_coded(printed(record, name, frame)[0])


def draw(patches, card, edge, corners, size=SIZE):
    """A picture of the chart: its corner patches' centres at corners (fractions of the picture)."""
    w, h = size
    to_chart = measure.homography(np.asarray(corners, np.float64) * [w, h], measure.GRID)
    ys, xs = np.mgrid[0:h, 0:w]
    p = np.stack([xs + 0.5, ys + 0.5, np.ones_like(xs)], -1) @ to_chart.T
    u, v = p[..., 0] / p[..., 2], p[..., 1] / p[..., 2]
    pic = np.empty((h, w, 3))
    pic[:] = card
    pic[(u > -OUTLINE) & (u < 5 + OUTLINE) & (v > -OUTLINE) & (v < 3 + OUTLINE) & (p[..., 2] > 0)] = edge
    c, r = np.rint(u).astype(int), np.rint(v).astype(int)
    on = ((c >= 0) & (c < 6) & (r >= 0) & (r < 4) & (np.abs(u - c) <= measure.PATCH_SIDE / 2)
          & (np.abs(v - r) <= measure.PATCH_SIDE / 2) & (p[..., 2] > 0))
    pic[on] = np.asarray(patches)[(r * 6 + c)[on]]
    return pic


def write_tiff(path, pic, bits=16, order="<"):
    """A picture (0..1) as an uncompressed TIFF, 8 or 16 bits a colour."""
    h, w = pic.shape[:2]
    data = (np.rint(np.clip(pic, 0, 1) * (2 ** bits - 1)).astype(np.dtype(order + "u2") if bits == 16 else np.uint8)).tobytes()
    tags = [(256, 4, w), (257, 4, h), (258, 3, None), (259, 3, 1), (262, 3, 2), (273, 4, None), (277, 3, 3), (278, 4, h),
            (279, 4, len(data)), (284, 3, 1)]
    after = 8 + 2 + 12 * len(tags) + 4
    out = (b"II*\0" if order == "<" else b"MM\0*") + struct.pack(order + "IH", 8, len(tags))
    for tag, kind, value in tags:
        if tag == 258:
            out += struct.pack(order + "HHII", tag, kind, 3, after)
        elif tag == 273:
            out += struct.pack(order + "HHII", tag, kind, 1, after + 6)
        elif kind == 3:
            out += struct.pack(order + "HHIHH", tag, kind, 1, value, 0)
        else:
            out += struct.pack(order + "HHII", tag, kind, 1, value)
    Path(path).write_bytes(out + struct.pack(order + "I", 0) + struct.pack(order + "HHH", bits, bits, bits) + data)


def write(path, pic):
    """A picture (0..1): .tif at 16 bits, .jpg at 8."""
    from PIL import Image
    path = Path(path)
    if path.suffix == ".tif":
        write_tiff(path, pic)
    else:
        Image.fromarray(np.rint(np.clip(pic, 0, 1) * 255).astype(np.uint8)).save(path, quality=92)   # the darkroom's own (fos_dev.c)


def render(record, out, kinds=None, mkcr2=None):
    """Every set's pictures of the record's chart frames into out/<set>/; kinds: a set's file type, where it is
    not the usual. With mkcr2, the canon set is the Canon's RAW frames and not their plain prints."""
    out = Path(out)
    made = {}
    for name in sorted(record.chart):
        (out / name).mkdir(parents=True, exist_ok=True)
        ext = (kinds or {}).get(name, ".tif" if name == "locked" else ".jpg")
        for f in record.charts():
            if name == "canon" and mkcr2:
                raw_frame(out / name / ("%02d.CR2" % f.n), record, f, mkcr2)
            else:
                write(out / name / ("%02d%s" % (f.n, ext)), draw(*printed(record, name, f), record.corners(name, f.n)))
        made[name] = out / name
    return made


def raw_frame(path, record, frame, mkcr2=MKCR2):
    """A chart frame as the Canon's RAW file: the scene as light, through mkcr2's sensor."""
    if not Path(mkcr2).exists():
        raise Bad(f"no {mkcr2}: make -C ml-dev/filmos/sim out/mkcr2")
    pic = draw(*scene(frame), record.corners("canon", frame.n), RAW_SIZE)
    pfm = Path(path).with_suffix(".pfm")
    pfm.write_bytes(b"PF\n%d %d\n-1.0\n" % RAW_SIZE + pic[::-1].astype("<f4").tobytes())     # rows from the bottom up
    r = subprocess.run([str(mkcr2), str(path), "--half", "--image", str(pfm)], capture_output=True, text=True)
    pfm.unlink()
    if r.returncode:
        raise Bad(f"mkcr2 did not make {path}: {r.stderr.strip()}")


def table(record, out, look=None):
    """The made-up film (or another look of its shape) as the film stock's table file in out/, where and as
    tools/gentables.py writes them: 33 points a side over Cineon code, 0.18 = mid grey."""
    import genfilms
    import gentables
    key = record.fields["film stock"]
    g = np.arange(genfilms.GRID, dtype=np.float32) / (genfilms.GRID - 1)
    b, gg, r = np.meshgrid(g, g, g, indexing="ij")              # red changes fastest
    rgb = np.clip(film(lut.decode(np.stack([r, gg, b], -1).reshape(-1, 3), "cineon"), look or look_of(record)), 0, 1)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / ("LOOK%02d.LUT" % gentables.shelf().index(key))
    path.write_bytes(b"FOL1" + struct.pack("<I", genfilms.look_hash(key, genfilms.look_bytes(genfilms.FILMS[key])))
                     + (rgb * 255 + 0.5).astype(np.uint8).tobytes())
    return out


def main():
    ap = argparse.ArgumentParser(description="A made-up paired shot's pictures.")
    ap.add_argument("out")
    ap.add_argument("--record", default=str(RECORD))
    ap.add_argument("--raw", action="store_true", help="the canon set as RAW frames")
    ap.add_argument("--mkcr2", default=str(MKCR2))
    a = ap.parse_args()
    try:
        record = Record(a.record)
        if not record.made_up:
            raise Bad(f"{a.record}: not a made-up paired shot (\"made up: yes\"). Its pictures are shot, not drawn")
        made = render(record, a.out, mkcr2=a.mkcr2 if a.raw else None)
    except Bad as e:
        sys.exit(f"madeup: {e}")
    for name, where in made.items():
        print(f"{where}: {len(record.charts())} frames, " + (
            ("the chart as RAW frames" if a.raw else "the chart printed plainly") if name == "canon"
            else "the made-up film, every frame levelled" if name == "automatic" else "the chart through the made-up film"))


if __name__ == "__main__":
    main()
