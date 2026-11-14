"""Every film stock's colour table, as files: the one place they are made.

    python3 gentables.py OUT --films FOSFILMS.BIN [--devtest PATH] [--plain] [--index FILE]

OUT gets LOOKnn.LUT for every film stock on the shelf, nn its place on it:
what the camera's card carries in ML/DARKROOM and what the desktop darkroom
reads, the same bytes in both, so the two give the same colour (#124). The
camera makes no table of its own and stops with "no colour table" if one is
missing.

A table is "FOL1", a hash of the film stock's look, then 33 x 33 x 33 RGB
bytes over Cineon code, red changing fastest. It comes from one of three
places:

  look  mixed from the film stock's look by the camera's own film model,
        built for a computer (devtest -T: fos_dev_table in fos_dev.c)
  lut   baked from the film stock's LUT in films/luts/ (genfilms.bake);
        films/getluts.py fetches the Film-Luts ones
  reference
        baked from the look built from a paired shot of the real film
        (films/buildlook.py wrote it as references/<name>/look.txt), for a
        film stock whose record there says "measured: yes". This is what
        makes a measured film stock's colour the measured one (#119)

--films    the film list devtest reads (tools/genfilms.py writes it)
--devtest  the build's devtest (default: sim/out/devtest)
--plain    a Film-Luts film stock whose LUT has not been fetched keeps the
           table mixed from its look, with a warning. Without it that is an
           error: a release must not ship a plain print in place of a film's
           colour. (A film stock that names a LUT of your own which is not in
           films/luts/, as CineStill 400T does, always falls back to its look.)
--index    where the list of tables goes (default: OUT/TABLES.txt): file,
           film stock, where it came from, SHA-256
--references  the paired shots' records (default: ml-dev/references)

Fails if any film stock ends up without a table, or with one that is not
for its look. Needs numpy (for the LUTs).
"""

import argparse
import hashlib
import os
import struct
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import genfilms  # noqa: E402
from genfilms import FILMS, GRID  # noqa: E402
from filmluts import STOCKS  # noqa: E402  (genfilms put films/ on the path)

FETCHED = {s[0] for s in STOCKS}        # the film stocks whose LUT films/getluts.py fetches
REFERENCES = HERE.parents[1] / "references"

SIZE = 8 + GRID ** 3 * 3


def shelf():
    """The film stocks in shelf order: the built-in ones, then the rest."""
    built = genfilms.builtin_keys()
    return built + [k for k in FILMS if k not in built]


def measured(references):
    """The film stocks a paired shot's record claims as measured: {film stock: (the paired shot, its look)}. A
    made-up paired shot claims nothing, whatever its record says."""
    import filmshape
    import measure
    out = {}
    for path in sorted(Path(references).glob("*/record.txt")):
        try:
            record = measure.Record(path)
            if record.made_up or not record.claimed:
                continue
            key = record.fields["film stock"]
            record.film                 # on the shelf?
            if key in out:
                sys.exit("gentables: two paired shots claim %s as measured: %s and %s. One is its reference" % (key, out[key][0], record.name))
            look = path.with_name("look.txt")
            if not look.exists():
                sys.exit("gentables: %s says %s is measured, and there is no %s (films/buildlook.py writes it)" % (path, key, look))
            out[key] = (record.name, filmshape.load(look))
        except (measure.Bad, ValueError) as e:
            sys.exit("gentables: %s" % e)
    return out


def check(path, key):
    """Why the file is not this film stock's table, or None if it is."""
    if not path.exists():
        return "no table"
    data = path.read_bytes()
    if len(data) != SIZE or data[:4] != b"FOL1":
        return "not a table (%d bytes)" % len(data)
    if struct.unpack_from("<I", data, 4)[0] != genfilms.look_hash(key, genfilms.look_bytes(FILMS[key])):
        return "a table for another look (films.py and the camera's built-in looks disagree?)"
    return None


