#!/usr/bin/env python3
"""The compare half of the measuring command, on pictures whose distance is known.

    python3 measuretest.py

No film has been shot, so this draws its own pictures (madeup.py) and checks
what measure.py reads in them:

  - its dE2000 against the 34 pairs published with the formula (Sharma, Wu
    and Dalal, 2005), so "a known amount" does not rest on this code alone
  - the made-up paired shot's record, and records with something wrong
  - a set against itself: 0 and 0
  - a set against a copy moved by a known amount: that amount. Tone alone
    leaves colour at 0, colour alone leaves tone at 0
  - the made-up paired shot, read from an 8-bit JPEG and a 16-bit TIFF,
    against the same numbers worked out with no picture
  - only the deciding frames are held to the pass marks
  - blown and black patches are left out and counted
  - a black-and-white film stock: tone alone, over all 24 patches
  - the kinds of file, a picture that is not sRGB, pictures of another size

Needs numpy and Pillow.
"""

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
from measure import BUILT, DECIDES, REPORTED, Bad, Distance, Record  # noqa: E402

# L*, a*, b* of the two colours and their dE2000, from the paper's table of test data
SHARMA = [
    (50.0000, 2.6772, -79.7751, 50.0000, 0.0000, -82.7485, 2.0425), (50.0000, 3.1571, -77.2803, 50.0000, 0.0000, -82.7485, 2.8615),
    (50.0000, 2.8361, -74.0200, 50.0000, 0.0000, -82.7485, 3.4412), (50.0000, -1.3802, -84.2814, 50.0000, 0.0000, -82.7485, 1.0000),
    (50.0000, -1.1848, -84.8006, 50.0000, 0.0000, -82.7485, 1.0000), (50.0000, -0.9009, -85.5211, 50.0000, 0.0000, -82.7485, 1.0000),
    (50.0000, 0.0000, 0.0000, 50.0000, -1.0000, 2.0000, 2.3669), (50.0000, -1.0000, 2.0000, 50.0000, 0.0000, 0.0000, 2.3669),
    (50.0000, 2.4900, -0.0010, 50.0000, -2.4900, 0.0009, 7.1792), (50.0000, 2.4900, -0.0010, 50.0000, -2.4900, 0.0010, 7.1792),
    (50.0000, 2.4900, -0.0010, 50.0000, -2.4900, 0.0011, 7.2195), (50.0000, 2.4900, -0.0010, 50.0000, -2.4900, 0.0012, 7.2195),
    (50.0000, -0.0010, 2.4900, 50.0000, 0.0009, -2.4900, 4.8045), (50.0000, -0.0010, 2.4900, 50.0000, 0.0010, -2.4900, 4.8045),
    (50.0000, -0.0010, 2.4900, 50.0000, 0.0011, -2.4900, 4.7461), (50.0000, 2.5000, 0.0000, 50.0000, 0.0000, -2.5000, 4.3065),
    (50.0000, 2.5000, 0.0000, 73.0000, 25.0000, -18.0000, 27.1492), (50.0000, 2.5000, 0.0000, 61.0000, -5.0000, 29.0000, 22.8977),
    (50.0000, 2.5000, 0.0000, 56.0000, -27.0000, -3.0000, 31.9030), (50.0000, 2.5000, 0.0000, 58.0000, 24.0000, 15.0000, 19.4535),
    (50.0000, 2.5000, 0.0000, 50.0000, 3.1736, 0.5854, 1.0000), (50.0000, 2.5000, 0.0000, 50.0000, 3.2972, 0.0000, 1.0000),
    (50.0000, 2.5000, 0.0000, 50.0000, 1.8634, 0.5757, 1.0000), (50.0000, 2.5000, 0.0000, 50.0000, 3.2592, 0.3350, 1.0000),
    (60.2574, -34.0099, 36.2677, 60.4626, -34.1751, 39.4387, 1.2644), (63.0109, -31.0961, -5.8663, 62.8187, -29.7946, -4.0864, 1.2630),
    (61.2901, 3.7196, -5.3901, 61.4292, 2.2480, -4.9620, 1.8731), (35.0831, -44.1164, 3.7933, 35.0232, -40.0716, 1.5901, 1.8645),
    (22.7233, 20.0904, -46.6940, 23.0331, 14.9730, -42.5619, 2.0373), (36.4612, 47.8580, 18.3852, 36.2715, 50.5065, 21.2231, 1.4146),
    (90.8027, -2.0831, 1.4410, 91.1528, -1.6435, 0.0447, 1.4441), (90.9257, -0.5406, -0.9208, 88.6381, -0.8985, -0.7239, 1.5381),
    (6.7747, -0.2908, -2.4247, 5.8714, -0.0985, -2.2286, 0.6377), (2.0776, 0.0795, -1.1350, 0.9033, -0.0636, -0.5514, 0.9082),
]

