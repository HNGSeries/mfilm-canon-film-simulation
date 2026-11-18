"""M-Film's own covers for the GRKit effects: the end of a film box, in three bands.

    python3 grkit/covers.py OUT [--size 240]      every film stock's cover as OUT/<key>.png, and the
                                                  camera's simpler one as OUT/<key>.small.png

GRKit draws an effect's icon from a template (a brand band, a small name, a big number). M-Film draws its
own instead and puts it into each .GRF after `grkit effects build` (patch_grf): the file keeps its icon as
40 x 40 RGBA pixels at GRF_ICON, under a CRC-32 (GRKit crates/grkit-core/src/effects.rs, abi.rs).

A cover, top to bottom:

    +-----+--------------------+
    | [ ] |      KODAK  C-41   |   the brand band: a light block, the brand and the process
    +-----+--------------------+
    |        Portra            |   the film's panel: its name, large
    +==========================+   a line of the accent
    |  ISO               400   |   the speed, large, on black
    +--------------------------+

The colours are those of the film stock's canister on M-Film's shelf (ml-dev/filmos/tools/catalog.py);
the built-in eight, which the camera paints by hand, have theirs here. They are M-Film's own designs in
the colours of each brand, with the names as plain text and no logo.

It is drawn large and made smaller for the camera, so the small cover is smooth rather than pixelated.
Needs Pillow.
"""

import argparse
import re
import sys
import zlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import mfilm_grkit as m

FONTS = m.ROOT / "site" / "fonts"          # Barlow, SIL Open Font License 1.1
NAME_FONT = FONTS / "BarlowCondensed-Bold.ttf"
SMALL_FONT = FONTS / "Barlow-Bold.ttf"

# GRKit's GRFX0001 file (crates/grkit-core/src/abi.rs): its length at 8, a CRC-32 at 12 that is read as
# zero while it is computed, and the icon at 1684, 40 x 40 RGBA8 with alpha 0 or 255.
GRF_MAGIC = b"GRFX0001"
GRF_BYTES, GRF_CRC, GRF_ICON = 8, 12, 1684
ICON = 40

C = m.catalog
G, MT, AM, RD, OR, CR, GR, VI, BL = C.GRAY, C.METAL, C.AMBER, C.RED, C.ORANGE, C.CRIMSON, C.GREEN, C.VIOLET, C.BLUE

# The built-in eight have no label in the catalog (fos_film.c paints them by hand).
BUILTIN = {
    "portra400": C.portra("400"),
    "cinestill800t": C.L(C.STRIPES, (G, 20), (G, 20), C.KRED, C.W, C.W, "CINESTILL", "CINESTILL", "800T"),
    "ektar100": C.L(C.BAND, (G, 236), (RD, 150), C.YEL, (RD, 150), C.K, "KODAK", "EKTAR", "100"),
    "gold200": C.L(C.BAND, C.YEL, (RD, 150), C.KRED, (RD, 150), C.K, "KODAK", "GOLD", "200"),
    "superia400": C.superia("400", (BL, 110)),
    "velvia50": C.L(C.STRIPES, (VI, 110), (VI, 110), (VI, 225), C.W, (VI, 225), "FUJICHROME", "VELVIA", "50"),
    "hp5": C.ilford("HP5 PLUS", "400", C.KRED),
    "trix400": C.L(C.BAND, C.YEL, (G, 20), C.KRED, C.K, C.K, "KODAK", "TRI-X", "400"),
}

PROCESS = {"neg": "C-41", "cine": "C-41", "slide": "E-6", "xpro": "X-PRO", "bw": "B&W"}

# Where the film's name on the cover is not its name less its brand and speed.
NAMES = {
    "e100gx": "Ektachrome GX", "e100vs": "Ektachrome VS", "tmax3200": "T-Max P",
    "tmax100": "T-Max", "tmax400": "T-Max", "bw400cn": "BW400CN", "hie": "HIE Infrared",
    "cinestill800t": "CineStill", "cinestill400t": "CineStill", "superia200xpro": "Superia X-Pro",
    "elite100xpro": "Elite X-Pro", "xproslide200": "X-Pro Slide",
}