def main():
    ap = argparse.ArgumentParser(description="Every film stock's colour table, as files.")
    ap.add_argument("out")
    ap.add_argument("--films", required=True)
    ap.add_argument("--devtest", default=str(HERE.parent / "sim/out/devtest"))
    ap.add_argument("--plain", action="store_true")
    ap.add_argument("--index")
    ap.add_argument("--references", default=str(REFERENCES))
    a = ap.parse_args()
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("LOOK*.LUT"):
        old.unlink()
    keys = shelf()
    built = len(genfilms.builtin_keys())

    # every film stock's table from its look. Beside the directory, by its name: the
    # darkroom keeps paths in 128 bytes, as on the camera
    r = subprocess.run([str(Path(a.devtest).resolve()), "-T", out.name], cwd=out.parent, capture_output=True, text=True,
                       env=dict(os.environ, FOS_FILMS=str(Path(a.films).resolve())))
    if r.returncode:
        sys.exit("gentables: devtest -T failed:\n" + (r.stderr or r.stdout).strip())

    # then from its LUT, for the film stocks that have one
    source, unfetched = {}, []
    for i, key in enumerate(keys):
        source[key] = "look"
        if i < built:
            continue
        if genfilms.bake(key, i, out):
            source[key] = "lut"
        elif key in FETCHED:
            unfetched.append(key)
            source[key] = "look (its LUT is not fetched)"
        elif FILMS[key].get("lut"):
            source[key] = "look (its own LUT is not in films/luts/)"
    # and from its reference, for the film stocks that are measured
    import filmshape
    for key, (name, look) in measured(a.references).items():
        filmshape.write_table(key, out, look)
        source[key] = "reference (%s)" % name
        if key in unfetched:
            unfetched.remove(key)
    if unfetched:
        msg = "%d film stocks' LUTs are not in films/luts/filmluts (films/getluts.py fetches them): %s" % (
            len(unfetched), ", ".join(unfetched))
        if not a.plain:
            sys.exit("gentables: " + msg)
        print("gentables: warning: " + msg + ". They get the table mixed from their look.", file=sys.stderr)

    bad, lines = [], []
    for i, key in enumerate(keys):
        path = out / ("LOOK%02d.LUT" % i)
        why = check(path, key)
        if why:
            bad.append("%s (%s): %s" % (path.name, key, why))
            continue
        lines.append("%s  %-16s %-42s %s" % (path.name, key, source[key], hashlib.sha256(path.read_bytes()).hexdigest()))
    if bad:
        sys.exit("gentables: %d of %d film stocks have no usable table:\n  " % (len(bad), len(keys)) + "\n  ".join(bad))
    extra = sorted(p.name for p in out.glob("LOOK*.LUT") if p.name not in {"LOOK%02d.LUT" % i for i in range(len(keys))})
    if extra:
        sys.exit("gentables: tables for film stocks that are not on the shelf: " + ", ".join(extra))
    index = Path(a.index) if a.index else out / "TABLES.txt"
    index.write_text("# file, film stock, made from, SHA-256 (tools/gentables.py)\n"
                     "# \"lut\": adapted from a film emulation table by Pat David, CC BY-SA 4.0, and licensed the same\n"
                     "# (https://creativecommons.org/licenses/by-sa/4.0/). THIRD_PARTY says what was changed.\n"
                     "# \"look\": mixed from M-Film's own film model.\n"
                     "# \"reference\": built from a paired shot of the real film, which the film stock is measured against\n"
                     "# (ml-dev/references).\n" + "\n".join(lines) + "\n")
    n_lut = sum(1 for k in keys if source[k] == "lut")
    n_ref = sum(1 for k in keys if source[k].startswith("reference"))
    print("%s: %d tables, %d from LUTs, %d from looks%s; list in %s" % (
        a.out, len(keys), n_lut, len(keys) - n_lut - n_ref, ", %d from references" % n_ref if n_ref else "", index))


if __name__ == "__main__":
    main()