# how far a number read from a picture may be from the one worked out: at 16 bits, and from an 8-bit JPEG,
# which holds a patch to about one level of 255: up to 1 in CIELAB for a strong colour, less in a mean
TIFF, JPEG = 0.02, 0.5
EIGHT = 0.6                 # one patch's L*, a* or b* from a picture of 8 bits, which rounds it by up to half a level

fail = 0


def check(ok, what):
    global fail
    fail |= not ok
    print(f"{'ok   ' if ok else 'FAIL '} {what}")


def refused(what, fn, *words):
    """fn() has to stop with a Bad that says every one of words."""
    try:
        fn()
    except Bad as e:
        check(all(w in str(e) for w in words), f"{what}: \"{e}\"")
    else:
        check(False, f"{what}: not refused")


def shoot(folder, record, name, values, ext=".tif", size=madeup.SIZE):
    """A set of pictures of the record's chart frames, drawn from values(frame): 24 patches as sRGB."""
    folder.mkdir(parents=True, exist_ok=True)
    for f in record.charts():
        madeup.write(folder / ("%02d%s" % (f.n, ext)), madeup.draw(values(f), 0.46, 0.2, record.corners(name, f.n), size))
    return folder


def numbers(g):
    """A group's numbers in a row, for setting two against each other."""
    return [x for n in (g.colour, g.tone, g.plain) if n is not None for x in (n.mean, n.worst)]


def apart(g, h):
    return float(np.max(np.abs(np.array(numbers(g)) - np.array(numbers(h)))))


