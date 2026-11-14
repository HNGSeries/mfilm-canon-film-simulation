#!/usr/bin/env python3
"""The look builder, on made-up paired shots.

    make -C ../filmos/sim out/devtest out/mkcr2 out/FOSFILMS.BIN && python3 buildtest.py

No film has been shot, so the paired shots are drawn (madeup.py): the chart
as a Canon's RAW frames, and as "scans" through a film whose numbers are
known. Checks that buildlook.py

  - builds, from the made-up paired shot, a look that is within the pass
    marks on the held-back frames, with one command, and writes its table
    and its numbers
  - never reads the held-back frames while building: with those scans made
    other pictures it builds the same two tables, byte for byte, and
    reports the look as not measured, though it fits what it was built from
  - drops the correction when it does not help on the held-back frames, and
    keeps it for a film the model's shape cannot make
  - builds a black-and-white film stock's look: one mix to grey, one curve
  - and that tools/gentables.py bakes a film stock's table from the look of
    a paired shot that claims it as measured, and from nowhere else if not

Needs numpy, scipy and Pillow, and the simulator's devtest, mkcr2 and film list.
"""

import copy
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import buildlook  # noqa: E402
import filmshape  # noqa: E402
import madeup  # noqa: E402
import measure  # noqa: E402
from buildlook import Built  # noqa: E402
from measure import BUILT, DECIDES, Record  # noqa: E402

fail = 0


def check(ok, what):
    global fail
    fail |= not ok
    print(f"{'ok   ' if ok else 'FAIL '} {what}")


