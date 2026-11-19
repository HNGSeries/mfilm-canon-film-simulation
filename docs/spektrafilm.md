# Nine film stocks from spektrafilm

[spektrafilm](https://github.com/andreavolpato/spektrafilm), by Andrea Volpato, is a physical model of colour
film. It builds each film from its maker's data: each layer's spectral sensitivity and characteristic curve, its
dyes' spectral density, the couplers between the layers. A picture is turned into light of every wavelength,
exposes the three layers, is developed, printed with an enlarger on a colour paper (a negative) or kept as it is
(a slide), and scanned. Its film profiles are CC BY-SA 4.0.

It has profiles of 18 camera films. Nine of them are on M-Film's shelf, and their colour tables now come from it:

| Film stock | spektrafilm profile | Its table before |
|---|---|---|
| Kodak Portra 160 | `kodak_portra_160` | Pat David's |
| Kodak Portra 400 | `kodak_portra_400` | M-Film's own look |
| Kodak Portra 800 | `kodak_portra_800` | Pat David's |
| Kodak Ektar 100 | `kodak_ektar_100` | M-Film's own look |
| Kodak Gold 200 | `kodak_gold_200` | M-Film's own look |
| Fujifilm Pro 400H | `fujifilm_pro_400h` | Pat David's |
| Fujifilm Velvia 100 | `fujifilm_velvia_100` | Pat David's |
| Fujifilm Provia 100F | `fujifilm_provia_100f` | Pat David's |
| Kodak Kodachrome 64 | `kodak_kodachrome_64` | Pat David's |

The other 59 keep their tables. spektrafilm has no black-and-white film and no cross-processing, and most of the
shelf's other colour films (Portra NC/VC/UC, Superia, Reala, Velvia 50, Astia, Kodachrome 25 and 200, the
Ektachromes, Agfa) are not among its profiles.

None of this measures a film: the tables before were looks made by eye, these come from the films' published data,
and only a paired shot of the real film says which is nearer ([how a film stock becomes measured](paired-shot.md)).

## How the tables are made

`ml-dev/films/spektra.py` asks spektrafilm, at one commit, for what its own program does by default, with no
spatial effects and nothing random ("lut_mode"): a negative printed on Kodak Portra Endura and the print scanned, a
slide film scanned as it is. It samples that at the darkroom's 33 × 33 × 33 points over Cineon code, where the
darkroom reads a film stock's table ([how the darkroom develops](../ml-dev/DEVELOPING.md), step 8). Each film stock's
exposure was set so that grey at 0.11, where the darkroom's scanner puts a frame's average, prints as bright as on
its table before: the brightness of the shelf stays, colour and contrast move.

Rendering needs Python 3.13 and spektrafilm; the build does not. The nine tables are kept here
(`ml-dev/films/spektra/*.tab`, with `ml-dev/films/spektra.sha256`), and `ml-dev/filmos/tools/gentables.py` puts each
behind its `LOOKnn.LUT` header and marks it `spektrafilm` in `TABLES.txt`. Grain, halation and softness stay
M-Film's, as for every film stock. The licence's notice and what was changed travel in every zip
(`SPEKTRAFILM_LICENSE.txt`, `SPEKTRAFILM_CHANGELOG.txt`): [THIRD_PARTY.md](../THIRD_PARTY.md#the-tables-from-spektrafilm-cc-by-sa-40).

## How they compare

On [`SAMPLE.CR2`](../ml-dev/films/sample/SAMPLE.CR2), developed by the darkroom built for a computer at its Large
size, and read as 30 × 20 blocks (as `measure.py` reads a picture). L\* is brightness, b\* yellow (+) to blue (−),
C\* how colourful; dE is CIEDE2000, the mean over the blocks, between the table before and the one from spektrafilm.

| Film stock | Before: L\* / b\* / C\* | spektrafilm: L\* / b\* / C\* | dE |
|---|---|---|---|
| Gold 200 | 44.1 / +7.5 / 10.1 | 44.9 / −4.0 / 9.0 | 9.4 |
| Kodachrome 64 | 47.0 / −6.3 / 9.5 | 47.3 / +0.1 / 5.4 | 7.5 |
| Portra 400 | 45.3 / +1.0 / 6.3 | 46.2 / −4.9 / 9.7 | 6.9 |
| Ektar 100 | 40.5 / −4.2 / 11.1 | 41.3 / −6.2 / 10.6 | 4.1 |
| Portra 160 | 48.2 / −1.4 / 7.6 | 49.9 / −4.5 / 8.9 | 4.0 |
| Pro 400H | 47.8 / −1.3 / 7.7 | 48.8 / −4.4 / 9.2 | 3.8 |
| Velvia 100 | 47.7 / −5.8 / 10.8 | 45.3 / −3.5 / 8.3 | 3.6 |
| Provia 100F | 46.2 / −4.2 / 8.2 | 45.1 / −3.4 / 7.2 | 3.0 |
| Portra 800 | 47.2 / −5.3 / 9.9 | 46.0 / −4.8 / 9.4 | 2.8 |

- The biggest moves: Gold 200 was warm all over, with lifted blacks; from spektrafilm its whites are white, the sky
  blue and the shadows deeper. Kodachrome 64 loses a magenta cast and much of its colour. Portra 400 goes from warm and
  muted to clear and more colourful.
- **The nine are closer to each other** than they were: 3.9 between two of them on average, against 6.8 before.
  Portra 400 and Portra 800 are 0.9 apart, hardly told apart on this frame. Modern negatives printed on the same paper
  are close in an ordinary scene; it shows on a shelf all the same.
- **The slide films come out less colourful than their name**, Velvia above all. The exposure rule above may suit
  them less than the negatives (the darkroom does not measure a slide's exposure), and this is one frame of late
  sun, with little strong colour. It wants more frames before it is believed.

spektrafilm's own program, on the same RAW with its own RAW import and its defaults, against the darkroom with the
Gold 200 table from spektrafilm: 7.8 apart as the darkroom exposes the frame, **1.6** (worst block 4.2) when the
darkroom is held at the exposure spektrafilm picked (`FOS_EV`, 0.58 stops less). What a table can't hold
(spektrafilm's halation, grain and couplers' edges, colours beyond sRGB that the darkroom cuts before the table) is
that small on this frame. The table before, M-Film's own Gold 200, was 12.0 from it.

**On a camera.** An EOS M built from main, with the nine tables on its card, developed a roll of Velvia 100 (7 frames
indoors) at its small size: each print is the computer build's with the same table, apart from grain (dE 0.00 to
0.12), at 22 to 29 s a frame as before, with nothing wrong in the log. Against the table before, 3 to 4 apart: walls
neutral instead of greenish, deeper shadows, 2 to 3 L\* darker, a little less colourful.

## Rendering them again

With spektrafilm cloned at the commit `ml-dev/films/spektra.py` names, `pip install -e` into Python 3.13, then:

```sh
python ml-dev/films/spektra.py           # writes ml-dev/films/spektra/ and spektra.sha256
python ml-dev/films/spektra.py --check   # only checks them (any Python)
```

To move to another commit of spektrafilm, change `COMMIT` and render again; `TABLES.txt` then shows which tables
changed. To take another of its films, add it to `STOCKS` with an exposure.