BLACK = (20, 19, 18)
WHITE = (250, 248, 244)


def label(key):
    return BUILTIN.get(key) or C.LABELS[key]


def brand(key):
    top = label(key)["top"].split()
    return (top[0] if top else "M-FILM").upper()


def process(key):
    f = m.FILMS[key]
    return "K-14" if key.startswith("kodachrome") else PROCESS[f["kind"]]


def name_and_speed(key):
    """('Portra NC', '160'), ('CineStill', '800T'), ('Provia', '100F'): the speed keeps a one-letter
    suffix (T, H, F, S ...), a longer one goes to the name."""
    f = m.FILMS[key]
    iso = str(f["iso"])
    words = f["name"].split()[1:]
    speed, rest = iso, []
    for w in words:
        if w.startswith(iso):
            tail = w[len(iso):]
            if len(tail) == 1:
                speed = w
            elif tail:
                rest.append(tail)
        else:
            rest.append(w)
    return NAMES.get(key, " ".join(rest) or f["name"]), speed


def luma(rgb):
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def readable(ink, ground):
    """The ink, or white or black where it would not read on the ground."""
    if abs(luma(ink) - luma(ground)) >= 90:
        return tuple(ink)
    return BLACK if luma(ground) > 140 else WHITE


def fit(draw, text, font_path, box_w, box_h, start):
    """The largest font (and horizontal squeeze) at which text fits box_w x box_h."""
    size = start
    while size > 4:
        font = ImageFont.truetype(str(font_path), size)
        l, t, r, b = draw.textbbox((0, 0), text, font=font, anchor="ls")
        if r - l <= box_w and b - t <= box_h:
            return font, 1.0
        if r - l <= box_w / 0.78 and b - t <= box_h:      # squeeze a little before going smaller
            return font, box_w / (r - l)
        size -= 1
    return ImageFont.truetype(str(font_path), 5), 1.0


def text_at(img, xy, text, font, fill, squeeze=1.0, anchor="ls"):
    """Draw text, squeezed horizontally when squeeze < 1."""
    if squeeze >= 1.0:
        ImageDraw.Draw(img).text(xy, text, font=font, fill=fill, anchor=anchor)
        return
    d = ImageDraw.Draw(img)
    l, t, r, b = d.textbbox((0, 0), text, font=font, anchor="ls")
    w, h = r - l + 4, b - t + 4
    layer = Image.new("L", (w, h), 0)
    ImageDraw.Draw(layer).text((2 - l, 2 - t), text, font=font, fill=255, anchor="ls")
    layer = layer.resize((max(1, round(w * squeeze)), h), Image.LANCZOS)
    x, y = xy
    if anchor[0] == "r":
        x -= layer.width - 2
    elif anchor[0] == "m":
        x -= layer.width // 2
    else:
        x -= 2
    img.paste(Image.new("RGB", layer.size, fill), (round(x), round(y + t - 2)), layer)


