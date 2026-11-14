# Does a frame developed with no film stock match a standard RAW developer?

Task for [#98](https://github.com/HNGSeries/mfilm-canon-film-simulation/issues/98), a child of the map
[#93](https://github.com/HNGSeries/mfilm-canon-film-simulation/issues/93). Measured 2026-11-14 on a Mac with
LibRaw 0.22.2 (rawpy 0.28), from 28 frames of 16 camera builds: `ml-dev/films/sample/SAMPLE.CR2` (EOS M,
ISO 800) and 27 public-domain CR2 files from [raw.pixls.us](https://raw.pixls.us) (CC0), which are not
committed here. Scripts and full numbers are in [`darkroom-raw/`](darkroom-raw/).

"The darkroom's picture" below is what `fos_dev.c` holds where `stage_key()` begins: scene-linear sRGB,
720 × 480, before the scanner's exposure and before any film stock. It comes from the camera's own code,
built for each camera (`devtest` with `-DCONFIG_…`), not from a copy of it.

Distances are CIE ΔE2000 over 8 × 8 block means of the print. As a scale: about 1 is the smallest
difference an eye sees side by side, and 5 is plain at a glance. EV is stops of light.

## Short answer

- **The steps are a standard RAW conversion.** Given the same white level, the darkroom's picture and
  LibRaw's are the same picture on all 28 frames: brightness within 0.013 EV, mean ΔE 0.10 to 0.66, 95 % of
  the print within ΔE 1.35. Every build's matrix is LibRaw's (largest difference 0.0001, which is rounding),
  the 1300D's included, and the balance it derives is LibRaw's "daylight" within 0.2 %.
- **The white level is where it stops matching.** `WHITE_LEVEL` is one number per camera, and a Canon
  saturates at different raw values at different ISOs: the 100D at 13583 at ISO 100 and about 15304 at
  ISO 400, the 550D at 13584 at ISO 100 and 15305 at ISO 1600. Of the 14 frames that have blown samples to
  read it from, the build's number is right within 0.02 EV on 4, too low on 6 and too high on 4.
  - **Too low** (0.08 to 0.31 EV; the sample, EOS M at ISO 800, is 0.20): highlights clip that much early
    and the whole picture is that much brighter. On the sample 1.45 % of the print has a clipped channel
    where 0.57 % would. A negative's scanner exposure cancels the brightness; a slide's fixed +1 EV does not.
  - **Too high** (0.06 to 0.26 EV: 50D and 550D at ISO 100, 7D at ISO 1250, 550D at ISO 1600): blown
    highlights come out pink, because green stops short of 1.0 while red and blue are clipped at it. A blown
    pixel is (1, 0.75, 1) on the 50D frame and (1, 0.71, 1) on the 550D frame. LibRaw does not do this: it
    lowers its white level to the frame's brightest sample. Seen by eye on the 50D frame, in the sky.
- **The fixed balance is the matrix's D65, and no Canon balance agrees with it.** A grey that Canon's own
  Daylight setting (5200 K, stored in every frame) calls neutral leaves the darkroom as roughly
  (1.2, 0.96, 0.78) in linear sRGB: warm, ΔE 5.7 to 10.1 at mid grey, median 7.8, on every one of the 28
  frames. The film stocks' own model calls 5500 K neutral (`stage_key()` shifts only film stocks whose
  balance is not 5500). By the code's own blackbody formula a grey in 5500 K light comes out
  (1.18, 1, 0.89), ΔE 5.3. So a daylight scene reaches a daylight film stock's table already warm by an
  amount plain at a glance, before the film stock has done anything.
- **The matrix is fixed per build, and that is not a problem for frames from that camera.** A CR2 carries no
  matrix to read; LibRaw looks the same table up by model name. The only way to get the wrong one is to
  develop a frame from a different camera model.
- **The two clips are what LibRaw does too, and cost little.** The clip after the balance touches 0 to 2.5 %
  of a print; the clip at 1.0 after the matrix cuts 0 to 0.5 % of the light. The clip at 0 touches up to
  20 % of the pixels of dark, noisy frames (7D at ISO 1250, EOS M at ISO 1600), where it is noise around
  black. None of it shows as a difference from LibRaw, which clips in the same places.

So, for the decision this unblocks: the camera side does not need a different conversion. It needs two
things settled before a film stock is compared with a reference, because both would otherwise be counted as
the film stock's error: the white level (a bug, pink highlights) and which light is neutral (a choice).

## What was compared

| Name | What it is |
|---|---|
| D | The darkroom's own picture: `devtest-CONFIG`, built from `fos_dev.c` with [`dump.patch`](darkroom-raw/dump.patch), which writes the picture where `stage_key()` begins and changes nothing else |
| L | LibRaw: daylight balance from the camera's matrix, sRGB primaries, no tone curve, no automatic brightness, highlights clipped, AHD demosaic, then the camera's crop boxed down to 720 × 480 |
| P | The darkroom's steps again in floating point (`steps()` in the script), used to take them apart |

"The same white balance" is the matrix's daylight on both sides. "The same white level" means LibRaw is told
the build's `WHITE_LEVEL` (its `user_sat`, which counts from black).

**Check on P.** P is within 0.015 EV and mean ΔE 0.58 of D on every frame, so it stands for the camera's code
when a step is varied.

**Why block means.** D puts each raw sample whole into one print pixel; L and P use a box filter that splits
samples between pixels. At one print pixel that is a few per cent of noise on fine detail and says nothing
about colour, so pictures are compared as 8 × 8 block means (90 × 60).

## Same steps

| Frame | Build | ISO | Matrix differs by | Balance differs by | Level, EV | Colour, per channel | dE2000 mean | dE2000 95 % |
|---|---|---|---|---|---|---|---|---|
| sample (EOS M) | EOSM | 800 | 0.0001 | 0.12 % | -0.005 | within 0.14 % | 0.36 | 1.06 |
| EOS 100D | 100D | 100 | 0.0001 | 0.16 % | -0.004 | within 1.62 % | 0.29 | 0.57 |
| EOS 1100D | 1100D | 160 | 0.0001 | 0.15 % | -0.005 | within 0.75 % | 0.23 | 0.38 |
| EOS 1300D | 1300D | 100 | 0.0001 | 0.11 % | -0.002 | within 0.40 % | 0.18 | 0.46 |
| EOS 500D | 500D | 200 | 0.0001 | 0.09 % | -0.004 | within 0.14 % | 0.15 | 0.38 |
| EOS 50D | 50D | 100 | 0.0001 | 0.13 % | -0.006 | within 1.33 % | 0.57 | 1.35 |
| EOS 550D | 550D | 100 | 0.0001 | 0.20 % | -0.012 | within 1.18 % | 0.24 | 0.45 |
| EOS 5D Mark II | 5D2 | 100 | 0.0001 | 0.15 % | -0.004 | within 0.22 % | 0.29 | 0.86 |
| EOS 5D Mark III | 5D3 | 200 | 0.0001 | 0.13 % | -0.004 | within 2.02 % | 0.17 | 0.41 |
| EOS 600D | 600D | 200 | 0.0001 | 0.13 % | -0.004 | within 0.58 % | 0.17 | 0.39 |
| EOS 60D | 60D | 100 | 0.0001 | 0.03 % | -0.003 | within 0.29 % | 0.16 | 0.33 |
| EOS 650D | 650D | 100 | 0.0001 | 0.14 % | -0.004 | within 0.21 % | 0.21 | 0.40 |
| EOS 6D | 6D | 100 | 0.0001 | 0.07 % | -0.002 | within 0.16 % | 0.19 | 0.51 |
| EOS 700D | 700D | 200 | 0.0001 | 0.04 % | -0.013 | within 0.36 % | 0.21 | 0.42 |
| EOS 70D | 70D | 100 | 0.0001 | 0.11 % | -0.005 | within 0.28 % | 0.24 | 0.66 |
| EOS 7D | 7D | 1250 | 0.0001 | 0.17 % | -0.000 | within 7.52 % | 0.59 | 0.99 |
| EOS Kiss X3 | 500D | 400 | 0.0001 | 0.09 % | -0.001 | within 0.13 % | 0.20 | 0.61 |
| EOS Kiss X4 | 550D | 100 | 0.0001 | 0.20 % | -0.004 | within 0.30 % | 0.32 | 0.73 |
| EOS Kiss X80 | 1300D | 100 | 0.0001 | 0.11 % | -0.001 | within 0.31 % | 0.19 | 0.47 |
| EOS M | EOSM | 1600 | 0.0001 | 0.12 % | -0.002 | within 5.58 % | 0.66 | 1.32 |
| EOS Rebel SL1 | 100D | 400 | 0.0001 | 0.16 % | -0.005 | within 2.25 % | 0.30 | 0.52 |
| EOS Rebel T1i | 500D | 1600 | 0.0001 | 0.09 % | -0.002 | within 0.41 % | 0.46 | 1.31 |
| EOS Rebel T2i | 550D | 1600 | 0.0001 | 0.20 % | -0.011 | within 1.13 % | 0.33 | 1.17 |
| EOS Rebel T3 | 1100D | 800 | 0.0001 | 0.15 % | -0.003 | within 0.63 % | 0.25 | 0.50 |
| EOS Rebel T3i | 600D | 100 | 0.0001 | 0.13 % | -0.004 | within 0.11 % | 0.10 | 0.27 |
| EOS Rebel T4i | 650D | 100 | 0.0001 | 0.14 % | -0.004 | within 0.42 % | 0.24 | 0.71 |
| EOS Rebel T5i | 700D | 400 | 0.0001 | 0.04 % | -0.007 | within 0.36 % | 0.10 | 0.14 |
| EOS Rebel T6 | 1300D | 200 | 0.0001 | 0.11 % | -0.010 | within 1.06 % | 0.28 | 0.59 |

## White level

| Frame | Build | ISO | Build's white level | Frame saturates at | Build is off by, EV | A blown pixel comes out (linear sRGB) |
|---|---|---|---|---|---|---|
| sample (EOS M) | EOSM | 800 | 13600 | 15304 | -0.20 | 1.00, 1.00, 1.00 |
| EOS 100D | 100D | 100 | 13583 | 13583 | -0.00 | 1.00, 1.00, 1.00 |
| EOS 50D | 50D | 100 | 15763 | 13433 | +0.25 | 1.00, 0.75, 1.00 |
| EOS 5D Mark III | 5D3 | 200 | 15488 | 15464 | +0.00 | 1.00, 1.00, 1.00 |
| EOS 60D | 60D | 100 | 12279 | 13583 | -0.17 | 1.00, 1.00, 1.00 |
| EOS 6D | 6D | 100 | 15490 | 15288 | +0.02 | 1.00, 0.98, 1.00 |
| EOS 7D | 7D | 1250 | 13584 | 12651 | +0.12 | 1.00, 0.86, 1.00 |
| EOS Kiss X4 | 550D | 100 | 15831 | 13584 | +0.26 | 1.00, 0.71, 1.00 |
| EOS Rebel SL1 | 100D | 400 | 13583 | 15304 | -0.20 | 1.00, 1.00, 1.00 |
| EOS Rebel T1i | 500D | 1600 | 13433 | 15760 | -0.25 | 1.00, 1.00, 1.00 |
| EOS Rebel T2i | 550D | 1600 | 15831 | 15305 | +0.06 | 1.00, 0.93, 1.00 |
| EOS Rebel T4i | 650D | 100 | 13645 | 13583 | +0.01 | 1.00, 0.99, 1.00 |
| EOS Rebel T5i | 700D | 400 | 15360 | 16080 | -0.08 | 1.00, 1.00, 1.00 |
| EOS Rebel T6 | 1300D | 200 | 13584 | 16383 | -0.31 | 1.00, 1.00, 1.00 |

No sample reaches saturation, so the frame says nothing about its white level: EOS 1100D (ISO 160), EOS 1300D (ISO 100), EOS 500D (ISO 200), EOS 550D (ISO 100), EOS 5D Mark II (ISO 100), EOS 600D (ISO 200), EOS 650D (ISO 100), EOS 700D (ISO 200), EOS 70D (ISO 100), EOS Kiss X3 (ISO 400), EOS Kiss X80 (ISO 100), EOS M (ISO 1600), EOS Rebel T3 (ISO 800), EOS Rebel T3i (ISO 100).

## Balance

| Frame | Build | Build's balance (R, B) | Canon Daylight 5200 K (R, B) | Grey under Canon Daylight comes out (linear sRGB) | dE2000 | As shot (R, B) | Grey under as shot | dE2000 |
|---|---|---|---|---|---|---|---|---|
| sample (EOS M) | EOSM | 2.42, 1.37 | 1.94, 1.56 | 1.34, 0.92, 0.76 | 10.1 | 2.03, 1.54 | 1.25, 0.95, 0.79 | 8.3 |
| EOS 100D | 100D | 2.41, 1.36 | 2.02, 1.54 | 1.26, 0.95, 0.77 | 8.5 | 1.99, 1.69 | 1.26, 0.96, 0.66 | 10.2 |
| EOS 1100D | 1100D | 2.52, 1.26 | 2.42, 1.44 | 1.02, 1.01, 0.79 | 6.8 | 2.83, 1.25 | 0.82, 1.05, 1.04 | 6.3 |
| EOS 1300D | 1300D | 2.29, 1.37 | 2.02, 1.50 | 1.19, 0.96, 0.83 | 6.6 | 2.02, 1.50 | 1.19, 0.96, 0.83 | 6.6 |
| EOS 500D | 500D | 2.38, 1.25 | 2.08, 1.42 | 1.20, 0.96, 0.75 | 7.9 | 2.30, 1.35 | 1.04, 1.00, 0.87 | 4.3 |
| EOS 50D | 50D | 2.33, 1.19 | 2.06, 1.36 | 1.17, 0.98, 0.74 | 7.8 | 1.96, 1.54 | 1.22, 0.98, 0.57 | 11.9 |
| EOS 550D | 550D | 2.38, 1.39 | 2.12, 1.53 | 1.16, 0.97, 0.82 | 6.2 | 2.05, 1.64 | 1.20, 0.97, 0.72 | 8.5 |
| EOS 5D Mark II | 5D2 | 2.57, 1.39 | 2.27, 1.70 | 1.15, 0.98, 0.70 | 8.6 | 2.43, 1.55 | 1.06, 1.00, 0.83 | 5.2 |
| EOS 5D Mark III | 5D3 | 2.25, 1.42 | 2.00, 1.58 | 1.18, 0.97, 0.81 | 6.6 | 1.65, 2.17 | 1.45, 0.92, 0.42 | 16.0 |
| EOS 600D | 600D | 2.50, 1.40 | 2.12, 1.55 | 1.24, 0.95, 0.80 | 7.8 | 2.07, 1.67 | 1.25, 0.95, 0.70 | 9.4 |
| EOS 60D | 60D | 2.43, 1.35 | 2.14, 1.54 | 1.17, 0.97, 0.77 | 7.1 | 2.14, 1.54 | 1.17, 0.97, 0.77 | 7.1 |
| EOS 650D | 650D | 2.41, 1.36 | 2.06, 1.62 | 1.21, 0.97, 0.72 | 8.7 | 2.11, 1.66 | 1.16, 0.98, 0.69 | 9.0 |
| EOS 6D | 6D | 2.22, 1.42 | 1.92, 1.69 | 1.20, 0.97, 0.72 | 8.5 | 1.92, 1.69 | 1.20, 0.97, 0.72 | 8.5 |
| EOS 700D | 700D | 2.42, 1.37 | 2.01, 1.49 | 1.29, 0.93, 0.83 | 8.8 | 1.94, 1.59 | 1.32, 0.93, 0.73 | 10.1 |
| EOS 70D | 70D | 2.22, 1.42 | 2.06, 1.68 | 1.08, 1.00, 0.74 | 7.7 | 2.19, 1.59 | 0.99, 1.02, 0.83 | 6.2 |
| EOS 7D | 7D | 2.33, 1.34 | 2.12, 1.49 | 1.13, 0.98, 0.81 | 5.9 | 2.12, 1.49 | 1.13, 0.98, 0.81 | 5.9 |
| EOS Kiss X3 | 500D | 2.38, 1.25 | 2.04, 1.41 | 1.23, 0.95, 0.76 | 8.2 | 2.21, 1.35 | 1.11, 0.98, 0.85 | 4.8 |
| EOS Kiss X4 | 550D | 2.38, 1.39 | 2.15, 1.53 | 1.14, 0.98, 0.82 | 5.8 | 2.21, 1.51 | 1.10, 0.99, 0.85 | 4.7 |
| EOS Kiss X80 | 1300D | 2.29, 1.37 | 2.06, 1.49 | 1.16, 0.97, 0.84 | 5.7 | 2.20, 1.41 | 1.06, 0.99, 0.94 | 2.3 |
| EOS M | EOSM | 2.42, 1.37 | 2.09, 1.63 | 1.19, 0.97, 0.71 | 8.5 | 1.58, 2.67 | 1.57, 0.91, 0.23 | 19.8 |
| EOS Rebel SL1 | 100D | 2.41, 1.36 | 2.07, 1.54 | 1.21, 0.96, 0.78 | 7.6 | 1.85, 1.80 | 1.37, 0.93, 0.58 | 12.8 |
| EOS Rebel T1i | 500D | 2.38, 1.25 | 2.06, 1.39 | 1.23, 0.95, 0.78 | 7.8 | 2.13, 1.36 | 1.17, 0.97, 0.83 | 6.2 |
| EOS Rebel T2i | 550D | 2.38, 1.39 | 2.16, 1.55 | 1.13, 0.98, 0.81 | 6.0 | 1.84, 2.11 | 1.31, 0.97, 0.42 | 15.4 |
| EOS Rebel T3 | 1100D | 2.52, 1.26 | 2.39, 1.45 | 1.03, 1.01, 0.77 | 7.2 | 1.98, 1.74 | 1.30, 0.96, 0.53 | 13.1 |
| EOS Rebel T3i | 600D | 2.50, 1.40 | 2.12, 1.54 | 1.24, 0.95, 0.82 | 7.8 | 2.43, 1.50 | 1.02, 1.01, 0.89 | 3.8 |
| EOS Rebel T4i | 650D | 2.41, 1.36 | 2.02, 1.57 | 1.25, 0.95, 0.76 | 8.6 | 1.98, 1.62 | 1.28, 0.95, 0.71 | 9.6 |
| EOS Rebel T5i | 700D | 2.42, 1.37 | 2.06, 1.51 | 1.24, 0.95, 0.82 | 7.7 | 2.08, 1.50 | 1.22, 0.95, 0.83 | 7.3 |
| EOS Rebel T6 | 1300D | 2.29, 1.37 | 2.00, 1.48 | 1.21, 0.95, 0.86 | 6.8 | 1.94, 1.70 | 1.23, 0.97, 0.67 | 9.8 |

## Clips

| Frame | Build | A camera channel over 1 after balance | sRGB under 0 after the matrix | sRGB over 1 with no camera channel clipped | Light cut by the clip at 1 |
|---|---|---|---|---|---|
| sample (EOS M) | EOSM | 1.45 % | 0.01 % | 0.66 % | 0.41 % |
| EOS 100D | 100D | 0.00 % | 0.01 % | 0.01 % | 0.00 % |
| EOS 1100D | 1100D | 0.00 % | 0.00 % | 0.00 % | 0.00 % |
| EOS 1300D | 1300D | 0.00 % | 0.00 % | 0.00 % | 0.00 % |
| EOS 500D | 500D | 0.00 % | 0.00 % | 0.00 % | 0.00 % |
| EOS 50D | 50D | 0.03 % | 0.11 % | 0.47 % | 0.09 % |
| EOS 550D | 550D | 0.00 % | 1.00 % | 0.00 % | 0.00 % |
| EOS 5D Mark II | 5D2 | 0.00 % | 6.17 % | 0.00 % | 0.00 % |
| EOS 5D Mark III | 5D3 | 0.02 % | 0.44 % | 0.22 % | 0.05 % |
| EOS 600D | 600D | 0.00 % | 0.00 % | 0.00 % | 0.00 % |
| EOS 60D | 60D | 0.15 % | 0.00 % | 0.31 % | 0.03 % |
| EOS 650D | 650D | 0.00 % | 0.00 % | 0.13 % | 0.01 % |
| EOS 6D | 6D | 0.16 % | 7.23 % | 0.05 % | 0.01 % |
| EOS 700D | 700D | 0.00 % | 0.00 % | 0.00 % | 0.00 % |
| EOS 70D | 70D | 0.00 % | 0.04 % | 0.00 % | 0.00 % |
| EOS 7D | 7D | 0.01 % | 19.81 % | 0.02 % | 0.01 % |
| EOS Kiss X3 | 500D | 0.00 % | 0.00 % | 0.00 % | 0.00 % |
| EOS Kiss X4 | 550D | 0.02 % | 0.00 % | 0.01 % | 0.01 % |
| EOS Kiss X80 | 1300D | 0.00 % | 0.00 % | 0.00 % | 0.00 % |
| EOS M | EOSM | 0.02 % | 19.36 % | 0.01 % | 0.01 % |
| EOS Rebel SL1 | 100D | 2.46 % | 0.30 % | 0.37 % | 0.50 % |
| EOS Rebel T1i | 500D | 1.35 % | 0.03 % | 0.60 % | 0.13 % |
| EOS Rebel T2i | 550D | 0.27 % | 1.61 % | 0.02 % | 0.17 % |
| EOS Rebel T3 | 1100D | 0.00 % | 0.01 % | 0.00 % | 0.00 % |
| EOS Rebel T3i | 600D | 0.01 % | 0.12 % | 0.03 % | 0.03 % |
| EOS Rebel T4i | 650D | 0.03 % | 0.00 % | 0.09 % | 0.01 % |
| EOS Rebel T5i | 700D | 0.17 % | 0.21 % | 0.07 % | 0.25 % |
| EOS Rebel T6 | 1300D | 0.40 % | 0.00 % | 0.08 % | 0.16 % |

## The matrix's neutral against a film stock's

| Light, K | A grey in that light comes out (linear sRGB, green 1) | dE2000 at mid grey |
|---|---|---|
| 5000 | 1.262, 1, 0.794 | 8.0 |
| 5200 | 1.225, 1, 0.833 | 6.9 |
| 5500 | 1.177, 1, 0.888 | 5.3 |
| 6000 | 1.111, 1, 0.974 | 3.2 |
| 6504 | 1.059, 1, 1.052 | 2.7 |

In "Same steps", *Level* is the darkroom's brightness against LibRaw's at the same white level, and *Colour*
is how far the three channels' ratios are from each other once brightness is levelled. The two largest
(7D at ISO 1250, EOS M at ISO 1600) are night frames where most of the print is noise around black.

In "White level", *Frame saturates at* is the raw value the frame's blown samples pile up at. Canon also
writes a white level into the file, which LibRaw reports; it is not the saturation value (100D at ISO 100:
the note says 12277, the samples pile at 13583), so it is not used here.

In "Balance", the multipliers are red and blue with green at 1. *Canon Daylight* is the camera's stored
setting for 5200 K, read from the maker note of each frame.

## Limits

- **No chart scene.** The ticket asked for one. There is no RAW of a colour chart in this repository, and
  none was taken from anyone else. Nothing above needs one: the same raw samples go through both sides. What
  a chart would add is how far the matrix's colours are from the chart's true colours, which neither side of
  this comparison measures, because both use the same matrix. The first paired shot will have that frame.
- **One frame is the maintainer's.** The other 27 are single public samples, one or three per camera, at
  whatever ISO they were shot. The white level is shown to change with ISO; its value at each ISO of each
  camera is not mapped.
- **14 of 28 frames have no blown sample**, so they say nothing about the white level.
- **The pink highlights were looked at on one frame** (50D); the rest are the arithmetic of a saturated pixel.
- **Canon's Daylight setting is 5200 K, not 5500 K**, and a camera's setting is its maker's taste as well as
  a measurement. The 5500 K figure is from the code's own formula, not from a frame.
- **Darkrooms was not run.** Whether it shares these two points is
  [#99](https://github.com/HNGSeries/mfilm-canon-film-simulation/issues/99).
- LibRaw is one standard developer. Its daylight balance is derived from the same matrix, so "matches
  LibRaw" says the steps are right, not that the balance is the one a photographer expects.

## Run it again

```sh
cd ml-dev/filmos && git apply ../../docs/research/darkroom-raw/dump.patch && cd sim && mkdir -p out
for c in EOSM 100D 650D 700D 6D 70D 5D3 5D2 7D 50D 60D 500D 550D 600D 1100D 1300D; do
  cc -O2 -std=gnu99 -DMFILM_VERSION='"x"' -DFOS_DEV_TEST -DCONFIG_$c -o out/devtest-$c devtest.c port_files.c films.c \
     ../fos_dev.c ../fos_print.c ../fos_looks.c ../fos_film.c ../fos_gfx.c ../fos_jpeg.c -lm
done    # on a Mac, add -I to a folder with a malloc.h that maps malloc_usable_size to malloc_size
python docs/research/darkroom-raw/darkroomraw.py ml-dev/filmos/sim/out results.json EOSM=ml-dev/films/sample/SAMPLE.CR2 50D=IMG_9516.CR2 ...
python docs/research/darkroom-raw/tables.py results.json
```

The public frames, by folder under `https://raw.pixls.us/data/Canon/`: EOS 5D Mark II `IMG_0051.CR2`,
EOS 5D Mark III `5G4A9394.CR2`, EOS 6D `EOS_6D_RAW.CR2`, EOS 7D `RAW_CANON_EOS_7D-raw.CR2`, EOS 50D
`IMG_9516.CR2`, EOS 60D `IMG_2014.CR2`, EOS 70D `RAW_CANON_EOS70D_01.CR2`, EOS 100D `IMG_3721.CR2`, EOS 500D
`IMG_0002.CR2`, EOS 550D `IMG_4047.CR2`, EOS 600D `_MG_2587.CR2`, EOS 650D `IMG_3517.CR2`, EOS 700D
`_MG_1948.CR2`, EOS 1100D `IMG_0962.CR2`, EOS 1300D `IMG_0778.CR2`, EOS Kiss X3 `IMG_2856-2.CR2`, EOS Kiss X4
`20120117-e01.CR2`, EOS Kiss X80 `IMG_3688.CR2`, EOS M `IMG_4624.CR2`, EOS Rebel SL1 `IMG_0308.CR2`, EOS Rebel
T1i `IMG_0493.CR2`, EOS Rebel T2i `IMG_9301.CR2`, EOS Rebel T3 `IMG_0294.CR2`, EOS Rebel T3i `IMG_0126.CR2`,
EOS Rebel T4i `IMG_6980.CR2`, EOS Rebel T5i `IMG_5139.CR2`, EOS Rebel T6 `IMG_2422.CR2`.