def main():
    record = Record(madeup.RECORD)
    tmp = Path(tempfile.mkdtemp())

    # ---- the formula
    d = np.array(SHARMA)
    got = measure.de2000(d[:, 0:3], d[:, 3:6])
    check(float(np.abs(got - d[:, 6]).max()) < 1e-4, f"dE2000 is the published one: all {len(SHARMA)} pairs of the paper's test data")
    same_l = d[:, 0] == d[:, 3]
    check(np.allclose(measure.de2000(d[same_l, 0:3], d[same_l, 3:6], lightness=False), d[same_l, 6], atol=1e-4)
          and bool(np.all(measure.de2000(d[~same_l, 0:3], d[~same_l, 3:6], lightness=False) < got[~same_l])),
          f"with the lightness part left out it is the same for the {int(same_l.sum())} pairs of one lightness, and less for the others")
    lab = measure.lab(measure.to_lin(madeup.CHECKER))
    check(np.allclose(measure.lab(measure.lab_to_lin(lab)), lab, atol=1e-9), "CIELAB and back")

    # ---- the record
    by_use = {use: [f.ev for f in record.charts(use)] for use in (BUILT, DECIDES, REPORTED, measure.HIGH)}
    check(len(record.frames) == 24 and by_use[DECIDES] == [-1, 0.5, 1.5] and sorted(by_use[BUILT]) == [-3, -2, 0, 1, 2]
          and by_use[REPORTED] == [-1, 0, 1] and by_use[measure.HIGH] == [3, 4],
          "the made-up record: 24 frames, built from −3 −2 0 +1 +2, decided by −1 +0.5 +1.5, open shade and +3 +4 reported")
    check(record.made_up and record.fields["measured"] == "no" and not record.tone_only
          and all(record.corners(s, f.n).shape == (4, 2) for s in ("canon", "locked", "automatic") for f in record.charts()),
          "it is made up, claims nothing, and says where the chart is in every chart frame of its three sets")
    text = madeup.RECORD.read_text(encoding="utf-8")

    def changed(old, new, name="record.txt"):
        assert old in text, old
        p = tmp / name
        p.write_text(text.replace(old, new), encoding="utf-8")
        return p

    refused("a record with nothing written for the scanner", lambda: Record(changed("scanner: none, made up", "scanner:")), "scanner")
    refused("a frame used for something else", lambda: Record(changed("| held back, decides\nframe 5", "| held back\nframe 5")), "held back")
    refused("a chart whose points cross", lambda: Record(changed("chart in canon: 0.3675,0.3800 0.6325,0.3800 0.6325,0.6200 0.3675,0.6200",
                                                                   "chart in canon: 0.3675,0.3800 0.6325,0.3800 0.3675,0.6200 0.6325,0.6200")),
            "go round")
    refused("a chart in a frame that shows none", lambda: Record(changed("chart in canon, frame 7:", "chart in canon, frame 11:")), "frame 11")
    refused("a field that is no field", lambda: Record(changed("lab: none", "laboratory: none")), "laboratory")
    refused("a film stock that is not on the shelf", lambda: Record(changed("film stock: gold200", "film stock: gold2000")).tone_only,
            "gold2000")
    refused("a set the record does not have", lambda: record.corners("frontier", 1), "frontier", "canon")

    # ---- the made-up paired shot, from pictures and worked out
    worked = Distance(record, {f.n: madeup.reading(record, "canon", f) for f in record.charts()},
                      {f.n: madeup.reading(record, "locked", f) for f in record.charts()})
    sets = madeup.render(record, tmp / "shot")
    both_tiff = madeup.render(record, tmp / "tiff", {"canon": ".tif"})
    for what, folders, limit in (("an 8-bit JPEG against a 16-bit TIFF", sets, JPEG), ("two 16-bit TIFFs", both_tiff, TIFF)):
        seen = measure.compare(record, "canon", folders["canon"], "locked", folders["locked"])
        far = max(apart(seen.groups[u], worked.groups[u]) for u in measure.CHART_USES)
        # a JPEG may put a patch on the other side of where blown or black begins, if it is within a level and a half of it
        edge = {u: sum(int((np.abs(madeup.reading(record, "canon", f).coded.max(1)[:, None] - [measure.BLOWN, measure.BLACK])
                            < 1.5 / 255).sum()) for f in record.charts(u)) if limit == JPEG else 0 for u in measure.CHART_USES}
        counts = all(abs(seen.groups[u].blown - worked.groups[u].blown) + abs(seen.groups[u].black - worked.groups[u].black) <= edge[u]
                     for u in measure.CHART_USES)
        check(far <= limit and counts, f"the made-up paired shot read from {what}: within {far:.3f} of the numbers worked out "
                                       f"(limit {limit}), " + ("the same patches left out" if limit == TIFF else
                                                               "the same patches left out but for those at the edge of blown"))
    g = worked.decides
    check(worked.within is False and g.colour.mean > measure.PASS["colour"] and g.tone.mean > measure.PASS["tone"],
          f"the made-up film is not a plain print: colour {g.colour.mean:.2f}, tone {g.tone.mean:.2f}, outside the pass marks")
    g = worked.groups[measure.HIGH]
    check(g.blown > 0 and g.colour.n == g.patches - g.blown - g.black and g.tone.n < 12,
          f"{g.blown} blown and {g.black} black of the {g.patches} patches at +3 and +4 are left out of the numbers and counted")

    # ---- against itself
    for name in ("canon", "locked"):
        same = measure.compare(record, name, sets[name], name, sets[name])
        check(all(max(numbers(same.groups[u])) == 0 for u in measure.CHART_USES) and same.within is True,
              f"the {name} set against itself: 0 for colour and tone, within the pass marks")

    # ---- a known amount. A softer chart, so a patch moved is still inside sRGB
    soft = lab * [1, 0.5, 0.5]
    soft[:, 0] = np.clip(soft[:, 0], 25, 85)

    def drawn(name, labs, **how):
        lin = measure.lab_to_lin(np.asarray(labs))
        assert lin.min() > 0.002 and lin.max() < 0.95, (name, lin.min(), lin.max())
        shutil.rmtree(tmp / name, ignore_errors=True)
        return shoot(tmp / name, record, "canon", lambda f: measure.to_srgb(lin), **how)

    base = drawn("soft", soft)
    for what, moved, tone, colour in (("5 L* lighter", soft + [5, 0, 0], 5.0, 0.0), ("3 L* darker", soft - [3, 0, 0], 3.0, 0.0)):
        m = measure.compare(record, "canon", base, "canon", drawn("moved", moved)).decides
        check(abs(m.tone.mean - tone) <= TIFF and abs(m.tone.worst - tone) <= TIFF and m.colour.worst <= TIFF,
              f"a copy {what}: tone {m.tone.mean:.3f}, colour {m.colour.mean:.3f}")
    m = measure.compare(record, "canon", base, "canon", drawn("moved", soft + [5, 0, 0], ext=".jpg")).decides
    check(abs(m.tone.mean - 5) <= JPEG and m.colour.mean <= JPEG, f"the same as an 8-bit JPEG: tone {m.tone.mean:.3f}, colour {m.colour.mean:.3f}")
    moved = soft + [0, 3, -2]
    want = measure.de2000(soft, moved, lightness=False)
    m = measure.compare(record, "canon", base, "canon", drawn("moved", moved)).decides
    check(abs(m.colour.mean - want.mean()) <= TIFF and abs(m.colour.worst - want.max()) <= TIFF and m.tone.worst <= TIFF
          and m.colour.mean > 1,
          f"a copy moved in colour alone (a* +3, b* −2): colour {m.colour.mean:.3f} (worked out: {want.mean():.3f}), tone {m.tone.mean:.3f}")
    pair = SHARMA[20]
    one, other = np.tile(pair[0:3], (24, 1)), np.tile(pair[3:6], (24, 1))
    m = measure.compare(record, "canon", drawn("one", one), "canon", drawn("other", other)).decides
    check(abs(m.colour.mean - pair[6]) <= TIFF and m.tone.worst <= TIFF,
          f"a pair from the paper as two pictures: colour {m.colour.mean:.3f} (published: {pair[6]:.4f}), tone {m.tone.mean:.3f}")

    # ---- only the deciding frames decide
    wild = drawn("wild", soft[::-1])        # every patch another patch's colour
    for use, n, decides in ((REPORTED, 15, False), (BUILT, 6, False), (DECIDES, 5, True)):
        other = tmp / "other"
        shutil.rmtree(other, ignore_errors=True)
        shutil.copytree(base, other)
        shutil.copy(wild / ("%02d.tif" % n), other / ("%02d.tif" % n))
        m = measure.compare(record, "canon", base, "canon", other)
        check(m.groups[use].colour.mean > 3 and (m.within is False) == decides
              and (max(numbers(m.decides)) > 0) == decides,
              f"frame {n} ({use}) made another picture: {use} colour {m.groups[use].colour.mean:.1f}, "
              f"the film stock is {'outside' if m.within is False else 'within'} the pass marks")
    (other / "07.tif").unlink()
    m = measure.compare(record, "canon", base, "canon", other)
    check(m.within is None and "not judged" in measure.report(m, "canon", "canon"), "a deciding frame with no picture: not judged")

    # ---- blown and black
    def with_patch(name, i, value):
        v = measure.to_srgb(measure.lab_to_lin(soft))
        v[i] = value
        return shoot(tmp / name, record, "canon", lambda f: v)

    for what, i, value, blown, black in (("a white patch", 18, 1.0, 3, 0), ("an orange patch with its red at the top", 6, [1.0, 0.5, 0.2], 3, 0),
                                         ("a black patch", 23, 0.004, 0, 3), ("a cyan patch with no red in it", 17, [0.0, 0.5, 0.6], 0, 0)):
        m = measure.compare(record, "canon", base, "canon", with_patch("ends", i, value)).decides
        left = (m.blown, m.black) == (blown, black)
        clean = max(numbers(m)) <= TIFF if blown or black else m.colour.worst > 3
        check(left and clean, f"{what} in one picture: {m.blown} blown and {m.black} black left out of three frames, "
                              + ("the numbers stay 0" if blown or black else f"it is measured ({m.colour.worst:.1f})"))

    # ---- a black-and-white film stock
    bw = Record(changed("film stock: gold200", "film stock: trix400", "bw.txt"))
    bw_sets = madeup.render(bw, tmp / "bw")
    seen = measure.compare(bw, "canon", bw_sets["canon"], "locked", bw_sets["locked"])
    worked_bw = Distance(bw, {f.n: madeup.reading(bw, "canon", f) for f in bw.charts()},
                         {f.n: madeup.reading(bw, "locked", f) for f in bw.charts()})
    g = seen.decides
    check(bw.tone_only and g.colour is None and g.tone.n == g.patches - g.blown - g.black and g.tone.n > 18
          and apart(g, worked_bw.decides) <= JPEG and "held to tone alone" in measure.report(seen, "canon", "locked"),
          f"a black-and-white film stock: tone alone, over all the patches ({g.tone.n} of {g.patches}): {g.tone.mean:.2f}")

    # ---- files
    pic = madeup.draw(*madeup.printed(record, "locked", record.frames[1]), record.corners("locked", 1))
    want = madeup.reading(record, "locked", record.frames[1])
    from PIL import Image, ImageCms
    eight = Image.fromarray(np.rint(pic * 255).astype(np.uint8))
    srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    files = {"16-bit TIFF": (tmp / "a.tif", lambda p: madeup.write_tiff(p, pic), 0.01),
             "16-bit TIFF, the other byte order": (tmp / "b.tif", lambda p: madeup.write_tiff(p, pic, order=">"), 0.01),
             "8-bit TIFF": (tmp / "c.tif", lambda p: madeup.write_tiff(p, pic, bits=8), EIGHT),
             "compressed 8-bit TIFF": (tmp / "d.tif", lambda p: eight.save(p, compression="tiff_lzw"), EIGHT),
             "PNG": (tmp / "e.png", eight.save, EIGHT),
             "JPEG with an sRGB profile": (tmp / "f.jpg", lambda p: eight.save(p, quality=92, icc_profile=srgb), 1.5)}
    for what, (path, save, limit) in files.items():
        save(path)
        got = measure.read_chart(measure.read_picture(path), record.corners("locked", 1))
        far = float(np.abs(got.lab - want.lab).max())
        check(far <= limit, f"reads a {what}: every patch's L*, a* and b* within {far:.3f} (limit {limit})")
    eight.save(tmp / "g.jpg", icc_profile=srgb.replace(b"sRGB", b"aRGB").replace("sRGB".encode("utf-16-be"), "aRGB".encode("utf-16-be")))
    refused("a picture in another colour space", lambda: measure.read_picture(tmp / "g.jpg"), "not sRGB")
    (tmp / "h.tif").write_bytes(b"not a picture")
    refused("a file that is no picture", lambda: measure.read_picture(tmp / "h.tif"), "h.tif")
    names = tmp / "names"
    names.mkdir()
    for n in ("scan-07.tif", "17.tif", "roll7-01.jpg", "notes.txt"):
        (names / n).write_bytes(b"")
    check(measure.picture_of(names, 7).name == "scan-07.tif" and measure.picture_of(names, 1).name == "roll7-01.jpg"
          and measure.picture_of(names, 2) is None, "frame 7's picture is the one whose name ends in 7, not 17 or roll7-01")
    (names / "0007.jpg").write_bytes(b"")
    refused("two pictures of one frame", lambda: measure.picture_of(names, 7), "0007.jpg", "scan-07.tif")
    small = measure.read_chart(measure.read_picture(shoot(tmp / "small", record, "locked", lambda f: madeup.printed(record, "locked", f)[0],
                                                          size=(450, 300)) / "01.tif"), record.corners("locked", 1))
    big = measure.read_chart(measure.read_picture(shoot(tmp / "big", record, "locked", lambda f: madeup.printed(record, "locked", f)[0],
                                                        size=(3000, 2000)) / "01.tif"), record.corners("locked", 1))
    check(float(np.abs(small.lab - want.lab).max()) <= 0.01 and float(np.abs(big.lab - want.lab).max()) <= 0.01,
          "the chart's place holds for a picture of 450 x 300 and of 3000 x 2000")
    refused("a chart too small to read", lambda: measure.read_chart(np.zeros((40, 60, 3)), record.corners("locked", 1)), "too small")

    # ---- the command
    cmd = [sys.executable, str(HERE / "measure.py"), "compare", str(madeup.RECORD)]
    r = subprocess.run(cmd + [f"canon={sets['canon']}", f"locked={sets['locked']}"], capture_output=True, text=True)
    check(r.returncode == 0 and "held back, decides" in r.stdout and "OUTSIDE the pass marks" in r.stdout
          and "grain: not measured" in r.stdout and r.stdout.index("held back, decides") < r.stdout.index("held back, reported"),
          "the command prints the deciding frames first and the others apart, and grain as not measured")
    r = subprocess.run(cmd + [f"canon={sets['canon']}", f"frontier={sets['locked']}"], capture_output=True, text=True)
    check(r.returncode == 1 and "chart in frontier" in r.stderr, f"a set the record does not have stops it: {r.stderr.strip()[:90]}")

    shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
