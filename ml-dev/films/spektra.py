"""Film stocks whose colour comes from spektrafilm, Andrea Volpato's physical film model:
https://github.com/andreavolpato/spektrafilm (its film profiles are CC BY-SA 4.0).

spektrafilm builds a film from the maker's data: each layer's spectral sensitivity, its
characteristic curve, its dyes' spectral density, the couplers between the layers. Light is
turned into a spectrum, exposes the three layers, is developed, printed with an enlarger on a
colour paper (a negative) or scanned as it is (a slide), and scanned. The tables these replace
were looks made by eye (Pat David's, filmluts.py, or M-Film's own for Portra 400, Ektar 100 and
Gold 200); these come from the film's own data. They are still not
measured against the real film: a paired shot is what does that (docs/paired-shot.md).

    python spektra.py            # render every film stock below into spektra/ (needs spektrafilm, at COMMIT)
    python spektra.py --check    # are the files in spektra/ the ones spektra.sha256 names? (no spektrafilm needed)

Rendering needs Python 3.13 with spektrafilm installed from its repository at COMMIT
(pip install -e <clone>; the core needs numpy, scipy, colour-science, numba, opt-einsum, pyfftw,
scikit-image, matplotlib, OpenImageIO, rawpy, exiv2, lensfunpy). The build needs none of that: the rendered tables
are in this repository (spektra/<key>.tab, 33 x 33 x 33 RGB bytes over Cineon code, red changing
fastest, as a LOOKnn.LUT after its header) and tools/gentables.py checks each against
spektra.sha256 before it takes it. The licence asks for its notice, unchanged, and a list of
what was changed to travel with the files: spektra/SPEKTRAFILM_LICENSE.txt and
spektra/CHANGELOG.txt, which this writes.

What spektrafilm is asked for is what its own program does by default, with no spatial effects and
nothing random (its "lut_mode"): a negative printed on Kodak Portra Endura; a slide film scanned
as it is. Grain, halation and softness stay M-Film's (films.py), as for every film stock.

How it compared with the tables before on ml-dev/films/sample/SAMPLE.CR2 and on a Velvia 100 roll
developed by an EOS M: docs/spektrafilm.md.
"""

import argparse
import hashlib
import sys
from pathlib import Path

REPO = "https://github.com/andreavolpato/spektrafilm"
# spektrafilm at one commit and no other, so the same M-Film source always gives the same colour (as #102 for Film-Luts)
COMMIT = "3bb2c2d2801ff68b92019cf1dbcbb133d60832bc"
DIR = Path(__file__).resolve().parent / "spektra"
SUMS = Path(__file__).resolve().with_name("spektra.sha256")
PAPER = "kodak_portra_endura"             # spektrafilm's own default paper

# film stock (films.py), spektrafilm's profile, and the exposure it is rendered at, in stops. Only the film stocks
# spektrafilm has a profile of: the rest keep the table they had. The exposure was set on 2026-11-17 so that grey
# at 0.11 prints as bright as the film stock's table before printed it (Pat David's, or M-Film's own look for
# Portra 400, Ektar 100 and Gold 200), so the shelf keeps its brightness: only colour and contrast move.
STOCKS = [
    ("portra160", "kodak_portra_160", 0.657),
    ("portra400", "kodak_portra_400", 0.319),
    ("portra800", "kodak_portra_800", 0.428),
    ("ektar100", "kodak_ektar_100", 0.297),
    ("gold200", "kodak_gold_200", 0.335),
    ("pro400h", "fujifilm_pro_400h", 0.654),
    ("velvia100", "fujifilm_velvia_100", 0.158),
    ("provia100f", "fujifilm_provia_100f", 0.047),
    ("kodachrome64", "kodak_kodachrome_64", 0.297),
]
KEYS = [k for k, *_ in STOCKS]
GRID = 33


def path(key):
    return DIR / f"{key}.tab"


def sums():
    """{film stock: the SHA-256 of its rendered table}, from spektra.sha256."""
    out = {}
    for line in SUMS.read_text(encoding="ascii").splitlines():
        if line.strip() and not line.startswith("#"):
            digest, name = line.split(None, 1)
            out[name.strip()] = digest
    return out


def problems():
    """Why the rendered tables can't be used: ["portra400.tab: ..."], [] when they all can."""
    try:
        pinned = sums()
    except OSError:
        return [f"no {SUMS.name}"]
    out = []
    for key in KEYS:
        name = path(key).name
        if not path(key).is_file():
            out.append(f"{name}: missing")
        elif name not in pinned:
            out.append(f"{name}: {SUMS.name} has no line for it")
        elif hashlib.sha256(path(key).read_bytes()).hexdigest() != pinned[name]:
            out.append(f"{name}: not the table {SUMS.name} names")
        elif path(key).stat().st_size != GRID ** 3 * 3:
            out.append(f"{name}: not a table ({path(key).stat().st_size} bytes)")
    extra = sorted(set(pinned) - {path(k).name for k in KEYS})
    out += [f"{name}: in {SUMS.name}, and no film stock has it" for name in extra]
    return out


