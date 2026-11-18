# M-Film for RICOH GR (a GRKit film pack)

**Status: started, not yet tried on a camera.** The colour is exported; the fit, the card files and a
camera test are still to do.

M-Film's film stocks as Film Look effects of [GRKit](https://github.com/ahonn/grkit), for the RICOH GR
III, GR IIIx and GR IV. GRKit runs from the SD card and never writes the firmware. Its Film Look replaces
the camera's colour matrix and tone curves, so the GR records each JPEG in the film stock's colour.

Made for **GRKit 1.6.3** (commit `e3e71fe`) and **M-Film 0.2.3**.

> ภาษาไทยสั้นๆ: ส่วนนี้แปลงฟิล์ม 68 ตัวของ M-Film เป็น effect ของ GRKit เพื่อใช้บน GR III / IIIx / IV
> ตอนนี้ export สีเป็น `.cube` ได้แล้ว แต่ยังไม่ได้ fit, ยังไม่ได้ทำไฟล์ลงการ์ด และยังไม่ได้ลองบนกล้อง
> ขั้น fit ต้องมีไฟล์ firmware ทางการของ GR III 2.10 (`fwdc239b.bin`) ซึ่งห้าม commit
> บน GR จะได้แค่สีกับ grain/glow ของ GRKit ส่วนชั้นฟิล์ม ม้วน และห้องมืดของ M-Film ยังทำบน GR ไม่ได้

## What carries over

| M-Film | On the GR, with GRKit |
|---|---|
| The film stock's colour (`LOOKnn.LUT`) | A Film Look effect, fitted to GRKit's model. Close to M-Film's colour, not the same |
| Grain | GRKit's grain: a level and a size, set by a recipe |
| Halation | GRKit's Glow module, Halation: a strength, set by a recipe |
| The light the film is made for (5500 K, 3200 K) | The white balance of the recipe |
| The vignette | Left to the camera's shading |
| The shelf, the roll, the frame counter, the darkroom | Not on the GR: a GRKit module can draw over the live view, but gets no keys, files or shutter |

GRKit's effect model is a 3 × 3 matrix, three tone curves, hue sectors and a matrix after the curves, and
it runs in the camera's processing before the JPEG. M-Film's table is a full 33 × 33 × 33 cube, so a film
stock whose colour bends in one hue only comes out further from M-Film's than the others. `grkit effects
import` grades each fit.

## How it is made

```bash
python3 grkit/mfilm_grkit.py plan --set all
```

```bash
python3 grkit/mfilm_grkit.py cubes --set all
```

`cubes` reads each film stock's table as the camera and Darkrooms read it (steps 5 and 8 of
[DEVELOPING.md](../ml-dev/DEVELOPING.md)) and writes a `.cube` whose input is GR scene light,
sRGB-encoded with no tone curve: GRKit's `srgb` input. The tables come from the darkroom's build, which
`mfilm_grkit.py --help` lists.

The steps after it need GRKit's CLI, built from its repository at `v1.6.3`, and your own copy of the
official GR III 2.10 firmware, from which the fit reads the Standard base gamma:

```bash
python3 grkit/mfilm_grkit.py effects --set colour --firmware fwdc239b.bin --grkit path/to/grkit
```

```bash
python3 grkit/mfilm_grkit.py card --set colour --grkit path/to/grkit
```

`card` writes `grkit/out/card/colour/GRKIT/EFFECTS/`. Copy `GRKIT` to the root of a card that has GRKit
and power on. Never commit the firmware: `.gitignore` keeps `fwdc*.bin` out.

## Three sets

A GR lists at most 64 effect files on its card and installs at most 40 at once, and GRKit's own effects
share them. So the pack comes as one set a shelf, and a card should carry one set:

| Set | Film stocks |
|---|---|
| `colour` | 27: colour negative and cine |
| `slide` | 19: slide and cross-processed |
| `bw` | 22: black and white |

## Still to do

1. **Fit and grade.** Run `effects` with the firmware and read each grade. A film stock whose fit is poor
   needs `--exposure` or is left out.
2. **The exposure.** `GREY` in `mfilm_grkit.py` says where the GR's 18% grey lands in M-Film's light. It
   is a provisional number; check it against the light of `ml-dev/films/sample/SAMPLE.CR2`.
3. **The boxes.** Each effect's cover is set in `BOXES`: GRKit's layout, and its own packaging colours
   (`LOOKS`, from GRKit's site, MIT) where it has them; Rollei, Lomography and CineStill keep the colours of
   M-Film's canister. None is checked against a photo of the real box yet. `check` refuses a text GRKit
   would refuse; `grkit effects build` is the final word.
4. **A camera.** Nothing here has run on a GR. Try a set on GR IIIx 1.71 first, read `GRKIT/REPORT.TXT`, and
   keep GRKit's [recovery guide](https://github.com/ahonn/grkit/blob/main/resources/RECOVERY.md) at hand.
5. **Recipes.** `recipes` writes each film stock's grain, glow and white balance in the shape of GRKit's
   recipe model. GRKit takes recipes only from its own presets and from the camera, so for now they are
   set by hand on the camera, or proposed to GRKit.

## Licences

Each effect keeps the licence of the table it is fitted from ([THIRD_PARTY.md](../THIRD_PARTY.md)): the 59
film stocks baked from Pat David's tables are **CC BY-SA 4.0**, credited to Pat David; the 9 mixed from
M-Film's own film model are **GPL-2.0**, as the rest of M-Film. GRKit's own effects from the same Film-Luts
commit say MIT; M-Film keeps the licence its THIRD_PARTY.md gives.

GRKit is MIT and is not part of this repository. GRKit's effect model and limits are read from its
repository; nothing of it is copied here.
