#!/usr/bin/env python3
"""The develop half of the measuring command, on the made-up paired shot.

    make -C ../filmos/sim out/devtest out/mkcr2 out/FOSFILMS.BIN && python3 looktest.py

No film has been shot, so the paired shot is drawn (madeup.py): the chart as
a Canon's RAW frames, and as "scans" through a made-up film. The darkroom
develops the frames with a table of that same film, so it has to land on the
scans; with a table of another film of the same shape it has to land as far
away as that film is, which is worked out here with no picture. Checks:

  - devtest holds a scanner exposure given from outside, and without one
    picks its own as before
  - the made-up look against its own scans: within the pass marks
  - another look: the distance worked out, and outside the pass marks
  - patches the sensor clipped are left out, though their print is not white
  - a film stock claimed as measured and outside a pass mark fails the
    command; one that is not claimed does not
  - a paired shot's files: a wrong checksum stops it, a missing file is
    fetched, a scan's patches kept as a file stand in for the scan
  - the darkroom's own exposure against the automatic scan is printed, and
    decides nothing

Needs numpy and Pillow, and the simulator's devtest, mkcr2 and film list.
"""

import copy
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import madeup  # noqa: E402
import measure  # noqa: E402
from measure import BUILT, DECIDES, MID_GREY, Bad, Distance, Look, Reading, Record  # noqa: E402

CLOSE = 0.75        # how far the darkroom's numbers may be from the ones worked out: it prints at 8 bits, through a
                    # table of 33 points a side, with the film stock's grain, glow and vignette on, as people get it

fail = 0


def check(ok, what):
    global fail
    fail |= not ok
    print(f"{'ok   ' if ok else 'FAIL '} {what}")


def refused(what, fn, *words):
    try:
        fn()
    except Bad as e:
        check(all(w in str(e) for w in words), f"{what}: \"{str(e)[-150:]}\"")
    else:
        check(False, f"{what}: not refused")


def numbers(g):
    return [x for n in (g.colour, g.tone) if n is not None for x in (n.mean,)]


