# Where the Film-Luts tables come from, and what picture they expect

Research for [#94](https://github.com/HNGSeries/mfilm-canon-film-simulation/issues/94), a child of the map
[#93](https://github.com/HNGSeries/mfilm-canon-film-simulation/issues/93). Researched 2026-11-13 from primary sources
only. Each claim links to the source that owns it. "States" marks what a source says; "Conclusion" marks what I
draw from it. Nothing here is legal advice.

## Short answer

- **None of the tables is a reference.** No table in the collection is documented as measured from real film by
  the person who published it. Film-Luts is a 2024 export of the colour tables built into G'MIC. G'MIC credits
  them to three people: Pat David (59 of the 63 film stocks M-Film takes from the collection), Juan Melara (the
  4 cinema print stocks) and Stuart Sowerby (Fujifilm camera simulations, which M-Film does not use).
- **Pat David's tables are hand-made looks.** He states he replicated "a very popular set of film emulation
  presets that are available commercially" by eye from examples online, and in 2023 that he cannot vouch for
  their validity: "I'm doubtful these would be identical at all."
- **They expect a finished sRGB picture**, 8 bits per channel, as a photo editor shows it. M-Film's
  `lut_space="srgb"` agrees with that for those 59.
- **The 4 print tables expect something else.** Their publisher states they "expect log film scans in Rec709
  colour space as their input". M-Film feeds them sRGB, so Kodak 2383, Kodak 2393, Fuji 3510 and Fuji 3513 get
  the wrong picture today.
- **Licence.** Film-Luts carries an MIT file, but its README says the maintainer "does not claim ownership of
  the LUTs". The only explicit upstream licence is CC BY-SA 4.0, on Pat David's work and on the RawTherapee
  collection that carries it. The print tables have no stated licence at all. Conclusion: M-Film's current MIT
  notice does not cover the tables; CC BY-SA 4.0 permits shipping baked tables, including in a paid program,
  on conditions (credit, same licence on the tables, no lock on them); the print tables are not cleared for
  either product.
- **The first set does not share one origin.** Pro 400H, Portra 160/400/800 and one HP5 table are from Pat
  David's first batch (August 2013). Velvia 50 and a second HP5 Plus table are from his second batch (September
  2013), whose method he does not describe. Ektar 100 is in none of his lists; its maker is not stated. Kodak
  Gold and CineStill 800T have no table in the collection.

## The chain, link by link

```
Pat David, 2013                      Stuart Sowerby                  Juan Melara, 2013
commercial presets, online           Fujifilm RAW FILE               print tables from a
examples, hand tuning                CONVERTER                       Reduser post, converted
      |                                    |                               |
      +--> also published as the           |                               |
      |    RawTherapee Film Simulation     |                               |
      |    Collection (CC BY-SA 4.0)       |                               |
      v                                    v                               v
      G'MIC built-in tables, compressed (Simulate Film filter, 296 tables)
                                |  exported by Yahia Angelo, March 2024
                                v
               Film-Luts: 296 .cube files, 13 points per axis
                                |  getluts.py, at every build
                                v
           M-Film: 63 film stocks, baked for the darkroom and Darkrooms
```

### 1. Film-Luts is an export of G'MIC's tables

- States: the repository describes itself as "G'MIC Film Luts Collection", was created on 2024-03-01 and has four
  commits, the last on 2024-03-07. Pinned here at
  [`af957b6`](https://github.com/YahiaAngelo/Film-Luts/tree/af957b631a304e6be94778b96cb3395de3438e9f).
- States: every `.cube` file opens with `# Created by: G'MIC (https://gmic.eu)` and `LUT_3D_SIZE 13`
  ([example](https://github.com/YahiaAngelo/Film-Luts/blob/af957b631a304e6be94778b96cb3395de3438e9f/luts/negative_new/fuji_400h.cube)).
  That header is the one G'MIC's `output_cube` command writes
  ([stdlib L5829](https://github.com/GreycLab/gmic/blob/4a5531830c13fc18f53428ba89922800584ad213/src/gmic_stdlib.gmic#L5829)).
- States: the nine folders (`bw`, `instant_consumer`, `instant_pro`, `fujixtransiii`, `negative_color`,
  `negative_new`, `negative_old`, `print`, `colorslide`) and their file counts (25, 54, 68, 15, 13, 39, 44, 12, 26)
  are exactly the nine categories and counts of G'MIC's "Simulate Film" filter
  ([stdlib L53540 onward](https://github.com/GreycLab/gmic/blob/4a5531830c13fc18f53428ba89922800584ad213/src/gmic_stdlib.gmic#L53540)).
- States: the README does not say how the files were exported, from which G'MIC version, or why 13 points.
  It says the maintainer "does not claim ownership of the LUTs" and that they "might be subject to copyrights and
  trademarks of their respective owners"
  ([README](https://github.com/YahiaAngelo/Film-Luts/blob/af957b631a304e6be94778b96cb3395de3438e9f/README.md)).
- Measured by me: 296 files hold 289 distinct tables. Seven pairs are byte-identical across folders (same git
  blob): `kodak_portra_160_nc`, `kodak_portra_160_vc`, `ilford_delta_3200` and `fuji_neopan_1600` in
  `negative_old` and a second folder, `kodak_tri-x_400` in `bw` and `negative_new`, `polaroid_669` and
  `polaroid_690` in `colorslide` and `instant_pro`.

### 2. G'MIC's tables are a compressed copy of other people's tables

- States: the filter's own note reads "The color LUTs proposed in this filter come from various free sources" and
  lists four: RawTherapee Film Simulation, Pat David Film Emulation, Fuji Film Simulation Profiles, and Print Film
  LUTs For Download
  ([stdlib L53660](https://github.com/GreycLab/gmic/blob/4a5531830c13fc18f53428ba89922800584ad213/src/gmic_stdlib.gmic#L53660)).
- States: G'MIC's page generator credits each category
  ([stdlib L11226](https://github.com/GreycLab/gmic/blob/4a5531830c13fc18f53428ba89922800584ad213/src/gmic_stdlib.gmic#L11226),
  shown at [gmic.eu/color_presets](https://gmic.eu/color_presets/)):

  | G'MIC category (Film-Luts folder) | Credited to | Film stocks M-Film takes from it |
  |---|---|---|
  | Black and White (`bw`) | Pat David | 20 |
  | Slide [Color] (`colorslide`) | Pat David | 17 |
  | Negative [Color] (`negative_color`) | Pat David | 9 |
  | Negative [Old] (`negative_old`) | Pat David | 8 |
  | Negative [New] (`negative_new`) | Pat David | 5 |
  | Print Films (`print`) | Juan Melara | 4 |
  | Instant [Consumer], Instant [Pro] | Pat David | 0 |
  | Fuji XTrans III (`fujixtransiii`) | Stuart Sowerby | 0 |

- States: G'MIC does not store the original tables. `compress_clut` shrinks each to at most 33 points per axis,
  rounds it to 8 bits, and keeps only a set of key colours, with error targets of 0.45 on average and 2.5 at
  most in delta E
  ([stdlib L14085](https://github.com/GreycLab/gmic/blob/4a5531830c13fc18f53428ba89922800584ad213/src/gmic_stdlib.gmic#L14085)).
  The `clut` command rebuilds a table from those at a requested size, 33 by default
  ([stdlib L15595](https://github.com/GreycLab/gmic/blob/4a5531830c13fc18f53428ba89922800584ad213/src/gmic_stdlib.gmic#L15595));
  the filter itself uses 48 for the final picture
  ([stdlib L53674](https://github.com/GreycLab/gmic/blob/4a5531830c13fc18f53428ba89922800584ad213/src/gmic_stdlib.gmic#L53674)).
- Conclusion: a Film-Luts table is two lossy steps away from its author's file: G'MIC's compression, then a
  13-point export, coarser than any size G'MIC uses itself. How much colour that loses is not measured here.

### 3. Pat David's tables (59 of M-Film's 63)

Who and how, in his own words:

- States (30 August 2013): "I figured it would be fun to replicate the effects found in a very popular set of film
  emulation presets that are available commercially". He did not have the presets: "I don't have Photoshop,
  Lightroom, Adobe Camera Raw, or Aperture. Which also means I don't have a means to access those presets
  directly. What I do have is (some) patience and examples online." And: "these are my approximations, so they
  aren't exact. There's a lot of 'creative' interpretations going on, and I had to fill in some things with
  artistic liberties." He files the post under the topic "VSCO". The product is not named in the text
  ([post](https://patdavid.net/2013/08/film-emulation-presets-in-gmic-gimp/)).
- States: that post covers Fuji 160C, 400H, 800Z, Ilford HP5, Kodak Portra 160/400/800, T-MAX 3200, Tri-X 400
  (the "new" set); Fuji Neopan 1600, Superia 100/400/800/1600, Ilford Delta 3200, Kodak Portra 160 NC/VC and
  400 NC/UC/VC (the "old" set); and the instant films, "all in various intensities of the effect".
- States (6 September 2013): the slide, colour negative and black-and-white sets are announced as films "that I
  am working on". The post lists them and does not say how they were made or from what
  ([addendum](https://patdavid.net/2013/09/film-emulation-presets-in-gmic-gimp/)).
- States (13 May 2023, asked how the collection was built): "These were generally a combination of manually
  tweaking and fiddling in an iterative process and sometimes using a starting point from others works." "This was
  usually less a rigorous application of parameters (as you've mentioned - color checkers + specific temperature
  lights, etc) and more of attempting to replicate a feeling for general tones". "Some of those CLUTs were likely
  also reverse-generated from other color curve packages". "As far as vouching for validity or approximation of
  any of the results - I'd say no - I'm doubtful these would be identical at all."
  ([discuss.pixls.us](https://discuss.pixls.us/t/how-was-the-rawtherapee-film-simulation-collection-created-and-thanks/34265/13)).
  In 2019: "Portra 400 was likely a combination of multiple other efforts tweaked to something pleasing."
  ([discuss.pixls.us](https://discuss.pixls.us/t/the-source-of-film-simulations/13583/4)).
- States: VSCO's own page lists Film 01 as Fuji 160C, Pro 400H, 800Z, Kodak Portra 160/400/800, Portra 800 HC,
  Ilford HP5, Tri-X 400 and T-MAX 3200, and Film 02 as Fuji Neopan 1600, Superia 100/400/800/1600, Ilford Delta
  3200, Kodak Portra 160 NC/VC and 400 NC/UC/VC
  ([vsco.co](https://www.vsco.co/features/photo-filters/preset-packs)).
- Conclusion: the "new" and "old" sets are the film lists of VSCO Film 01 and 02, name for name, including the
  "Portra 800 HC" variant, and the post carries the author's own "VSCO" tag. So `negative_new` and `negative_old`
  are hand-made copies of how VSCO's presets looked in online examples. They are two steps from real film, and the
  first step (how VSCO built its presets) is not documented by any source read here.
- Conflict between sources: Pat David calls the `-`, `+`, `++` variants "various intensities of the effect".
  RawTherapee's page says they "refer to the strength the film was pushed or pulled during development"
  ([RawPedia, archived](https://web.archive.org/web/20250201220737/https://rawpedia.rawtherapee.com/Film_Simulation)).
  The author's wording is the one to trust; neither is a measurement of push processing.

What picture they expect:

- States: the RawTherapee collection that carries these tables says "Unless otherwise noted in the filename, they
  are all in the sRGB color space, 8-bit per channel, in the PNG image format" (`README.txt` inside
  [HaldCLUT.zip](http://rawtherapee.com/shared/HaldCLUT.zip), version 2015-09-20).
- States: Pat David built and showed them on finished photos in GIMP ("mouseover for original"), and built the
  table files to apply "to my images with Imagemagick".
- States: RawTherapee encodes the picture with the sRGB curve, clipped, straight before the table lookup
  ([improcfun.cc L3153](https://github.com/RawTherapee/RawTherapee/blob/64c2d90a3248c7ad41842d9162368858b61aac6a/rtengine/improcfun.cc#L3153-L3226);
  the table profile defaults to sRGB in
  [clutstore.cc](https://github.com/RawTherapee/RawTherapee/blob/64c2d90a3248c7ad41842d9162368858b61aac6a/rtengine/clutstore.cc#L122)).
  G'MIC maps the table onto the 0 to 255 values of the open image with no conversion
  ([stdlib L53674](https://github.com/GreycLab/gmic/blob/4a5531830c13fc18f53428ba89922800584ad213/src/gmic_stdlib.gmic#L53674)).
- Conclusion: the input is an ordinary finished sRGB photo, already tone-mapped by a camera or RAW developer,
  with values clipped to the display range. No source states the white balance, exposure or contrast of the
  photos the looks were tuned on. `lut_space="srgb"` in `ml-dev/films/filmluts.py` is the right encoding; what
  the darkroom does before it (scanner exposure, highlight roll-off in `ml-dev/films/lut.py`) is M-Film's own
  choice and cannot be checked against the source.

### 4. Juan Melara's print tables (4 of M-Film's 63)

- States (original post, January 2013): "Reduser member Bjorn Benckert from Syndicate Entertainment made
  available a set of print LUTs. Unfortunately they weren't in the correct format for Resolve. So I took the time
  to convert them into a format Resolve reads." He calls a print table "an accurate and measured emulation of
  film", without saying who measured these or how
  ([old post](https://juanmelara.com.au/blog/print-film-emulation-luts-for-download-old)).
- States (same post as archived in 2018): the download was `log2hd_cube_luts.zip` with Fujifilm 3510, Fujifilm
  3513, Kodak 2383 and Kodak 2393, each "in three flavours: ConstLclip, ConstLmap and CUSPclip. Each of these
  treat out of gamut colours in a different way", and "These LUTs use a generic HD profile as the target device"
  ([archive](https://web.archive.org/web/20180107230212/http://juanmelara.com.au:80/blog/print-film-emulation-luts-for-download)).
  Those are the twelve names in Film-Luts' `print` folder.
- States, on the input: "The only requirement these LUTs have is that the source footage is in log gamma"
  (2013), and "PFE LUTs expect log film scans in Rec709 colour space as their input", with Cineon or ARRI LogC
  given as the encodings to convert to
  ([current post](https://juanmelara.com.au/blog/print-film-emulation-luts-for-download)).
- Measured by me: a grey ramp through Film-Luts' `print/kodak_2383_constlmap.cube` gives almost the same output
  as through the `Rec709_Kodak_2383_D65.cube` Juan Melara offers today. Inputs 106, 128, 149 of 255 come out as
  about 95, 143, 188 and 93, 143, 190. That is a contrast slope above 2 in the mid-tones, where Pat David's
  negative tables have about 1 (Fuji 400H: 129, 150, 167).
- Conclusion: the print tables in Film-Luts are still the log-input tables; G'MIC did not convert them, it only
  applies them to display pictures. M-Film sets `lut_space="srgb"` for all 63, so the four print stocks are
  given a picture their publisher says they were not made for. `lut.py` already has `cineon` and `logc3`
  encodings; which of the two the 2013 files assume is not stated beyond "log gamma".

### 5. Stuart Sowerby's Fujifilm tables (not used by M-Film)

- States: "I have created a set of LUTs (look up tables) based on the film simulations from Fujifilm's own 'RAW
  FILE CONVERTER' software", "designed to be applied to a neutral RAW file, this means no auto-levels or custom
  tone curves" ([post](https://blog.sowerby.me/fuji-film-simulation-profiles/)).
- Conclusion: these reproduce Fujifilm's digital camera renderings, not film. The `fuji_xtrans_iii_velvia` table
  is unrelated to the Velvia tables in `colorslide`. No film stock in `filmluts.py` uses this folder.

## The first set, stock by stock

| Film stock | Table in Film-Luts | Origin the sources give | Used by M-Film today |
|---|---|---|---|
| Fujifilm Pro 400H | `negative_new/fuji_400h` | Pat David, first batch; hand-made copy of a commercial preset | Yes (`pro400h`) |
| Kodak Portra 160 | `negative_new/kodak_portra_160` | Same | Yes (`portra160`) |
| Kodak Portra 800 | `negative_new/kodak_portra_800` | Same | Yes (`portra800`) |
| Kodak Portra 400 | `negative_new/kodak_portra_400` | Same; "a combination of multiple other efforts tweaked to something pleasing" | No, hand-written in `films.py` |
| Ilford HP5 Plus | `negative_new/ilford_hp_5` and `bw/ilford_hp_5_plus_400`, two different tables | First is Pat David's first batch; second is his second batch, method not stated by the source | No, hand-written |
| Fujichrome Velvia 50 | `colorslide/fuji_velvia_50` | Pat David, second batch; method not stated by the source | No, hand-written (`velvia100` uses `colorslide/fuji_velvia_100_generic`, same batch) |
| Kodak Ektar 100 | `negative_color/kodak_ektar_100` | Not stated by the source. Absent from all three of Pat David's lists; present in the RawTherapee collection, which credits Pat David, Pavlov Dmitry and Michael Ezra without saying who made which file | No, hand-written |
| Kodak Gold 200 | none | No table with "gold" in its name exists in the collection | No, hand-written |
| CineStill 800T | none | No table exists in the collection | No, hand-written |

Across all 63 film stocks M-Film takes from the collection: 15 use first-batch tables (the 13 in `negative_new` and
`negative_old`, plus `bw/ilford_delta_3200` and `bw/fuji_neopan_1600`, which are byte-identical to the
`negative_old` files), 44 use second-batch tables, and 4 use the print tables.

## Licences

What each source states:

| Link in the chain | Licence stated |
|---|---|
| Film-Luts | MIT, "Copyright (c) 2024 Yahia" ([LICENSE](https://github.com/YahiaAngelo/Film-Luts/blob/af957b631a304e6be94778b96cb3395de3438e9f/LICENSE)). README: "Unless specified otherwise, the content of this repository is shared under MIT License", and the maintainer "does not claim ownership of the LUTs". |
| G'MIC | The software is under CeCILL-C or CeCILL 2.1, the user's choice ([stdlib header](https://github.com/GreycLab/gmic/blob/4a5531830c13fc18f53428ba89922800584ad213/src/gmic_stdlib.gmic#L12-L21)). A licence for the table data itself is not stated by the source; the filter calls its sources "free". |
| RawTherapee Film Simulation Collection | "CC BY-SA 4.0" (line 2 of `README.txt` in [HaldCLUT.zip](http://rawtherapee.com/shared/HaldCLUT.zip)). |
| Pat David | CC BY-SA 4.0 "unless otherwise noted": "free to share and adapt my works in any way you'd like (even commercially), provided you give me credit and that any changes you make to my works will be licensed under the same conditions" ([about](https://patdavid.net/about/#licensing)). |
| Juan Melara | Not stated by the source. The posts call the tables "free"; the download holds no licence file; the tables were first "made available" by someone else. |
| Stuart Sowerby | Not stated by the source. |

What CC BY-SA 4.0 itself states ([legal code](https://creativecommons.org/licenses/by-sa/4.0/legalcode.en)):

- The grant covers only rights "that the Licensor has authority to license" (Section 1, Licensed Rights).
- Sharing requires credit, a link to the licence and a note of changes (Section 3(a)).
- "Adapted Material" must be shared under BY-SA 4.0 or later or a "BY-SA Compatible License" (Section 3(b)(1)).
  That list holds two licences for version 4.0: the Free Art License 1.3 and GPLv3, the latter one way
  ([compatible licences](https://creativecommons.org/compatible-licenses/)). GPL-2.0 is not on it.
- No terms or "Effective Technological Measures" may restrict the recipient's rights in adapted material
  (Section 3(b)(3)).
- Nothing in it forbids commercial use.

Conclusions:

1. **The MIT notice is not enough.** `THIRD_PARTY.md` ships Film-Luts' MIT text with the card files as the
   licence of the tables. The Film-Luts maintainer says he does not own them, so MIT can cover his scripts and
   packaging at most. The upstream terms apply to the tables.
2. **Open-source M-Film, Pat David's tables.** A baked table is the same table in another format, so it is adapted
   material and stays CC BY-SA 4.0. Shipping it as a data file on the card is within the licence if the release
   credits Pat David and the RawTherapee Film Simulation Collection, links CC BY-SA 4.0 and says the tables were
   converted. The tables cannot be relicensed as GPL-2.0, so they need to be marked as separate from the program.
   Whether a sample photo developed through a table (`docs/films/`, `ML/SAMPLES`) carries the table's licence is
   not something the licence text answers; it is not decided here.
3. **Paid, closed-source Darkrooms, Pat David's tables.** The licence allows selling. It requires the same credit,
   and that the baked tables stay CC BY-SA 4.0: a customer may take them out and share them, and the program may
   not encrypt or otherwise lock them. Whether a closed program that reads such a table as data counts as adapted
   material itself is a question the licence text does not settle; it needs a lawyer's reading before Darkrooms
   relies on it.
4. **A risk no licence file removes.** Pat David states the first batch replicates a commercial product's presets
   and that some tables "were likely also reverse-generated from other color curve packages". CC BY-SA passes on
   only what he could license. Which tables were reverse-generated, and from what, is not stated. For a paid
   product this risk is open and cannot be sized from the sources.
5. **The print tables are not cleared.** No licence is stated at any link above Film-Luts, and the person who
   published them says they came from someone else. Nothing found permits redistribution in either product.
6. **Names.** G'MIC and RawTherapee both state that film names are used "for informational purposes only" under a
   fair-use claim ([gmic.eu](https://gmic.eu/color_presets/)). That is their position, not a grant from the
   trademark owners. `THIRD_PARTY.md` already carries M-Film's own disclaimer.

## What remains unknown

- **How VSCO built the presets Pat David copied.** Not stated by any source read. So no chain from any
  first-batch table back to real film can be shown.
- **What the second batch was made from** (slide, colour negative, black and white: 44 of M-Film's stocks,
  including Velvia). The addendum only says "working on". The 2023 answer covers the whole collection in general
  terms and names no source per film. Several names in that batch resemble another commercial product's film
  list; I could not confirm that from the product's own pages, so it stays a lead, not a finding.
- **Who made the Ektar 100 table**, and what Pavlov Dmitry and Michael Ezra contributed to the RawTherapee
  collection.
- **Who measured the print tables, on what equipment, and under what terms** Bjorn Benckert released them. The
  Reduser post is not linked from Juan Melara's page and was not found. Which log encoding the 2013 files assume
  (Cineon, REDlogFilm or other) is not stated beyond "log gamma".
- **How Film-Luts was exported**: G'MIC version, command, and why 13 points per axis. That the files are G'MIC's
  tables rests on the file header, the folder names and the counts; I did not run G'MIC to compare values. The
  seven byte-identical pairs suggest G'MIC keeps one table per name, so a name shared by two categories gives one
  table; which original survived in each pair is not stated.
- **How much colour is lost** between an original table, G'MIC's compressed copy and the 13-point export.
  RawTherapee's identity file is level 12, which is 144 points per axis; the level of each file in its collection
  was not checked. Measurable by comparing the RawTherapee file with the Film-Luts file for one stock; not done
  here.
- **What photos the looks were tuned on**: white balance, exposure, contrast and RAW developer. Not stated, so the
  step the darkroom runs before the table cannot be matched to the author's.
- **Whether a program that embeds a CC BY-SA table becomes adapted material.** A legal question, not a research
  one.
- [rawpedia.rawtherapee.com](https://rawpedia.rawtherapee.com/Film_Simulation) returned 404 on the day; its text
  was read from the Internet Archive copy of 2025-02-01. The collection's `README.txt` was read from the live zip.

## What this means for the map

- A Film-Luts table can serve as a starting look. It cannot serve as a reference, and its author says so.
- "Whether the Film-Luts tables can be trusted", which the colour model waits on: not as evidence of how real
  film looks. For 59 stocks they are one person's taste, partly copied from a commercial product; for 4 they are
  fed the wrong input.
- Two things found on the way are plain defects rather than decisions: the print stocks' input encoding, and the
  third-party notice that names MIT for tables the MIT licensor does not own.

## How to repeat the checks

- Folder and file list, identical files: `gh api "repos/YahiaAngelo/Film-Luts/git/trees/af957b631a?recursive=1"`
  and group the `luts/` entries by blob hash.
- Table size: the header of any `.cube` file, and 2197 data rows (13 cubed).
- Grey ramp: read the rows at index `(i*13 + i)*13 + i` for `i` from 0 to 12 and compare with the same inputs
  through `Rec709_Kodak_2383_D65.cube` from
  [Juan Melara's download](https://juanmelara.com.au/s/Print-Film-Emulation-LUTs.zip).
- G'MIC lines are pinned to commit `4a5531830c13fc18f53428ba89922800584ad213`; RawTherapee lines to
  `64c2d90a3248c7ad41842d9162368858b61aac6a`.