def render(key, size=400, compact=False):
    """The cover, size x size, opaque. compact: for 40 pixels, only what reads at that size: the brand
    alone and larger, and the speed without "ISO"."""
    lab = label(key)
    ink = m.ink
    band, body, accent = ink(lab["band"]), ink(lab["bg"]), ink(lab["accent"])
    s = size / 100
    img = Image.new("RGB", (size, size), BLACK)
    d = ImageDraw.Draw(img)

    # the brand band
    top_end = round(30 * s)
    d.rectangle([0, 0, size, top_end], fill=tuple(band))
    d.rectangle([0, 0, round(20 * s), top_end], fill=WHITE if luma(band) < 200 else tuple(body))
    d.rectangle([round(20 * s), 0, round(23 * s), top_end], fill=tuple(accent))
    on_band = readable(ink(lab["text"]), band)
    if compact:
        font, squeeze = fit(d, brand(key), SMALL_FONT, size - round(30 * s), round(14 * s), round(17 * s))
        text_at(img, (size - round(4 * s), round(22 * s)), brand(key), font, on_band, squeeze, anchor="rs")
    else:
        small = ImageFont.truetype(str(SMALL_FONT), round(11 * s))
        d.text((size - round(5 * s), round(13 * s)), brand(key), font=small, fill=on_band, anchor="rs")
        d.text((size - round(5 * s), round(26 * s)), process(key), font=small, fill=on_band, anchor="rs")

    # the film's panel
    panel_end = round(66 * s)
    d.rectangle([0, top_end, size, panel_end], fill=tuple(body))
    name, speed = name_and_speed(key)
    font, squeeze = fit(d, name, NAME_FONT, size - round(10 * s), round(28 * s), round(34 * s))
    on_body = readable(ink(lab["num"]), body)
    text_at(img, (size // 2, round(60 * s)), name, font, on_body, squeeze, anchor="ms")

    # a line of the accent, then the speed
    d.rectangle([0, panel_end, size, panel_end + round(4 * s)], fill=tuple(accent))
    if compact:
        font, squeeze = fit(d, speed, NAME_FONT, size - round(12 * s), round(26 * s), round(31 * s))
        text_at(img, (size // 2, round(96 * s)), speed, font, WHITE, squeeze, anchor="ms")
    else:
        tiny = ImageFont.truetype(str(SMALL_FONT), round(10 * s))
        d.text((round(6 * s), round(93 * s)), "ISO", font=tiny, fill=WHITE, anchor="ls")
        font, squeeze = fit(d, speed, NAME_FONT, size - round(30 * s), round(26 * s), round(30 * s))
        text_at(img, (size - round(6 * s), round(95 * s)), speed, font, WHITE, squeeze, anchor="rs")
    return img


def camera_icon(key):
    """The cover as the camera keeps it: 40 x 40 RGBA bytes, drawn at 10 times and made smaller."""
    return render(key, ICON * 10, compact=True).resize((ICON, ICON), Image.LANCZOS).convert("RGBA").tobytes()


def checksum(blob):
    """GRKit's checksum: CRC-32 of the file with its CRC field read as zero."""
    return zlib.crc32(blob[:GRF_CRC] + b"\0\0\0\0" + blob[GRF_CRC + 4:]) & 0xFFFFFFFF


def patch_grf(path, icon):
    """Put icon (40 x 40 RGBA, alpha 0 or 255) into a GRFX0001 file and write its CRC again."""
    blob = bytearray(Path(path).read_bytes())
    if blob[:8] != GRF_MAGIC or int.from_bytes(blob[GRF_BYTES:GRF_BYTES + 4], "little") != len(blob):
        raise ValueError(f"{path}: not a GRFX0001 file")
    if checksum(bytes(blob)) != int.from_bytes(blob[GRF_CRC:GRF_CRC + 4], "little"):
        raise ValueError(f"{path}: its CRC is wrong already")
    if len(icon) != ICON * ICON * 4 or any(a not in (0, 255) for a in icon[3::4]):
        raise ValueError("an icon is 40 x 40 RGBA with alpha 0 or 255")
    blob[GRF_ICON:GRF_ICON + len(icon)] = icon
    blob[GRF_CRC:GRF_CRC + 4] = checksum(bytes(blob)).to_bytes(4, "little")
    Path(path).write_bytes(bytes(blob))


def grf_name(effect_id):
    """The file GRKit writes an effect to: the first 8 hex digits of the ID's SHA-256 (effects.rs)."""
    import hashlib
    return hashlib.sha256(effect_id.encode()).hexdigest()[:8].upper() + ".GRF"


def main():
    ap = argparse.ArgumentParser(description="M-Film's covers for the GRKit effects, as PNG files.")
    ap.add_argument("out", type=Path)
    ap.add_argument("--size", type=int, default=240)
    ap.add_argument("--camera", action="store_true", help="also <key>.40.png, the 40 x 40 the camera gets")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    for key in m.FILMS:
        render(key, a.size).save(a.out / f"{key}.png", optimize=True)
        render(key, a.size, compact=True).save(a.out / f"{key}.small.png", optimize=True)
        if a.camera:
            Image.frombytes("RGBA", (ICON, ICON), camera_icon(key)).save(a.out / f"{key}.40.png")
    print(f"{a.out}: {len(m.FILMS)} covers")


if __name__ == "__main__":
    sys.exit(main())
