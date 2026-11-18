"""make check: the fake cameras' screens show the film OS, and at their own size.

    python3 checkshots.py out/check/xa2 out/check/xf1

Each shot must be the camera's width x 480, mostly drawn (not LiveView showing
through everywhere), and the screens the script went to must differ.
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image

WIDTH = {"xa2": 720, "xf1": 640}
SHOTS = ["home", "shelf", "shelf-turned", "loaded"]
LIVEVIEW = (40, 70, 60)

bad = 0
for d in map(Path, sys.argv[1:]):
    pics = {}
    for name in SHOTS:
        p = d / f"{name}.ppm"
        if not p.exists():
            print(f"{p}: missing"); bad += 1; continue
        a = np.asarray(Image.open(p).convert("RGB"))
        pics[name] = a
        if a.shape != (480, WIDTH[d.name], 3):
            print(f"{p}: {a.shape[1]} x {a.shape[0]}, not {WIDTH[d.name]} x 480"); bad += 1
        drawn = 1 - (a == LIVEVIEW).all(axis=2).mean()
        if drawn < 0.5:
            print(f"{p}: only {drawn:.0%} drawn"); bad += 1
    for x, y in [("home", "shelf"), ("shelf", "shelf-turned"), ("shelf-turned", "loaded")]:
        if x in pics and y in pics and np.array_equal(pics[x], pics[y]):
            print(f"{d}: {x} and {y} are the same screen: the keys didn't arrive"); bad += 1
print("check: " + ("the film OS ran on " + " and ".join(p.split("/")[-1] for p in sys.argv[1:]) if not bad else f"{bad} problems"))
sys.exit(1 if bad else 0)
