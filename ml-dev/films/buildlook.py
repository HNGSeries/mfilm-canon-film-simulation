#!/usr/bin/env python3
"""A film stock's look, built from its paired shot.

    make -C ../filmos/sim out/devtest out/mkcr2 out/tables/TABLES.txt
    python3 buildlook.py RECORD [--files DIR] [--out DIR]

Fits a look of the shape film has (filmshape.py) to a paired shot and bakes
it into the film stock's table file (#119, #129):

  1. For every frame the record marks "built from", the chart's patches as
     light, from the Canon's RAW frame as the darkroom has it before the
     scanner and the film stock (devtest), and the same patches in the
     locked scan. A patch the sensor clipped, or that is blown or black in
     the scan, is left out.
  2. The tone curves, from the six grey patches across those frames: one
     curve a colour, each fitted alone.
  3. The two mixes, from all the patches, with the curves held.
  4. A small smooth correction on top (5 points a side), fitted to what is
     left over on the same frames.

That gives two tables: the model alone, and the model with the correction.
Each is then measured with the measuring command (measure.py look), which
develops the frames with it and judges it on the held-back frames. The
correction is kept only if it lowers the distance there by a tenth or more
(KEEP); fitted to twenty-odd colours it can as well fit their noise.

The held-back frames are not opened while building. They only choose
between the two tables and say whether the look is within the pass marks. A
look that fits the frames it was built from and not the held-back ones is
not measured.

Beyond the ends of the bracket the curves go on as their shape takes them.
(A maker's datasheet curve, read into numbers by us, is meant to shape them
there; none has been read yet.)

It writes, into --out (default: filmos/sim/out/references/<name>/built):

    LOOKnn.LUT   the film stock's table, as the camera and Darkrooms read it
    look.txt     the look's numbers, which the table is baked from

and, for a paired shot that was shot, look.txt beside the record as well:
that one belongs in the repository, and tools/gentables.py bakes the film
stock's table from it once the record says "measured: yes".

Needs numpy, scipy and Pillow, and the simulator's devtest.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import filmshape  # noqa: E402
import measure  # noqa: E402
from measure import BUILT, DECIDES, GREYS, MID_GREY, PASS, Bad, Darkroom, Look, Record  # noqa: E402

MID = 0.18                              # where the mid-grey patch of the chart frame at box speed is put: the table's mid grey
LUMA = np.array([0.2126729, 0.7151522, 0.0721750])
KEEP = 0.9                              # the correction stays if the held-back distance with it is this much of the one without, or less
SMOOTH, SMALL = 0.3, 0.03               # the correction: how much its bending and its size count against the fit
FEW = 12                                # fewer grey patches than this cannot give a curve


# ---------------------------------------------------------------- what it is built from

class Patches:
    """The patches a look is built from: light, what the darkroom has of each before the film stock (0.18 = mid
    grey); coded, what the locked scan has, as sRGB; patch, which of the chart's 24 each is; frames and left, how
    many frames they come from and how many patches were left out."""

    def __init__(self, record, files, dark):
        files = Path(files)
        kept = record.path.with_name("locked.txt")
        scans = ({n: r for n, r in measure.load_readings(kept).items() if n in {f.n for f in record.charts(BUILT)}}
                 if kept.exists() else measure.read_set(record, "locked", files / "locked", BUILT))
        frames = [f for f in record.charts(BUILT) if f.n in scans and measure.picture_of(files / "canon", f.n, measure.RAW)]
        at = [f for f in frames if f.ev == 0]
        if not at:
            raise Bad(f"{record.path}: no \"built from\" chart frame at exposure 0 with its RAW file and its locked scan")
        scene = {f.n: dark.scene(measure.picture_of(files / "canon", f.n, measure.RAW), record.corners("canon", f.n)) for f in frames}
        grey = scene[at[0].n][0][MID_GREY] @ LUMA
        if scene[at[0].n][1][MID_GREY] or grey <= 0:
            raise Bad(f"{record.path}: frame {at[0].n}'s mid-grey patch is clipped or black in the RAW frame")
        self.gain = MID / grey
        light, coded, patch = [], [], []
        self.left = 0
        for f in frames:
            keep = ~(scene[f.n][1] | scans[f.n].blown | scans[f.n].black)
            self.left += int((~keep).sum())
            light.append(scene[f.n][0][keep] * self.gain)
            coded.append(scans[f.n].coded[keep])
            patch.append(np.flatnonzero(keep))
        self.light, self.coded, self.patch = np.concatenate(light), np.concatenate(coded), np.concatenate(patch)
        self.frames = frames
        self.grey = np.isin(self.patch, GREYS)
        if self.grey.sum() < FEW:
            raise Bad(f"{record.path}: only {int(self.grey.sum())} grey patches to build the tone curves from")


# ---------------------------------------------------------------- the fit

def _curve(p):
    c0, a, t, c, lo, hi = p
    mid = lo + (hi - lo) / (1 + np.exp(-c0))
    return dict(mid=float(mid), a=float(a), b=float(t * 0.98 * np.sqrt(3 * a * c)), c=float(c), lo=float(lo), hi=float(hi))


# a curve as the fit moves it: where mid grey is, the contrast, the bend as a share of the most that still rises,
# the tightening, the darkest and the lightest
START = [np.log(0.46 / 0.54), 0.6, 0.0, 0.006, 0.02, 0.97]
LOW, HIGH = [-5, 0.05, -0.999, 1e-5, 0.0, 0.6], [5, 3.0, 0.999, 0.2, 0.3, 1.0]


def fit_curve(light, coded):
    """The tone curve through some grey patches: light and what the scan has there, one colour."""
    s = np.log2(np.maximum(light, 1e-9) / 0.18)

    def miss(p):
        # the ends a little towards a usual print's, for a bracket that does not reach them
        return np.concatenate([filmshape.curve(s, _curve(p)) - coded, 0.02 * (p[4:] - START[4:])])

    return _curve(least_squares(miss, START, bounds=(LOW, HIGH)).x)


def _mix(off):
    """A 3 x 3 whose rows add up to 1, from its six other numbers."""
    m = np.zeros((3, 3))
    m[~np.eye(3, dtype=bool)] = off
    m[np.eye(3, dtype=bool)] = 1 - m.sum(1)
    return m


def fit_colour(p):
    """A colour film stock's look from its patches: the curves from the greys, then the two mixes."""
    look = dict(mix=np.eye(3).tolist(), out=np.eye(3).tolist(),
                curve=[fit_curve(p.light[p.grey, c], p.coded[p.grey, c]) for c in range(3)])
    want = measure.lab(measure.to_lin(p.coded))

    def miss(x):
        got = filmshape.film(p.light, dict(look, mix=_mix(x[:6]), out=_mix(x[6:])))
        return (measure.lab(measure.to_lin(got)) - want).ravel()

    x = least_squares(miss, np.zeros(12), bounds=(-0.6, 0.6)).x
    return dict(look, mix=_mix(x[:6]).tolist(), out=_mix(x[6:]).tolist())


