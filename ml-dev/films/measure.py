#!/usr/bin/env python3
"""How far apart two sets of pictures of the same chart frames are: the compare half of the measuring command.

    python3 measure.py compare RECORD SET=DIR SET=DIR

RECORD is the record of a paired shot (../references/<name>/record.txt; the
made-up one is the example of the format). Each SET=DIR is one set of
pictures of the record's frames: SET names the lines of the record that say
where the chart is in them ("chart in SET: ..."), DIR holds the pictures.
Frame 7's picture is the one whose name ends in 7: 07.tif, scan-07.jpg. The
first set is the look (a developer's pictures of the Canon frames), the
second what it is held against (the locked scan); differences are the second
less the first. The same command sets one scan against another, or the
darkroom against Darkrooms (#101).

In every frame that shows the chart it reads the 24 patches, the middle half
of each, found from the centres of the chart's four corner patches, and
prints

  colour   dE2000 with its lightness part left out, the mean over the
           patches and the worst patch
  tone     the difference in L*, the mean over the six grey patches and
           the worst
  dE2000   the plain one, for reading; it decides nothing

for the frames that decide ("held back, decides" in the record), and apart
from them for the others. A black-and-white film stock has tone only, over
all 24 patches: how a colour turns to grey is part of its look. A patch that
is blown or black in either picture is left out and counted: blown is any of
its three colours at the top of the picture's range, black all three at the
bottom (BLOWN, BLACK).
Grain has no method yet and prints as not measured.

Only the deciding frames are held to the pass marks (PASS: on the mean, and
WORST times that on the worst patch). They are provisional, the agent's
starting figures until a roll has been scanned twice (#113, #117).

Pictures are sRGB: 8-bit JPEG or PNG, 8- or 16-bit TIFF. A picture that says
it is in another colour space is refused. An uncompressed TIFF is read here
at its full depth; a compressed 16-bit one needs tifffile.

Needs numpy and Pillow.
"""

import argparse
import re
import struct
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))       # films.py, for a film stock's kind

PATCHES = ["dark skin", "light skin", "blue sky", "foliage", "blue flower", "bluish green",
           "orange", "purplish blue", "moderate red", "purple", "yellow green", "orange yellow",
           "blue", "green", "red", "yellow", "magenta", "cyan",
           "white", "neutral 8", "neutral 6.5", "neutral 5", "neutral 3.5", "black"]
GREYS = list(range(18, 24))

PASS = {"colour": 3.0, "tone": 3.0}     # the pass marks, on the mean. Provisional (#101, #117)
WORST = 2.0                             # the worst patch may be this many times the pass mark
# of the picture's range. Blown: any of a patch's three colours at or above BLOWN. Black: all three at or
# under BLACK (one colour at nothing is what a strong colour looks like in sRGB, the chart's cyan for one)
BLOWN, BLACK = 0.99, 0.01
PATCH_SIDE = 0.85                       # a patch's side, of the distance between two patches' centres
MIDDLE = 0.5                            # how much of the side is read
FEW = 16                                # fewer pixels than this in a patch: the chart is too small to read

# what a frame is used for (#111). The first four show the chart and are read
BUILT, DECIDES, REPORTED, DRIFT = "built from", "held back, decides", "held back, reported", "drift"
CHART_USES = [DECIDES, REPORTED, BUILT, DRIFT]
USES = CHART_USES + ["grain", "by eye", "bare film"]
FIELDS = ["paired shot", "film stock", "film format", "film expiry", "film batch", "film storage", "film camera", "film lens",
          "canon camera", "canon lens", "light", "second light", "date", "chart", "chart age",
          "lab", "process", "scanner", "scanner settings", "originals", "shot by", "consent"]
OPTIONAL = ["made up", "measured"]

M_XYZ = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])


class Bad(Exception):
    """Something in a record or a picture that stops the measuring; the message says what."""


# ---------------------------------------------------------------- colour

def to_lin(v):
    v = np.asarray(v, np.float64)
    return np.where(v <= 0.04045, v / 12.92, ((np.maximum(v, 0) + 0.055) / 1.055) ** 2.4)


def to_srgb(lin):
    lin = np.clip(np.asarray(lin, np.float64), 0, 1)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)


