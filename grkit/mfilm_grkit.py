#!/usr/bin/env python3
"""M-Film's film stocks as GRKit Film Look effects, for RICOH GR III, GR IIIx and GR IV.

    python3 grkit/mfilm_grkit.py plan  [--set colour|slide|bw|all] [--json]
    python3 grkit/mfilm_grkit.py cubes [--set ...]
    python3 grkit/mfilm_grkit.py effects --firmware fwdc239b.bin [--grkit grkit] [--set ...]
    python3 grkit/mfilm_grkit.py card  [--grkit grkit] [--set ...]
    python3 grkit/mfilm_grkit.py recipes [--set ...]

GRKit (https://github.com/ahonn/grkit) runs code on the GR from the SD card,
and its Film Look replaces the camera's colour matrix and tone curves. This
turns M-Film's film stocks into its effects, one film stock to one effect:

  plan     what each film stock becomes: its effect ID and name, its box,
           the recipe that goes with it, its licence
  cubes    each film stock's colour as a .cube, from the table the camera
           and Darkrooms read (LOOKnn.LUT), with GR scene light as its input
  effects  the .cubes fitted to GRKit's effect model by `grkit effects
           import`, then given M-Film's box and attribution. Needs GRKit's
           CLI and your own official GR III 2.10 firmware file (the fit reads
           the Standard base gamma from it); neither is in this repository
  card     the effects compiled into GRKIT/EFFECTS, ready to copy to a card
           that has GRKit (`grkit effects build`)
  recipes  each film stock's grain, glow and white balance, in the shape of
           GRKit's recipe model. GRKit takes recipes only from its own
           presets and from the camera for now, so this is a proposal

Everything is written under grkit/out/ (not in git).

The tables come from the darkroom's build:

    make -C ml-dev/filmos/sim out/devtest out/FOSFILMS.BIN
    python3 ml-dev/films/getluts.py
    python3 ml-dev/filmos/tools/gentables.py ml-dev/filmos/sim/out/tables \\
        --films ml-dev/filmos/sim/out/FOSFILMS.BIN --devtest ml-dev/filmos/sim/out/devtest

What carries over and what does not (README.md says more):

  - The colour: steps 5 and 8 of ml-dev/DEVELOPING.md, the scanner's exposure
    and the film stock's table. GRKit fits them to a 3 x 3 matrix, three tone
    curves and hue sectors, so a film stock comes out close to M-Film's, not
    the same.
  - Grain, halation and the vignette are outside the table. Grain and glow
    become a recipe's settings of GRKit's own grain and Glow; the vignette is
    left to the camera's shading.
  - The GR meters each frame itself, so there is no per-frame scanner: the
    film stock's exposure is fixed (GREY).

Needs numpy.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ML = ROOT / "ml-dev"
sys.path[:0] = [str(ML / "films"), str(ML / "filmos" / "tools")]
from films import FILMS  # noqa: E402
import catalog  # noqa: E402

# The GRKit this is made for: its latest release when the pack was started. The effect model, the limits
# below and the recipe fields are read from this commit.
GRKIT_VERSION = "1.6.3"
GRKIT_COMMIT = "e3e71feec5aa1c7543193361c4c56084de4cb0a3"
GRKIT_REPO = "https://github.com/ahonn/grkit"

MFILM_VERSION = (ROOT / "VERSION").read_text().strip()

TABLES = ML / "filmos" / "sim" / "out" / "tables"
OUT = Path(__file__).resolve().parent / "out"

# M-Film's tables (gentables.py): "FOL1", the look's hash, then 33 x 33 x 33 RGB bytes, red fastest.
GRID = 33
HEADER = 8
CIN_BLACK = 0.0108                  # fos_dev.c

# GRKit lists at most 64 effect files of GRKIT/EFFECTS and installs at most 40 of them
# (runtime/effects.h EFFECTS_LISTED, crates/grkit-core/src/abi.rs MAX_COUNT). Its own catalog shares
# them, so the pack comes in sets of one shelf each, and a card should carry one set at a time.
LISTED, INSTALLED = 64, 40
SETS = {
    "colour": ("neg", "cine"),
    "slide": ("slide", "xpro"),
    "bw": ("bw",),
}

# Where 18% grey of the GR's scene lands in M-Film's light (1.0 = the Canon's white level), before the film
# stock's own ev. A metered Canon frame has grey about 3.2 stops under its white level, 0.11, which is also
# the key the scanner brings a negative's frame to (DEVELOPING.md step 5); a slide film stock gets 1 stop
# more, as the darkroom gives it. Provisional: to be checked against the sample frame's light
# (devtest's FOS_DUMP_LIN on ml-dev/films/sample/SAMPLE.CR2).
GREY = 0.11
SLIDE_EV = 1.0

# Effect names are 1 to 16 printable ASCII characters (GRKit effects/README.md): the film stock's name
# without its brand, except where that is too long or says too little:
NAMES = {
    "cinestill800t": "CineStill 800T",
    "cinestill400t": "CineStill 400T",
    "e100gx": "E100GX",
    "e100vs": "E100VS",
    "superia200xpro": "Superia 200 XPro",
}

# GRKit's recipe fields (crates/grkit-core/src/recipes/model.rs): Grain level 0 Off .. 4 Extra Strong, size
# 0 Auto, 1 small .. 3 large; Glow bloom and halation 0 Off .. 3 Strong; white balance mode 14 is ColorTemp1,
# the one that takes kelvin (native/tables.rs COLOR_TEMPERATURE_MODE).
WB_COLOR_TEMP = 14
WB_NO_SHIFT = 14


# ---------------------------------------------------------------- the shelf

def shelf(tables=TABLES):
    """[(file, key, made_from)] in the order of TABLES.txt, which gentables.py writes."""
    index = Path(tables) / "TABLES.txt"
    if not index.exists():
        sys.exit(f"{index}: no tables. Build them first (python3 grkit/mfilm_grkit.py --help says how).")
    rows = []
    for line in index.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            file, key, made_from = line.split()[:3]
            rows.append((file, key, made_from))
    return rows


def film_set(key):
    kind = FILMS[key]["kind"]
    return next(s for s, kinds in SETS.items() if kind in kinds)


def chosen(rows, which):
    return [r for r in rows if which == "all" or film_set(r[1]) == which]


# ---------------------------------------------------------------- colour

def read_table(path):
    """A LOOKnn.LUT as uint8 [blue][green][red][rgb]."""
    data = Path(path).read_bytes()
    if data[:4] != b"FOL1" or len(data) != HEADER + GRID ** 3 * 3:
        raise ValueError(f"{path}: not an M-Film colour table")
    return np.frombuffer(data, np.uint8, offset=HEADER).reshape(GRID, GRID, GRID, 3)


def cineon(light):
    """Light (1.0 = white level) to Cineon code 0..1, as cineon_encode in fos_dev.c."""
    x = np.maximum(light, 0) * (1 - CIN_BLACK) + CIN_BLACK
    return np.clip((685 + 300 * np.log10(x)) / 1023, 0, 1)


def positions(code):
    """Cineon code 0..1 to a place in the table in 1/256 of a cell, as tables_ready and cin_pos do."""
    c = np.floor(np.asarray(code) * 65535 + 0.5).astype(np.int64)
    return (c * ((GRID - 1) * 256)) >> 16


def tetra(table, pos):
    """The table at places pos [..., 3] (red, green, blue in 1/256), through the cell's tetrahedron,
    exactly as lut_apply in fos_dev.c: 8-bit results."""
    flat = table.reshape(-1, 3).astype(np.int64)
    pr, pg, pb = (pos[..., i] for i in range(3))
    ir, ig, ib = pr >> 8, pg >> 8, pb >> 8
    fr, fg, fb = pr & 255, pg & 255, pb & 255
    base = (ib * GRID + ig) * GRID + ir
    R, G, B = 1, GRID, GRID * GRID
    cases = [
        (fr >= fg) & (fg >= fb),
        (fr >= fg) & (fg < fb) & (fr >= fb),
        (fr >= fg) & (fg < fb) & (fr < fb),
        (fr < fg) & (fb >= fg),
        (fr < fg) & (fb < fg) & (fb >= fr),
        (fr < fg) & (fb < fg) & (fb < fr),
    ]
    #           o1  o2      w0        w1       w2       w3
    shapes = [(R, R + G, 256 - fr, fr - fg, fg - fb, fb),
              (R, R + B, 256 - fr, fr - fb, fb - fg, fg),
              (B, R + B, 256 - fb, fb - fr, fr - fg, fg),
              (B, G + B, 256 - fb, fb - fg, fg - fr, fr),
              (G, G + B, 256 - fg, fg - fb, fb - fr, fr),
              (G, R + G, 256 - fg, fg - fr, fr - fb, fb)]
    o1 = np.select(cases, [s[0] for s in shapes])
    o2 = np.select(cases, [s[1] for s in shapes])
    w = [np.select(cases, [s[i] for s in shapes]) for i in range(2, 6)]
    o3 = R + G + B
    out = (w[0][..., None] * flat[base] + w[1][..., None] * flat[base + o1]
           + w[2][..., None] * flat[base + o2] + w[3][..., None] * flat[base + o3] + 128) >> 8
    return out.astype(np.uint8)


def srgb_decode(v):
    v = np.asarray(v, float)
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def scale(key):
    """What GR scene light is multiplied by to become M-Film's light before the table."""
    f = FILMS[key]
    ev = f.get("ev", 0.0) + (SLIDE_EV if f.get("slide") else 0.0)
    return GREY / 0.18 * 2 ** ev