def fit_grey(p):
    """A black-and-white film stock's look: one mix to grey and one curve. The curve from the greys, then the mix
    and the curve together, on how light every patch is."""
    grey = p.coded.mean(1)
    curve = fit_curve(p.light[p.grey] @ LUMA, grey[p.grey])
    want = measure.lab(measure.to_lin(np.repeat(grey[:, None], 3, 1)))[:, 0]
    start = np.concatenate([LUMA[[0, 2]], [np.log((curve["mid"] - curve["lo"]) / (curve["hi"] - curve["mid"])), curve["a"],
                                           curve["b"] / (0.98 * np.sqrt(3 * curve["a"] * curve["c"])), curve["c"], curve["lo"], curve["hi"]]])

    def look_of(x):
        return dict(mix=[[float(x[0]), float(1 - x[0] - x[1]), float(x[1])]], curve=[_curve(x[2:])])

    def miss(x):
        return np.concatenate([measure.lab(measure.to_lin(filmshape.film(p.light, look_of(x))))[:, 0] - want, 2 * (x[6:] - START[4:])])

    x = least_squares(miss, np.clip(start, [0, 0] + LOW, [1, 1] + HIGH), bounds=([0, 0] + LOW, [1, 1] + HIGH)).x
    return look_of(x)


def fit_bend(p, look):
    """The correction: 5 x 5 x 5 points over the table's cube, fitted to what the look leaves over on the patches,
    with its bending and its size counted against it so that it stays smooth and small."""
    n = filmshape.BEND
    left = p.coded - filmshape.film(p.light, look)
    w = filmshape.bend_weights(p.light)
    # the second difference along each of the three ways through the cube
    rows = []
    idx = np.arange(n ** 3).reshape(n, n, n)
    for axis in range(3):
        a, b, c = (np.take(idx, range(k, n - 2 + k), axis).ravel() for k in range(3))
        d = np.zeros((len(a), n ** 3))
        d[np.arange(len(a)), a], d[np.arange(len(a)), b], d[np.arange(len(a)), c] = 1, -2, 1
        rows.append(d)
    bendy = np.concatenate(rows)
    lhs = w.T @ w + SMOOTH * bendy.T @ bendy + SMALL * np.eye(n ** 3)
    return np.linalg.solve(lhs, w.T @ left).reshape(n, n, n, 3)


# ---------------------------------------------------------------- building and judging

def score(distance):
    """A look's distance on the held-back frames as one number: colour and tone, each as a share of its pass mark."""
    g = distance.decides
    if g.missing or not g.tone.n or not (distance.tone_only or g.colour.n):
        return float("inf")
    return g.tone.mean / PASS["tone"] + (0 if distance.tone_only else g.colour.mean / PASS["colour"])