def body(key):
    """The rendered table of a film stock, as the bytes after a LOOKnn.LUT's header."""
    return path(key).read_bytes()


# ---------------------------------------------------------------- rendering (needs spektrafilm)

def _spektrafilm_root():
    import spektrafilm
    root = Path(spektrafilm.__file__).resolve().parents[2]
    if not (root / "SPEKTRAFILM_LICENSE.txt").is_file():
        sys.exit(f"spektra.py: spektrafilm is not installed from a clone ({root}): pip install -e <clone at {COMMIT[:12]}>")
    import subprocess
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    if head != COMMIT:
        sys.exit(f"spektra.py: the spektrafilm installed is at {head or 'an unknown commit'}, not {COMMIT}")
    return root


def _render(profile, lin, ev):
    import numpy as np
    from spektrafilm import init_params, simulate
    p = init_params(film_profile=profile, print_profile=PAPER)
    p.io.scan_film = bool(p.film.is_positive)          # a slide film is scanned as it is, as spektrafilm's own program does
    p.debug.lut_mode = True                            # no spatial effects, nothing random, no exposure of its own
    p.io.input_color_space, p.io.input_cctf_decoding = "sRGB", False
    p.io.output_color_space, p.io.output_cctf_encoding = "sRGB", True
    return np.clip(simulate(np.asarray(lin, np.float64) * 2.0 ** ev, p), 0, 1)


def render():
    import numpy as np
    import lut
    root = _spektrafilm_root()
    positives = _positives()
    g = np.arange(GRID, dtype=np.float32) / (GRID - 1)
    b, gg, r = np.meshgrid(g, g, g, indexing="ij")              # red changes fastest, as the camera's grid
    grid = lut.decode(np.stack([r, gg, b], -1).reshape(-1, 3), "cineon").reshape(GRID * GRID, GRID, 3)
    DIR.mkdir(exist_ok=True)
    log = []
    for key, profile, ev in STOCKS:
        rgb = _render(profile, grid, ev).reshape(-1, 3)
        path(key).write_bytes((rgb * 255 + 0.5).astype(np.uint8).tobytes())
        how = "scanned as it is" if profile in positives else f"printed on {PAPER}"
        log.append(f"{key}.tab  from {profile}, {how}, at {ev:+.3f} EV")
        print(log[-1], flush=True)
    (DIR / "SPEKTRAFILM_LICENSE.txt").write_bytes((root / "SPEKTRAFILM_LICENSE.txt").read_bytes())
    write_notes(log)
    print(f"{len(STOCKS)} tables in {DIR}, sums in {SUMS.name}")


CHANGES = """What M-Film changed in making these files from spektrafilm's profiles

Derived from spektrafilm by Andrea Volpato, {repo}, licensed CC BY-SA 4.0 (SPEKTRAFILM_LICENSE.txt).
Modified by the M-Film project, https://github.com/HNGSeries/mfilm-canon-film-simulation.

Each .tab here is spektrafilm's rendering, at commit {commit}, of one film profile, sampled at
33 x 33 x 33 points over Cineon code (linear sRGB in, sRGB out, 8 bits), with spektrafilm's lut_mode:
no spatial effects, nothing random. A negative is printed on Kodak Portra Endura and the print scanned;
a slide film is scanned as it is. The exposure is M-Film's: grey at 0.11 prints as bright as the film
stock's earlier table printed it. M-Film puts each one, behind an 8-byte header, in the film stock's
LOOKnn.LUT (ml-dev/filmos/tools/gentables.py; TABLES.txt marks them "spektrafilm").

{log}
"""


def write_notes(log):
    """CHANGELOG.txt (what was changed, as the licence asks) and spektra.sha256."""
    (DIR / "CHANGELOG.txt").write_text(CHANGES.format(repo=REPO, commit=COMMIT, log="\n".join(log)), encoding="utf-8")
    lines = ["# SHA-256 of each table rendered from spektrafilm (spektra.py writes it; tools/gentables.py checks it)"]
    lines += [f"{hashlib.sha256(path(k).read_bytes()).hexdigest()}  {path(k).name}" for k in KEYS]
    SUMS.write_text("\n".join(lines) + "\n", encoding="ascii")


def _positives():
    from spektrafilm import init_params
    return {p for _, p, _ in STOCKS if init_params(film_profile=p, print_profile=PAPER).film.is_positive}


def main():
    ap = argparse.ArgumentParser(description="The film stocks whose colour comes from spektrafilm.")
    ap.add_argument("--check", action="store_true", help="only check the rendered tables against spektra.sha256")
    a = ap.parse_args()
    if not a.check:
        render()
    bad = problems()
    if bad:
        sys.exit("spektra.py: the rendered tables:\n  " + "\n  ".join(bad))
    print(f"{len(KEYS)} tables rendered from spektrafilm at {COMMIT[:12]}, each the one {SUMS.name} names")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
