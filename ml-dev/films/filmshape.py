"""A look of the shape film has: what a measured film stock's table is baked from (#119).

    scene light (0.18 = mid grey)
      -> mix      three colours to the film's three layers (3 x 3, each row adds up to 1)
      -> curve    a tone curve for each layer, with a toe and a shoulder
      -> out      the print's three colours to sRGB's, as light (3 x 3, rows add up to 1)
      -> sRGB
      -> bend     a small smooth correction on top, 5 points a side (optional)

For a black-and-white film stock: one mix of the three colours into grey
and one curve.

A curve gives the print's value, 0..1 as sRGB codes it, from s, the stops
from mid grey:

    lo + (hi - lo) / (1 + exp(-(c0 + a s + b s^2 + c s^3)))

lo and hi are the darkest and lightest the print gets; a is the contrast; b
bends the toe against the shoulder and c tightens both (b^2 < 3 a c keeps
it rising everywhere). "mid" is the value at mid grey, from which c0 comes.

A look is a dict: mix, curve (a list of dicts: mid, a, b, c, lo, hi), out
(not for black-and-white), bend (5 x 5 x 5 x 3, added to the sRGB values;
its points are spread evenly over Cineon code, red first). buildlook.py
fits one to a paired shot, madeup.py has a made-up one, tools/gentables.py
bakes one into a table file.

Needs numpy.
"""

import re
from pathlib import Path

import numpy as np

import lut

GRID = 33               # a table's points a side (genfilms.GRID)
BEND = 5                # the correction's
CURVE = ("mid", "a", "b", "c", "lo", "hi")


def to_lin(v):
    v = np.asarray(v, np.float64)
    return np.where(v <= 0.04045, v / 12.92, ((np.maximum(v, 0) + 0.055) / 1.055) ** 2.4)


def to_srgb(lin):
    lin = np.clip(np.asarray(lin, np.float64), 0, 1)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)


def curve(s, c):
    """A tone curve's value at s stops from mid grey."""
    mid = (c["mid"] - c["lo"]) / (c["hi"] - c["lo"])
    z = np.log(mid / (1 - mid)) + c["a"] * s + c["b"] * s ** 2 + c["c"] * s ** 3
    return c["lo"] + (c["hi"] - c["lo"]) / (1 + np.exp(-np.clip(z, -60, 60)))


def bend_at(lin, bend):
    """The correction at some scene light: its 5 x 5 x 5 points, read between as a table is."""
    p = np.clip(np.asarray(lut.encode(np.asarray(lin, np.float64), "cineon"), np.float64), 0, 1) * (BEND - 1)
    i = np.minimum(p.astype(int), BEND - 2)
    f = p - i
    out = 0
    for corner in range(8):
        d = [(corner >> k) & 1 for k in range(3)]               # red, green, blue
        w = np.prod([f[..., k] if d[k] else 1 - f[..., k] for k in range(3)], 0)
        out = out + w[..., None] * bend[i[..., 2] + d[2], i[..., 1] + d[1], i[..., 0] + d[0]]
    return out


def bend_weights(lin):
    """bend_at as a matrix: a row for each colour of lin, a column for each of the correction's points (red first)."""
    p = np.clip(np.asarray(lut.encode(np.asarray(lin, np.float64), "cineon"), np.float64), 0, 1) * (BEND - 1)
    i = np.minimum(p.astype(int), BEND - 2)
    f = p - i
    w = np.zeros((len(p), BEND ** 3))
    for corner in range(8):
        d = [(corner >> k) & 1 for k in range(3)]
        at = ((i[:, 2] + d[2]) * BEND + i[:, 1] + d[1]) * BEND + i[:, 0] + d[0]
        np.add.at(w, (np.arange(len(p)), at), np.prod([f[:, k] if d[k] else 1 - f[:, k] for k in range(3)], 0))
    return w


def film(lin, look):
    """Scene light (0.18 = mid grey) through the look -> sRGB, 0..1."""
    lin = np.asarray(lin, np.float64)
    m = np.maximum(lin @ np.array(look["mix"], np.float64).T, 1e-9)
    s = np.log2(m / 0.18)
    v = np.stack([curve(s[..., i], c) for i, c in enumerate(look["curve"])], -1)
    v = to_srgb(to_lin(v) @ np.array(look["out"], np.float64).T) if "out" in look else np.repeat(v, 3, -1)
    if look.get("bend") is not None:
        v = v + bend_at(lin, np.asarray(look["bend"], np.float64))
    return np.clip(v, 0, 1)


def bake(look):
    """The look as a table's bytes: 33 x 33 x 33 RGB over Cineon code, red changing fastest (what follows the
    eight bytes of a LOOKnn.LUT's header)."""
    g = np.arange(GRID, dtype=np.float32) / (GRID - 1)
    b, gg, r = np.meshgrid(g, g, g, indexing="ij")
    rgb = film(lut.decode(np.stack([r, gg, b], -1).reshape(-1, 3), "cineon"), look)
    return (rgb * 255 + 0.5).astype(np.uint8).tobytes()


def write_table(key, out, look):
    """The look as the film stock's table file in out/, named and headed as tools/gentables.py's are."""
    import struct
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "filmos/tools"))
    import genfilms
    import gentables
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / ("LOOK%02d.LUT" % gentables.shelf().index(key))
    path.write_bytes(b"FOL1" + struct.pack("<I", genfilms.look_hash(key, genfilms.look_bytes(genfilms.FILMS[key]))) + bake(look))
    return path


def rising(look):
    """Every curve of the look rises everywhere."""
    return all(c["a"] > 0 and c["c"] >= 0 and c["b"] ** 2 < 3 * c["a"] * c["c"] + 1e-12 and c["hi"] > c["lo"] for c in look["curve"])


def save(path, look, about=()):
    """The look as text: the numbers a table is baked from, for the repository."""
    out = ["# " + line for line in about]
    rows = lambda m: "  ".join(" ".join("%.6f" % v for v in row) for row in m)       # noqa: E731
    out.append("mix: " + rows(look["mix"]))
    for c in look["curve"]:
        out.append("curve: " + " ".join("%s %.6f" % (k, c[k]) for k in CURVE))
    if "out" in look:
        out.append("out: " + rows(look["out"]))
    if look.get("bend") is not None:
        out.append("bend: " + " ".join("%.5f" % v for v in np.asarray(look["bend"]).ravel()))
    Path(path).write_text("\n".join(out) + "\n", encoding="utf-8")


def load(path):
    """What save wrote."""
    look = {"curve": []}
    for i, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        key, _, value = line.partition(":")
        try:
            if key == "curve":
                parts = value.split()
                c = dict(zip(parts[0::2], (float(v) for v in parts[1::2])))
                if tuple(c) != CURVE:
                    raise ValueError
                look["curve"].append(c)
            elif key in ("mix", "out"):
                look[key] = np.array([float(v) for v in re.split(r"\s+", value.strip())]).reshape(-1, 3).tolist()
            elif key == "bend":
                look[key] = np.array([float(v) for v in value.split()]).reshape(BEND, BEND, BEND, 3)
            else:
                raise ValueError
        except ValueError:
            raise ValueError(f"{path}:{i}: not a line of a look") from None
    n = len(look["curve"])
    if (n, len(look.get("mix", [])), "out" in look) not in ((3, 3, True), (1, 1, False)) or not rising(look):
        raise ValueError(f"{path}: not a look (three curves with two mixes, or one curve with one, each curve rising)")
    return look
