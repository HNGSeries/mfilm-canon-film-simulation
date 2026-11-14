"""The tables of darkroom-raw.md from results.json:  python tables.py results.json"""

import json
import sys

r = json.load(open(sys.argv[1]))
frames = [f for f in r["frames"] if "failed" not in f and "error" not in f["darkroom"]]
def name(f):
    if "SAMPLE" in f["file"]:
        return "sample (EOS M)"
    n = f["file"].split("/")[-2].replace("_", " ")
    return n.replace("maintainer", "maintainer's,") if n.startswith("maintainer") else n

print("## Same steps\n")
print("| Frame | Build | ISO | Matrix differs by | Balance differs by | Level, EV | Colour, per channel | dE2000 mean | dE2000 95 % |")
print("|---|---|---|---|---|---|---|---|---|")
for f in frames:
    c = f.get("D_vs_libraw_same_white")
    if not c or "ev" not in c:
        continue
    pre = max(abs(x - 1) for x in f["pre_vs_libraw_daylight"]) * 100
    ch = max(abs(x - 1) for x in c["channel_ratio_after_levelling"]) * 100
    print("| %s | %s | %s | %.4f | %.2f %% | %+.3f | within %.2f %% | %.2f | %.2f |" % (
        name(f), f["config"], f.get("iso", "?"), f["matrix_max_abs_diff"], pre, c["ev"], ch, c["de2000_mean"], c["de2000_p95"]))

print("\n## White level\n")
print("| Frame | Build | ISO | Build's white level | Frame saturates at | Build is off by, EV | A blown pixel comes out (linear sRGB) |")
print("|---|---|---|---|---|---|---|")
for f in frames:
    w = f["white_level"]
    if not w.get("pile"):
        continue
    ev = w["ev"]
    s = f.get("saturated_pixel_linear_srgb")
    print("| %s | %s | %s | %d | %d | %+.2f | %s |" % (name(f), f["config"], f.get("iso", "?"), w["build"], w["pile"], -ev,
                                                  "%.2f, %.2f, %.2f" % tuple(s) if s else ""))
none = [name(f) + " (ISO %s)" % f.get("iso", "?") for f in frames if not f["white_level"].get("pile")]
print("\nNo sample reaches saturation, so the frame says nothing about its white level: " + ", ".join(none) + ".")

print("\n## Balance\n")
print("| Frame | Build | Build's balance (R, B) | Canon Daylight 5200 K (R, B) | Grey under Canon Daylight comes out (linear sRGB) | dE2000 | As shot (R, B) | Grey under as shot | dE2000 |")
print("|---|---|---|---|---|---|---|---|---|")
for f in frames:
    g = f.get("grey_under_canon_balance", {})
    if "5200" not in g:
        continue
    d, a = g["5200"], g["as shot"]
    cw = f["canon_wb"]["5200"]
    aw = f["libraw"]["as_shot_wb"]
    print("| %s | %s | %.2f, %.2f | %.2f, %.2f | %.2f, %.2f, %.2f | %.1f | %.2f, %.2f | %.2f, %.2f, %.2f | %.1f |" % (
        name(f), f["config"], f["darkroom"]["pre"][0], f["darkroom"]["pre"][2], cw[0], cw[2], *d["linear_srgb"], d["de2000_at_mid_grey"],
        aw[0], aw[2], *a["linear_srgb"], a["de2000_at_mid_grey"]))

print("\n## Clips\n")
print("| Frame | Build | A camera channel over 1 after balance | sRGB under 0 after the matrix | sRGB over 1 with no camera channel clipped | Light cut by the clip at 1 |")
print("|---|---|---|---|---|---|")
for f in frames:
    c = f.get("clips")
    if not c:
        continue
    print("| %s | %s | %.2f %% | %.2f %% | %.2f %% | %.2f %% |" % (name(f), f["config"], c["camera_channel_over_1_percent"], c["srgb_below_0_percent"],
                                                         c["srgb_over_1_percent"], c["light_cut_by_clip_at_1_percent"]))

print("\n## The matrix's neutral against a film stock's\n")
print("| Light, K | A grey in that light comes out (linear sRGB, green 1) | dE2000 at mid grey |")
print("|---|---|---|")
for t in ("5000", "5200", "5500", "6000", "6504"):
    b = r["balance"][t]
    print("| %s | %.3f, 1, %.3f | %.1f |" % (t, b["linear_srgb_g1"][0], b["linear_srgb_g1"][2], b["de2000_at_mid_grey"]))