def choose(plain, bent):
    """Whether the correction stays: the two looks' distances on the held-back frames."""
    return score(bent) <= KEEP * score(plain)


class Built:
    """A look built from a paired shot. patches, what it was built from; looks and tables, the model alone
    ("plain") and with the correction ("bent"); measured, each as the measuring command has it (a measure.Look);
    kept, which of the two is the film stock's; look, table and distance, that one's."""

    def __init__(self, record, files, out, devtest=None, films=None, mkcr2=None, draw=True):
        self.record, files, out = record, Path(files), Path(out)
        if record.made_up and draw:
            import madeup
            madeup.render(record, files, mkcr2=mkcr2 or madeup.MKCR2)
        elif not record.made_up:
            kept = record.path.with_name("locked.txt").exists()
            measure.fetch_files(record, files, ["canon"] if kept else ["canon", "locked"])
        key = record.fields["film stock"]
        # the frames as light: any table will do to develop with, the light is read before it
        start = filmshape.write_table(key, out / "start", dict(mix=np.eye(3).tolist(), out=np.eye(3).tolist(),
                                                               curve=[_curve(START)] * 3)).parent
        self.patches = p = Patches(record, files, Darkroom(key, devtest, films, start, bare=record.made_up))
        plain = fit_grey(p) if record.tone_only else fit_colour(p)
        self.looks = {"plain": plain, "bent": dict(plain, bend=fit_bend(p, plain))}
        self.tables = {name: filmshape.write_table(key, out / name, look).parent for name, look in self.looks.items()}
        # only now the held-back frames: each table as the measuring command has it
        self.measured = {name: Look(record, files, devtest, films, self.tables[name], draw=False) for name in self.looks}
        self.kept = "bent" if choose(self.measured["plain"].distance, self.measured["bent"].distance) else "plain"
        self.look, self.distance = self.looks[self.kept], self.measured[self.kept].distance
        self.table = filmshape.write_table(key, out, self.look)
        about = [f"The look of {record.film['name']} ({key}), built from the paired shot \"{record.name}\" by films/buildlook.py:",
                 "a mix of the three colours, a tone curve for each, a second mix" + (", and a correction" if self.kept == "bent" else "")
                 + " (filmshape.py). The film stock's table is baked from these numbers."]
        self.written = [out / "look.txt"] + ([] if record.made_up else [record.path.with_name("look.txt")])
        for path in self.written:
            filmshape.save(path, self.look, about)

    @property
    def state(self):
        """"measured" when the held-back frames are within the pass marks; else why not."""
        if self.distance.within:
            return "measured"
        if self.distance.groups[BUILT].within:
            return "not measured: it is within the pass marks on the frames it was built from and not on the held-back ones"
        return "not measured: it is outside the pass marks"

    def report(self):
        r, p = self.record, self.patches
        exposures = ", ".join(measure._ev(f) for f in p.frames)
        out = [f"{r.film['name']} from the paired shot \"{r.name}\"{' (made up)' if r.made_up else ''}",
               f"  built from {len(p.frames)} frames (the chart at {exposures}): {len(p.patch)} patches, {int(p.grey.sum())} of them grey; "
               f"{p.left} left out"]
        for name, label in (("plain", "the model alone"), ("bent", "with the correction")):
            g = self.measured[name].distance.decides
            numbers = f"tone {g.tone.mean:.2f}" if g.tone.n else "nothing to judge"
            if g.colour is not None and g.colour.n:
                numbers = f"colour {g.colour.mean:.2f}, " + numbers
            out.append(f"  {label + ':':21} on the held-back frames {numbers}" + ("   <- kept" if name == self.kept else ""))
        out.append("  the correction is " + ("kept: it lowers the distance on the held-back frames by a tenth or more" if self.kept == "bent"
                                             else "dropped: it does not lower the distance on the held-back frames by a tenth"))
        out.append(self.measured[self.kept].report())
        out.append(f"  {r.film['name']}: {self.state}")
        if self.state == "measured" and not r.made_up and not r.claimed:
            out.append(f"  to claim it, write \"measured: yes\" in {r.path}: the shelf's table is then baked from look.txt, "
                       "and CI holds it to the pass marks")
        out.append(f"  written: {self.table}, {', '.join(str(p) for p in self.written)}")
        return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="A film stock's look, built from its paired shot.")
    ap.add_argument("record")
    ap.add_argument("--files", help="where the paired shot's files are kept (default: filmos/sim/out/references/<name>)")
    ap.add_argument("--out", help="where the table and the look go (default: <files>/built)")
    ap.add_argument("--devtest")
    ap.add_argument("--films")
    ap.add_argument("--mkcr2")
    a = ap.parse_args()
    try:
        record = Record(a.record)
        files = Path(a.files) if a.files else measure.SIM / "references" / record.name
        print(Built(record, files, a.out or files / "built", a.devtest, a.films, a.mkcr2).report())
    except Bad as e:
        sys.exit(f"buildlook: {e}")


if __name__ == "__main__":
    main()