def cube(table, key, size=GRID):
    """The film stock's colour over GRKit's `srgb` input (sRGB-encoded scene light, no tone curve):
    [blue][green][red][rgb] floats 0..1, the print M-Film's darkroom makes of that light."""
    axis = srgb_decode(np.linspace(0, 1, size))
    b, g, r = np.meshgrid(axis, axis, axis, indexing="ij")
    light = np.stack([r, g, b], -1) * scale(key)
    return tetra(table, positions(cineon(np.minimum(light, 16)))) / 255.0


def write_cube(path, rgb, title):
    """A Resolve .cube: red changing fastest."""
    size = rgb.shape[0]
    lines = [f'TITLE "{title}"', f"LUT_3D_SIZE {size}", "DOMAIN_MIN 0 0 0", "DOMAIN_MAX 1 1 1"]
    lines += [f"{p[0]:.6f} {p[1]:.6f} {p[2]:.6f}" for p in rgb.reshape(-1, 3)]
    Path(path).write_text("\n".join(lines) + "\n", encoding="ascii")


# ---------------------------------------------------------------- what each film stock becomes

def name(key):
    if key in NAMES:
        return NAMES[key]
    full = FILMS[key]["name"]
    return full.split(" ", 1)[1] if " " in full else full


def effect_id(key):
    """GRKit keeps an effect's settings by its ID: stable, lowercase, and apart from GRKit's own."""
    return f"mfilm-{key}-v1"