def main():
    record = Record(madeup.RECORD)
    key = record.fields["film stock"]
    tmp = Path(tempfile.mkdtemp())
    text = madeup.RECORD.read_text(encoding="utf-8")
    shot = tmp / "shot"

    def changed(name, *pairs):
        t = text
        for old, new in pairs:
            assert old in t, old
            t = t.replace(old, new)
        (tmp / name).mkdir(exist_ok=True)
        (tmp / name / "record.txt").write_text(t, encoding="utf-8")
        return Record(tmp / name / "record.txt")

    def other_scans(name, look, rec=record):
        """The same RAW frames with the scans through another film: look, or a function of the frame."""
        folder = tmp / name
        folder.mkdir()
        os.symlink(shot / "canon", folder / "canon")
        madeup.render(rec, folder, look=look, sets=["locked", "automatic"])
        return folder

    # ---- one command, on the made-up paired shot
    r = subprocess.run([sys.executable, str(HERE / "buildlook.py"), str(madeup.RECORD), "--files", str(shot), "--out", str(tmp / "out")],
                       capture_output=True, text=True)
    table = tmp / "out" / ("LOOK%02d.LUT" % __import__("gentables").shelf().index(key))
    check(r.returncode == 0 and "Kodak Gold 200: measured" in r.stdout and table.exists() and (tmp / "out/look.txt").exists()
          and not madeup.RECORD.with_name("look.txt").exists(),
          "one command builds the made-up paired shot's look, says it is measured, and writes its table and its numbers "
          "(not beside a made-up record)")
    print("      " + "\n      ".join(r.stdout.splitlines()[1:5]) if r.returncode == 0 else r.stderr)

    b = Built(record, shot, tmp / "again", draw=False)
    g, built = b.distance.decides, b.distance.groups[BUILT]
    check(b.state == "measured" and g.colour.mean < 1 and g.tone.mean < 1 and built.within,
          f"the look it builds: colour {g.colour.mean:.2f} and tone {g.tone.mean:.2f} on the held-back frames, "
          f"{built.colour.mean:.2f} and {built.tone.mean:.2f} on the frames it was built from")
    check(b.table.read_bytes() == table.read_bytes() and filmshape.rising(b.look)
          and np.abs(np.frombuffer(filmshape.bake(filmshape.load(tmp / "out/look.txt")), np.uint8).astype(int)
                     - np.frombuffer(table.read_bytes()[8:], np.uint8)).max() <= 1,
          "built again it is the same table, and the table baked from the written numbers is that table (within one level of 255)")
    plain, bent = (buildlook.score(b.measured[k].distance) for k in ("plain", "bent"))
    check(b.kept == "plain" and "bend" not in b.look and bent > buildlook.KEEP * plain and "the correction is dropped" in b.report(),
          f"the correction does not help here and is dropped: the held-back distance is {plain:.3f} without it, {bent:.3f} with it")

    # ---- the held-back frames are not read while building
    away = copy.deepcopy(madeup.LOOK)
    for c in away["curve"]:
        c["a"] *= 1.3
    away["out"] = [[1.25, -0.17, -0.08], [-0.10, 1.20, -0.10], [-0.05, -0.20, 1.25]]
    built_from = {f.n for f in record.charts(BUILT)}
    w = Built(record, other_scans("wild", lambda f: None if f.n in built_from else away), tmp / "wild-out", draw=False)
    same = all((w.tables[k] / table.name).read_bytes() == (b.tables[k] / table.name).read_bytes() for k in ("plain", "bent"))
    g = w.distance.decides
    check(same, "with every scan but the built-from ones made another film's, it builds the same two tables, byte for byte")
    check(w.distance.groups[BUILT].within and w.distance.within is False and w.state.startswith("not measured: it is within the pass marks on "
                                                                                                  "the frames it was built from")
          and w.state in w.report(),
          f"that look fits what it was built from and not the held-back frames (colour {g.colour.mean:.2f}, tone {g.tone.mean:.2f}): "
          "reported as not measured")

    # ---- a film the model's shape cannot make: the correction earns its place
    n = filmshape.BEND
    grid = np.arange(n) / (n - 1)
    bb, gg, rr = np.meshgrid(grid, grid, grid, indexing="ij")
    twist = 0.25 * np.stack([np.sin(np.pi * gg) * (rr - bb), np.sin(np.pi * rr) * (bb - gg) * 0.8, np.sin(np.pi * bb) * (gg - rr)], -1)
    t = Built(record, other_scans("twisted", dict(madeup.LOOK, bend=twist)), tmp / "twisted-out", draw=False)
    plain, bent = (t.measured[k].distance.decides.colour.mean for k in ("plain", "bent"))
    check(t.kept == "bent" and "bend" in t.look and bent < buildlook.KEEP * plain and "the correction is kept" in t.report()
          and "bend:" in (tmp / "twisted-out/look.txt").read_text(),
          f"for a film with a twist the model cannot make, the correction is kept: colour {plain:.2f} without it, {bent:.2f} with it, "
          "on the held-back frames")

    # ---- a black-and-white film stock
    bw = changed("bw", ("film stock: gold200", "film stock: trix400"))
    k = Built(bw, other_scans("bw-shot", None, bw), tmp / "bw-out", draw=False)
    grey = np.frombuffer(k.table.read_bytes()[8:], np.uint8).reshape(-1, 3)
    g = k.distance.decides
    check(k.state == "measured" and g.colour is None and g.tone.mean < 1 and len(k.look["curve"]) == 1 and "out" not in k.look
          and bool((grey[:, 0] == grey[:, 1]).all() and (grey[:, 1] == grey[:, 2]).all()),
          f"a black-and-white film stock: one mix to grey ({', '.join('%.2f' % v for v in k.look['mix'][0])}; the made-up one: "
          f"{', '.join('%.2f' % v for v in madeup.LOOK_BW['mix'][0])}) and one curve, tone {g.tone.mean:.2f} on the held-back frames, "
          "a grey table")

    # ---- a paired shot that was shot: its look goes beside the record, and onto the shelf once it is claimed
    refs = tmp / "refs"
    for name, claim in (("shot-a", "measured: yes"), ("shot-b", "measured: no")):
        (refs / name).mkdir(parents=True)
        (refs / name / "record.txt").write_text(text.replace("made up: yes", "# made up: yes").replace("measured: no", claim)
                                                .replace("paired shot: made-up", "paired shot: " + name)
                                                .replace("film stock: gold200", "film stock: " + ("gold200" if name == "shot-a" else "portra400")),
                                                encoding="utf-8")
    real = Built(Record(refs / "shot-a/record.txt"), shot, tmp / "real-out", draw=False)
    check((refs / "shot-a/look.txt").exists() and real.written[-1] == refs / "shot-a/look.txt",
          "for a paired shot that is not made up, the look's numbers are written beside its record")
    shutil.copy(refs / "shot-a/look.txt", refs / "shot-b/look.txt")
    cmd = [sys.executable, str(HERE.parent / "filmos/tools/gentables.py"), str(tmp / "tables"), "--films", str(measure.SIM / "FOSFILMS.BIN"),
           "--devtest", str(measure.SIM / "devtest"), "--plain", "--references"]
    r = subprocess.run(cmd + [str(refs)], capture_output=True, text=True)
    index = {line.split()[1]: line for line in (tmp / "tables/TABLES.txt").read_text().splitlines() if line.startswith("LOOK")} \
        if r.returncode == 0 else {}
    baked = filmshape.bake(filmshape.load(refs / "shot-a/look.txt"))
    check(r.returncode == 0 and "reference (shot-a)" in index.get(key, "") and (tmp / "tables" / table.name).read_bytes()[8:] == baked
          and "reference" not in index.get("portra400", "reference") and "1 from references" in r.stdout,
          f"the shelf's table for {key} is baked from the look of the paired shot that claims it as measured; "
          "a film stock whose paired shot does not claim it keeps its own")
    (refs / "shot-a/look.txt").unlink()
    r = subprocess.run(cmd + [str(refs)], capture_output=True, text=True)
    check(r.returncode != 0 and "look.txt" in r.stderr, f"claimed as measured with no look built: the shelf's tables are not made ({r.stderr.strip()[-70:]})")
    r = subprocess.run(cmd + [str(madeup.RECORD.parents[1])], capture_output=True, text=True)
    check(r.returncode == 0 and "from references" not in r.stdout, "the made-up paired shot puts nothing on the shelf")

    shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    sys.path.insert(0, str(HERE.parent / "filmos/tools"))
    main()
