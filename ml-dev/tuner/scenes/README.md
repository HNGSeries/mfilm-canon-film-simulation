# Photographs for the Colour Tuner

The M-Film Colour Tuner (a page kept as a Claude artifact, not in this repository) shows a film's
look on a few scenes. A photograph in it is a CR2 as the camera's darkroom has it before the film goes
on: scene-linear sRGB, 4096 = 1.0, made by `fos_dev.c` itself. These are the tools that make one.

| File | What it is |
|---|---|
| `scenedump.c` | `fos_dev.c`, stopped once the RAW is read: the screen's print (720 × 480) and a bigger print (Medium, the sensor three by three: 1728 × 1152 from 18 MP) as linear values |
| `packscene.py` | those values as the PNG the page reads: low bytes on top, high bytes below |
| `scenes.json` | the page's list of scenes, as published |
| `printdump.c` | the camera's own prints of a CR2 without grain, to check the page against |
| `check.js` | the page's darkroom (taken out of the page file) against `printdump`'s prints |

## Adding a photograph

A CR2 from a camera `fos_dev.c` knows, shot level or upright. Build for that camera (`-DCONFIG_650D`,
`-DCONFIG_6D` and so on; none is the EOS M), from `ml-dev/filmos/sim` after `make` there (the film list is
read from `out/`):

```sh
F=..            # ml-dev/filmos
T=../../tuner/scenes
gcc -O2 -std=gnu99 -I$F -o out/scenedump $T/scenedump.c port_files.c films.c \
    $F/fos_print.c $F/fos_looks.c $F/fos_film.c $F/fos_gfx.c $F/fos_jpeg.c -lm
./out/scenedump photo.CR2 out/photo_s.u16 out/photo_m.u16 1
python3 $T/packscene.py out/photo_s.u16 720 480 out/photo.png
python3 $T/packscene.py out/photo_m.u16 1728 1152 out/photo-m.png
```

Publish `photo.png` and `photo-m.png` to the artifact as `scenes/photo.png` and `scenes/photo-m.png`, and
add a line to `scenes.json`:

```json
{"id": "photo", "name": "…", "from": "…", "big": {"file": "photo-m.png", "size": [1728, 1152], "label": "Medium"}}
```

`scenedump` prints the sizes. A frame shot upright says `portrait 1 picture_x0 200 picture_w 320`: its
picture is the middle of the screen's print and its Medium print is 1152 × 1728, so its line also has
`"pic": [200, 320]` and `"size": [1152, 1728]`.

The page needs no change. A Medium print is about 5 to 6 MB as a PNG (a Large one, 2592 × 1728, about
15 MB: too much to load for each scene). The photographs themselves are not in this repository: only the
tools.

## Why two sizes

As in the camera: the exposure is metered on the screen's print and the halation gathered from it
(`stage_key`, `stage_glow`), and a bigger print is then made from its own pixels with that exposure and
that glow (`big_finish`). The page does the same, so it needs both.

## Checking the page

`scenedump` of `ml-dev/films/sample/SAMPLE.CR2` gives the page's first scene byte for byte. With the page
saved as `page.html`, `printdump` built the same way, and its prints, the dumps and the films' tables
(the page's `looks/*.png` as raw bytes, `look_<film>.bin`) in `build/` beside `check.js`:

```sh
./out/printdump SAMPLE.CR2 portra400 1 build/ref_portra400_s.rgb build/ref_portra400_m.rgb
node check.js films.json page.html
```

`check.js` names the frames it checks (`CASES`): one from an EOS M, one from a 650D shot level and one shot
upright. On 13 Nov 2026, with Portra 400, CineStill 800T, Velvia 50, HP5 and Ektar 100: the Medium print
differed from the camera's in at most 58 of 5,971,968 values, by one level; the screen's print in at most
9 of 1,036,800. (The page works the exposure out in double precision, the camera in single.)
