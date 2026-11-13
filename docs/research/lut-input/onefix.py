"""Would one change to the tables' input move every film stock at once? (#97)

    python onefix.py <ml-dev> --apple apple_srgb.jpg

Replaces what the build feeds the tables (the scanner's exposure, the sRGB
curve, a highlight roll-off) with one tone curve for all three channels,
read off a finished photo of the same RAW (quantile matching of the linear
picture to the photo), and measures every table again against the photo
route. The curve is fitted on the one picture it is measured on, so this is
the most a tone curve alone can do, not a design.
"""

import argparse
import sys
from pathlib import Path

import numpy as np

import lutinput as L


def fit_curve(lin, photo):
    """One monotone curve, linear value -> photo code, from the two pictures' quantiles."""
    q = np.linspace(0, 100, 513)
    x, y = np.percentile(lin.reshape(-1), q), np.percentile(photo.reshape(-1), q)
    x = np.maximum.accumulate(x + np.arange(len(x)) * 1e-9)
    return lambda v: np.interp(v, x, y).astype(np.float32)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mldev")
    ap.add_argument("--apple")
    a = ap.parse_args()
    films_dir = Path(a.mldev) / "films"
    sys.path.insert(0, str(films_dir))
    import lut as luts
    from filmluts import DIR, FILMS, STOCKS

    pics = L.develop(films_dir / "sample" / "SAMPLE.CR2", a.apple)
    photos = {"canon": "photo_canon"}
    if a.apple:
        photos["apple"] = "photo_apple"
    lin = pics["lin_asshot"]
    curves = {n: fit_curve(lin, pics[p]) for n, p in photos.items()}
    for n, c in curves.items():
        print(f"curve from {n}: linear 0.02 0.05 0.09 0.18 0.36 0.72 -> code "
              + " ".join(f"{float(c(v)) * 255:.0f}" for v in (0.02, 0.05, 0.09, 0.18, 0.36, 0.72)))
    print("no film, the fed picture against the photo: "
          + "; ".join(f"curve {cn} vs photo {pn}: dE {L.compare(curves[cn](lin), pics[pp], False)['de_mean']:.2f}"
                      for cn in curves for pn, pp in photos.items()))

    res = {}
    for key, path, brand, name, iso, kind in STOCKS:
        if kind == "print":
            continue
        f = FILMS[key]
        table = luts.load(str(films_dir / "luts" / DIR / f"{path}.cube"), "srgb")
        grid = L.baked(luts, table)
        ev = L.scanner_ev(pics["lin_daylight"], bool(f.get("slide"))) + f["ev"]
        today = L.way_a(luts, grid, L.exposed(lin, ev))
        for pn, pp in photos.items():
            target = L.way_b(table, pics[pp])
            res.setdefault((kind, pn, "today"), []).append(L.compare(today, target, kind == "bw"))
            for cn, c in curves.items():
                fixed = L.way_b(table, c(lin))
                res.setdefault((kind, pn, "curve " + cn), []).append(L.compare(fixed, target, kind == "bw"))
    print("\nagainst the photo route: dE2000 mean (lowest to highest film stock), L* diff, contrast, chroma")
    for (kind, pn, how), v in res.items():
        de = [r["de_mean"] for r in v]
        extra = f"  chroma {np.mean([r['chroma'] for r in v]):.2f}  hue {np.mean([r['hue_abs'] for r in v]):.1f}" if "chroma" in v[0] else ""
        print(f"  {kind:5s} photo {pn:5s} fed {how:11s}  dE {np.mean(de):5.2f} ({min(de):.1f} to {max(de):.1f})  "
              f"L* {np.mean([r['dL'] for r in v]):+5.1f}  contrast {np.mean([r['contrast'] for r in v]):.2f}{extra}")


if __name__ == "__main__":
    main()
