"""The Fujifilm port's preview pictures (preview/): the film OS's screens, as the
fake cameras draw them through fujiport.c, set in a drawing of each camera's back
with its keys named as the port maps them.

    make mockups

The bodies are schematic, not to scale and without any maker's marks: they show
where the keys are and what each does in the film OS, nothing more.
"""

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "mockup"
PREVIEW = HERE / "preview"
FONTS = HERE.parent / "filmos" / "fonts"
CARD_STATE = HERE / "out" / "card" / "ML" / "SETTINGS" / "MFILM.FUJ"

BODY = (34, 34, 36)
BODY_EDGE = (58, 58, 62)
BEZEL = (12, 12, 13)
KEY = (52, 52, 56)
KEY_EDGE = (86, 86, 92)
INK = (214, 210, 200)
DIM = (140, 136, 128)
ACCENT = (236, 168, 52)        # M-Film's amber
BG = (22, 21, 20)


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


F_KEY = font("Barlow-SemiBold.ttf", 15)
F_CALL = font("Barlow-Medium.ttf", 19)
F_CALL_B = font("Barlow-Bold.ttf", 19)
F_TITLE = font("BarlowCondensed-Bold.ttf", 34)
F_SUB = font("Barlow-Medium.ttf", 18)


def run(camera, scene, outdir):
    """the fake camera through a scene, with a card that has no roll yet"""
    outdir.mkdir(parents=True, exist_ok=True)
    CARD_STATE.unlink(missing_ok=True)
    subprocess.run([str(HERE / "out" / f"fakefuji-{camera}"), str(HERE / "scenes" / scene), str(outdir)],
                   check=True, cwd=HERE, stderr=subprocess.DEVNULL)


def shot(camera, name):
    return Image.open(OUT / camera / f"{name}.ppm").convert("RGB")


def key(d, cx, cy, r, label, round_=True):
    if round_:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=KEY, outline=KEY_EDGE, width=2)
    else:
        w = d.textlength(label, font=F_KEY) / 2 + 14
        d.rounded_rectangle([cx - w, cy - r * 0.75, cx + w, cy + r * 0.75], radius=8,
                            fill=KEY, outline=KEY_EDGE, width=2)
    d.text((cx, cy), label, font=F_KEY, fill=INK, anchor="mm")


def callout(d, points, fuji, fos):
    """a line from a key (the first point) to what it does: '<fuji key>  <film OS>'"""
    d.line(points, fill=ACCENT, width=2, joint="curve")
    x0, y0 = points[0]
    d.ellipse([x0 - 4, y0 - 4, x0 + 4, y0 + 4], fill=ACCENT)
    x1, y1 = points[-1]
    w = d.textlength(fuji + "  ", font=F_CALL_B)
    d.text((x1 + 10, y1), fuji + "  ", font=F_CALL_B, fill=INK, anchor="lm")
    d.text((x1 + 10 + w, y1), fos, font=F_CALL, fill=DIM, anchor="lm")