def ink(colour):
    """A catalog ink (ramp, level) as [r, g, b], as fos_gfx.c builds its palette."""
    ramp, level = colour
    names = ["GRAY", "METAL", "AMBER", "RED", "ORANGE", "CRIMSON", "GREEN", "VIOLET", "BLUE"]
    lo, mid, hi, mid_at = RAMPS[names[ramp]]

    def lerp(a, b, t, n):
        return [int(max(0, min(255, a[i] + (b[i] - a[i]) * t // n))) for i in range(3)]

    if not mid_at:
        return lerp(lo, hi, level, 255)
    return lerp(lo, mid, level, mid_at) if level < mid_at else lerp(mid, hi, level - mid_at, 255 - mid_at)


def _rgb(x):
    return [(x >> 16) & 255, (x >> 8) & 255, x & 255]


RAMPS = {k: (_rgb(lo), _rgb(mid), _rgb(hi), at) for k, (lo, mid, hi, at) in {
    "GRAY": (0x040303, 0x000000, 0xFFFCF6, 0),
    "METAL": (0x050608, 0x878F98, 0xF4F7FA, 150),
    "AMBER": (0x080402, 0xF4A81C, 0xFFF2D2, 185),
    "RED": (0x080202, 0xDF262D, 0xFFD8D4, 150),
    "ORANGE": (0x080302, 0xEA5D1E, 0xFFDEC9, 160),
    "CRIMSON": (0x060102, 0x9C1320, 0xF6C4C8, 120),
    "GREEN": (0x020604, 0x13894B, 0xD0F5DF, 140),
    "VIOLET": (0x040208, 0x5A2D8A, 0xE9DCF7, 120),
    "BLUE": (0x020508, 0x1E77C6, 0xD5EBFF, 150),
}.items()}

# A box for the film stocks the catalog has no label for (the built-in eight): body, band, text by shelf.
PLAIN_BOX = {
    "neg": ([236, 232, 224], [214, 150, 30], [30, 26, 22]),
    "cine": ([28, 26, 24], [200, 40, 45], [240, 236, 228]),
    "slide": ([40, 70, 140], [40, 70, 140], [240, 236, 228]),
    "xpro": ([120, 40, 120], [230, 120, 40], [240, 236, 228]),
    "bw": ([236, 232, 224], [28, 26, 24], [28, 26, 24]),
}


def icon(key):
    """GRKit's film box (effects/README.md, Icons) in the colours of M-Film's canister."""
    f = FILMS[key]
    label = catalog.LABELS.get(key)
    if label:
        brand = (label["top"].split() or ["M-FILM"])[0]
        box = {"template": "box", "brand": brand, "name": " ".join(filter(None, [label["word"], label["sub"]])),
               "number": label["num_s"], "band": True,
               "colors": {"body": ink(label["bg"]), "band": ink(label["band"]), "brand": ink(label["text"]),
                          "text": ink(label["num"]), "accent": ink(label["accent"])}}
    else:
        body, band, text = PLAIN_BOX[f["kind"]]
        words = f["name"].split()
        number = next((w for w in reversed(words) if any(c.isdigit() for c in w)), "")
        box = {"template": "box", "brand": words[0], "name": " ".join(w for w in words[1:] if w != number),
               "number": number, "band": True,
               "colors": {"body": body, "band": band, "brand": text, "text": text, "accent": band}}
    if not box["name"]:                 # "CineStill 800T": the number is all the name there is
        box["name"] = box.pop("number")
    if not box.get("number"):
        box.pop("number", None)
    return box


def grain(key):
    """M-Film's grain as GRKit's: amplitude in display units at mid-tones and clump size in pixels
    (films.py) to a level 1..4 and a size 1..3."""
    f = FILMS[key]
    amount, size = f.get("grain", 0), f.get("grain_size", 1.0)
    if amount <= 0:
        return {"level": 0, "size": 0}
    level = 1 if amount < 0.012 else 2 if amount < 0.02 else 3 if amount < 0.03 else 4
    return {"level": level, "size": 1 if size < 0.95 else 2 if size < 1.25 else 3}


def glow(key):
    """M-Film's halation strength (0 to 0.4 on the shelf) to GRKit's Halation 0..3. M-Film has no bloom."""
    h = FILMS[key].get("halation", 0)
    return {"bloom": 0, "halation": 0 if h <= 0 else 1 if h <= 0.15 else 2 if h <= 0.3 else 3,
            "halationColor": 0}


def white_balance(key):
    """Loading a roll sets the camera to the light the film is made for (#115): 5500 K, 3200 K tungsten."""
    return {"mode": WB_COLOR_TEMP, "shiftBa": WB_NO_SHIFT, "shiftGm": WB_NO_SHIFT,
            "kelvin": FILMS[key].get("balance", 5500)}


def licence(made_from):
    """The table's licence (THIRD_PARTY.md): the 59 baked from Pat David's tables stay CC BY-SA 4.0."""
    return "CC BY-SA 4.0" if made_from == "lut" else "GPL-2.0-only"


def plan(rows):
    out = []
    for file, key, made_from in rows:
        f = FILMS[key]
        out.append({
            "key": key, "film": f["name"], "kind": f["kind"], "set": film_set(key), "iso": f["iso"],
            "table": file, "made_from": made_from, "licence": licence(made_from),
            "effect_id": effect_id(key), "name": name(key), "icon": icon(key),
            "describe": catalog.DESC.get(key, ""),
            "recipe": {"id": f"mfilm-{key}", "effect": effect_id(key), "grain": grain(key), "glow": glow(key),
                       "whiteBalance": white_balance(key)},
        })
    return out


def check(entries):
    """What GRKit would refuse, before anything is run."""
    problems = []
    ids = [e["effect_id"] for e in entries]
    if len(set(ids)) != len(ids):
        problems.append("two film stocks have the same effect ID")
    for e in entries:
        n = e["name"]
        if not (1 <= len(n) <= 16 and n.isascii() and n.isprintable()):
            problems.append(f"{e['key']}: effect name {n!r} is not 1 to 16 printable ASCII characters")
    for s in SETS:
        count = sum(e["set"] == s for e in entries)
        if count > INSTALLED:
            problems.append(f"set {s}: {count} effects, more than the {INSTALLED} GRKit installs at once")
    return problems


# ---------------------------------------------------------------- steps

def run_grkit(grkit, *args):
    exe = shutil.which(grkit) or (grkit if Path(grkit).exists() else None)
    if not exe:
        sys.exit(f"{grkit}: GRKit's CLI is not here. Build it from {GRKIT_REPO} at v{GRKIT_VERSION} "
                 f"(cargo build --release -p grkit-cli) and pass --grkit target/release/grkit.")
    subprocess.run([exe, *map(str, args)], check=True)


def do_cubes(rows, tables, out):
    out.mkdir(parents=True, exist_ok=True)
    for file, key, _ in rows:
        write_cube(out / f"{effect_id(key)}.cube", cube(read_table(Path(tables) / file), key),
                   f"M-Film {MFILM_VERSION} {FILMS[key]['name']}")
    print(f"{out}: {len(rows)} cubes")


def do_effects(rows, entries, cubes, out, firmware, grkit):
    if not Path(firmware).is_file():
        sys.exit(f"{firmware}: the official GR III 2.10 firmware file (fwdc239b.bin) is needed for the fit. "
                 "It is Ricoh's: download it from Ricoh, and never commit it.")
    out.mkdir(parents=True, exist_ok=True)
    for (_, key, _), e in zip(rows, entries):
        if (out / e["effect_id"]).exists():
            shutil.rmtree(out / e["effect_id"])
        label = "".join(c for c in e["name"].upper() if c.isalnum())[:4]
        run_grkit(grkit, "effects", "import", "--lut", cubes / f"{e['effect_id']}.cube", "--firmware", firmware,
                  "--input", "srgb", "--id", e["effect_id"], "--name", e["name"], "--label", label,
                  "--shape", "film", "--out", out)
        path = out / e["effect_id"] / "effect.json"
        effect = json.loads(path.read_text())
        effect["icon"] = e["icon"]
        effect["attribution"].update(
            target=f"{e['film']}, as M-Film {MFILM_VERSION} develops it (its table {e['table']})",
            license=e["licence"],
            generator=f"M-Film {MFILM_VERSION} (https://github.com/HNGSeries/mfilm-canon-film-simulation)")
        path.write_text(json.dumps(effect, indent=2) + "\n")
    print(f"{out}: {len(rows)} effects. Read each one's grade and warnings above before using it.")


def do_card(entries, effects, out, grkit, which):
    dest = out / which / "GRKIT" / "EFFECTS"
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    stage = out / which / "source"
    if stage.exists():
        shutil.rmtree(stage)
    for e in entries:
        shutil.copytree(effects / e["effect_id"], stage / e["effect_id"])
    run_grkit(grkit, "effects", "build", "--source", stage, "--out", dest)
    shutil.rmtree(stage)
    print(f"{dest}: copy GRKIT/ to the root of a card that has GRKit {GRKIT_VERSION}, then power on.")


def do_recipes(entries, out):
    out.mkdir(parents=True, exist_ok=True)
    path = out / "recipes.json"
    path.write_text(json.dumps({"grkit": GRKIT_VERSION, "recipes": [e["recipe"] for e in entries]}, indent=2) + "\n")
    print(f"{path}: {len(entries)} recipes (a proposal: GRKit cannot load them from a file yet)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("step", choices=["plan", "cubes", "effects", "card", "recipes"])
    ap.add_argument("--set", default="colour", choices=[*SETS, "all"],
                    help="which shelf: colour (default), slide, bw, or all (plan and cubes only)")
    ap.add_argument("--tables", type=Path, default=TABLES)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--firmware", type=Path, help="official GR III 2.10 firmware, fwdc239b.bin (effects)")
    ap.add_argument("--grkit", default="grkit", help="GRKit's CLI (effects, card)")
    ap.add_argument("--json", action="store_true", help="plan: as JSON")
    a = ap.parse_args()

    rows = chosen(shelf(a.tables), a.set)
    entries = plan(rows)
    problems = check(plan(shelf(a.tables)))
    if problems:
        sys.exit("\n".join(problems))
    if a.set == "all" and a.step in ("effects", "card"):
        sys.exit(f"one set at a time: GRKit lists at most {LISTED} effect files on a card and installs {INSTALLED}")

    if a.step == "plan":
        if a.json:
            print(json.dumps({"grkit": GRKIT_VERSION, "mfilm": MFILM_VERSION, "films": entries}, indent=2))
        else:
            for e in entries:
                r = e["recipe"]
                print(f"{e['effect_id']:28} {e['name']:17} {e['set']:7} {e['licence']:13} grain {r['grain']['level']}"
                      f"/{r['grain']['size']}  halation {r['glow']['halation']}  {r['whiteBalance']['kelvin']} K")
            print(f"{len(entries)} film stocks, GRKit {GRKIT_VERSION}, M-Film {MFILM_VERSION}")
    elif a.step == "cubes":
        do_cubes(rows, a.tables, a.out / "cubes")
    elif a.step == "effects":
        if not a.firmware:
            sys.exit("effects needs --firmware fwdc239b.bin (official GR III 2.10)")
        do_effects(rows, entries, a.out / "cubes", a.out / "effects", a.firmware, a.grkit)
    elif a.step == "card":
        do_card(entries, a.out / "effects", a.out / "card", a.grkit, a.set)
    elif a.step == "recipes":
        do_recipes(entries, a.out / a.set)


if __name__ == "__main__":
    main()
