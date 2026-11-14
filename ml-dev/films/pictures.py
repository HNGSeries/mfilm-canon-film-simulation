#!/usr/bin/env python3
"""The film pictures in the docs, made from the sample RAW by the darkroom's own code.

    make -C ../filmos/sim out/devtest && python3 getluts.py     # once
    python3 pictures.py             # make them all again
    python3 pictures.py --check     # are the ones in the repository what today's code makes?
    python3 pictures.py --list      # is there one for every film on the shelf, and no other? (no developing)

Develops sample/SAMPLE.CR2 with every film on the shelf, as the camera's
darkroom would at its Large size (devtest, with the tables tools/gentables.py
makes), and writes

    docs/films/<film>.jpg       900 x 600, the pictures of FILMS.md and of the website
    docs/films/grid.jpg         all of them on one sheet, named
    docs/samples/<film>.jpg     1200 x 800, the nine the READMEs show
    site/img/samples/<film>.jpg the same, for the website's first screen

Run it again whenever the colour changes. It stops if the Film-Luts LUTs have
not been fetched, so a picture never shows a plain print in place of a film's
colour, and if FILMS.md does not list exactly the films on the shelf.

--check develops into a scratch folder and compares: a picture more than
CLOSE levels (of 255) from the one in the repository, on average, is named.
Not byte for byte: a JPEG depends on the library that wrote it.

Needs numpy and Pillow, and gcc's devtest (see above).
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOOLS = HERE.parent / "filmos/tools"
sys.path.insert(0, str(TOOLS))
import gentables  # noqa: E402
from genfilms import FILMS, GROUP  # noqa: E402

SAMPLES = ["portra400", "gold200", "ektar100", "superia400", "velvia50", "kodachrome64", "cinestill800t", "pro400h", "trix400"]
SITE = ["portra400", "gold200", "ektar100", "superia400", "velvia50", "kodachrome64", "cinestill800t", "trix400"]
SHELVES = ["COLOUR", "SLIDE", "B&W", "CINE"]
CLOSE = 2.0


def listed():
    """What is wrong with the pictures and pages as they stand: a list of complaints."""
    keys = gentables.shelf()
    bad = []
    have = {p.stem for p in (ROOT / "docs/films").glob("*.jpg")} - {"grid"}
    if have - set(keys):
        bad.append("docs/films has pictures of films that are not on the shelf: " + ", ".join(sorted(have - set(keys))))
    if set(keys) - have:
        bad.append("docs/films has no picture of: " + ", ".join(sorted(set(keys) - have)))
    page = set(re.findall(r'docs/films/([\w-]+)\.jpg">', (ROOT / "FILMS.md").read_text(encoding="utf-8")))
    if page != set(keys):
        bad.append("FILMS.md and the shelf differ: " + ", ".join(sorted(page ^ set(keys))))
    for name in ("README.md", "README.th.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        for key in re.findall(r'docs/(?:samples|films)/([\w-]+)\.jpg', text):
            if not (ROOT / "docs/samples" / (key + ".jpg")).exists() and not (ROOT / "docs/films" / (key + ".jpg")).exists():
                bad.append(f"{name} shows docs/.../{key}.jpg, which is not there")
    for key in SAMPLES:
        if not (ROOT / "docs/samples" / (key + ".jpg")).exists():
            bad.append(f"docs/samples has no {key}.jpg")
    return keys, bad


def develop(devtest, tmp, keys):
    """Every film's Large print of the sample RAW, as Pillow images, in shelf order."""
    from PIL import Image
    tmp = Path(tmp)
    films = tmp / "FOSFILMS.BIN"
    for cmd in ([sys.executable, str(TOOLS / "genfilms.py"), str(films)],
                [sys.executable, str(TOOLS / "gentables.py"), str(tmp / "T"), "--films", str(films), "--devtest", str(devtest)]):
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            sys.exit((r.stderr or r.stdout).strip())
    # beside a link to the frame, by short names: the darkroom keeps paths in 128 bytes, as on a card
    os.symlink(HERE / "sample/SAMPLE.CR2", tmp / "frame.CR2")
    out = []
    for key in keys:
        r = subprocess.run([str(devtest), "-f", key, "frame.CR2", "o.fop"], cwd=tmp, capture_output=True, text=True,
                           env=dict(os.environ, FOS_FILMS="FOSFILMS.BIN", FOS_LUT_DIR="T", FOS_SIZE="2", FOS_JPEG=key + ".jpg"))
        if r.returncode or not (tmp / (key + ".jpg")).exists():
            sys.exit(f"pictures: devtest did not develop {key}:\n{r.stderr.strip()}")
        im = Image.open(tmp / (key + ".jpg")).convert("RGB")
        im.load()
        out.append(im)
    return out


