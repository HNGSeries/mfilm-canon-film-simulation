"""Every film stock's colour table, as files: the one place they are made.

    python3 gentables.py OUT --films FOSFILMS.BIN [--devtest PATH] [--plain] [--index FILE]

OUT gets LOOKnn.LUT for every film stock on the shelf, nn its place on it:
what the camera's card carries in ML/DARKROOM and what the desktop darkroom
reads, the same bytes in both, so the two give the same colour (#124). The
camera makes no table of its own and stops with "no colour table" if one is
missing.

A table is "FOL1", a hash of the film stock's look, then 33 x 33 x 33 RGB
bytes over Cineon code, red changing fastest. It comes from one of two
places:

  look  mixed from the film stock's look by the camera's own film model,
        built for a computer (devtest -T: fos_dev_table in fos_dev.c)
  lut   baked from the film stock's LUT in films/luts/ (genfilms.bake);
        films/getluts.py fetches the Film-Luts ones

--films    the film list devtest reads (tools/genfilms.py writes it)
--devtest  the build's devtest (default: sim/out/devtest)
--plain    a Film-Luts film stock whose LUT has not been fetched keeps the
           table mixed from its look, with a warning. Without it that is an
           error: a release must not ship a plain print in place of a film's
           colour. (A film stock that names a LUT of your own which is not in
           films/luts/, as CineStill 400T does, always falls back to its look.)
--index    where the list of tables goes (default: OUT/TABLES.txt): file,
           film stock, where it came from, SHA-256

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

SIZE = 8 + GRID ** 3 * 3


def shelf():
    """The film stocks in shelf order: the built-in ones, then the rest."""
    built = genfilms.builtin_keys()
    return built + [k for k in FILMS if k not in built]


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
    index.write_text("# file, film stock, made from, SHA-256 (tools/gentables.py)\n" + "\n".join(lines) + "\n")
    n_lut = sum(1 for k in keys if source[k] == "lut")
    print("%s: %d tables, %d from LUTs, %d from looks; list in %s" % (a.out, len(keys), n_lut, len(keys) - n_lut, index))


if __name__ == "__main__":
    main()