def lab(lin):
    """Linear sRGB (clipped to 0..1) -> CIELAB, white the picture's own (D65)."""
    xyz = np.clip(lin, 0, 1) @ M_XYZ.T / M_XYZ.sum(1)
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def lab_to_lin(l):
    """CIELAB -> linear sRGB, not clipped: outside 0..1 is outside sRGB."""
    l = np.asarray(l, np.float64)
    fy = (l[..., 0] + 16) / 116
    f = np.stack([fy + l[..., 1] / 500, fy, fy - l[..., 2] / 200], -1)
    xyz = np.where(f ** 3 > 216 / 24389, f ** 3, (116 * f - 16) * 27 / 24389) * M_XYZ.sum(1)
    return xyz @ np.linalg.inv(M_XYZ).T


def de2000(l1, l2, lightness=True):
    """CIEDE2000 between two CIELAB colours; lightness=False leaves its lightness part out."""
    L1, a1, b1 = l1[..., 0], l1[..., 1], l1[..., 2]
    L2, a2, b2 = l2[..., 0], l2[..., 1], l2[..., 2]
    cb = (np.hypot(a1, b1) + np.hypot(a2, b2)) / 2
    g = 0.5 * (1 - np.sqrt(cb ** 7 / (cb ** 7 + 25.0 ** 7)))
    a1, a2 = (1 + g) * a1, (1 + g) * a2
    c1, c2 = np.hypot(a1, b1), np.hypot(a2, b2)
    h1, h2 = np.degrees(np.arctan2(b1, a1)) % 360, np.degrees(np.arctan2(b2, a2)) % 360
    dl, dc = L2 - L1, c2 - c1
    dh = h2 - h1
    dh = np.where(dh > 180, dh - 360, np.where(dh < -180, dh + 360, dh))
    dh = np.where(c1 * c2 == 0, 0, dh)
    dH = 2 * np.sqrt(c1 * c2) * np.sin(np.radians(dh) / 2)
    lm, cm = (L1 + L2) / 2, (c1 + c2) / 2
    hs = h1 + h2
    hm = np.where(np.abs(h1 - h2) > 180, np.where(hs < 360, hs + 360, hs - 360), hs) / 2
    hm = np.where(c1 * c2 == 0, hs, hm)
    t = (1 - 0.17 * np.cos(np.radians(hm - 30)) + 0.24 * np.cos(np.radians(2 * hm))
         + 0.32 * np.cos(np.radians(3 * hm + 6)) - 0.20 * np.cos(np.radians(4 * hm - 63)))
    sl = 1 + 0.015 * (lm - 50) ** 2 / np.sqrt(20 + (lm - 50) ** 2)
    sc, sh = 1 + 0.045 * cm, 1 + 0.015 * cm * t
    rt = (-2 * np.sqrt(cm ** 7 / (cm ** 7 + 25.0 ** 7))
          * np.sin(np.radians(60 * np.exp(-((hm - 275) / 25) ** 2))))
    light = (dl / sl) ** 2 if lightness else 0
    return np.sqrt(np.maximum(light + (dc / sc) ** 2 + (dH / sh) ** 2 + rt * (dc / sc) * (dH / sh), 0))


# ---------------------------------------------------------------- the record

class Frame:
    def __init__(self, n, shows, ev, shutter, use):
        self.n, self.shows, self.ev, self.shutter, self.use = n, shows, ev, shutter, use

    def __repr__(self):
        return f"frame {self.n}"