def main():
    record = Record(madeup.RECORD)
    key = record.fields["film stock"]
    tmp = Path(tempfile.mkdtemp())
    text = madeup.RECORD.read_text(encoding="utf-8")
    cmd = [sys.executable, str(HERE / "measure.py"), "look"]

    # ---- the made-up look against its own scans
    files = tmp / "made-up"
    look = Look(record, files)
    g = look.distance.decides
    check(look.distance.within is True and g.colour.mean < 1 and g.tone.mean < 1,
          f"the darkroom with the made-up film's table against the made-up film's scans: colour {g.colour.mean:.2f}, "
          f"tone {g.tone.mean:.2f}, within the pass marks")
    check(abs(look.held - np.log2(11552 / (1400 / 0.18))) < 0.1 and abs(look.canon[look.at.n].lab[MID_GREY, 0]
                                                                         - madeup.reading(record, "locked", look.at).lab[MID_GREY, 0]) < 0.5,
          f"the scanner's exposure is set on frame {look.at.n}'s mid-grey patch: {look.held:+.2f} stops "
          "(the made-up sensor puts mid grey 0.57 stops under the table's)")

    # ---- devtest holds an exposure given from outside
    def develop(n, ev=None):
        env = dict(os.environ, FOS_FILMS=str(measure.SIM / "FOSFILMS.BIN"), FOS_MIX="1")
        env.pop("FOS_EV", None)
        if ev is not None:
            env["FOS_EV"] = str(ev)
        shutil.copy(files / "canon" / ("%02d.CR2" % n), tmp / "f.CR2")
        r = subprocess.run([str(measure.SIM / "devtest"), "-f", key, "f.CR2", "o.fop"], cwd=tmp, env=env, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        own = float(re.search(r"scanner: key [\d.]+, (-?[\d.]+) EV", r.stderr).group(1))
        return int(re.search(r"film: \w+, mul (\d+)", r.stderr).group(1)), own, "scanner: held" in r.stderr

    dark, light = develop(2), develop(6)                    # the chart at −3 and at +2
    offset = record.film["ev"]
    check(not dark[2] and not light[2] and dark[1] > light[1] + 3
          and all(abs(m - 4096 * 2 ** (own + offset)) < 8 for m, own, _ in (dark, light)),
          f"with no exposure given the scanner picks its own for each frame, as before: {dark[1]:+.2f} and {light[1]:+.2f} stops")
    dark, light = develop(2, 1.25), develop(6, 1.25)
    check(dark[2] and light[2] and dark[0] == light[0] == int(4096 * 2 ** 1.25 + 0.5),
          f"given 1.25 stops it holds them for both frames: the picture times {dark[0] / 4096:.3f}")

    # ---- what the sensor clipped
    cut = {f.ev: int(look.canon[f.n].cut.sum()) for f in record.charts() if "main light" in f.shows}
    printed = max(float(look.canon[f.n].coded[look.canon[f.n].cut].max()) for f in record.charts() if look.canon[f.n].cut.any())
    check(all(cut[e] == 0 for e in (-3, -2, -1, 0)) and 0 < cut[1] < cut[2] < cut[3] < cut[4] and cut[4] >= 22 and printed < measure.BLOWN
          and g.blown >= cut[1] + cut[3],
          f"patches the sensor clipped are left out as blown: {cut[1]}, {cut[2]}, {cut[3]} and {cut[4]} of 24 at +1 to +4, none at 0 "
          f"and under, though the lightest of them is printed at {printed:.2f}, not white")

    # ---- another look of the same shape: the distance worked out
    other = copy.deepcopy(madeup.LOOK)
    for c in other["curve"]:
        c["a"] *= 1.3
    other["curve"][2]["mid"] = 0.49
    other["out"] = [[1.25, -0.17, -0.08], [-0.10, 1.20, -0.10], [-0.05, -0.20, 1.25]]
    tables = madeup.table(record, tmp / "T", other)
    far = Look(record, files, tables=tables)

    def through(frame, stops):
        return Reading.of_coded(madeup.film(madeup.scene(frame)[0] * 2.0 ** stops, other))

    lo, hi = -4.0, 4.0                                      # the exposure that puts its mid grey where the scan's is
    want = madeup.reading(record, "locked", far.at).lab[MID_GREY, 0]
    for _ in range(30):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if through(far.at, mid).lab[MID_GREY, 0] < want else (lo, mid)
    worked = {}
    for f in record.charts():
        worked[f.n] = through(f, lo)
        worked[f.n].cut = far.canon[f.n].cut
    worked = Distance(record, worked, {f.n: madeup.reading(record, "locked", f) for f in record.charts()})
    apart = max(abs(a - b) for u in (DECIDES, BUILT) for a, b in zip(numbers(far.distance.groups[u]), numbers(worked.groups[u])))
    g, w = far.distance.decides, worked.decides
    check(apart <= CLOSE and far.distance.within is False and w.colour.mean > measure.PASS["colour"],
          f"the darkroom with another film's table: colour {g.colour.mean:.2f} and tone {g.tone.mean:.2f} "
          f"(worked out: {w.colour.mean:.2f} and {w.tone.mean:.2f}; within {apart:.2f}, limit {CLOSE}), outside the pass marks")

    # ---- claimed or not
    def changed(name, *pairs):
        t = text
        for old, new in pairs:
            assert old in t, old
            t = t.replace(old, new)
        (tmp / name).mkdir(exist_ok=True)
        (tmp / name / "record.txt").write_text(t, encoding="utf-8")
        return tmp / name / "record.txt"

    claimed = changed("claimed", ("measured: no", "measured: yes"))
    runs = {what: subprocess.run(cmd + [str(rec), "--files", str(tmp / "runs")] + (["--tables", str(tables)] if pushed else []),
                                 capture_output=True, text=True)
            for what, rec, pushed in (("claimed, outside", claimed, True), ("claimed, within", claimed, False),
                                      ("not claimed, outside", madeup.RECORD, True))}
    r = runs["claimed, outside"]
    check(r.returncode == 1 and "claimed as measured, and OUTSIDE the pass marks: FAILS" in r.stdout and "Kodak Gold 200" in r.stderr,
          f"a film stock claimed as measured and pushed outside a pass mark fails the command: {r.stderr.strip()}")
    r = runs["claimed, within"]
    check(r.returncode == 0 and "claimed as measured, and within the pass marks" in r.stdout, "claimed and within: it passes")
    r = runs["not claimed, outside"]
    check(r.returncode == 0 and "not measured yet (OUTSIDE the pass marks, and not claimed)" in r.stdout,
          "the same look not claimed: reported, and the command passes")
    check("the darkroom's own exposure against the automatic scan" in r.stdout and "this decides nothing" in r.stdout
          and look.automatic is not None and look.automatic.decides.tone.n > 0,
          "the paired shot has an automatic scan: the darkroom's own exposure is held against it, printed apart, deciding nothing")
    bare = Look(Record(changed("bare", ("chart in automatic:", "# chart in automatic:"))), tmp / "bare-files")
    check(bare.automatic is None and "automatic" not in bare.report(), "a paired shot with no automatic scan: nothing is said of one")

    # ---- a paired shot that was shot: its files
    shot = tmp / "shot"
    shutil.copytree(files, shot)
    names = sorted(str(p.relative_to(shot)) for p in shot.glob("*/*"))
    lines = "".join(f"file {n}: {measure.checksum(shot / n)}\n" for n in names)
    own = madeup.table(record, tmp / "own")

    def real(name, more=""):
        return Record(changed(name, ("made up: yes", "# made up: yes"), ("measured: no", "measured: no\n" + lines + more)))

    r = Look(real("real"), shot, tables=own)
    check(len(names) == 36 and numbers(r.distance.decides) == numbers(look.distance.decides),
          f"a record that names its {len(names)} files and their checksums: the same numbers from the same files")
    with open(shot / "locked/05.tif", "ab") as f:
        f.write(b"\0")
    refused("a scan that is not the file the record names", lambda: Look(real("real"), shot, tables=own), "locked/05.tif", "sha256")
    shutil.copy(files / "locked/05.tif", shot / "locked/05.tif")
    published = tmp / "published"
    published.mkdir()
    (shot / "canon/04.CR2").rename(published / "canon-04.CR2")
    refused("a file that is missing, with nowhere to fetch it from", lambda: Look(real("real"), shot, tables=own), "canon/04.CR2", "files at")
    r = Look(real("real", f"files at: {published.as_uri()}\n"), shot, tables=own)
    check((shot / "canon/04.CR2").exists() and numbers(r.distance.decides) == numbers(look.distance.decides),
          "a missing frame is fetched from where the record says the files are published, and checked")
    (published / "canon-04.CR2").write_bytes(b"not the frame")
    (shot / "canon/04.CR2").unlink()
    refused("a fetched file that is not the one named", lambda: Look(real("real", f"files at: {published.as_uri()}\n"), shot, tables=own),
            "canon/04.CR2", "sha256")
    shutil.copy(files / "canon/04.CR2", shot / "canon/04.CR2")

    # ---- a scan's patches kept as a file
    kept = real("kept")
    read = subprocess.run([sys.executable, str(HERE / "measure.py"), "read", str(kept.path), f"locked={shot / 'locked'}"],
                          capture_output=True, text=True)
    back = measure.load_readings(kept.path.with_name("locked.txt")) if read.returncode == 0 else {}
    scans = measure.read_set(kept, "locked", shot / "locked")
    check(sorted(back) == sorted(scans) and all(np.abs(back[n].lab - scans[n].lab).max() < 1e-3 for n in back),
          f"read writes a scan's patches beside the record ({read.stdout.strip()[-40:]}), and they read back the same")
    shutil.rmtree(shot / "locked")
    r = Look(Record(kept.path), shot, tables=own)
    check(max(abs(a - b) for a, b in zip(numbers(r.distance.decides), numbers(look.distance.decides))) < 0.01,
          "with the patches kept, the scan's pictures are not needed: the same numbers without them")

    shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
