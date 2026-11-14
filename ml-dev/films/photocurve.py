"""The tone curve of a finished photo, read off Canon's own JPEGs.

    python photocurve.py frame.CR2 [frame.CR2 ...]

The Film-Luts tables were made for finished photos, and lut.py's "photo"
input space gives them one: the tone curve of Canon's Standard picture
style, with mid grey left where the plain sRGB curve has it (#110, #125).
This is where that curve's three numbers come from, PHOTO_FIT in lut.py.

Each frame is a CR2 shot in Standard picture style, contrast 0, sRGB, and
it carries the camera's own JPEG. The curve is read from the pair: the
linear picture's luminance quantiles (LibRaw, camera white balance, no tone
curve) against the JPEG's. A camera brightens a frame by an amount of its
own, so each frame's curve is slid along its exposure until it crosses the
plain sRGB curve at PIVOT. The points of all the frames are then fitted
together as

    display = 1 / (1 + exp(-(c0 + a s + b s^2 + c s^3)))     s = stops from PIVOT

with c0 fixed so the curve is sRGB's at PIVOT. Prints a, b and c.

PHOTO_FIT was fitted on nine public-domain frames from raw.pixls.us (CC0),
which are not kept here: under https://raw.pixls.us/data/Canon/, EOS 500D
IMG_0002.CR2, EOS 50D IMG_9516.CR2, EOS 550D IMG_4047.CR2, EOS 5D Mark II
IMG_0051.CR2, EOS Kiss X3 IMG_2856-2.CR2, EOS Kiss X4 20120117-e01.CR2,
EOS Rebel T1i IMG_0493.CR2, EOS Rebel T2i IMG_9301.CR2, EOS Rebel T3
IMG_0294.CR2. Needs numpy, rawpy and Pillow.
"""

import io
import struct
import sys

import numpy as np
import rawpy
from PIL import Image

from lut import PHOTO_PIVOT as PIVOT

LUMA = np.array([0.2126729, 0.7151522, 0.0721750])
W, H = 720, 480


def srgb_to_lin(v):
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * x ** (1 / 2.4) - 0.055)


def style(path):
    """(picture style, contrast, colour space) from Canon's maker note; 0x81 is Standard, 1 is sRGB."""
    b = open(path, "rb").read(4 << 20)

    def ifd(off):
        n = struct.unpack_from("<H", b, off)[0]
        return {struct.unpack_from("<H", b, off + 2 + 12 * i)[0]: struct.unpack_from("<HII", b, off + 4 + 12 * i) for i in range(n)}
    exif = ifd(ifd(struct.unpack_from("<I", b, 4)[0])[0x8769][2])
    maker = ifd(exif[0x927C][2])
    proc = struct.unpack_from("<11h", b, maker[0x00A0][2])
    settings = struct.unpack_from("<14h", b, maker[0x0001][2])
    return proc[10] & 0xFF, settings[13], exif.get(0xA001, (0, 0, 0))[2] & 0xFFFF


def blocks(a):
    return a.reshape(H // 8, 8, W // 8, 8).mean((1, 3))


def frame(path):
    """One frame's curve: stops from where it crosses sRGB at PIVOT, and display values."""
    with rawpy.imread(path) as raw:
        img = raw.postprocess(gamma=(1, 1), no_auto_bright=True, output_bps=16, use_camera_wb=True,
                              output_color=rawpy.ColorSpace.sRGB, user_flip=0)
        jpeg = Image.open(io.BytesIO(raw.extract_thumb().data)).convert("RGB")
    lin = np.asarray(Image.fromarray((img / 65535.0 @ LUMA).astype(np.float32), "F").resize((W, H), Image.BOX))
    photo = np.asarray(jpeg.resize((W, H), Image.BOX), np.float64) / 255
    q = np.linspace(0.5, 99.5, 199)
    x = np.percentile(blocks(lin), q)
    y = lin_to_srgb(np.percentile(blocks(srgb_to_lin(photo) @ LUMA), q))
    x0 = np.interp(lin_to_srgb(PIVOT), y, x)             # the linear value the photo shows as sRGB(PIVOT)
    s = np.arange(-5, 3.76, 0.25)
    s = s[(s >= np.log2(x[1] / x0)) & (s <= np.log2(x[-2] / x0))]
    v = np.interp(x0 * 2.0 ** s, x, y)
    keep = (v > 0.004) & (v < 0.985)
    return s[keep], v[keep]


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    ss, vv = [], []
    for path in sys.argv[1:]:
        st, contrast, space = style(path)
        if (st, contrast, space) != (0x81, 0, 1):
            print(f"{path}: not Standard, contrast 0, sRGB (style {st:#x}, contrast {contrast}, colour space {space}): left out",
                  file=sys.stderr)
            continue
        s, v = frame(path)
        print(f"{path}: {len(s)} points, {s.min():+.1f} to {s.max():+.1f} stops", file=sys.stderr)
        ss.append(s)
        vv.append(v)
    if not ss:
        sys.exit("no frame to fit")
    s, v = np.concatenate(ss), np.concatenate(vv)
    c0 = np.log(lin_to_srgb(PIVOT) / (1 - lin_to_srgb(PIVOT)))
    coef = np.linalg.lstsq(np.stack([s, s ** 2, s ** 3], 1), np.log(v / (1 - v)) - c0, rcond=None)[0]
    print("PHOTO_FIT = (%.4f, %.4f, %.4f)     # %d frames, %d points" % (*coef, len(ss), len(s)))


if __name__ == "__main__":
    main()
