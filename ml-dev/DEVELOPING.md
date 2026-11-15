# How the darkroom develops a frame

What `ml-dev/filmos/fos_dev.c` does to a Canon RAW frame, step by step, as arithmetic. It is written down
for **Darkrooms**, which has to do the same so the two give the same picture
([#132](https://github.com/HNGSeries/mfilm-canon-film-simulation/issues/132), decided in
[#119](https://github.com/HNGSeries/mfilm-canon-film-simulation/issues/119)): a difference between them can
then only come from one of these steps, and the check at the end says how big it is.

Numbers below are light on a scale where **1.0 is the camera's white level**, unless a step says
otherwise. The code holds them as integers, 4096 for 1.0. Where a detail is only in the code, the
function is named.

## The steps

**1. Black and white level.** A raw sample `s` becomes `(s − black) / (white − black)`.

- `black` is the mean of the masked columns left of the picture in this frame; 2048 if the frame has
  none or the mean is not believable (below 0 or above half the white level).
- `white` is one number per camera: `WHITE_LEVEL` in `fos_dev.c`, which lists every camera's.

**2. The frame's own white balance.** The three colours are multiplied by the balance the camera wrote
into the frame: Canon's maker note, tag `0x4001`, the four 16-bit numbers from index 63: red, green,
green, blue. The multipliers are red/green, 1, blue/green.

- They are used only if the two greens are equal, green is between 512 and 4096, and red and blue are
  each between a quarter of green and eight times it. Otherwise the frame is developed as daylight,
  with the balance that makes the camera matrix's white neutral, and the log says so.
- The film stock adds no balance of its own. Loading a roll put the camera on the film stock's Kelvin
  ([#115](https://github.com/HNGSeries/mfilm-canon-film-simulation/issues/115)).

**3. Where this frame clips.** Each balanced colour is cut at `clip`. `clip` is 1.0 unless the frame
says otherwise: a Canon's samples stop at a raw value that changes with ISO, so the frame's own blown
samples are looked for (`white_row`, `white_pile`, `white_clip`).

- For each of the three colours the brightest raw samples are counted in bins of 8 raw values (at 14
  bits), on two rows in every sixteen. A colour has a pile when its top four bins hold 16 samples or
  more and at least twice what the eight bins under them hold. `clip` is the lowest pile of the three,
  on the scale of step 1.
- With no pile nothing is blown: `clip` is 1.0, or where the brightest samples are if that is higher.
- A `clip` below 0.5 or above 1.5 is not believed, and 1.0 is used.
- If a balance multiplier is below 1, `clip` is multiplied by the least of them, so a blown pixel has
  all three colours at the clip and is neutral.

**4. Camera colour to sRGB.** A 3 × 3 matrix, as in dcraw: take the camera's `XYZ_CAM` (LibRaw's, in
`fos_dev.c`), multiply by sRGB's RGB-to-XYZ, divide each row by its sum, and invert. Each result is cut
to between 0 and `clip`. This is linear sRGB.

**5. The scanner's exposure.** The picture is multiplied by `2^(ev + the film stock's ev)`, and values
above 16 are cut (`stage_key`).

- For a negative film stock, `ev` brings the frame's key to 0.11. The key is the log-average of
  luminance: on the picture at the size of the camera's print (720 × 480), every fourth pixel each way,
  `l = 0.2126 R + 0.7152 G + 0.0722 B` cut at 1.0, `key = exp(mean(ln(l + 0.0001)))`,
  `ev = log2(0.11 / key)`, kept between −2 and +3.5.
- For a slide film stock nothing is measured: `ev` is 1.
- **Held from outside** (the measuring command): the picture is multiplied by `2^E` and nothing else.
  `E` is the whole of it, the film stock's own offset included.

**6. Vignette.** Each pixel is multiplied by `1 − 0.06 x² − 0.06 y²`, with `x` and `y` running from −1 to
1 across the picture.

**7. Glow round highlights (halation).** Where the luminance of step 5's picture is above the film
stock's threshold (`hal_thr`, 0.75 unless the film stock says otherwise), what is above it is gathered
on a grid a quarter of the 720 × 480 print each way, and spread by two passes of [1 2 1] each way
(`stage_glow`). A pixel takes the glow that is over its own share: the grid's value there, less what
the pixel's own luminance (step 5's, at the size being printed, before the vignette) is above the
threshold, and nothing where that comes below zero (`finish_pos`). This is added to the light, times
the film stock's `halation` and its tint (red 1, green 0.28, blue 0.06 unless it says otherwise). So a
highlight is not lit by its own glow: the film stock's table has a highlight's colour already, a large
bright area keeps it, and the glow falls on what lies beside it. A film stock with `halation` 0 has
none.

**8. The film stock's table.** Each colour `x` becomes a Cineon code,
`v = (685 + 300 log10(0.9892 x + 0.0108)) / 1023`, kept between 0 and 1. The three codes are a place in
the film stock's table: `LOOKnn.LUT`, 33 points a side, red changing fastest, three bytes of sRGB a
point, after an 8-byte header. Between points the table is read through the tetrahedron the place falls
in (`lut_apply`), not along the three axes. The place is held to 1/256 of the distance between two
points. The result is the print: sRGB, 8 bits.

**9. Grain.** Noise is added to the print's 8-bit values, strongest in the mid tones
(`finish_grain`). It is random, so two developers' grain never agrees pixel for pixel.

**10. The file.** A JPEG at quality 92, colour at half size each way (4:2:0), sRGB.

Steps 1 to 5 and 8 are the colour. They are what #119 means by "the same steps before the table" and
"how each reads the table", and they are what the check below is about. Steps 6, 7 and 9 are the rest of
the look. They sit outside the table, so the two developers have to agree on them as well for the same
picture, but a measured film stock's table does not carry them.

## What a patch the sensor clipped looks like

A colour cut at `clip` in step 3 or 4 does not come out white: the table prints it as a pale colour.
The measuring command has to leave such patches out, so the computer build of the darkroom writes, for
every pixel of the print, whether one of its colours reached `clip` (`FOS_DUMP_CUT`). Darkrooms needs to
be able to say the same for the frames of a reference, or its pictures have to be read with the
darkroom's.

## The check

```sh
make -C ml-dev/filmos/sim out/devtest out/tables/TABLES.txt
python3 ml-dev/films/measure.py darkrooms <folder of Darkrooms' pictures>
```

The folder holds Darkrooms' pictures of `ml-dev/films/sample/SAMPLE.CR2`, developed as people get them,
one for each of the first film stocks, named by film stock: `portra400.jpg`, `gold200.jpg`,
`ektar100.jpg`, `velvia50.jpg`, `cinestill800t.jpg`, `hp5.jpg`, `pro400h.jpg`. The command develops the
same frame with the darkroom at its Large size, reduces both pictures to 30 × 20 blocks of light, and
compares the blocks: plain dE2000, the mean and the worst block.

The provisional limit for "the same picture" is 1 on the mean and 3 at the worst block. For scale, the
darkroom against itself at another size, on the sample with Kodak Gold 200: Large against Medium is 0.33
and 1.31, Large against Small 0.59 and 2.45. So a mean under about 0.3 cannot be asked of two pictures
of different sizes; what is left at that level is grain, the glow's grid and the JPEG.

Darkrooms is closed source. Its pictures are compared here, and only the numbers go back to #132.

## The computer build's switches

`ml-dev/filmos/sim/out/devtest` is `fos_dev.c` built for a computer. Beyond what the camera does, it
reads these from the environment:

| | |
|---|---|
| `FOS_EV` | the scanner's exposure, held: the whole of step 5 |
| `FOS_DUMP_LIN` | the picture after step 4, as a file: three 32-bit integers a pixel, 4096 = 1.0 |
| `FOS_DUMP_CUT` | a byte a pixel, 1 where a colour reached `clip` |
| `FOS_BARE` | no glow and no grain (for the measuring command's made-up film) |
| `FOS_LUT_DIR` | where the tables are |
| `FOS_JPEG`, `FOS_SIZE` | the JPEG the photographer gets, and its size (1 Medium, 2 Large) |