def xa2(screen, callouts=True):
    """an X-A2-like back: a 3:2 screen, on the right the command dial, PLAY,
    the four-way pad round MENU/OK, DISP/BACK; the shutter and Fn on the top plate"""
    W, H = 1580 if callouts else 1180, 800
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    bx, by, bw, bh = 40, 120, 1100, 640
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=46, fill=BODY, outline=BODY_EDGE, width=3)
    d.rounded_rectangle([bx + 640, by - 30, bx + 1010, by + 6], radius=10, fill=BODY, outline=BODY_EDGE, width=3)   # top plate
    sx, sy = bx + 60, by + 80
    d.rounded_rectangle([sx - 16, sy - 16, sx + 720 + 16, sy + 480 + 16], radius=14, fill=BEZEL)
    img.paste(screen, (sx, sy))
    # the keys
    kx = bx + 930
    shx, shy = bx + 930, by - 44                              # the shutter, on the top plate
    d.ellipse([shx - 30, shy - 14, shx + 30, shy + 14], fill=KEY, outline=KEY_EDGE, width=2)
    fnx, fny = bx + 760, by - 12
    key(d, fnx, fny, 17, "Fn")
    d.rounded_rectangle([kx + 40, by + 40, kx + 140, by + 110], radius=30, fill=KEY, outline=KEY_EDGE, width=2)
    for i in range(6):                                        # the dial's knurl
        d.line([(kx + 58 + i * 14, by + 50), (kx + 58 + i * 14, by + 100)], fill=KEY_EDGE, width=2)
    key(d, kx - 40, by + 175, 24, "PLAY")
    cx, cy = kx + 30, by + 330
    d.ellipse([cx - 100, cy - 100, cx + 100, cy + 100], fill=KEY, outline=KEY_EDGE, width=2)
    for ang, (dx, dy) in {"up": (0, -70), "down": (0, 70), "left": (-70, 0), "right": (70, 0)}.items():
        tri = {"up": [(0, -10), (-9, 6), (9, 6)], "down": [(0, 10), (-9, -6), (9, -6)],
               "left": [(-10, 0), (6, -9), (6, 9)], "right": [(10, 0), (-6, -9), (-6, 9)]}[ang]
        d.polygon([(cx + dx + x, cy + dy + y) for x, y in tri], fill=INK)
    d.ellipse([cx - 44, cy - 44, cx + 44, cy + 44], fill=BODY, outline=KEY_EDGE, width=2)
    d.text((cx, cy - 8), "MENU", font=F_KEY, fill=INK, anchor="mm")
    d.text((cx, cy + 10), "OK", font=F_KEY, fill=INK, anchor="mm")
    dbx, dby = kx + 30, by + 520
    key(d, dbx, dby, 22, "DISP/BACK", round_=False)
    if callouts:
        tx = bx + bw + 50
        callout(d, [(shx + 30, shy), (tx, shy)], "Shutter, half-way", "leave, as on every camera")
        callout(d, [(fnx + 17, fny), (tx, fny)], "Fn", "INFO: settings, exposures")
        callout(d, [(kx + 140, by + 75), (tx, by + 75)], "Command dial", "the wheel: films, values")
        callout(d, [(kx - 16, by + 175), (tx, by + 175)], "PLAY", "prints")
        callout(d, [(cx + 71, cy - 71), (tx, cy - 71)], "4-way", "the arrows: shelves, select")
        callout(d, [(cx + 31, cy + 31), (cx + 76, cy + 76), (tx, cy + 76)], "MENU/OK", "SET: open, load")
        callout(d, [(dbx + 62, dby), (tx, dby)], "DISP/BACK", "MENU: back")
    return img


def xf1(screen):
    """an XF1-like back: a 4:3 screen (640 x 480), a small pad with a dial round it"""
    W, H = 1040, 640
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    bx, by, bw, bh = 30, 40, 980, 570
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=40, fill=BODY, outline=BODY_EDGE, width=3)
    sx, sy = bx + 40, by + 45
    d.rounded_rectangle([sx - 12, sy - 12, sx + 640 + 12, sy + 480 + 12], radius=12, fill=BEZEL)
    img.paste(screen, (sx, sy))
    kx = bx + 820
    key(d, kx, by + 90, 22, "PLAY")
    cx, cy = kx, by + 290
    d.ellipse([cx - 92, cy - 92, cx + 92, cy + 92], fill=KEY, outline=KEY_EDGE, width=6)
    d.ellipse([cx - 40, cy - 40, cx + 40, cy + 40], fill=BODY, outline=KEY_EDGE, width=2)
    d.text((cx, cy - 8), "MENU", font=F_KEY, fill=INK, anchor="mm")
    d.text((cx, cy + 10), "OK", font=F_KEY, fill=INK, anchor="mm")
    key(d, kx, by + 470, 22, "DISP/BACK", round_=False)
    return img


def titled(img, title, sub):
    W, H = img.size
    out = Image.new("RGB", (W, H + 90), BG)
    out.paste(img, (0, 90))
    d = ImageDraw.Draw(out)
    d.text((40, 30), title, font=F_TITLE, fill=INK, anchor="lm")
    d.text((40, 70), sub, font=F_SUB, fill=DIM, anchor="lm")
    return out


def main():
    run("xa2", "check.txt", OUT / "xa2")
    run("xa2", "mockup-settings.txt", OUT / "xa2")
    run("xf1", "check.txt", OUT / "xf1")
    PREVIEW.mkdir(exist_ok=True)

    note = "Mockup: drawn by the film OS through fujiport.c on a fake camera; the body is schematic"
    titled(xa2(shot("xa2", "shelf")), "M-Film on a Fujifilm X-A2: the keys",
           "Each key as the port maps it. " + note).save(PREVIEW / "xa2-keys.png")
    for name, title in [("home", "Home"), ("shelf-bw", "The film shelf, B&W"),
                        ("loaded", "A roll loaded"), ("settings", "Settings")]:
        titled(xa2(shot("xa2", name), callouts=False), f"X-A2 · {title}", note).save(PREVIEW / f"xa2-{name}.png")
    titled(xf1(shot("xf1", "shelf")), "XF1 · The film shelf",
           "Its screen is 640 wide: the film OS's 720 is squeezed to fit, and small text breaks up").save(
        PREVIEW / "xf1-shelf.png")
    print("mockups in", PREVIEW)


if __name__ == "__main__":
    main()