class Record:
    """A paired shot's record: fields, its lines before the frames; frames, by
    number; chart, per set of pictures, where the chart is in each frame (None:
    in every frame that has no line of its own)."""

    def __init__(self, path):
        self.path = Path(path)
        self.fields, self.frames, self.chart = {}, {}, {}
        for i, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            line = re.sub(r"(^|\s)#.*", "", line).strip()
            if not line:
                continue
            if ":" not in line:
                raise Bad(f"{self.path}:{i}: not \"field: value\": {line}")
            key, value = (s.strip() for s in line.split(":", 1))
            key = " ".join(key.lower().split())
            try:
                self._line(key, value)
            except Bad as e:
                raise Bad(f"{self.path}:{i}: {e}") from None
        missing = [f for f in FIELDS if not self.fields.get(f)]
        if missing:
            raise Bad(f"{self.path}: nothing written for: {', '.join(missing)}")
        if not self.frames:
            raise Bad(f"{self.path}: no frames")
        for name, where in self.chart.items():
            for n in where:
                if n is not None and (n not in self.frames or self.frames[n].use not in CHART_USES):
                    raise Bad(f"{self.path}: \"chart in {name}, frame {n}\", but frame {n} does not show the chart")

    def _line(self, key, value):
        m = re.fullmatch(r"frame (\d+)", key)
        if m:
            n = int(m.group(1))
            parts = [p.strip() for p in value.split("|")]
            if len(parts) != 4:
                raise Bad("a frame is \"shows | exposure | shutter speed | used for\"")
            shows, ev, shutter, use = parts
            if n in self.frames:
                raise Bad(f"frame {n} is there twice")
            if use not in USES:
                raise Bad(f"\"{use}\" is not what a frame is used for ({'; '.join(USES)})")
            try:
                ev = float(ev.replace("−", "-")) if ev else None
            except ValueError:
                raise Bad(f"exposure \"{ev}\" is not a number of stops") from None
            if use in CHART_USES and ev is None:
                raise Bad(f"frame {n} shows the chart and has no exposure")
            self.frames[n] = Frame(n, shows, ev, shutter, use)
            return
        m = re.fullmatch(r"chart in ([\w-]+)(?:, frame (\d+))?", key)
        if m:
            n = int(m.group(2)) if m.group(2) else None
            try:
                pts = np.array([[float(c) for c in p.split(",")] for p in value.split()])
            except ValueError:
                pts = np.zeros(0)
            if pts.shape != (4, 2) or pts.min() < 0 or pts.max() > 1:
                raise Bad("where the chart is: four points \"x,y\", each a fraction of the picture from its top left")
            d = np.roll(pts, -1, 0) - pts
            turn = d[:, 0] * np.roll(d, -1, 0)[:, 1] - d[:, 1] * np.roll(d, -1, 0)[:, 0]
            if not (np.all(turn > 1e-6) or np.all(turn < -1e-6)):
                raise Bad("the four points do not go round the chart (dark skin, bluish green, black, white)")
            if n in self.chart.setdefault(m.group(1), {}):
                raise Bad(f"\"{key}\" is there twice")
            self.chart[m.group(1)][n] = pts
            return
        if key not in FIELDS + OPTIONAL:
            raise Bad(f"\"{key}\" is not a field of a record")
        if key in self.fields:
            raise Bad(f"\"{key}\" is there twice")
        if key in OPTIONAL and value not in ("yes", "no"):
            raise Bad(f"\"{key}\" is yes or no")
        self.fields[key] = value

    @property
    def name(self):
        return self.fields["paired shot"]

    @property
    def made_up(self):
        return self.fields.get("made up") == "yes"

    @property
    def film(self):
        """The film stock as the shelf has it (films.py)."""
        import films
        key = self.fields["film stock"]
        if key not in films.FILMS:
            raise Bad(f"{self.path}: film stock \"{key}\" is not on the shelf (films.py)")
        return films.FILMS[key]

    @property
    def tone_only(self):
        return self.film["kind"] == "bw"

    def charts(self, use=None):
        """The frames that show the chart, in order; with use, the ones used for that."""
        return [f for n, f in sorted(self.frames.items()) if f.use in CHART_USES and (use is None or f.use == use)]

    def corners(self, name, n):
        """The centres of the chart's four corner patches in frame n of the set, as fractions of the picture."""
        if name not in self.chart:
            raise Bad(f"{self.path}: no \"chart in {name}\" (it has: {', '.join(sorted(self.chart)) or 'none'})")
        where = self.chart[name]
        if n not in where and None not in where:
            raise Bad(f"{self.path}: no \"chart in {name}\" for frame {n}")
        return where.get(n, where.get(None))


# ---------------------------------------------------------------- pictures

EXT = (".tif", ".tiff", ".jpg", ".jpeg", ".png")


def picture_of(folder, n):
    """Frame n's picture in the folder, or None."""
    folder = Path(folder)
    if not folder.is_dir():
        raise Bad(f"{folder}: not a folder of pictures")
    hits = [p for p in sorted(folder.iterdir()) if p.suffix.lower() in EXT and re.search(r"(?:^|\D)0*%d$" % n, p.stem)]
    if len(hits) > 1:
        raise Bad(f"{folder}: more than one picture of frame {n}: {', '.join(p.name for p in hits)}")
    return hits[0] if hits else None


def _srgb_only(path, icc):
    if icc and b"sRGB" not in icc and "sRGB".encode("utf-16-be") not in icc:
        raise Bad(f"{path}: its colour profile is not sRGB. The numbers are for sRGB pictures: convert it first")


