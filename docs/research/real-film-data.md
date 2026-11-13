# What published data exists for the real film stocks?

Research note for [issue #95](https://github.com/HNGSeries/mfilm-canon-film-simulation/issues/95), a child of the map in [issue #93](https://github.com/HNGSeries/mfilm-canon-film-simulation/issues/93). All sources were fetched on 2026-11-13. Only the makers' own documents and the open projects' own repositories are used as evidence. Where a statement is my own reasoning and not something a source says, it is marked **(my reasoning)**.

## Short answer

- **Five of the seven datasheets could be opened.** Kodak Portra 400, Gold 200, Ektar 100, Fujichrome Velvia 50 and Fujifilm Pro 400H each give spectral sensitivity curves, characteristic curves and a spectral dye density graph, plus a grain figure. Ilford HP5 Plus could not be fetched. No CineStill 800T datasheet was found, and CineStill's product page could not be fetched.
- **The curves exist first-party only as printed graphs.** None of the opened datasheets has a table of curve values, and I found no first-party file of numbers. The only first-party numbers are the grain figures and a few aim densities. In the Kodak and Pro 400H PDFs the graphs are vector drawings; in the Velvia 50 PDF they are raster images.
- **The dye density graph is weaker than its name suggests.** For the three Kodak film stocks and Pro 400H it shows only the whole film at mid-grey and at minimum density, not the three dyes separately. Only Velvia 50 shows the yellow, magenta and cyan dyes one by one.
- **Grain is published in two units that cannot be compared.** Kodak gives a Print Grain Index (a rating of a print viewed at 14 inches). Fujifilm gives one diffuse RMS granularity number.
- **Two open projects already turn these graphs into pictures**, both by reading the graphs into numbers by hand: `spektrafilm` (GPLv3 code, CC BY-SA 4.0 data) and `spectral_film_lut` (MIT). Between them they hold data for five of the seven film stocks. Neither has HP5 Plus or CineStill 800T.
- **A datasheet describes the film, not the picture.** For a negative, the colour of the final picture is set by the second stage: the print paper or the scanner and its software. That part is not in any film datasheet, and both open projects say in their own READMEs that datasheet curves alone are not enough.

## Part one: what each datasheet gives

| Film stock | Maker's datasheet | Spectral sensitivity | Characteristic curves | Spectral dye density | Grain figure |
|---|---|---|---|---|---|
| Kodak Portra 400 | E-4050, February 2016 [1] | Yes, three layers | Yes, R G B, Status M | Whole film only: mid-scale neutral and minimum density. No separate dyes | Print Grain Index. 135: 37 (4x6 in), 59 (8x10), 89 (16x20). 120: 25, 37, 59 |
| Kodak Gold 200 | E-7022, June 2023 [2] | Yes, three layers | Yes, R G B, Status M | Whole film only: mid-scale neutral and minimum density | Print Grain Index. 135: 44 (4x6 in), 64 (8x10). 120: 33, 44, 64 (16x20) |
| Kodak Ektar 100 | E-4046, February 2016 [3] | Yes, three layers | Yes, R G B, Status M | Whole film only: mid-scale neutral and minimum density | Print Grain Index. 135: less than 25 (4x6 in), 38 (8x10), 66 (16x20). 120: less than 25, less than 25, 38 |
| Fujichrome Velvia 50 | AF3-0221E2 [4] | Yes, three layers | Yes, R G B, Status A | Yes, yellow, magenta and cyan dyes separately | Diffuse RMS granularity 9 |
| CineStill 800T | No datasheet found. Product page: could not fetch | could not fetch | could not fetch | could not fetch | could not fetch |
| Ilford HP5 Plus | Could not fetch [6] | could not fetch | could not fetch | could not fetch | could not fetch |
| Fujifilm Pro 400H | AF3-176E [5] | Yes, four layers (blue, green, red, and the fourth cyan-sensitive layer) | Yes, R G B, Status M | Whole film only: mid-scale density and minimum density | Diffuse RMS granularity 4 |

Notes on the rows:

- **Kodak sheets.** All three also say the film can be scanned on desktop and drum scanners or that it gives "high-quality results when scanned", and say nothing about how [1][2][3]. Portra 400 and Ektar 100 add a modulation transfer function graph; the Gold 200 sheet has none.
- **Gold 200.** The 135 table in the sheet prints the magnification as 4.4X under both print sizes [2]. The index values above are copied as printed.
- **Print Grain Index.** Kodak's own words in all three sheets: it "replaces rms granularity and has a different scale which cannot be compared to rms granularity", a rating of 25 is "the approximate visual threshold for graininess", four units are one just-noticeable difference, the viewing distance is fixed at 14 inches, and the numbers "may not represent graininess observed from more specular printing illuminants" [1][2][3].
- **Fujifilm RMS.** Both sheets state the measurement: a micro-densitometer aperture of 48 micrometres, at a density of 1.0 above minimum [4][5]. The Pro 400H sheet adds a footnote to its value: "Based on Fujifilm measurements. Due to difference in measurement conditions, comparison with color reversal film is not possible." [5] So Fujifilm's own two numbers here (9 and 4) are not on one scale.
- **Velvia 50 dye curves.** They are drawn for separated exposures, each peaking near 1.0 [4]. They give the shape of each dye, not the amount of dye in a real picture.
- **Fujifilm sheets also give** an MTF graph and resolving power (Velvia 50: 80 and 160 lines/mm; Pro 400H: 50 and 125 lines/mm) [4][5].
- **Pro 400H is discontinued**, but Fujifilm still links its datasheet from its film support page [5].

### Numbers, or only graphs?

Only graphs. In every datasheet I opened the curves are drawn figures with no table of values beside them [1][2][3][4][5]. I found no first-party spreadsheet, CSV or table of these curves anywhere. This was not an exhaustive search of the makers' sites, so "none found" is the claim, not "none exists".

One detail matters for anyone who wants numbers. I checked how each PDF stores its curves page:

| PDF | Curves page | How the graphs are stored |
|---|---|---|
| Portra 400 E-4050 | 4 | Vector drawing, no raster images on the page |
| Gold 200 E-7022 | 4 | Vector drawing, no raster images on the page |
| Ektar 100 E-4046 | 4 | Vector drawing, no raster images on the page |
| Pro 400H AF3-176E | 8 | Vector drawing, no raster images on the page |
| Velvia 50 AF3-0221E2 | 8 | Four raster images, one per graph |

Method: `pdfimages -list` on that page, and a look at the rendered page. A vector graph can be read out of the PDF's drawing commands more exactly than a raster graph can be traced. I did not extract any values. Either way the result is a reading of a small printed graph, not data the maker published as numbers **(my reasoning)**.

### CineStill 800T and Ilford HP5 Plus

- **CineStill 800T.** `cinestillfilm.com` and `cinestill.film` product pages answered HTTP 429 on every try. A CineStill blog post about 800T did load [7]. It links no datasheet and shows no curves. It describes the film as motion picture technology made to work in standard photo lab processing, calls the process a trade secret, and quotes Kodak as saying the process "has little to no effect on sensitometric curve of the film". The post carries the tag "5219" but its text does not name the Kodak film it starts from.
- **A related first-party sheet exists.** Kodak's datasheet for VISION3 500T 5219/7219, publication H-1-5219t, July 2015, is fuller than any of the still-film sheets: characteristic curves, spectral sensitivity, spectral dye density with separate peak-normalised cyan, magenta and yellow curves, MTF, and diffuse RMS granularity as a curve against exposure [8]. Whether it describes CineStill 800T is not established here. The sheet is for process ECN-2 and for film with its rem-jet backing [8], and 800T is sold without that backing for a different process, so even if the film starts as 5219 the sheet's curves would not carry over unchanged **(my reasoning)**.
- **Ilford HP5 Plus.** The datasheet address is known [6] but `ilfordphoto.com` answered HTTP 403 to every fetch, and an archived copy could not be retrieved. Nothing in the table is filled in for it.

## Part two: open projects that turn such data into pictures

Only projects whose repository I read are listed. Commit hashes are the versions read.

| Project | What it models | Film stocks from the first set | Where its data came from | From negative to picture | Licence | Maintained |
|---|---|---|---|---|---|---|
| [spektrafilm](https://github.com/andreavolpato/spektrafilm) (was agx-emulsion), Python, read at `3bb2c2d` | Spectral simulation of the whole chain: scene light onto a virtual negative, dye couplers, grain, halation, enlarger with filters, print paper, then a scan of the print [9] | Portra 400, Gold 200, Ektar 100, Pro 400H. Has Velvia 100 but not Velvia 50. Has Kodak Vision3 500T but not CineStill 800T. No HP5 Plus [10] | Its own reading of maker datasheet graphs: "processing raw measurement data from data-sheets and/or scientific papers" [11] | Print paper model (Kodak Endura papers, Fujifilm Crystal Archive, Kodak 2383 and 2393 print film) followed by a virtual scan. The scan is the light through or off the material under a standard illuminant, seen by the standard observer. It is not a model of any real scanner [12]. A direct "scan film" mode skips the print | Code GPL-3.0. Profiles and LUTs CC BY-SA 4.0 [13] | Last commit on `main` 2026-06-06 (release v0.3.3), `dev` branch 2026-06-10, repository last pushed 2026-07-14. 2,219 stars. Many ports depend on it |
| [spectral_film_lut](https://github.com/JanLohse/spectral_film_lut), Python, read at `a15043f` | Builds LUT files for film emulation from digitised datasheets: negative, print and slide materials, colour and black-and-white, with grain and MTF data per stock [14] | Portra 400, Gold 200, Ektar 100, Velvia 50, Pro 400H. Has Kodak Vision3 500T 5219 but not CineStill 800T. Black-and-white negatives are Kodak Tri-X 400 and Kodak 5222 only, no HP5 Plus [15] | "its datasheet was digitized" [14]. Each stock is a Python file of points read off the graphs [16] | Three routes: print the negative onto a print material (20 print films and papers); or "scan" it with Academy Printing Density, which the project itself says loses accuracy; or with no print material, "a digital scan with a simple mathematical inversion" [17]. No model of a real scanner | MIT | Yes. Last commit and release v0.18.14 on 2026-11-08 |
| [vkdt `filmsim` module](https://github.com/hanatos/vkdt/tree/18819cf215e48d48ded265b7aabb2c61d8dfd9f7/src/pipe/modules/filmsim), GLSL on Vulkan, read at `18819cf` | A GPU implementation of spektrafilm inside the vkdt raw editor, with its own grain model [18] | Whatever spektrafilm's profiles hold; the data file is generated from them [18] | spektrafilm's profiles, converted by a script in the module [18] | Same as spektrafilm: print paper, or the virtual negative, or a real scanned negative as input printed onto virtual paper [18] | vkdt is BSD-2-Clause. The film data stays CC BY-SA 4.0 [18] | Yes. Module last changed 2026-10-31 |
| [SoftLoaf-Spectral](https://github.com/Flemyng1999/SoftLoaf-Spectral), C++, README only, read at `f6578a0` | Spectral film-emulation LUTs, with a separate workbench for digitising real negatives against a measured target [19] | None shipped. Its README says the releases include no "film/paper curves, frozen spectral models, photographs or scan calibrations" and that data stays local "pending data-rights review" [19] | Its own extraction from maker documents, not distributed [19] | Three routes: negative through standard Academy Printing Density, negative printed on paper, slide viewed by transmitted light. Its README says the negative route "uses standard APD rather than simulated recapture lighting, sensor responses or camera calibration" [19] | AGPL-3.0 | Active (last commit 2026-10-31) but very small: 4 stars |
| [film_grain_rendering](https://github.com/alasdairnewson/film_grain_rendering), C++, read at `4dbdf36` | Grain only: the grain rendering algorithm of Newson, Faraj, Galerne and Delon, on 8-bit grey images [20] | None. It has no film stocks. Its inputs are an average grain radius and its spread, set by the user [20] | Not built from datasheet data [20] | Not applicable | "GPL V3+" stated in the README; the repository has no licence file [20] | No. Last commit 2020-11-11 |

Things read but not listed as separate projects:

- **Ports of spektrafilm.** GitHub search shows many (OFX plugin, Rust, Android, iOS, macOS, Photoshop plug-in). I read only the README of [spektrafilm-rs](https://github.com/turbasvin/spektrafilm-rs/blob/9dd59b0380194b93686aaa230a8bb9680aa270a4/README.md), which calls itself a Rust port aiming at identical output. They add no new film data as far as I read.
- **ART raw editor.** Its own documentation describes a bridge that runs spektrafilm or spectral_film_lut as an external 3D LUT generator [21]. It is a way to use those two, not a third model.

### What the two main projects do about missing data

This is the most useful evidence for the map, because both projects started from the same datasheets as in part one.

- **Dye spectra.** spektrafilm's README, under the Portra 400 example from datasheet E-4050: "note that the CMY diffuse densities are generic because they are usually not published" [9]. This matches the "whole film only" cells in part one.
- **Couplers.** spektrafilm's author: "data-sheet curves are really not enough to reproduce a decent film look", because the dye couplers that give a negative its saturation are not in the datasheet and have to be modelled and tuned [9]. spectral_film_lut says the same in its own words: "There is also undocumented behavior like interlayer effects, for which simplified assumptions have been made" and "There is especially little data available about the interlayer interaction" [14].
- **Grain.** For the Kodak still-film stocks, which publish only a Print Grain Index, spectral_film_lut's RMS values carry comments such as `rms=3.7,  # guessed` (Portra 400), `rms=4.4,  # guessed value` (Gold 200) and `rms=2.1,  # guessed value` (Ektar 100), and their grain curves are marked `# copied from kodak 5207` [16]. For Pro 400H it overrides the published number: `rms=3.5,  # data says 4.0, but seems to grainy due to high d-min value` [16]. spektrafilm's `dev` branch likewise carries a per-stock `rms_granularity` preset for the Kodak still films (for example 4.5 for Portra 400) that cannot have come from the Kodak sheets, since those give no RMS value [22] **(the "cannot have come from" is my reasoning)**.
- **Precision.** spectral_film_lut: "The accuracy is limited by the precision of the published data" [14]. spektrafilm: "Fujifilm data are less self-consistent than Kodak data" [9].
- **Checking against real film.** Neither README reports a comparison of its output with a real print or a real scan of the same scene. spektrafilm's test suite compares the code against its own earlier output [9]. I did not search their forums or issue trackers for such a comparison.

## Part three: what datasheet data cannot give toward a lab-scan look

The map's target is the picture people know from a lab scan. A film datasheet stops one stage short of that.

1. **The second stage is not in the film's datasheet, and it sets the colour.**
   The standard that defines printing density says so directly: "The spectral responsivities associated with any printing density metric are the product of the spectral power distribution of a printer light source, the spectral transmittance, reflection, and absorbance of the optical components of the photographic printer, and the spectral sensitivities of the print medium onto which the sample is to be printed." It defines a scanner's responsivities the same way, as "determined by the spectral power distribution of the illumination, the spectral filtration effects of various optical components, and the spectral sensitivity of the detector" [23]. None of those three things belongs to the film.
   vkdt's documentation, summarising spektrafilm's author: "the final colors depend heavily on the second stage of the imaging process, whether it's the scanner's color processing or the analog RA4 color reversal printing process" [18].
   Kodak's own motion picture sheet describes the dye density curves as "useful for adjusting or optimizing any device that scans or prints the film" [8], which treats the scanner as a separate device to be set up, not as something the film data settles.

2. **The datasheet's densities are measured by a densitometer, not by a scanner.**
   The negative film sheets give Status M density and the slide sheet Status A [1][2][3][4][5]. A real scanner has its own light source and sensor, so it reads different numbers from the same negative. The open projects stand in for this with either a standard observer under a standard illuminant [12] or Academy Printing Density, and spectral_film_lut says of the latter: "This results in a loss of accuracy, as the print stock's sensitivity is not accounted for" [17]. That these stand-ins differ from a lab scanner is **my reasoning**; no source I read measures the gap.

3. **The lab scanner's software is not described anywhere I could fetch.**
   Turning the orange negative into a positive, setting the colour balance and contrast for each frame, and any sharpening or grain handling are done by the scanner's software and its operator **(my reasoning)**. I found no first-party description of what a lab scanner such as a Fujifilm Frontier or a Noritsu does to the picture; the one Fujifilm scanner page I fetched says nothing about it. This is likely the largest part of a lab-scan look and it is the least documented **(my reasoning)**.

4. **Even the film's own part is incomplete.**
   Separate dye spectra are missing for four of the five opened sheets (part one), and the interlayer effects that give colour negatives their saturation are not published at all [9][14]. A model built from the datasheet has to assume them, then be tuned by eye or against something else.

5. **The grain figure does not describe grain in a scan.**
   Print Grain Index rates an optical print under diffuse light at a 14 inch viewing distance and "cannot be compared to rms granularity" [1][2][3]. Fujifilm's RMS number is one value at one density through a 48 micrometre aperture, and Fujifilm says its negative and slide values cannot be compared with each other [5]. Neither says how grain looks at a given scan resolution after the scanner's optics and sharpening **(my reasoning)**. The open projects fill the gap with guessed values [16].

6. **The curves are typical, under stated conditions.**
   Kodak's notice on its motion picture sheet: the curves "represent product tested under the conditions of exposure and processing specified. They are representative of production coatings, and therefore do not apply directly to a particular box or roll of photographic material" [8]. Fujifilm's sheets carry a similar notice that the data come from general production runs [4][5]. The three Kodak still-film sheets I opened do not carry such a notice. Real rolls also vary with age, storage, the lab's chemistry and exposure error **(my reasoning)**.

7. **Slide film is the closest case, and still needs a scanner.**
   Velvia 50 is a finished picture once developed, and its sheet is the only one with separate dye curves [4], so a datasheet model has the least to assume there. A scan of the slide still passes through a scanner **(my reasoning)**.

What this means for the map, as far as this ticket can say **(my reasoning)**: datasheet curves can supply a film-stock-specific starting model, and two open projects show how far that goes. They cannot serve as the reference for a lab-scan look, because the part of that look added by the scanner or print is missing from them. The reference has to come from real scans.

## What remains unknown

- **Ilford HP5 Plus.** What its datasheet contains. The file needs to be opened by hand in a browser [6]. A search-engine summary suggested it has a characteristic curve and a spectral sensitivity figure made under tungsten light; that is unverified and not used above.
- **CineStill 800T.** Whether CineStill publishes any technical data, and a first-party statement of which Kodak film it starts from. The product pages need to be opened by hand.
- **First-party numbers.** Whether Kodak Alaris, Eastman Kodak, Fujifilm or Harman would give curve values on request. No one was asked.
- **How good the digitised numbers are.** Nobody in the sources read reports checking spektrafilm or spectral_film_lut output against real film of the same scene.
- **Which emulsion version the digitised data describes.** spectral_film_lut tags its data with years (Portra 400: 2010, Gold 200: 2007, Ektar 100: 2008, Pro 400H: 2004, Velvia 50: 2007) [16], while Kodak's current sheets are dated 2016 and 2023 [1][2][3]. Whether the curves changed between revisions was not checked.
- **What a lab scanner does.** No first-party description of Frontier or Noritsu colour processing was found. This is the gap that matters most for the map's target.
- **Rights.** The map allows "numbers from datasheets". The numbers available today are third-party readings of the makers' graphs, under CC BY-SA 4.0 (spektrafilm profiles) and MIT (spectral_film_lut), and spektrafilm's own metadata says "Original data are property of the respective holders" [11]. Whether M-Film, which is under GPL version 2, may take those readings, or should make its own from the PDFs, is not decided here.
- **Black-and-white.** Neither main project has HP5 Plus. spectral_film_lut has Tri-X 400 and Kodak 5222; spektrafilm's `dev` branch has Tri-X and Double-X [15][22].

## Sources

Makers' datasheets:

1. Kodak Alaris, *KODAK PROFESSIONAL PORTRA 400 Film*, Publication E-4050, revised 2-16. <https://imaging.kodakalaris.com/sites/default/files/files/products/e4050_portra_400.pdf> (redirects to `business.kodakmoments.com`).
2. Kodak Alaris, *KODAK GOLD 200 Film*, Publication E-7022, revised 06-23. <https://www.kodakprofessional.com/sites/default/files/wysiwyg/pro/resources/E7022%20Gold%20tech%20sheet.pdf>
3. Kodak Alaris, *KODAK PROFESSIONAL EKTAR 100 Film*, Publication E-4046, revised 2/16. <https://imaging.kodakalaris.com/sites/default/files/files/products/e4046_ektar_100.pdf> (redirects to `business.kodakmoments.com`).
4. Fujifilm, *FUJICHROME Velvia 50 Professional [RVP50]*, Product Information Bulletin, Ref. No. AF3-0221E2. <https://asset.fujifilm.com/www/ie/files/2019-09/3d88b84d7cbd43d8c3a32ca72d107ae4/films_velvia-50_datasheet_01.pdf>, linked from <https://www.fujifilm.com/ie/en/consumer/support/films/negative-and-reversal>.
5. Fujifilm, *FUJICOLOR PRO 400H PROFESSIONAL*, Product Information Bulletin, Ref. No. AF3-176E. <https://asset.fujifilm.com/www/ie/files/2019-09/d68b00b13f1b6234629342317be9cf2b/films_pro-400h_datasheet_01.pdf>, linked from the same support page.
6. Harman Technology (Ilford Photo), HP5 Plus technical information. <https://www.ilfordphoto.com/amfile/file/download/file/1903/product/691/>. **Could not fetch** (HTTP 403).
7. CineStill, "What Makes 800T the Original and Only True 800-Speed Tungsten-Balanced Film for Still Photography", 17 March 2024. <https://cinestill.film/blogs/news/what-makes-800t-the-original-and-only-true-800-speed-tungsten-balanced-film-for-still-photography>. Product page <https://cinestillfilm.com/products/800tungsten-high-speed-color-film-135-36>: **could not fetch** (HTTP 429).
8. Eastman Kodak, *KODAK VISION3 500T Color Negative Film 5219 / 7219 / SO-219*, Publication H-1-5219t, revised 7-15. <https://www.kodak.com/content/products-brochures/Film/VISION3-500T-Color-Negative-Film-7219-TECHNICAL-DATA.pdf>

Open projects:

9. spektrafilm README. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/README.md> (lines 62-65 dye densities; 84-88 pipeline; 107-126 couplers; 329-337 tests; 424-425 Fujifilm data).
10. spektrafilm profiles folder. <https://github.com/andreavolpato/spektrafilm/tree/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm/data/profiles>
11. spektrafilm profile metadata. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm/profiles/io.py#L97-L102>
12. spektrafilm scanning stage. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/src/spektrafilm/runtime/stages/scanning.py#L53-L121>
13. spektrafilm licences. <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/LICENSE> and <https://github.com/andreavolpato/spektrafilm/blob/3bb2c2d2801ff68b92019cf1dbcbb133d60832bc/SPEKTRAFILM_LICENSE.txt>
14. spectral_film_lut README. <https://github.com/JanLohse/spectral_film_lut/blob/a15043f6fe2d365d0c359d22e0868076800916d9/README.md> (lines 14-24).
15. spectral_film_lut stock folders. <https://github.com/JanLohse/spectral_film_lut/tree/a15043f6fe2d365d0c359d22e0868076800916d9/src/spectral_film_lut>
16. spectral_film_lut stock files: [Portra 400](https://github.com/JanLohse/spectral_film_lut/blob/a15043f6fe2d365d0c359d22e0868076800916d9/src/spectral_film_lut/negative_film/kodak_portra_400.py#L401) (lines 9, 401, 541), [Gold 200](https://github.com/JanLohse/spectral_film_lut/blob/a15043f6fe2d365d0c359d22e0868076800916d9/src/spectral_film_lut/negative_film/kodak_gold_200.py#L489) (lines 9, 349, 489), [Ektar 100](https://github.com/JanLohse/spectral_film_lut/blob/a15043f6fe2d365d0c359d22e0868076800916d9/src/spectral_film_lut/negative_film/kodak_ektar_100.py#L424) (lines 9, 284, 424), [Pro 400H](https://github.com/JanLohse/spectral_film_lut/blob/a15043f6fe2d365d0c359d22e0868076800916d9/src/spectral_film_lut/negative_film/fuji_pro_400h.py#L389) (lines 9, 249, 389), [Velvia 50](https://github.com/JanLohse/spectral_film_lut/blob/a15043f6fe2d365d0c359d22e0868076800916d9/src/spectral_film_lut/reversal_film/fuji_velvia_50.py#L13) (lines 13, 364).
17. spectral_film_lut interface text. <https://github.com/JanLohse/spectral_film_lut/blob/a15043f6fe2d365d0c359d22e0868076800916d9/src/spectral_film_lut/gui.py#L432-L437> and <https://github.com/JanLohse/spectral_film_lut/blob/a15043f6fe2d365d0c359d22e0868076800916d9/src/spectral_film_lut/gui.py#L637-L645>
18. vkdt `filmsim` readme. <https://github.com/hanatos/vkdt/blob/18819cf215e48d48ded265b7aabb2c61d8dfd9f7/src/pipe/modules/filmsim/readme.md>
19. SoftLoaf-Spectral README. <https://github.com/Flemyng1999/SoftLoaf-Spectral/blob/f6578a02b8b579fd453814dbc56206195cfccb0d/README.md>
20. film_grain_rendering README. <https://github.com/alasdairnewson/film_grain_rendering/blob/4dbdf368418cc20afa00749d14e30fc7bc32cda7/README.txt>
21. ART, "Spectral film simulation howto", version 0.6, 2026-10-22. <https://artraweditor.github.io/SpectralFilmSimHowto>
22. spektrafilm `dev` branch grain presets and profiles. <https://github.com/andreavolpato/spektrafilm/blob/6cd00c8d4f30b5b550f50f4bbd3753c9f2a48507/src/spektrafilm/data/presets/grain.toml> and <https://github.com/andreavolpato/spektrafilm/tree/6cd00c8d4f30b5b550f50f4bbd3753c9f2a48507/src/spektrafilm/data/profiles>

Standards:

23. SMPTE ST 2065-2:2020, *Academy Printing Density (APD) — Spectral Responsivities, Reference Measurement Device and Spectral Calculation*, Introduction and definitions 3.5 and 3.8. <https://pub.smpte.org/doc/st2065-2/20200527-pub/st2065-2-2020.pdf>
