# Do the Film-Luts tables get the input they were made for?

Task for [#97](https://github.com/HNGSeries/mfilm-canon-film-simulation/issues/97), a child of the map
[#93](https://github.com/HNGSeries/mfilm-canon-film-simulation/issues/93). Measured 2026-11-14 on a Mac, from
`ml-dev/films/sample/SAMPLE.CR2` (EOS M, ISO 800, a street in afternoon sun) and the 59 Film-Luts tables that
expect a finished sRGB photo. The 4 cinema print tables are left out: they are
[#107](https://github.com/HNGSeries/mfilm-canon-film-simulation/issues/107). Scripts and full numbers are in
[`lut-input/`](lut-input/).

All distances are CIE ΔE2000, averaged over the 720 × 480 print. As a scale: about 1 is the smallest
difference an eye sees side by side, and 5 is plain at a glance.

## Short answer

- **No, not exactly, and the miss is the same for every film stock.** What the build feeds a table is flatter
  than a finished photo: shadows sit 12 to 22 codes (of 255) higher and the picture has 80 to 88 % of the
  contrast of a camera JPEG or of macOS's RAW developer, before and after the table.
- **Brightness is inside the range of finished photos, not outside it.** The middle of this picture reaches
  the table at code 96 (negatives) or 108 (slides). The camera's own JPEG puts it at 128, macOS's RAW developer
  at 101, dcraw's defaults at 58.
- **There is no single "input they were made for".** Two finished photos of the same RAW, through the same
  table, are 6.2 apart (camera JPEG against macOS). Today's build is 7.8 from the camera JPEG route and 5.3
  from the macOS route for negatives. So the build is about as far from a finished photo as two finished
  photos are from each other. dcraw's defaults are 13 to 20 from both.
- **The tables pass the gap through; they do not make it.** With no table at all, the fed picture is 8.5 from
  the camera JPEG and 5.7 from the macOS photo. After a table: 7.8 and 5.3.
- **One change to the input moves all 59 at once.** Every one of them goes through the same two steps: the
  scanner's exposure (`stage_key` in `fos_dev.c`) and `encode(lin, "srgb")` in `lut.py`. The gap barely
  changes from one film stock to the next (7.1 to 9.3 across the 21 negatives against the camera JPEG, 4.9 to
  5.9 against macOS). Replacing those two steps with a single tone curve read off a finished photo brings
  contrast to 1.00 for every film stock and cuts the distance to that photo's route to 3.8 (camera JPEG) or 2.7
  (macOS) for negatives, and to 1.6 or 0.6 for black-and-white.
- **Which curve is a choice, not a measurement.** The curve read off the camera JPEG leaves the build 6.8 from
  the macOS route, and the other way round 6.5. Nothing in the tables' origin says which finished photo their
  maker had in mind ([#94](https://github.com/HNGSeries/mfilm-canon-film-simulation/issues/94): made by eye,
  for ordinary photos).

## What was compared

**A, as the build does it today.** The RAW's samples boxed into the print, black subtracted, scaled to the
white level, daylight balance, clipped, the camera's matrix to linear sRGB, clipped, the scanner's exposure,
then the film stock's table as `genfilms.bake()` makes it: a 33-point grid over Cineon code, each point
decoded to light, rolled off above 0.8, given the sRGB curve, and put through the `.cube`.

**B, a finished photo first.** The same RAW developed to an 8-bit sRGB photo, then the `.cube` applied to it
directly. Three developers, because "a standard RAW developer" is not one thing:

| Name | What it is | White balance |
|---|---|---|
| canon | The camera's own JPEG, stored full-size inside the CR2. Picture Style Auto, contrast 0, saturation 0 | as shot (auto) |
| apple | macOS 27.2's RAW engine (`sips`), converted from Display P3 to sRGB | as shot |
| dcraw | LibRaw 0.22 with dcraw's defaults: BT.709 curve, brightness set so 1 % of pixels clip, no tone curve | daylight |

In each pair A is given the same white balance as B, and vignette, halation and grain are left out of both,
so the two differ only in what the table is fed.

**Checks on A.** The linear picture rebuilt in the script is 0.997 of the one the camera's code makes (median
ratio; dumped from a scratch build of `devtest`). The finished A, with the vignette added, is within 0.1 to
0.3 L\* of `devtest`'s own print for Portra 160, Pro 400H, Velvia 100, Kodachrome 64 and T-MAX 400, and
within ΔE 0.7 to 0.8 (0.2 for T-MAX) once grain is averaged away in 8 × 8 blocks. So A is the camera's
picture, not an approximation of it.

**The scanner's exposure on this frame.** Negatives: +0.44 EV from the log-average rule (the camera's code
says +0.45), plus the film stock's +0.2, so +0.64 EV. Slides and cross-processed: a fixed +1.0 EV.

## What the table is fed

Luminance code (0 to 255) the table receives for scene light a given number of stops from the picture's
log-average. Read across a row to see the tone curve of each route.

| Stops | Today, negatives | Today, slides | canon | apple | dcraw |
|---|---|---|---|---|---|
| −3 | 32 | 37 | 20 | 16 | 10 |
| −2 | 48 | 55 | 44 | 34 | 20 |
| −1 | 68 | 77 | 80 | 60 | 36 |
| 0 | 96 | 108 | 128 | 101 | 58 |
| +1 | 133 | 149 | 176 | 151 | 90 |
| +2 | 180 | 201 | 213 | 201 | 130 |
| +3 | 242 | 251 | 236 | 237 | 189 |

- Today's column is the plain sRGB curve: a straight run with no toe. All three developers fall away faster
  in the shadows. From −3 to +2 stops the build spans 148 codes, the camera JPEG 193, macOS 185.
- At the top the build keeps climbing to 242 where the camera JPEG and macOS have already shouldered off at
  236 to 237. The roll-off above 0.8 in `lut.py` is gentler than either.
- The fed picture against the photo with no table: contrast 0.80 (canon), 0.81 (apple); chroma 0.79 (canon),
  1.00 (apple); hue +3° and +4° on average, 5° to 6° in absolute terms.

## After the table

A against B, mean over the film stocks of each kind. L\* is A minus B; contrast and chroma are A over B
(spread of L\*, mean C\*); hue is the mean absolute difference in degrees, weighted by chroma.

| B | Kind (count) | ΔE mean | Lowest to highest | ΔE 95th pct | L\* | Contrast | Chroma | Hue |
|---|---|---|---|---|---|---|---|---|
| canon | negative (21) | 7.8 | 7.1 to 9.3 | 15.2 | −7.4 | 0.83 | 0.87 | 6.4° |
| canon | slide (15) | 5.6 | 5.2 to 6.4 | 10.6 | −2.8 | 0.86 | 0.90 | 6.8° |
| canon | cross-processed (3) | 5.4 | 4.8 to 5.9 | 11.3 | −3.0 | 0.86 | 1.04 | 6.0° |
| canon | black-and-white (20) | 9.0 | 6.2 to 11.9 | 19.8 | −11.0 | 0.80 | | |
| apple | negative (21) | 5.3 | 4.9 to 5.9 | 8.4 | −0.6 | 0.82 | 1.03 | 6.6° |
| apple | slide (15) | 4.7 | 4.3 to 5.4 | 8.4 | +3.8 | 0.86 | 1.07 | 5.8° |
| apple | cross-processed (3) | 4.7 | 4.1 to 5.4 | 8.9 | +3.6 | 0.86 | 1.10 | 6.4° |
| apple | black-and-white (20) | 5.1 | 3.7 to 7.5 | 10.8 | −3.8 | 0.81 | | |
| dcraw | negative (21) | 14.6 | 12.6 to 15.6 | 21.5 | +17.2 | 1.09 | 1.12 | 7.1° |
| dcraw | slide (15) | 18.5 | 16.9 to 20.1 | 27.1 | +21.9 | 1.19 | 1.19 | 6.3° |
| dcraw | cross-processed (3) | 20.5 | 17.4 to 24.3 | 30.0 | +22.6 | 1.25 | 1.06 | 16.7° |
| dcraw | black-and-white (20) | 12.1 | 10.6 to 13.9 | 19.7 | +15.1 | 1.13 | | |

The yardstick: two finished photos through the same table.

| Pair | Negative | Slide | Cross-processed | Black-and-white |
|---|---|---|---|---|
| canon against apple | 6.2 | 6.0 | 6.0 | 5.5 |
| canon against dcraw | 18.5 | 18.8 | 20.3 | 18.5 |
| apple against dcraw | 13.2 | 13.6 | 14.8 | 13.0 |

(For this table dcraw was run with the as-shot white balance, like the other two.)

**Exposure alone does not close it.** With A's exposure moved so its median matches B's, and nothing else
changed, the distance to canon is 5.6 for negatives (contrast 0.88, and A is then 4.8 L\* lighter overall),
to apple 5.0 (contrast 0.83), to dcraw 3.5 (contrast 0.83). The contrast deficit stays in every case.

Named film stocks, A against B:

| Film stock | canon: ΔE, L\*, contrast, chroma | apple: ΔE, L\*, contrast, chroma |
|---|---|---|
| Kodak Portra 160 | 7.4, −6.7, 0.84, 0.81 | 5.2, +0.5, 0.81, 0.99 |
| Fujifilm Pro 400H | 7.4, −6.4, 0.84, 0.83 | 5.3, +0.3, 0.82, 1.02 |
| Fujifilm Superia 200 | 7.3, −6.7, 0.84, 0.88 | 5.3, −0.1, 0.82, 1.03 |
| Fujifilm Velvia 100 | 6.4, −3.4, 0.86, 0.98 | 5.4, +3.8, 0.87, 1.09 |
| Fujifilm Provia 100F | 6.0, −3.3, 0.85, 0.85 | 4.6, +3.3, 0.86, 1.07 |
| Kodak Kodachrome 64 | 5.4, −2.2, 0.85, 0.97 | 4.9, +4.5, 0.84, 1.09 |
| Kodak Elite 100 X-Pro | 5.9, −3.4, 0.88, 1.05 | 5.4, +3.9, 0.88, 1.20 |
| Kodak T-MAX 400 | 9.1, −11.2, 0.80 | 5.1, −3.6, 0.80 |
| Ilford Delta 400 | 9.0, −10.9, 0.78 | 5.0, −3.8, 0.80 |

Pro 400H is the only first-set film stock among the 59.

## One change to the input

`onefix.py` swaps the scanner's exposure, the roll-off and the sRGB curve for one tone curve, the same for
red, green and blue, read off a finished photo by matching the linear picture's quantiles to the photo's.
Distance to the photo route, mean over each kind:

| Photo route | Fed | Negative | Slide | Cross-processed | Black-and-white |
|---|---|---|---|---|---|
| canon | today | 7.8 | 5.6 | 5.4 | 9.0 |
| canon | curve from canon | 3.8 | 3.7 | 2.9 | 1.6 |
| canon | curve from apple | 6.5 | 6.3 | 6.3 | 5.6 |
| apple | today | 5.3 | 4.7 | 4.7 | 5.1 |
| apple | curve from apple | 2.7 | 2.6 | 1.8 | 0.6 |
| apple | curve from canon | 6.8 | 6.4 | 6.2 | 5.2 |

- With the matching curve, contrast is 1.00 to 1.01 and L\* within 0.3 for every kind.
- What is left for colour film stocks (1.8 to 3.8) is hue, about 5° to 7°: the developer's own colour
  rendering, which a tone curve cannot give. For black-and-white almost nothing is left.
- The curve is fitted on the one picture it is scored on. Read these as the most a tone curve can do, not as
  what a shipped curve would score on other frames.

## What this does not show

- **One RAW.** One scene, one camera, one ISO. The shape of the result (flatter input, the same for every
  film stock) follows from the code and should hold; the sizes will move with the scene. For negatives the
  scanner's exposure depends on the frame, so the brightness gap in particular is this frame's.
- **Not a comparison with real film.** B is "the table used as its maker intended", which is still a look
  made by eye. A smaller distance to B is not a smaller distance to a reference.
- **No Lightroom, Canon DPP, darktable or RawTherapee.** Lightroom is installed here but cannot be driven
  from a command; the others are not installed. The three developers used already disagree by 6 to 20.
- **The camera JPEG is Picture Style Auto with auto white balance.** A Standard or Neutral style would land
  elsewhere again.

## Seen on the way, for other tickets

- The camera's code clips at a white level of 13600 for the EOS M at every ISO. In this ISO 800 frame the
  samples run to 15441, and 0.04 % of them are above 13600. LibRaw scales the same file to a higher white,
  which makes its linear picture 0.85 of the darkroom's. Anyone comparing the darkroom with LibRaw in linear
  light ([#98](https://github.com/HNGSeries/mfilm-canon-film-simulation/issues/98)) has to set the white level
  by hand first, and `rawpy`'s `user_sat` did not do it here.
- The Film-Luts tables are small: Pro 400H's is 13 points a side. The build resamples them to 33 points over
  Cineon code.

## Reproduce

```sh
python3 -m venv venv && venv/bin/pip install numpy rawpy pillow
(cd ml-dev/films && python getluts.py)                      # the tables, not kept in the repository
sips -s format tiff ml-dev/films/sample/SAMPLE.CR2 --out apple.tif          # macOS only
sips -m "/System/Library/ColorSync/Profiles/sRGB Profile.icc" -s format jpeg -s formatOptions 100 apple.tif --out apple_srgb.jpg
venv/bin/python docs/research/lut-input/lutinput.py ml-dev out --apple apple_srgb.jpg     # report.txt, results.json
(cd docs/research/lut-input && ../../../venv/bin/python onefix.py ../../../ml-dev --apple ../../../apple_srgb.jpg)
```

`--cam-dir` and `--cam-lin` take prints and a linear dump from `ml-dev/filmos/sim/out/devtest` for the checks
on A. `devtest` builds on a Mac with a one-line `malloc.h` shim (`#include <malloc/malloc.h>`,
`#define malloc_usable_size malloc_size`); the linear dump came from a scratch copy of `fos_dev.c` that writes
`pixel_linear()` for every pixel at the top of `stage_key()`. `results.json` holds every film stock's numbers.
