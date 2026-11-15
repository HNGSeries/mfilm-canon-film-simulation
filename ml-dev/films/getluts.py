"""Fetch the Film-Luts LUTs the films in filmluts.py use, into luts/filmluts/.

    python getluts.py               # once
    python getluts.py --from ~/Film-Luts      # from a clone you already have
    python getluts.py --check       # are the ones in luts/filmluts/ all there, and the pinned ones? (no fetching)
    python getluts.py --pin         # after changing COMMIT in filmluts.py: fetch, and write filmluts.sha256 again

Downloads the collection (about 40 MB) at the one commit filmluts.py names
(COMMIT) and keeps only the LUTs a film names. Whichever way they come,
each is checked against its SHA-256 in filmluts.sha256 before anything is
written: a LUT that differs or is missing is named, and nothing is kept
(#102). So the same M-Film source always bakes the same tables.

They are not part of this repository. The ones M-Film uses are Pat
David's, CC BY-SA 4.0 (THIRD_PARTY.md); Film-Luts is an export of G'MIC's
copy of them, and its maintainer does not claim to own them.
"""

import argparse
import hashlib
import io
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import filmluts
from filmluts import COMMIT, DIR, REPO, SUMS, ZIP

HERE = Path(__file__).resolve().parent


def download(url):
    # curl first: Python from python.org on a Mac often can't check
    # certificates until "Install Certificates.command" has been run
    if shutil.which("curl"):
        r = subprocess.run(["curl", "-fsSL", url], capture_output=True)
        if r.returncode == 0:
            return r.stdout
    with urllib.request.urlopen(url) as resp:
        return resp.read()


def from_zip(want):
    """{path in the repository: bytes} for the wanted LUTs, from GitHub's zip of COMMIT."""
    data = zipfile.ZipFile(io.BytesIO(download(ZIP)))
    out = {}
    for name in data.namelist():
        rel = name.split("/", 1)[1] if "/" in name else name     # drop "Film-Luts-<commit>/"
        if rel in want:
            out[rel] = data.read(name)
    return out


def from_dir(root, want):
    root = Path(root).expanduser()
    return {rel: (root / rel).read_bytes() for rel in want if (root / rel).is_file()}


def from_git(want):
    """The same from a clone of COMMIT alone."""
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["git", "init", "-q", tmp], check=True)
        subprocess.run(["git", "-C", tmp, "fetch", "-q", "--depth", "1", REPO, COMMIT], check=True)
        subprocess.run(["git", "-C", tmp, "checkout", "-q", "FETCH_HEAD"], check=True)
        return from_dir(tmp, want)


def wrong(files, want):
    """Why these are not the LUTs to bake from: the ones that are not COMMIT's, and the ones not there."""
    return filmluts.not_pinned(files) + [f"{rel}: missing" for rel in sorted(want - set(files))]


def stop(what, problems):
    print(f"getluts: {what}:")
    for p in problems:
        print("  " + p)
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description="Fetch the Film-Luts LUTs the lab's films use.")
    ap.add_argument("--from", dest="src", help="a Film-Luts clone already on this computer")
    ap.add_argument("--check", nargs="?", const="", metavar="DIR",
                    help="fetch nothing: check the LUTs in DIR (luts/filmluts) against filmluts.sha256")
    ap.add_argument("--pin", action="store_true", help=f"write {SUMS} from what is fetched (after changing COMMIT)")
    a = ap.parse_args()
    dest = HERE / "luts" / DIR
    want = filmluts.wanted()
    if a.check is not None:
        folder = Path(a.check) if a.check else dest
        problems = wrong(filmluts.fetched(folder), want)
        if problems:
            stop(f"{folder} does not hold the LUTs of Film-Luts at {COMMIT[:12]} (getluts.py fetches them)", problems)
        print(f"{len(want)} LUTs in {folder}, as Film-Luts has them at {COMMIT[:12]}")
        return
    if a.src:
        files = from_dir(a.src, want)
    else:
        print(f"downloading {REPO} at {COMMIT[:12]} ...")
        try:
            files = from_zip(want)
        except Exception as e:                   # no zip: try git
            print(f"  zip download failed ({e}); trying git clone")
            files = from_git(want)
    if a.pin:
        if want - set(files):
            stop("not written: the collection at this commit lacks", sorted(want - set(files)))
        lines = [f"{hashlib.sha256(files[rel]).hexdigest()}  {rel}" for rel in sorted(files)]
        (HERE / SUMS).write_text(
            f"# SHA-256 of the Film-Luts LUTs the film stocks use, at {REPO}/tree/{COMMIT}\n"
            "# (getluts.py --pin writes this; getluts.py and tools/gentables.py check against it)\n"
            + "\n".join(lines) + "\n", encoding="ascii", newline="\n")
        print(f"{len(lines)} LUTs pinned in {SUMS}")
    else:
        problems = wrong(files, want)
        if problems:
            stop(f"nothing kept: these are not the LUTs of Film-Luts at {COMMIT[:12]}", problems)
    for rel, data in files.items():
        dst = dest / rel[len("luts/"):]
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
    print(f"{len(files)} of {len(want)} LUTs -> {dest}")


if __name__ == "__main__":
    main()
