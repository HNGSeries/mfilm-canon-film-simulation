# References

A film stock is **measured** when its colour and tone are within the pass marks of a **paired shot** of the
real film: the same chart frames on the film, scanned by a lab as a **locked scan**, and on a Canon. Each
paired shot has a folder here with its **record**, `record.txt`: what was shot, how, what each frame is used
for, and where the chart is in each picture. The words in bold are in [GLOSSARY.md](../../GLOSSARY.md).

No film has been shot yet, so no film stock is measured. The one folder is [made-up](made-up/record.txt): a
paired shot that is drawn, not shot, so the measuring command can be tested. Its record is the example of
the format, with every field explained in it.

## Comparing two sets of pictures

```sh
cd ml-dev/films
python3 madeup.py /tmp/shot                # the made-up paired shot's pictures
python3 measure.py compare ../references/made-up/record.txt canon=/tmp/shot/canon locked=/tmp/shot/locked
```

`compare` takes a record and two sets of pictures of its frames, the look first and what it is held against
second. For the frames that decide (the chart at −1, +1 and +3 stops) it prints colour and tone, each as a
mean and a worst patch, and says whether they are within the pass marks; the other chart frames are printed
apart and decide nothing. The pass marks are provisional until a roll has been scanned twice.

- **Colour** is dE2000 with its lightness part left out, over the chart's 24 patches.
- **Tone** is the difference in L\* over the six grey patches. A black-and-white film stock has tone only,
  over all 24 patches.
- A patch that is blown or black in either picture is left out and counted.

The made-up film is not a plain print, so the command reports it as outside the pass marks: that is the
known distance the tests check (`python3 measuretest.py`). Needs numpy and Pillow.

What is not here yet: developing the Canon frames with a held scanner exposure and running this in CI for
every film stock that has a reference, and building a look from a paired shot.