def _tiff(path):
    """An uncompressed TIFF's pixels at their own depth, or None if it is another kind of TIFF."""
    data = Path(path).read_bytes()
    if data[:4] not in (b"II*\0", b"MM\0*"):
        raise Bad(f"{path}: not a TIFF")
    e = "<" if data[:2] == b"II" else ">"
    tags = {}
    try:
        at = struct.unpack_from(e + "I", data, 4)[0]
        for i in range(struct.unpack_from(e + "H", data, at)[0]):
            tag, kind, count = struct.unpack_from(e + "HHI", data, at + 2 + 12 * i)
            size = {1: 1, 2: 1, 3: 2, 4: 4, 7: 1}.get(kind)
            if size is None:
                continue
            where = at + 10 + 12 * i if size * count <= 4 else struct.unpack_from(e + "I", data, at + 10 + 12 * i)[0]
            tags[tag] = (data[where:where + count] if size == 1
                         else list(struct.unpack_from(e + str(count) + "HI"[size // 4], data, where)))
        w, h, bits = tags[256][0], tags[257][0], tags[258]
        spp = tags.get(277, [1])[0]
        if (tags.get(259, [1])[0] != 1 or tags.get(284, [1])[0] != 1 or 273 not in tags or len(set(bits)) != 1
                or bits[0] not in (8, 16) or (tags.get(262, [2])[0], spp) not in ((2, 3), (2, 4), (1, 1))):
            return None
        _srgb_only(path, tags.get(34675))
        counts = tags.get(279) or [w * h * spp * bits[0] // 8]
        raw = b"".join(data[o:o + c] for o, c in zip(tags[273], counts))
        pix = np.frombuffer(raw, np.uint8 if bits[0] == 8 else np.dtype(e + "u2"), w * h * spp).reshape(h, w, spp)
    except (KeyError, IndexError, struct.error, ValueError):
        raise Bad(f"{path}: a TIFF this cannot read") from None
    pix = pix.astype(np.float64) / (255 if bits[0] == 8 else 65535)
    return np.repeat(pix, 3, 2) if spp == 1 else pix[..., :3]


def read_picture(path):
    """An sRGB picture as height x width x 3, 0..1 as coded."""
    path = Path(path)
    if path.suffix.lower() in (".tif", ".tiff"):
        pix = _tiff(path)
        if pix is not None:
            return pix
        try:
            import tifffile
        except ImportError:
            tifffile = None
        if tifffile:
            try:
                pix = np.asarray(tifffile.imread(str(path)))
            except Exception as e:      # tifffile raises its own, and ValueError when it lacks a codec
                raise Bad(f"{path}: {e}") from None
            if pix.dtype not in (np.uint8, np.uint16) or pix.ndim not in (2, 3):
                raise Bad(f"{path}: not an 8- or 16-bit picture")
            pix = pix.astype(np.float64) / (255 if pix.dtype == np.uint8 else 65535)
            return np.repeat(pix[..., None], 3, 2) if pix.ndim == 2 else pix[..., :3]
    from PIL import Image
    try:
        im = Image.open(path)
        im.load()
    except Exception as e:              # Pillow raises many kinds for a file it cannot read
        raise Bad(f"{path}: {e}") from None
    if im.mode not in ("RGB", "RGBA", "L"):
        raise Bad(f"{path}: a {im.mode} picture, which Pillow reads at 8 bits or not at all. "
                  "Save it as an uncompressed TIFF, or install tifffile")
    _srgb_only(path, im.info.get("icc_profile"))
    return np.asarray(im.convert("RGB"), np.float64) / 255


def homography(src, dst):
    """The 3 x 3 that takes the four points src to the four points dst."""
    rows, rhs = [], []
    for (x, y), (u, v) in zip(src, dst):
        rows += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]
        rhs += [u, v]
    return np.append(np.linalg.solve(np.array(rows, np.float64), np.array(rhs, np.float64)), 1).reshape(3, 3)


GRID = np.array([[0, 0], [5, 0], [5, 3], [0, 3]], np.float64)   # the corner patches' centres, in patches across and down


class Reading:
    """A chart as one picture has it: lab, the 24 patches' CIELAB; coded,
    their mean sRGB values, 0..1."""

    def __init__(self, lin, coded):
        self.lab, self.coded = lab(np.asarray(lin, np.float64)), np.asarray(coded, np.float64)

    @classmethod
    def of_coded(cls, coded):
        """From 24 sRGB values, as a picture of even patches would be read."""
        return cls(to_lin(coded), coded)

    @property
    def blown(self):
        return self.coded.max(1) >= BLOWN

    @property
    def black(self):
        return self.coded.max(1) <= BLACK


def read_chart(pix, corners, what="the picture"):
    """The chart's 24 patches in a picture: the middle half of each, averaged as light."""
    h, w = pix.shape[:2]
    px = np.asarray(corners, np.float64) * [w, h]
    to_chart, to_pic = homography(px, GRID), homography(GRID, px)
    half = PATCH_SIDE * MIDDLE / 2
    lin, coded = np.zeros((24, 3)), np.zeros((24, 3))
    for i in range(24):
        c, r = i % 6, i // 6
        sq = np.array([[c - half, r - half, 1], [c + half, r - half, 1], [c + half, r + half, 1], [c - half, r + half, 1]]) @ to_pic.T
        sq = sq[:, :2] / sq[:, 2:]
        x0, y0 = np.floor(sq.min(0)).astype(int)
        x1, y1 = np.ceil(sq.max(0)).astype(int)
        if x0 < 0 or y0 < 0 or x1 > w or y1 > h:
            raise Bad(f"{what}: the chart's {PATCHES[i]} patch is outside the picture")
        ys, xs = np.mgrid[y0:y1, x0:x1]
        p = np.stack([xs + 0.5, ys + 0.5, np.ones_like(xs)], -1) @ to_chart.T
        inside = (np.abs(p[..., 0] / p[..., 2] - c) <= half) & (np.abs(p[..., 1] / p[..., 2] - r) <= half)
        if inside.sum() < FEW:
            raise Bad(f"{what}: the chart is too small to read ({int(inside.sum())} pixels in a patch)")
        box = pix[y0:y1, x0:x1][inside]
        lin[i], coded[i] = to_lin(box).mean(0), box.mean(0)
    return Reading(lin, coded)


def read_set(record, name, folder):
    """Every chart frame's reading from a folder of pictures, by frame number. A frame with no picture is not in it."""
    out = {}
    for f in record.charts():
        path = picture_of(folder, f.n)
        if path:
            out[f.n] = read_chart(read_picture(path), record.corners(name, f.n), str(path))
    return out


# ---------------------------------------------------------------- the numbers

class Number:
    """A mean over patches and the worst of them: where it is (frame, patch)."""

    def __init__(self, values, frames, patches):
        self.n = len(values)
        self.mean = float(np.mean(values)) if self.n else None
        worst = int(np.argmax(values)) if self.n else None
        self.worst = float(values[worst]) if self.n else None
        self.frame, self.patch = (frames[worst], patches[worst]) if self.n else (None, None)

    def within(self, mark):
        return self.n > 0 and self.mean <= mark and self.worst <= WORST * mark


class Group:
    """The frames of one use, measured together."""

    def __init__(self, use, frames, a, b, tone_only):
        self.use, self.frames, self.tone_only = use, frames, tone_only
        self.missing = [f for f in frames if f.n not in a or f.n not in b]
        self.read = [f for f in frames if f not in self.missing]
        self.patches = 24 * len(self.read)
        self.blown = self.black = 0
        col, tone, plain, signed = ([], [], []), ([], [], []), ([], [], []), []
        self.per_frame = {}
        for f in self.read:
            ra, rb = a[f.n], b[f.n]
            blown, black = ra.blown | rb.blown, (ra.black | rb.black) & ~(ra.blown | rb.blown)
            self.blown, self.black = self.blown + int(blown.sum()), self.black + int(black.sum())
            keep = ~(blown | black)
            dc, de, dl = de2000(ra.lab, rb.lab, lightness=False), de2000(ra.lab, rb.lab), rb.lab[:, 0] - ra.lab[:, 0]
            toned = keep if tone_only else keep & np.isin(np.arange(24), GREYS)
            for store, values, which in ((col, dc, keep), (tone, np.abs(dl), toned), (plain, de, keep)):
                store[0].extend(values[which])
                store[1].extend([f] * int(which.sum()))
                store[2].extend(np.flatnonzero(which))
            signed.extend(dl[toned])
            self.per_frame[f.n] = (float(dc[keep].mean()) if keep.any() else None, float(np.abs(dl[toned]).mean()) if toned.any() else None,
                                   int((~keep).sum()))
        self.colour = None if tone_only else Number(*col)
        self.tone, self.plain = Number(*tone), Number(*plain)
        self.lighter = float(np.mean(signed)) if signed else None

    @property
    def within(self):
        """Inside the pass marks: None when a frame has no picture, so nothing can be said."""
        if self.missing or not self.frames:
            return None
        return self.tone.within(PASS["tone"]) and (self.tone_only or self.colour.within(PASS["colour"]))


class Distance:
    """Two sets of readings of a record's chart frames, held against each other."""

    def __init__(self, record, a, b):
        self.record, self.tone_only = record, record.tone_only
        self.groups = {use: Group(use, record.charts(use), a, b, self.tone_only) for use in CHART_USES}

    @property
    def decides(self):
        return self.groups[DECIDES]

    @property
    def within(self):
        return self.decides.within


def compare(record, name_a, folder_a, name_b, folder_b):
    """The distance between two folders of pictures of a record's frames."""
    return Distance(record, read_set(record, name_a, folder_a), read_set(record, name_b, folder_b))


def _ev(f):
    return "0" if not f.ev else f"{f.ev:+g}".replace("-", "−")


def report(d, name_a, name_b):
    r = d.record
    out = [f"{r.film['name']}, paired shot \"{r.name}\"{' (made up)' if r.made_up else ''}: {name_a} against {name_b}"]
    for use in CHART_USES:
        g = d.groups[use]
        if not g.frames:
            continue
        shows = sorted({f.shows for f in g.frames})
        out.append(f"  {use}: {'; '.join(shows)} at {', '.join(_ev(f) for f in g.frames)} "
                   f"(frame{'s' if len(g.frames) > 1 else ''} {', '.join(str(f.n) for f in g.frames)})")
        if g.missing:
            out.append(f"    no picture in both sets of frame{'s' if len(g.missing) > 1 else ''} {', '.join(str(f.n) for f in g.missing)}")
        if not g.read:
            continue
        decides = use == DECIDES
        for label, number, mark, unit in (("colour", g.colour, PASS["colour"], ""), ("tone", g.tone, PASS["tone"], " L*"),
                                          ("dE2000", g.plain, None, "")):
            if number is None:
                out.append(f"    {label:7} not measured: a black-and-white film stock is held to tone alone, over all 24 patches")
                continue
            if not number.n:
                out.append(f"    {label:7} no patch left to read")
                continue
            line = (f"    {label:7} mean {number.mean:5.2f}{unit}   worst {number.worst:5.2f}{unit} "
                    f"(frame {number.frame.n}, {PATCHES[number.patch]})")
            if mark is None:
                line += "   for reading"
            elif decides:
                line += f"   {'within' if number.within(mark) else 'OUTSIDE'} the pass mark of {mark:g}, {WORST * mark:g} on the worst patch"
            if label == "tone" and g.lighter is not None and abs(g.lighter) >= 0.05:
                line += f"; {name_b} is {'lighter' if g.lighter > 0 else 'darker'} by {abs(g.lighter):.2f}"
            out.append(line)
        out.append("    by frame: " + ", ".join(
            f"{f.n} ({'' if g.tone_only else ('–' if g.per_frame[f.n][0] is None else '%.2f' % g.per_frame[f.n][0]) + ' / '}"
            f"{'–' if g.per_frame[f.n][1] is None else '%.2f' % g.per_frame[f.n][1]})" for f in g.read)
            + ("   tone" if g.tone_only else "   colour / tone"))
        left = g.blown + g.black
        out.append(f"    left out: {left} of {g.patches} patches" + (f" ({g.blown} blown, {g.black} black)" if left else ""))
        if decides:
            out.append("    " + {True: "within the pass marks", False: "OUTSIDE the pass marks",
                                 None: "not judged: frames are missing"}[g.within])
    if not d.decides.frames:
        out.append("  no frame is held back to decide: nothing here is held to a pass mark")
    out.append("  grain: not measured (it has no method yet)")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="How far apart two sets of pictures of the same chart frames are.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compare", help="chart patches in two sets of pictures of a record's frames")
    c.add_argument("record")
    c.add_argument("look", metavar="SET=DIR", help="the look: where the chart is, and the folder of pictures")
    c.add_argument("against", metavar="SET=DIR", help="what it is held against")
    a = ap.parse_args()
    try:
        sets = []
        for s in (a.look, a.against):
            if "=" not in s:
                raise Bad(f"\"{s}\": a set is SET=DIR, as in canon=developed/")
            sets += s.split("=", 1)
        record = Record(a.record)
        print(report(compare(record, *sets), sets[0], sets[2]))
    except Bad as e:
        sys.exit(f"measure: {e}")


if __name__ == "__main__":
    main()
