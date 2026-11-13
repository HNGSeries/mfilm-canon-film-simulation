"""packscene.py in.u16 width height out.png

A scenedump .u16 (scene-linear sRGB, 4096 = 1.0, three uint16 a pixel) as the Colour Tuner reads it:
an RGB PNG twice as high, the values' low bytes on top and their high bytes below, so a browser's
8-bit canvas gets every bit back.
"""
import sys
import numpy as np
from PIL import Image

src, w, h, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
v = np.fromfile(src, dtype="<u2")
assert v.size == w * h * 3, f"{src}: {v.size} values, not {w} x {h} x 3"
v = v.reshape(h, w, 3)
png = np.concatenate([(v & 255).astype(np.uint8), (v >> 8).astype(np.uint8)], axis=0)
Image.fromarray(png, "RGB").save(out, optimize=True, compress_level=9)
back = np.asarray(Image.open(out)).astype(np.uint16)
assert np.array_equal(back[:h] | (back[h:] << 8), v), "the PNG doesn't give the values back"
print(out, f"{w} x {h}", f"{len(open(out, 'rb').read()) / 1e6:.2f} MB", "max", int(v.max()))
