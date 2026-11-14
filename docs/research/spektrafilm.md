# What can spektrafilm give M-Film as a source of colour for its film stocks?

Research note for [issue #116](https://github.com/HNGSeries/mfilm-canon-film-simulation/issues/116), a child of the map in [issue #93](https://github.com/HNGSeries/mfilm-canon-film-simulation/issues/93). It feeds the decision in [issue #110](https://github.com/HNGSeries/mfilm-canon-film-simulation/issues/110). It goes deeper on one project that [the datasheet note](https://github.com/HNGSeries/mfilm-canon-film-simulation/blob/research/real-film-data/docs/research/real-film-data.md) only touched.

Everything here was read on 2026-11-14 from a fresh clone of [spektrafilm](https://github.com/andreavolpato/spektrafilm): `main` at `3bb2c2d`, `dev` at `6cd00c8`, `experimental` at `28bf883`, and its commit history. Repository facts (stars, issues) come from GitHub's API on the same day. Three things come from outside the repository and are marked where used: the author's own forum write-up that the README links to, Creative Commons' list of compatible licences, and M-Film's own files.

**Nothing was run.** spektrafilm was not installed and no table was baked. Every statement about what it does is a reading of its code and documents. Where a statement is my own reasoning and not something a source says, it is marked **(my reasoning)**.

## Short answer

- **Yes, a 33-point colour table per film stock can be made from it, and it already ships a tool for that.** The tool's default size is 33 points, the same as the camera's darkroom. It writes a table for one film stock printed on one print paper, with grain, halation and every other effect that depends on neighbouring pixels switched off.
- **By name, it covers 9 of the 72 film stocks on M-Film's shelf, and 4 of the 7 in the first set.** It has Kodak Portra 400, Gold 200, Ektar 100 and Fujifilm Pro 400H. It does not have Fujichrome Velvia 50 (only Velvia 100), CineStill 800T (only Kodak Vision3 500T) or Ilford HP5 Plus. It has no black-and-white film stock at all on its main branch.
- **Its picture is a print on paper, not a lab scan.** A negative is printed through a model of a darkroom enlarger onto a model of a print paper, and the print is then "scanned" by the standard human observer under a standard light. There is no model of a Noritsu, a Frontier or any other real scanner, and no step that turns a negative into a positive the way scanner software does.
- **The numbers come from the makers' datasheets, read off the graphs, then corrected and fitted by the author.** The points read off the graphs and the code that turns them into the shipped data files were taken out of the public repository in March 2026. Only the finished data files are published now.
- **The author does not claim it matches real film.** His own estimate, in February 2025, was "something like 60-85% accurate or more, which doesn't say much", and he wrote that the amount of saturation "is arbitrarily guessed". The repository holds no measured comparison with real film. Its tests compare the code with its own earlier output.
- **The licences are stricter than Film-Luts' MIT licence.** The code is GPLv3. The data files, and by the author's own licence text any table made from them, are CC BY-SA 4.0: credit is required on every copy and changed versions must stay CC BY-SA 4.0. M-Film is GPL-2.0 and Darkrooms is closed-source. Whether either can carry such tables is a question for the maintainer and, if needed, the author. This note quotes the texts and gives no legal opinion.
- **It needs Python 3.13 and a dozen scientific libraries, and its author says it takes about 10 seconds for a 6-megapixel picture.** That makes it a tool for the computer that builds the card files, not something the camera could run **(my reasoning)**.
- **The project has been quiet since July 2026.** The last public commit is from 2026-07-08 and the author's last reply on GitHub is from 2026-06-04. Three licence questions from other projects, opened in October 2026, have no answer from him.
- **As a starting model it is careful about the things a datasheet describes, for the few film stocks it has.** What is missing between its output and a lab scan is the scanner and its software, a real choice of colour balance and of black and white points, and any check against real film. A paired shot would still be needed for every film stock **(my reasoning)**.

## 1. What goes in, what comes out, and whether a table can be made

### The picture it expects and gives

The runtime's own README states the contract: "linear RGB in named primaries → film + print + scan physics → linear RGB in named primaries" [1]. In plain words:

- **In:** a picture in linear light, as the scene was, not yet given any display curve. The colour space is named by the caller; the default is ProPhoto RGB [2]. The desktop program can also open a RAW file itself, through the `rawpy` library [3].
- **Out:** a picture in linear light in a named output colour space, sRGB by default, with the sRGB display curve applied unless the caller turns it off [2].
- The main README adds the practical advice: "The simulation expects linear scene-referred files as input", exported for example as "a 32-bit float TIFF in linear ProPhoto RGB" [3].

### The steps, as read from the code

All of this is `src/spektrafilm/runtime/` at `3bb2c2d`.

1. **Prepare.** Optional automatic exposure (centre-weighted), then crop and resize [4].
2. **Expose the film.** Each pixel's RGB is turned back into a spectrum of light, and that spectrum is weighed by the film stock's three spectral sensitivity curves to give the exposure of its three layers. The light is taken to be the film stock's own reference light (daylight D55 for most, tungsten for the two tungsten cinema films). Exposure compensation, lens blur, a diffusion filter and halation are applied here [5].
3. **Develop the film.** The exposure goes through the film stock's characteristic curves to give the density of the cyan, magenta and yellow dyes. The interlayer effect of the dye couplers is applied here, and grain is added here [6].
4. **Print it.** The dye densities become a spectrum of light passing through the negative, lit by an enlarger lamp (a 3400 K lamp behind a heat filter) through yellow, magenta and cyan filters. That light is weighed by the print paper's spectral sensitivities, and the result goes through the paper's own characteristic curves to give the dyes of the print [7].
5. **"Scan" the print.** The print's dyes become a spectrum of light under the print's viewing light (D50 for the papers, a cinema projector lamp for the two print films), and the CIE 1931 standard observer turns that into a colour. Glare, blur and an unsharp mask can be added. The colour is converted to the output colour space [8].

One switch, `scan_film`, skips step 4 and looks at the film directly instead of the print [9]. For a slide film that gives the slide. For a negative it gives a picture of the orange negative itself: I found no step anywhere in the code that inverts it, and the code that sets black and white points says of this case "do not correct negative film scans" [10].

Two details of step 4 matter for M-Film:

- **The colour balance of the print is set by a rule, not by a person or a scanner.** The enlarger's neutral filter setting is looked up per pair of film stock and paper from a table shipped with the code [11]. The README describes it as "the starting settings that make an 18% gray target photographed with the correct reference illuminant fully neutral in the final print" [3].
- **Print exposure is tied to middle grey.** The print exposure is scaled so that the negative of an 18.4 % grey gets a fixed exposure on the paper [7].

### Making a table

spektrafilm has its own table maker, the package `spektrafilm_lut_creator`, with a command-line tool. Its README example is exactly the size M-Film uses [3]:

```
spektrafilm-lut build --film kodak_portra_400 --print kodak_portra_endura \
    --input vlog --output srgb --topology 1lut --resolution 33
```

What I read about it:

- **Size.** `resolution: int = 33` is the default [12]. Any size from 2 up is accepted.
- **File formats.** Adobe `.cube`, a Panasonic Lumix variant of `.cube`, Autodesk `.3dl`, and a Hald image as an 8-bit PNG [13].
- **One table per film stock and paper.** The "1lut" layout is one table that does film, print and scan together. Other layouts split the chain into two, three or four tables [12][14].
- **What is switched off for a table.** A table can only map one colour to one colour, so the tool forces a "LUT mode" that turns off every effect that depends on neighbouring pixels or on chance: halation, grain, glare, lens blur, the diffusion filters and the spread of the coupler effect across the picture. It also turns off automatic exposure, exposure compensation, the scanner's black and white point correction and the unsharp mask [15]. The colour part of the coupler effect stays on [16].
- **What the table expects in.** The tool makes the grid in an encoded input space, decodes it to linear light and hands that to the runtime [13]. The input spaces it accepts are seven display encodings (sRGB, Rec.709, Display P3, Rec.2020, DCI-P3, Adobe RGB, ProPhoto RGB), sixteen camera log encodings (among them ARRI LogC3, Sony S-Log3, Panasonic V-Log and Canon Log 3) and three HDR encodings [17]. **Cineon is not among them.** Plain linear inputs are registered but switched off, because, in the code's words, "a uniform [0, 1] .cube domain can't represent scene-linear highlights past diffuse white without a log shaper" [17].
- **Exposure.** For a display-encoded input such as sRGB, the tool by default multiplies the picture so that the brightest input value lands 4 stops above middle grey on the film, and its own notes say that the picture "comes out slightly brighter than its source preview" as a side effect [12].
- **Slide film.** The table maker always runs film, then print, then scan. It never sets the `scan_film` switch [18]. So a slide film given to it is printed onto the named paper, not looked at directly, which is not how a slide is seen. The `experimental` branch keeps this: its bake is fixed to the "full film -> print -> scan route" [19].
- **A quality report.** An optional check runs eleven tests on each table. Five look at the table itself: does it reproduce spektrafilm's own pipeline between grid points, and is it smooth and free of folds. Six look at the model's output for odd behaviour, such as a hue turning by more than 30 degrees. None of them compares with real film [20].
- **What the tool says about its output.** Every bundle gets a README that says the table is "the *neutral developed and printed* render" and "**not** a stylistic look-up grade" with "no extra contrast, no shifted hue, no taste layer" [21].

### Fitting it to the camera's table

The camera's table is a 33-point grid over Cineon code values, red changing fastest; each grid point is decoded to linear light, sent through the film stock's colour function, and stored as 8-bit values (`ml-dev/filmos/fos_dev.c`, `lut_build`, with `GRID 33`) [22]. `ml-dev/films/lut.py` says of its encodings that scene-linear Rec.709 has "0.18 = mid grey" and that the output of every table is "taken as an sRGB / Rec.709 display image" [23].

Set against what was read above **(my reasoning, nothing run)**:

- The shipped `spektrafilm-lut` tool cannot make that table directly, because it has no Cineon input.
- The runtime underneath can be called with any linear picture. M-Film's build could make its own 33-point grid, decode it from Cineon to linear Rec.709 as it does today, hand that to the runtime in LUT mode, and store the sRGB result. The grid order is the same in both (red fastest) [13][22].
- The runtime's middle grey is 0.184 [5], close to the 0.18 M-Film uses, so the two exposure scales should line up without a large correction. This was not tested.
- Grain, halation and softness would stay M-Film's own, as they do with Film-Luts today, because a table cannot carry them.

## 2. Which film stocks and print papers it has

### What is in the repository

On `main` there are 28 data files: 20 films and 8 print materials [24][25].

| Kind | Film stocks in spektrafilm `main` |
|---|---|
| Colour negative, still | Kodak Portra 160, Portra 400, Portra 800 (also pushed one and two stops), Ektar 100, Gold 200, Ultramax 400; Fujifilm Pro 400H, C200, X-Tra 400 |
| Colour negative, cinema | Kodak Vision3 50D, 250D, 200T, 500T; Kodak Verita 200D |
| Slide | Kodak Ektachrome 100 (E100), Kodachrome 64; Fujifilm Velvia 100, Provia 100F |
| Print paper | Kodak Portra Endura, Supra Endura, Ultra Endura, Endura Premier, Ektacolor Edge; Fujifilm Crystal Archive Type II |
| Cinema print film | Kodak Vision 2383, Kodak Vision Premier 2393 |

Each negative names the paper it is meant to be printed on: the Kodak still films name Kodak Portra Endura, the Fujifilm ones name Fujifilm Crystal Archive Type II, the cinema films name Kodak 2383 [24]. One paper carries the author's comment "problematic" (Kodak Ultra Endura) [25].

The `dev` and `experimental` branches add three black-and-white data files: Kodak Double-X Negative Film 5222, Kodak Tri-X Reversal Film 7266 and Kodak Print Film 2302. All three are cinema materials [26]. **The file named `kodak_trix` is the cinema reversal film 7266, not the still film Tri-X 400.** An open request on the project's tracker says the same and lists HP5 Plus among the still films that do "not exist upstream" [27].

### Against the first set

| First set | In spektrafilm? | Nearest thing it has |
|---|---|---|
| Kodak Portra 400 | Yes | |
| Kodak Gold 200 | Yes | |
| Kodak Ektar 100 | Yes | |
| Fujifilm Pro 400H | Yes | |
| Fujichrome Velvia 50 | No | Fujifilm Velvia 100, a different film with its own datasheet |
| CineStill 800T | No | Kodak Vision3 500T. In his forum write-up the author shows a "Simulation with Kodak Vision3 to imitate Cinestill" made by raising halation by hand [28] |
| Ilford HP5 Plus | No | Nothing. No file named for Ilford or HP5 exists in any branch or anywhere in the history |

### Against the whole shelf

`FILMS.md` lists 72 film stocks. Matching by name only:

| Shelf section | On the shelf | Also in spektrafilm `main` | Which |
|---|---|---|---|
| Colour negative | 25 | 6 | Portra 400, Ektar 100, Gold 200, Portra 160, Portra 800, Pro 400H |
| Slide and cross-processed | 19 | 3 | Velvia 100, Provia 100F, Kodachrome 64 |
| Black and white | 22 | 0 | |
| Cinema | 6 | 0 as a film to shoot | Kodak 2383 and 2393 exist, but as print films for the second stage |
| **All** | **72** | **9** | |

Near misses, not counted: spektrafilm's "Fujifilm X-Tra 400" was read from the datasheet "fujicolor superia x-tra 400 NEW AF3-151E" [29], and M-Film has a "Fujicolor Superia 400". spektrafilm's Ektachrome is the 2018 E100, and M-Film has E100GX and E100VS. Whether any of these pairs is the same film was not checked.

The author keeps a public vote on which film stock to read in next; the README links to it [3]. I did not read the vote.

## 3. Where the numbers come from, and how close the author says it is

### The source of each film stock's numbers

Every shipped data file carries the same statement of origin: "This profile was created by processing raw measurement data from data-sheets and/or scientific papers. Original data are property of the respective holders. Film/photo-paper: Kodak and Fujifilm data-sheets, scientific publications, and technical material." It then lists five public sets of measured surface colours (among them Munsell and a set of human skin) that were also used [30].

The data files themselves do not say which datasheet. The repository's history does. Until 2026-03-17 the repository held, for every film stock, the points read off the datasheet graphs as small CSV files, with a note naming the sheet [29]:

| Film stock | Note in its folder |
|---|---|
| Kodak Portra 400 | "Portra 400 e4050 2016" |
| Kodak Gold 200 | "kodak gold 200 2007 e-7022 (same as 2016 e-7022)", Status M, daylight |
| Kodak Ektar 100 | "e4046 2016", Status M |
| Fujifilm Pro 400H | "Datasheet: AF3-176E" |
| Fujifilm Velvia 100 | "AF3-202E" |
| Kodak Vision3 500T | "2015 h15219t" |
| Kodak Portra Endura paper | "e-4021 september 2009" |
| Kodak 2383 print film | "March 2005 H-1-2383t" |

These are the same Kodak and Fujifilm sheets the datasheet note opened, except that the Gold 200 sheet named here is the 2007 one and the current one is dated June 2023.

What the folders held shows what was not in the datasheets [29]:

- For Portra 400, Ektar 100 and Pro 400H there were only two dye density curves, "mid" and "min": the whole film at mid-grey and at minimum density. There were no separate cyan, magenta and yellow dye curves.
- A folder called `generic_a` held separate cyan, magenta and yellow dye curves taken from a textbook: "Giorgianni Madden Kriss, Digital Color Management, Wiley 2009, Page 112, Film A".
- The README says the same of Portra 400: "the CMY diffuse densities are generic because they are usually not published" [3].
- Velvia 100 and the Vision3 films did have separate dye curves of their own.

**Those CSV files and the code that made the data files are no longer public.** Commit `a6dbcfd` of 2026-03-17, "refactor: move relevant data to profiles_creator", deleted them, and no later commit on any branch brings them back [31]. Later commit messages still speak of a "creator" and of "refinement.py", and the code refers many times to a `spektrafilm-research` folder and to "private" notes, none of which is in the repository or among the author's public repositories [32]. The old CSV files can still be read in the history at the commit before the deletion [29].

### What is done to the numbers before they are shipped

The shipped data files are not the datasheet points. From the author's own words and the commit history:

- **Unmixing.** "Published data are measured with densitometers, RGB or diffuse, and they need to be unmixed to refer to the density developed in each channel independently." [28]
- **Correction toward neutral.** "Most of the times data is not self consistent after 'the unmixing' and I need to apply some reasonable corrections. I am assuming that the film should be able to reproduce a neutral-ish 18% gray when printed, even when under- or overexposed." [28]
- **Fujifilm needs more of it.** Of Pro 400H after unmixing: "It has strong hue shifts and it is not really usable in this state. Maybe additional calibrations are needed but not specified in the datasheet?" [28] The README says "Fujifilm data are less self-consistent than Kodak data" [3].
- **Refitting.** The data files were regenerated many times in 2026, with commits such as "feat: non-linear unmixing of status densities", "feat: unmix sensitivities of negative emulsions" and "chore: refit and update license of profiles" [33]. All 28 on `main` are dated 2026-05-28 [24].

### What is not from any datasheet

- **Saturation.** The strength of the interlayer effect, which sets how saturated a negative's colours are, is not in a datasheet. On `main` it is one set of nine numbers shared by every colour negative, with the comment "just eyeballed, optimize!" [34]. On `dev` the numbers are replaced by ones "Optimized on 2026/06/07 from study a22": still one shared set for all still colour negatives, one each for daylight and tungsten cinema negatives, and only four slide films with numbers of their own [35]. The study is not public.
- **Grain.** On `main` the grain settings are the same defaults for every film stock [2]. On `dev` each film stock gets an RMS granularity number (4.5 for Portra 400, 5.0 for Gold 200, 4.0 for Ektar 100 and for Pro 400H) [36]. Kodak's still-film sheets publish no RMS number, as the datasheet note found, so these are the author's values.
- **Halation.** Strength and size come from two tags on each film stock ("still" or "cine", and how strong its anti-halation layer is), mapped to preset numbers in the code [34].

### What the author says about closeness to real film

- **The aim.** "The aim is not just to imitate a generic 'film look,' but to build a model that is grounded in measurements and predicts real-world behaviors of photographic materials." [3]
- **The limit of datasheets.** "data-sheet curves are really not enough to reproduce a decent film look." [3]
- **His own estimate.** "Given the data I used, I would guess that the simulation is something like 60-85% accurate or more, which doesn't say much. Any suggestion on how to compare results to real life is welcome. Any expert in film colors that can judge by eye?" (first post of his forum write-up, 2025-02-09, about version 0.1.0) [28]
- **Saturation.** "Keep in mind that the saturation level is arbitrarily guessed" [28]
- **Slide film.** In June 2026 he wrote: "still slide film is perfected in spektrafilm, and it needs some more love" [37].
- **Comparisons with real prints.** In the same thread he reprocessed a user's picture and posted it beside an image labelled "RA4 Print", judging it by eye: "i think the color of the t-shirt might have improved a little compared to the last time i saw the comparison". Asked how exact he expects such matches to become, he answered "i am not sure either, the closer the better of course" and called these tests "only to check how things are going" [37].
- **Why a print and not a scan.** His write-up starts from the point that a negative's final colours "depend heavily on the second stage of the imaging process, whether it's the scanner's color processing or the analog RA4 color reversal printing process", and he chose the second: "Analog printing seemed like the most authentic way to define the look" [28].

In the repository itself I found no measured comparison with real film. The regression tests compare the pipeline with stored copies of its own earlier output [3][38]. I found no mention of Noritsu, Frontier or "lab scan" anywhere in the source.

### What is missing between its output and a lab scan

Set against M-Film's target, the picture people know from a lab scan **(my reasoning, built on the readings above)**:

1. **The second stage is a different machine.** A lab scan is a negative read by a scanner and turned into a positive by its software. spektrafilm's picture is a negative printed optically on paper and then seen by the standard observer. Those are two different second stages, and the datasheet note found that the second stage sets much of the colour.
2. **Its "scanner" is the standard observer, not a device.** The author's own code says so on the `experimental` branch, which adds the opposite direction (a real scanned negative in, a virtual print out). It needs a correction matrix "to undo the scanner/camera colour rendering vs the standard observer over the film dyes" and notes that "a real scan's level is set by scanner gain" [39].
3. **Colour balance is fixed by a rule.** Every pair of film stock and paper is balanced so that mid-grey prints neutral [3][11]. A lab scanner balances each frame or each roll its own way. A locked scan removes the frame-by-frame part of that, not the scanner's own balance.
4. **Black and white points are the paper's.** In a table the scanner's black and white correction is off [15], so white is the white of the modelled paper and black is its deepest black.
5. **Saturation is the author's setting, shared by all colour negatives**, not something measured per film stock [34][35].
6. **The dye colours are generic for the still negatives** in the first set [3][29].
7. **Nothing checks any of it against real film.**

So the useful reading is this **(my reasoning)**: spektrafilm can give a film-stock-specific starting point in which the things a datasheet does describe (which colours each layer sees, and the shape of the tone curves) are modelled with care, for 9 of the 72 film stocks. The things a datasheet does not describe are either the author's judgement or a darkroom print standing in for a scanner. The distance to a lab scan can only be found with a paired shot.

## 4. What the licences say

Texts are quoted. No legal opinion is given.

### spektrafilm's code

The `LICENSE` file is the GNU General Public License version 3 [40]. `pyproject.toml` says `license = { text = "GPLv3" }` [41] and `CITATION.cff` says `license: "GPL-3.0-or-later"` [42].

The README says how the author reads it [3]:

> *The project is GPLv3 licensed*, so any derivative work must also be open source under the same license. Derivatve work includes any software, plugin, or tool that incorporates spektrafilm code or is directly inspired by its methods.

> If *GPLv3 is not compatible with your project*, please reach out to discuss alternative options. I am very open to collaboration and integration, but I want to ensure that spektrafilm remains open source and for the community.

On the output of the program, GPLv3 section 2 says [40]:

> The output from running a covered work is covered by this License only if the output, given its content, constitutes a covered work.

### spektrafilm's data files and any table made from them

A second file, `SPEKTRAFILM_LICENSE.txt`, is headed "License for spektrafilm profiles, LUTs, and direct derivatives ... License: CC BY-SA 4.0" [43]. It is an author's preamble followed by the full text of the Creative Commons Attribution-ShareAlike 4.0 licence. The preamble says what it covers:

> This license applies to the original spektrafilm profiles that can be found at https://github.com/andreavolpato/spektrafilm, in the subfolder src/spektrafilm/data/profiles, and to all direct derivatives of the profiles, such as copies in other projects, LUTs, or any other format that encodes the same content.

> LUTs and similar artifacts are interpreted as direct encodings of the information in the original profiles. I chose not to release them under GPLv3 because GPL's software-shaped "derivative work" model fits LUTs poorly and would have made adoption more difficult.

What it allows:

> Use these profiles and LUTs freely to grade anything - personal, educational, or commercial; small project or feature film; any platform, any deliverable. The works you make are yours. No royalties. No copyleft on your finished film or photograph.

What it requires:

> Modify, remix, regrade, recombine. Modified profiles or LUTs must stay CC BY-SA 4.0 and credit spektrafilm.

> Every copy, redistribution, modification, or derivative of these files - in any format, in any context, across any chain of hands - must preserve:
>
> - Andrea Volpato, named as the original author.
> - https://github.com/andreavolpato/spektrafilm, as the canonical source.
> - The CC BY-SA 4.0 license notice (this file, or a link to it).
> - A note that the file has been modified, if it has, and by whom.

> This applies whether the LUT is shipped inside a .cube header, an ICC profile field, an app's About screen, a paid plugin, a derived .3dl, training-data documentation, or anywhere else. ... Removing or hiding this information ends the license grant immediately (CC BY-SA 4.0, Section 6(a)).

What it asks for without requiring, under the heading "These are not legal requirements":

> Paid apps and tools that add real value are welcome. Charge for what you built - UI, performance, support, a service. Please don't repackage the LUTs themselves as a paid LUT pack: CC BY-SA technically allows it, but that's not the spirit of the project, and any buyer can legally redistribute for free anyway.

> Don't use "spektrafilm" or my name in product branding without asking. ... Factual reference is welcome and even encouraged, for example "graded with spektrafilm", or "this app uses spektrafilm LUTs".

From the Creative Commons text in the same file, the share-alike condition (section 3(b)) [43]:

> 1. The Adapter's License You apply must be a Creative Commons license with the same License Elements, this version or later, or a BY-SA Compatible License.
>
> 3. You may not offer or impose any additional or different terms or conditions on, or apply any Effective Technological Measures to, Adapted Material that restrict exercise of the rights granted under the Adapter's License You apply.

The table maker acts on this by itself: it copies `SPEKTRAFILM_LICENSE.txt` into every bundle and writes the author, the licence and the project address into the header of every `.cube` file [44].

Two things in the repository do not say quite the same:

- The README describes the table licence as "a strict '*commercial use, free share, no resale*' custom license" [3]. The licence file it links to is CC BY-SA 4.0, and that file lists "no resale" among the requests that "are not legal requirements" [43].
- The licence file speaks of tables as files that "encode the same content" as the data files. It does not speak of a table someone bakes with their own code on a grid of their own, as M-Film would. Whether the author means that case too is not written down.

### M-Film

- `README.md`: "This repository: GPL-2.0 (LICENSE), as the camera side builds on Magic Lantern. Darkrooms (the desktop program) is a separate, closed-source program under its own licence." [45]
- `THIRD_PARTY.md` says how the present tables are handled: Film-Luts is under the MIT licence, the `.cube` files are not in the repository, and "The camera's card files are made from them, though: the colour tables in `ML/DARKROOM` and the sample photos in `ML/SAMPLES`, so the notice below comes with them." [46]
- The MIT licence there asks only that "The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software." [46]
- GPL version 2, in M-Film's `LICENSE`, says of output: "the output from the Program is covered only if its contents constitute a work based on the Program". Of files that merely travel together it says: "mere aggregation of another work not based on the Program with the Program (or with a work based on the Program) on a volume of a storage or distribution medium does not bring the other work under the scope of this License." [47]

### What Creative Commons says about mixing BY-SA 4.0 with the GPL

Creative Commons' list of compatible licences names two for BY-SA 4.0: the Free Art License 1.3 and the GPL version 3. Of the second it says [48]:

> The GNU General Public License version 3 was declared a "BY-SA–Compatible License" for version 4.0 on 8 October 2015. Note that compatibility with the GPLv3 is one-way only, which means you may license your contributions to adaptations of BY-SA 4.0 materials under GPLv3, but you may not license your contributions to adaptations of GPLv3 projects under BY-SA 4.0.

GPL version 2 is not on the list.

### What follows from the texts, and what does not

Facts, from the above:

- Film-Luts tables can ship with a copyright notice and nothing more. spektrafilm tables, by the author's licence text, need the author's name, the project address, the licence notice and a note of changes on every copy, and a changed table must stay CC BY-SA 4.0.
- M-Film's plan is to tune each look toward its paired shot. A table changed that way would be a modified one in the licence file's words **(my reasoning)**.
- M-Film is GPL-2.0. The only GPL version on Creative Commons' compatibility list is version 3.
- Darkrooms is closed-source. The author's README says a tool "that incorporates spektrafilm code or is directly inspired by its methods" must be GPLv3, and asks those for whom "GPLv3 is not compatible" to "reach out".

Not decided here, because they are legal questions or the author's to answer:

- Whether a CC BY-SA 4.0 table may sit on the card as a data file beside GPL-2.0 code, the way the Film-Luts tables do today.
- Whether a closed-source program may ship or download CC BY-SA 4.0 tables.
- Whether a table baked by M-Film's own code from spektrafilm's data files is a "direct derivative" in the author's sense.
- Whether a look that began as a spektrafilm table and was then tuned by measurement stays under CC BY-SA 4.0 for good.

The licence file gives an email address for "private inquiries about commercial licensing, name use, or custom work" [43]. Three such requests were made in public on the project's tracker in October 2026 (a paid iOS app, an MIT-licensed RAW editor, and a question about another app's GPL compliance). None has a reply from the author as of 2026-11-14 [49].

## 5. What it needs to run, and how alive it is

### To run

- **Language.** Python. `requires-python = "~=3.13"` [41], and the README warns: "Since spektrafilm is not compatible with the latest Python version, an older version like 3.13 must be used." [3]
- **Libraries.** The core needs numpy, scipy, colour-science, scikit-image, matplotlib, opt-einsum, numba, OpenImageIO, pyfftw, rawpy, exiv2 and lensfunpy. The default install also pulls in the desktop program's libraries (qtpy, PySide6, napari, Pillow, pyconify) and `markdown` for the table maker. There is no smaller install on `main` [41].
- **Install.** From the Git repository with `pip` or `uv`. The README shows no install from PyPI [3].
- **Time for one picture.** "On my laptop it takes roughly 10 seconds to process 6 MP images." "Full resolution export is very slow at the moment." [3]
- **Time for one table.** Not stated. A 33-point table is 35,937 colours, about as many pixels as a 190 by 190 picture, and a comment in the table maker says its 729-sample test pass "is sub-second" [14]. I did not time a bake.
- **Where it could run (my reasoning).** On the computer that builds M-Film's card files, once per film stock. It could not run on the camera.

There are faster rewrites by other people, which the README lists: a GPU version inside the vkdt raw editor, a Rust port, an OFX plugin and a bridge in the ART raw editor [3]. I did not read them for this note.

### How alive

| Fact | Value on 2026-11-14 | Source |
|---|---|---|
| First public commit | 2025-02-07 (as "agx-emulsion") | history |
| Commits on `main` | 331, of which 300 by the author | history |
| Last commit on `main` | 2026-06-07, `3bb2c2d`, "fix: vlog midgray exposure" | history |
| Last commit on any branch | 2026-07-08, `28bf883` on `experimental` | history |
| Last push | 2026-07-14 | GitHub API |
| Releases | v0.3.3 (2026-06-06), v0.3.2 (2026-05-28), v0.1.0-alpha (2025-02-07). `main` now says version 0.3.4 with no release | GitHub API, [41] |
| Stars, forks | 2,232 and 328 | GitHub API |
| Issues | 19 open, 19 closed | GitHub API |
| Pull requests | 12 open, 26 closed | GitHub API |
| Author's last comment on an issue or pull request | 2026-06-04 (none by him among the 30 comments made since) | GitHub API [49] |
| Author's last forum post found | 2026-07-28: "i am on vacation and a bit disconnected these days" | forum [37] |

Read together: the project moved very fast from February 2025 to July 2026 (the table maker, the black-and-white work and a new way to rebuild spectra all date from May to July 2026). Since then there has been no public commit for four months, and issues and pull requests from others have gone unanswered, while users keep posting (the forum thread had 1,063 posts, the latest on 2026-11-13) [28][49]. The README describes it as "a nights-and-weekends project" and warns that "The project is in rapid development, some ares are still being build and will change fast." [3]

One more thing bears on depending on it. The code tells callers not to expect stability: "Backward-compatibility shims ... The runtime is a moving target by design; downstream packages adapt." [1] A table baked today is tied to the version that baked it; the tool writes that version into each table's header [44].

## Not known / not verified

- **Nothing was run.** No table was baked, so nothing here says what a spektrafilm table looks like on a Canon picture, how long a bake takes, or whether the build would work on the maintainer's computer.
- **How close its output is to real film.** No one in the sources read has measured it. The only figures are the author's own guess from 2025.
- **How far its print is from a lab scan of the same negative.** Not measured by anyone in the sources read. This is the gap that matters most for M-Film's target.
- **Whether the licences allow what M-Film and Darkrooms would do.** The four questions at the end of part 4 are open. The author was not asked.
- **Whether the author will answer.** His last public activity found is from July 2026. I did not check for activity outside GitHub and the one forum.
- **The data behind the data files.** The points read off the datasheets and the code that processes them are private since March 2026. The older copies in the history were listed but not compared with the datasheets, and I did not check which licence covered them at that time.
- **Stand-ins.** Whether Velvia 100 data says anything useful about Velvia 50, or Vision3 500T data about CineStill 800T, is not established. The datasheet note raised the same doubt for 800T.
- **Name matches.** The shelf comparison is by name. Whether spektrafilm's "Fujifilm X-Tra 400" is M-Film's "Fujicolor Superia 400", and which version of each emulsion the datasheets describe, was not checked.
- **New film stocks.** Whether M-Film could add a film stock to spektrafilm (HP5 Plus, Velvia 50) without the private code that makes the data files was not tried. The file format is plain JSON and is read in full in [30].
- **The forum.** The author's thread has more than a thousand posts. I read the first post in full and four of his later posts. There may be comparisons with real film in the rest.
- **Third-party parts inside spektrafilm.** It ships other people's data (a table for rebuilding spectra, filter curves, ICC colour profiles under CC BY-SA 3.0 and other licences [50]). Their terms were not read beyond the ICC folder's own README.
- **The ports.** The GPU, Rust and OFX versions were not read. They may be faster or licensed differently.

## Sources

spektrafilm, `main` at `3bb2c2d2801ff68b92019cf1dbcbb133d60832bc` unless another commit is named:

1. Runtime README. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm/README.md>
2. Runtime settings and their defaults (`IOParams`, `GrainParams`, `DebugParams`). <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm/runtime/params_schema.py>
3. Main README. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/README.md> (lines 3-7 project status; 12, 25 aim; 36-55 licence statements; 62-65 generic dye densities; 84-88 the chain; 107-111 couplers; 165-209 table maker; 217-318 install; 329-337 tests; 347-384 input and neutral filters; 406-411 expected input; 420-425 speed and Fujifilm data).
4. Pipeline order. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm/runtime/pipeline.py#L174-L196>
5. Filming stage. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm/runtime/stages/filming.py#L52-L134>
6. Film development call and the coupler model. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm/runtime/stages/filming.py#L73-L85> and <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm/model/couplers.py>
7. Printing stage and the enlarger lamp. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm/runtime/stages/printing.py#L39-L124> and <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm/model/illuminants.py#L19-L33>
8. Scanning stage. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm/runtime/stages/scanning.py#L46-L139>
9. The `scan_film` switch in the pipeline. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm/runtime/pipeline.py#L181-L184>
10. Black and white point service. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm/runtime/services/color_reference.py#L116-L130>
11. Neutral filter table and its lookup. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm/data/filters/neutral_print_filters.json> and <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm/runtime/params_builder.py#L45-L72>
12. Table bundle settings. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm_lut_creator/bundles.py#L27-L160>
13. Table maker README and sampling grid. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm_lut_creator/README.md> and <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm_lut_creator/grid.py>
14. Table builder. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm_lut_creator/builders.py> (lines 63-66 test pass; 387-415 one-table layout; 934-954 the bake).
15. What "LUT mode" turns off. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm/runtime/params_builder.py#L98-L142>
16. Coupler effect without its spatial part. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm/model/couplers.py#L135-L159>
17. Input and output colour spaces of the table maker. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm_lut_creator/color_spaces.py#L259-L470>
18. How the table maker sets up the pipeline. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm_lut_creator/builders.py#L774-L795>
19. `experimental` at `28bf883e1672e884307edc75852549376e13644e`: bake route. <https://github.com/andreavolpato/spektrafilm/blob/28bf883e1672e884307edc75852549376e13644e/src/spektrafilm_lut_creator/bake.py>
20. Quality checks. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm_lut_creator/qa/README.md>
21. Text written into each bundle. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm_lut_creator/bundle_text.py#L72-L98>
22. M-Film, `ml-dev/filmos/fos_dev.c`, lines 147-148 and 252-275 (at `8118e9c`).
23. M-Film, `ml-dev/films/lut.py`, lines 1-22 and 96 (at `8118e9c`).
24. The 28 data files, read one by one for their `info` and `metadata` blocks. <https://github.com/andreavolpato/spektrafilm/tree/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm/data/profiles>
25. List of film stocks and papers in code. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm/model/stocks.py>
26. `dev` at `6cd00c8d4f30b5b550f50f4bbd3753c9f2a48507`: `kodak_doublex.json`, `kodak_trix.json`, `kodak_2302.json`. <https://github.com/andreavolpato/spektrafilm/tree/6cd00c8d4f30b5b550f50f4bbd3753c9f2a48507/src/spektrafilm/data/profiles>
27. spektrafilm issue 74, "Black-and-white films in main: promote the dev cine stocks, add still films?", opened 2026-11-09 by a user. <https://github.com/andreavolpato/spektrafilm/issues/74>
28. Andrea Volpato (forum name "arctic"), "Spectral film simulations from scratch", first post, 2025-02-09, last edited 2026-05-30. <https://discuss.pixls.us/t/spectral-film-simulations-from-scratch/48209>. Linked from the README [3]. Read through the forum's JSON address for the topic.
29. Datasheet points and their notes, at `b1955d6924d1c5c57e36a65f5ab05825c8e499e0`, the commit before they were deleted. <https://github.com/andreavolpato/spektrafilm/tree/b1955d6924d1c5c57e36a65f5ab05825c8e499e0/src/spectral_film_lab/data/film>
30. Data file format and the statement of origin. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm/profiles/io.py#L80-L170>
31. Commit `a6dbcfdaed50757192781dbfb25c032c202eb8aa`, 2026-03-17. <https://github.com/andreavolpato/spektrafilm/commit/a6dbcfdaed50757192781dbfb25c032c202eb8aa>. Checked with `git log --all` that no file with "creator" or "refine" in its path exists in any commit except the table maker.
32. References to material outside the repository, for example <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm/runtime/params_builder.py#L218-L223> ("private halation implementation notes") and [13] ("spektrafilm-research/studies"). The author's public repositories were listed through GitHub's API; none has either name.
33. Commits `c2ccdcf` (2026-04-22), `bc95c01` (2026-04-23), `ad5c8d2` (2026-05-28), each changing every data file. <https://github.com/andreavolpato/spektrafilm/commit/ad5c8d2>
34. Per-film settings applied in code: coupler numbers and halation presets. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm/runtime/params_builder.py#L161-L252>
35. `dev`: coupler presets. <https://github.com/andreavolpato/spektrafilm/blob/6cd00c8d4f30b5b550f50f4bbd3753c9f2a48507/src/spektrafilm/data/presets/couplers.toml>
36. `dev`: grain presets. <https://github.com/andreavolpato/spektrafilm/blob/6cd00c8d4f30b5b550f50f4bbd3753c9f2a48507/src/spektrafilm/data/presets/grain.toml>
37. Later posts by the author in the same forum: thread [28] posts 947 (2026-06-14), 951 (2026-06-15) and 979 (2026-06-23); and his most recent post found, 2026-07-28, in "Spektrafilm darktable module implementation discussion". Read through the forum's JSON addresses.
38. Regression tests. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/tests/test_regression_baselines.py>
39. `experimental`: settings for converting a real scanned negative. <https://github.com/andreavolpato/spektrafilm/blob/28bf883e1672e884307edc75852549376e13644e/src/spektrafilm/runtime/params_schema.py#L183-L220> and <https://github.com/andreavolpato/spektrafilm/blob/28bf883e1672e884307edc75852549376e13644e/src/spektrafilm/model/convert.py#L1-L28>
40. GPLv3 text. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/LICENSE> (section 2 at lines 154-161).
41. Packaging. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/pyproject.toml>
42. Citation file. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/CITATION.cff>
43. Licence for data files and tables. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/SPEKTRAFILM_LICENSE.txt> (lines 1-23 scope; 46-55 what is allowed; 62-76 attribution; 98-126 requests; 130-136 contact; 368-385 share-alike).
44. Licence and credit written into bundles. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm_lut_creator/builders.py#L1123-L1193>, <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm_lut_creator/bundle_text.py#L386-L428> and <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm_lut_creator/metadata.py#L60-L84>
45. M-Film, `README.md`, lines 332-338 (at `8118e9c`).
46. M-Film, `THIRD_PARTY.md` (at `8118e9c`).
47. M-Film, `LICENSE` (GNU GPL version 2), section 0 and section 2 (at `8118e9c`).
48. Creative Commons, "Compatible Licenses", section "Version 4.0". <https://creativecommons.org/share-your-work/licensing-considerations/compatible-licenses/>
49. spektrafilm issues 58 (2026-10-12), 59 (2026-10-16) and 62 (2026-10-28), and the 40 most recent issue comments, read through GitHub's API. <https://github.com/andreavolpato/spektrafilm/issues/58>, <https://github.com/andreavolpato/spektrafilm/issues/59>, <https://github.com/andreavolpato/spektrafilm/issues/62>
50. Bundled ICC profiles and their licences. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm/data/icc/README.md>
