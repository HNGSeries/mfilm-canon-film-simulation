# References

A film stock is **measured** when its colour and tone are within the pass marks of a **paired shot** of the
real film: the same chart frames on the film, scanned by a lab as a **locked scan**, and on a Canon. Each
paired shot has a folder here with its **record**, `record.txt`: what was shot, how, what each frame is used
for, and where the chart is in each picture. The words in bold are in [GLOSSARY.md](../../GLOSSARY.md).

No film has been shot yet, so no film stock is measured. The one folder is [made-up](made-up/record.txt): a
paired shot that is drawn, not shot, so the measuring command can be tested. Its record is the example of
the format, with every field explained in it.

## Measuring a look against its reference

```sh
make -C ml-dev/filmos/sim out/devtest out/mkcr2 out/tables/TABLES.txt
python3 ml-dev/films/measure.py look         # every film stock that has a reference
```

`look` develops the paired shot's Canon frames with the darkroom's own code built for a computer and the
film stock's table, and holds the chart's patches against the locked scan's. For the frames that decide
(the chart at −1, +0.5 and +1.5 stops) it prints colour and tone, each as a mean and a worst patch, and says
whether they are within the pass marks. The other chart frames are printed apart and decide nothing. The
pass marks are provisional until a roll has been scanned twice.

- **Colour** is dE2000 with its lightness part left out, over the chart's 24 patches.
- **Tone** is the difference in L\* over the six grey patches. A black-and-white film stock has tone only,
  over all 24 patches.
- A patch that is blown or black in either picture is left out and counted. So is a patch the Canon's
  sensor clipped, though the darkroom does not print it white: three stops over, a Canon has lost every
  patch lighter than mid grey, and the film has not. That is why the frames that decide stop at +1.5, and
  the chart at +3 and +4 is printed as "highlights" and decides nothing.
- **The scanner's exposure is held.** It is set once, so that the mid-grey patch of the chart frame at box
  speed is as light as in the locked scan, and kept for every frame, as the lab kept its own. The
  darkroom's automatic exposure, which is what people get, is held against the automatic scan where the
  paired shot has one. That is printed and decides nothing.

A record that says `measured: yes` claims its film stock as measured. From then on `look` fails, and CI
with it, when that film stock is outside a pass mark. A film stock that is not claimed is only reported.

## A paired shot's files

The Canon RAW frames and the scans are not in git. They are published with a release; the record says
where (`files at`) and has a checksum for each (`file canon/01.CR2: <sha256>`). `look` fetches the ones
that are missing into `ml-dev/filmos/sim/out/references/<name>/` and stops at a file that is not the one
the record names. A scan's patches can be kept in the repository instead of fetching the scan every time:

```sh
python3 ml-dev/films/measure.py read ml-dev/references/<name>/record.txt locked=<folder of the scan's pictures>
```

writes `locked.txt` beside the record, and `look` then uses it. The made-up paired shot has no files: its
frames and scans are drawn each time (`ml-dev/films/madeup.py`), and its film stock's table is the made-up
film, so the darkroom has to land on the "scan". A made-up film has no glow round its highlights and no
grain, so the darkroom prints it with neither; a real film stock is measured with both on. That is what CI
runs today.

## Comparing any two sets of pictures

```sh
cd ml-dev/films
python3 madeup.py /tmp/shot
python3 measure.py compare ../references/made-up/record.txt canon=/tmp/shot/canon locked=/tmp/shot/locked
```

`compare` is the second half alone: a record and two sets of pictures of its frames, the look first and
what it is held against second. It serves one scan against another, and the darkroom against Darkrooms.
Here it holds a plain print of the chart against the made-up film, which is far outside the pass marks, as
it should be.

## Building a look from a paired shot

```sh
python3 ml-dev/films/buildlook.py ml-dev/references/<name>/record.txt
```

fits a look of the shape film has to the paired shot: a mix of the three colours, a tone curve for each
with a toe and a shoulder, a second mix, then sRGB (for black-and-white, one mix to grey and one curve). It
uses only the frames the record marks "built from": the tone curves come from the six grey patches across
those exposures, the mixes from all the patches. A small smooth correction is fitted on top.

The model alone and the model with the correction are each baked into a table and measured with `look`, on
the held-back frames, which the fitting never opens. The correction stays only if it lowers the distance
there by a tenth or more. A look that fits the frames it was built from and not the held-back ones is not
measured, and the command says so.

It writes the film stock's table (`LOOKnn.LUT`, as the camera and Darkrooms read it) and `look.txt`, the
numbers the table is baked from. For a paired shot that was shot, `look.txt` goes beside the record and
belongs in the repository. Once the record says `measured: yes`, the shelf's table for that film stock is
baked from it (`ml-dev/filmos/tools/gentables.py`), in place of its table "in the style of" the film, and
CI holds it to the pass marks.

Tests, in `ml-dev/films`: `python3 measuretest.py`, `python3 looktest.py`, `python3 buildtest.py`. Needs
numpy, scipy and Pillow.

What is not here yet: curves shaped beyond the ends of the bracket by the maker's datasheet (none has been
read into numbers), and a paired shot of a real film.