def grid(keys, prints):
    """All the films on one sheet, eight across, each with its name, maker and shelf."""
    from PIL import Image, ImageDraw, ImageFont
    fonts = HERE.parent / "filmos/fonts"
    big, small = ImageFont.truetype(str(fonts / "Barlow-SemiBold.ttf"), 15), ImageFont.truetype(str(fonts / "Barlow-Medium.ttf"), 10)
    cols, w, h, gap, band = 8, 300, 200, 6, 40
    rows = (len(keys) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (w + gap) + gap, rows * (h + band + gap) + gap), (14, 13, 12))
    d = ImageDraw.Draw(sheet)
    for i, (key, im) in enumerate(zip(keys, prints)):
        x, y = gap + (i % cols) * (w + gap), gap + (i // cols) * (h + band + gap)
        sheet.paste(im.resize((w, h), Image.LANCZOS), (x, y))
        brand, name = FILMS[key]["name"].split(" ", 1)
        d.text((x + 4, y + h + 9), name, font=big, fill=(236, 232, 226))
        d.text((x + 8 + d.textlength(name, font=big), y + h + 14), f"{brand.upper()} · {SHELVES[GROUP[FILMS[key]['kind']]]}", font=small,
               fill=(150, 144, 136))
    return sheet


def write(dest, keys, prints):
    """The pictures into dest/docs/films, dest/docs/samples and dest/site/img/samples; the files written."""
    from PIL import Image
    made = []
    by = dict(zip(keys, prints))
    for sub, names, size, quality in (("docs/films", keys, (900, 600), 86), ("docs/samples", SAMPLES, (1200, 800), 88),
                                      ("site/img/samples", SITE, (1200, 800), 88)):
        (dest / sub).mkdir(parents=True, exist_ok=True)
        for key in names:
            p = dest / sub / (key + ".jpg")
            by[key].resize(size, Image.LANCZOS).save(p, quality=quality, optimize=True, progressive=True)
            made.append(p)
    p = dest / "docs/films/grid.jpg"
    grid(keys, prints).save(p, quality=86, optimize=True, progressive=True)
    made.append(p)
    return made


def main():
    ap = argparse.ArgumentParser(description="The film pictures in the docs, from the sample RAW.")
    ap.add_argument("--devtest", default=str(HERE.parent / "filmos/sim/out/devtest"))
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    keys, bad = listed()
    if a.list:
        if bad:
            sys.exit("pictures:\n  " + "\n  ".join(bad))
        print(f"pictures: one for each of the {len(keys)} films on the shelf, and FILMS.md lists the same films")
        return
    page = set(re.findall(r'docs/films/([\w-]+)\.jpg">', (ROOT / "FILMS.md").read_text(encoding="utf-8")))
    if page != set(keys):
        sys.exit("pictures: FILMS.md and the shelf differ, put that right first: " + ", ".join(sorted(page ^ set(keys))))
    if not Path(a.devtest).exists():
        sys.exit(f"pictures: no {a.devtest}: make -C ml-dev/filmos/sim out/devtest")
    import numpy as np
    from PIL import Image
    with tempfile.TemporaryDirectory() as tmp:
        prints = develop(Path(a.devtest).resolve(), tmp, keys)
        if a.check:
            far = []
            for p in write(Path(tmp) / "new", keys, prints):
                rel = p.relative_to(Path(tmp) / "new")
                old = ROOT / rel
                if not old.exists():
                    far.append(f"{rel}: not in the repository")
                    continue
                a_, b_ = Image.open(old).convert("RGB"), Image.open(p).convert("RGB")
                if a_.size != b_.size:
                    far.append(f"{rel}: {a_.size[0]} x {a_.size[1]} in the repository, {b_.size[0]} x {b_.size[1]} now")
                    continue
                apart = float(np.abs(np.asarray(a_, np.int16) - np.asarray(b_, np.int16)).mean())
                if apart > CLOSE:
                    far.append(f"{rel}: {apart:.1f} levels from what today's code makes")
            if far or bad:
                sys.exit("pictures: not what today's code makes (run pictures.py):\n  " + "\n  ".join(bad + far))
            print(f"pictures: all {len(keys)} films' pictures are what today's code makes (within {CLOSE} levels)")
            return
        made = write(ROOT, keys, prints)
    for p in (ROOT / "docs/films").glob("*.jpg"):
        if p.stem != "grid" and p.stem not in keys:
            p.unlink()
            print(f"pictures: removed {p.relative_to(ROOT)} (not on the shelf)")
    print(f"pictures: {len(made)} files for {len(keys)} films, {sum(p.stat().st_size for p in made) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
