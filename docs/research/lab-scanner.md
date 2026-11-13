# What does a lab scanner do to a negative on its way to a picture?

Research note for [issue #106](https://github.com/HNGSeries/mfilm-canon-film-simulation/issues/106), a child of the map in [issue #93](https://github.com/HNGSeries/mfilm-canon-film-simulation/issues/93). It builds on [the note for issue #95](https://github.com/HNGSeries/mfilm-canon-film-simulation/blob/research/real-film-data/docs/research/real-film-data.md), which covered the film datasheets and ended at "what a lab scanner does: no first-party description found". This note fills that gap as far as the sources allow. All sources were fetched on 2026-11-13.

## How to read this note

Every finding carries one of three labels:

- **[published]**: the maker says it, in a technical paper, a manual, a product page, a brochure or a patent.
- **[measured by others]**: someone outside the maker reports it. Each such finding says which kind it is, because they are not equal: an instrument measurement, a comparison of scans of the same negative, the word of someone who runs the machine, or an opinion.
- **[not known]**: looked for and not found.

Four cautions apply throughout:

- **A patent is not a product.** A patent shows what the maker's engineers designed and claimed. It does not prove that a given scanner does it. Where a paper or manual from the same maker says the same thing about a named machine, the note says so. Where only a patent says it, the note says "patent only".
- **Machines differ by generation.** "Frontier" covers a lamp-and-line-sensor generation and an LED-and-area-sensor generation. The table in part 1 keeps them apart.
- **My own reasoning** is marked **(my reasoning)**. Translations from Japanese are mine, and the original wording is given.
- **Who opened what.** I opened and read the Fujifilm sources [F1] to [F15] and the two standards-related sources myself. The Noritsu sources [N1] to [N11] and the outside sources [M1] to [M23] were opened by two helper agents that saved each page; I checked the quotes used here against the saved text, word for word, and looked at the one manual page whose screenshot matters [N1]. Sources nobody could open are listed at the end and are not described.

## Short answer

- **Neither maker's scanner is a densitometer, and they are not alike.** The current Frontier scanners (SP-3000, SP500) use red, green, blue and infrared LEDs and a black-and-white area sensor with pixel shifting [F6][F7]. The Noritsu HS-1800, LS-600 and LS-1100 use LEDs and line sensors [N3][N4][N10]. Older Frontiers used a halogen lamp and a three-line colour sensor [F2]. Fujifilm's own figure for two earlier LED models, the Frontier 330 and 340E, puts the LED peaks near 462, 531 and 637 to 652 nm [F5], against 450, 540 and 640 nm for Status M [S2]. The peaks of the SP-3000 and of the Noritsu scanners are not published. Fujifilm wrote that the change to LEDs "changed the spectral sensitivity" and forced it to re-tune its colour tables [F4].
- **The orange mask is not removed as a step of its own.** In both makers' descriptions the signal goes to density (a logarithm), then each of red and blue is given an offset and a gain that bring it onto green, and that offset and gain are worked out from the pictures themselves, using the prescan of the whole roll [F1][F8][F9][N5][N6]. The mask comes out as a by-product. Fujifilm calls this "complete one-channel processing" that needs no per-film setup [F2].
- **The tone curve is not fixed.** Fujifilm designed the base tone on "the gradation of the negative and paper system" [F2], then adds Hyper-Tone, a per-frame "digital dodging" that compresses highlights and shadows separately [F1]. Noritsu's equivalent is on by default for 35mm: "The scene is judged by each frame and the contrast is corrected", and switching it off gives "prints like the analog (optical) print" [N1].
- **Colour and density are corrected automatically for each frame, by what is in the frame, with the roll as context.** Fujifilm: setup is computed "based on this all film's data" [F1], and colour correction is raised for scenes under other light [F2]. Noritsu offers three settings: "Frame", "Order", and "Standard", which is "the color between Frame and Order" [N1].
- **The operator can override every frame.** Both machines show each frame and take density, cyan, magenta and yellow keys [F1][F10][N1]. Labs can also store their own setups: 65 custom conditions per input type on the SP-3000 [F6], and per-film "DX slope" corrections on Noritsu [N1]. A lab can equally run with no person looking: Noritsu's AUTO mode leaves colour and density "entrusted to the system" [N1].
- **Output: Noritsu's manual lists JPEG, bitmap and TIFF, with 16-bit TIFF available, an optional conversion to sRGB, and the corrections written into the saved file** [N1]. Fujifilm's papers give sRGB as the design goal and a separate processing path for files [F2][F3]; the SP-3000 manual I could open does not cover file format or bit depth [F6]. Labs report 8 bits from the Frontier and 16 from the Noritsu [M3]. Both sharpen and suppress grain as part of the normal chain [F1][F6][N1].
- **Nobody has published a number for how repeatable a lab scan is.** No colour difference figure, no patch values, for the same scanner twice, for Frontier against Noritsu, or for two labs [M-all]. What exists: Fujifilm's own statement, in a patent, that the same gray balance cannot be reproduced on the same scanner at a later time, on two scanners of one model, or on two models [F10]; and lab staff saying, without exception, that the setup and the person matter more than the machine [M4][M10].
- **So "the look of a lab scan" is, on this evidence, a family and not a point.** It varies by scanner generation, by the lab's stored setup, by what else is on the roll, by the content of the frame, and by the operator. The size of each of these is not measured anywhere I could find.

## 1. Light source and sensor

### What each machine has

| Machine | Light source | Sensor | Bits | Label and source |
|---|---|---|---|---|
| Frontier 350/370 input unit (paper of 2000) | Halogen lamp, through a cold filter, an aperture, a "negative/positive spectral correction filter" and a diffusion box, onto a slit | "5,000 画素 3 ライン CCD" (5,000-pixel three-line CCD), film moving past it; pigment colour filters; an electronic shutter for each colour | not stated | **[published]** [F2] |
| Frontier 390 (paper of 2002) | "400W ハロゲンランプ" (400 W halogen lamp) | as above, driven faster | not stated | **[published]** [F3] |
| Frontier 330 (launched 2001, paper of 2003) | LED, the first in the series; on a ceramic board with Peltier temperature control | Area sensor, a first for the series: Fujifilm's honeycomb CCD, 3.2 million pixels, moved by a two-axis piezo pixel shift to as many as 2896 × 4344 pixels per colour | 12 | **[published]** [F4] |
| Frontier 340E (paper of 2004) | LED; red LED moved about 15 nm shorter than in the 330 | as the 330 | not stated | **[published]** [F5] |
| Frontier SP-3000 | "High luminance LED type, diffusion box"; "LED circuit board with R×64, G×40, B×50 and IR×144" | "Black and white area Honeycomb CCD with precisely controlled pixel shifting function" | not stated | **[published]** [F6] |
| Frontier SP500 | "LED" | "Area CCD with Precision Pixel Shifting System" | not stated | **[published]** [F7] |
| Noritsu HS-1800 | LED unit holding "B LED, G LED, R1 LED, IR LED", heaters, a fan and a neutral density filter; held at 48.0 ± 1.0 °C | Two CCDs: a "BGR-CCD" and an "IR-CCD". The manuals speak of "Line Data" | not stated | **[published]** [N3][N4] |
| Noritsu LS-600 and LS-1100 | LED unit holding "LED Heater, B LED, G LED, R LED, IR LED and LED Thermosensor"; held at 47.0 ± 2.0 °C and 44.0 ± 1.0 °C | as above | not stated; optional "48bit Image Capture" | **[published]** [N2][N3][N4] |
| Noritsu QSS-3001 scanner section (brochure of 2001) | "HALOGEN LAMP (15V, 150W)" | not stated | not stated | **[published]** [N4] |

Notes on the table:

- **The SP-3000 is an area-sensor scanner.** This is the maker's own manual, in two places: the specification table says "Newly developed Super CCD Honeycomb (Area type), with precision pixel shifting system" and the parts list says "Black and white area Honeycomb CCD" [F6]. A news report of Fujifilm's 2004 press release says the same: "撮像素子にスーパーCCDハニカムを採用。光源はLED" (the sensor is a Super CCD Honeycomb; the light source is LED) [F14].
- **A black-and-white sensor with coloured LEDs means the LEDs do the colour separation.** A Fujifilm patent for this layout says the sensor "is a monochrome image sensor. Each color of the LED elements 64 R, 64 G, 64 B and 64 IR is separately lit in turn" [F11]. That the SP-3000 works this way follows from its parts list **(my reasoning)**; the manual does not describe the sequence.
- **The Noritsu line sensor is stated outright only in a patent.** Noritsu's LED light source patent describes "a three-line type CCD line sensor corresponding to the three primary colors of R (red), G (green) and B (blue) and a one-line type CCD line sensor having sensitivity for the infrared beam (IR)" [N10]. The service manual's "BGR-CCD", "IR-CCD", "R1 LED" and "ND Filter Solenoid" match that patent's parts [N3], which ties the patent to the product more firmly than usual **(my reasoning)**.
- **Bit depth is thin.** The only stated converter depth for a named product is the Frontier 330's 12 bits: "CCD で光電変換された画像データは，12bi でデジタル化された後…" (the image data from the CCD is digitised at 12 bits, then…) [F4]. Noritsu patents describe "RGB digital image data in a 16-bit gradation level" [N5], which is patent only.
- **The infrared channel is for dust and scratches**, not for the picture [F4][F6][N4].
- **An example of patent against product.** A Fujifilm patent on LED scanners argues that "less R light is required, more G light is required, and even more B light is required", and so claims more blue LEDs than green and more green than red [F12]. The SP-3000's board has the most red: 64 red, 40 green, 50 blue [F6].

### The LED colours, and how they compare with Status M

- **[published] Fujifilm printed its LED spectra once.** The Frontier 340E paper has a figure of the three LED curves over the transmittance of a slide film [F5]. Reading the peaks off that printed figure gives about 462 nm for blue, about 531 nm for green, about 652 nm for the Frontier 330's red and about 637 nm for the Frontier 340E's red. Each curve is narrow: roughly 15 to 30 nm wide at half height. These numbers are **my reading of a small printed graph**, good to perhaps 5 nm; the text gives only the shift: "FR340 の R の LED は，FR330 の R に比べて 15nm 程度短波長にしている" (the FR340's red LED is about 15 nm shorter in wavelength than the FR330's) [F5].
- **[published] Fujifilm moved the red LED for a film reason.** At the old red wavelength the transmittance of one slide film changed steeply and differed from another's; at the new one "読取濃度差を小さくすることができて" (the difference in read density could be made small) [F5]. So where the band sits changes the density the scanner reads from a given film.
- **[published] Noritsu gives bands, not peaks.** Its LED patent gives 400 to 480 nm, 520 to 560 nm, 620 to 750 nm for two red LED types together, and 830 to 950 nm for infrared [N10]. (The patent's sentence swaps the words "green" and "blue".) Patent only.
- **[not known] The LED peaks of the SP-3000, SP500, HS-1800, LS-600 and LS-1100.** No maker document gives them and nobody outside has published a measurement [M-all]. One writer says his spectrophotometer shows an iPad screen "closely matches the light source of a popular Fuji SP3000 film scanner" and gives no wavelengths [M17].
- **Status M, for comparison.** The film datasheets give Status M density, as [the note for issue #95](https://github.com/HNGSeries/mfilm-canon-film-simulation/blob/research/real-film-data/docs/research/real-film-data.md) records. I could not open ISO 5-3, which defines it. A third-party transcription of its tables, in an open project's source code, peaks at 450 nm for blue, 540 nm for green and 640 nm for red, with bands some 30 to 45 nm wide at half height **(widths are my arithmetic on that table)** [S2].
- **The gap, in the makers' own words.**
  - **[published]** A Fujifilm patent explains why a scanner's reading depends on where its band sits against the dye: when a film's density is read by detectors with different peak wavelengths, "the relation between the exposure and detected density differs between the photodetectors", so the differences between the red, green and blue readings "vary depending on exposure" [F8].
  - **[published]** Another gives a worked case: two scanners read the same gray patches, agree in green and blue and disagree in red, because one "reads R 1 … at a wavelength substantially equal to the peak for the cyan dye in the negative whereas the other scanner SC 2 reads R 2 … at a wavelength shorter than the peak. In this case, the R 2 characteristics provide an output of lower gamma" [F10].
  - **[published]** When the Frontier went from lamp to LED: "FR330 で光源が LED 化されて分光感度が変化したため，色再現テーブルを中心としたパラメータの最適化が必要であった" (because the light source became LED in the FR330 and the spectral sensitivity changed, the parameters, chiefly the colour reproduction tables, had to be optimised again) [F4].
  - **[published]** The motion picture standard says the same of Status M in general: "status M densities can only approximate printing densities for most materials" [S1].
- **What this adds to the earlier note (my reasoning).** The earlier note reasoned that a datasheet's Status M densities are not what a lab scanner reads. The makers' documents now say so directly, and add that two lab scanners do not read the same numbers as each other. Nobody has published how large the difference is for a named film stock on a named scanner.

## 2. How the orange mask is removed and the negative inverted

### Fujifilm

- **[published] The work is done in density.** A Fujifilm patent lists what happens to the sensor signal first: "A/D (analog/digital) conversion, log conversion, DC offset correction, dark correction and shading correction". Then tables do "color balance adjustment, contrast correction (toning) and density correction", a matrix does "chroma correction", and a three-dimensional table turns the result into data for the printer or the monitor [F10]. Patent only for the exact order; the named stages match the block list in Fujifilm's paper [F1].
- **[published] Fujifilm explains why subtracting the film base is not enough.** From the patent that sets out the method: the three dye densities for a gray object differ by amounts that "differ film to film … and vary depending on developing conditions"; and because of the detector-band effect in part 1, "it is impossible to correct the gray balance over the entire exposure range by measuring the density differences … at a highlight point or a shadow point and correcting the R-, G- and B-image signals by biasing them" [F8].
- **[published] What it does instead: a fitted line per channel.** The same patent [F8], patent only for the detail:
  1. A fixed curve per channel makes the three gray scales roughly parallel. "The same look-up tables are used irrespective of the kind of film."
  2. Strongly coloured pixels are thrown out, with their neighbours of similar hue, to leave near-gray pixels.
  3. The darkest and lightest points of what is left are found for each channel.
  4. Red is plotted against green, and blue against green, for the near-gray pixels. "The relation between the red density and the green density can be obtained by a known method, e.g., by obtaining a regression line by least squares method."
  5. Green is left alone. Red and blue are each given a gain and an offset: "DRc=α 1 ·DR+β 1".
  6. Only pixels of certain hues are used for each fit, with those "apt to involve color failure, excluded".
- **[published] The fit uses the whole roll.** A later Fujifilm patent: "candidate gray pixels are respectively extracted from a plurality of film images recorded on the same photographic film …, and a candidate gray pixel group made up of these candidate gray pixels extracted from the plurality of film images is used when estimating the gray balance", after which "gray balance correction conditions are set for each single film image" [F9]. Fujifilm's paper says the same of the product, in fewer words: "one complete film is scanned continuously under fixed scanning condition, thereby obtaining images for all frames. In the setup sequence, as a result of computation is performed based on this all film's data, setup performance is improved" [F1].
- **[published] No per-film data is needed, by design.** The Frontier 350/370 paper: "1 件先読み方式により，条件出し不要の完全 1 チャネル処理を実現している" (by reading one whole order ahead, complete one-channel processing with no need for condition setup is achieved) [F2]. In lab language a "channel" is a stored setup for a kind of film; one channel means one setup for all films.
- **[published] Fujifilm designed its films to suit.** Its 2004 professional film brochure says the four films "can be printed under identical conditions in a single print channel … due to the unification of their negative densities", and credits better scanning to "a reduction in discrepancy between designated grayscale regression lines and actual color negative density" [F13]. The phrase "grayscale regression lines" matches the fitted-line method above **(my reasoning)**.
- **[published] The film base is still measured, for another purpose.** The same patent uses "a value obtained by subtracting a measured base density of the negative film … from the minimum of the densities" as a sign of under- or over-exposure [F8], which feeds the tone step in part 3.

### Noritsu

- **[published] The manuals say nothing about the mask.** There is no base density or orange mask setting in the EZ Controller or LS-600 manuals. The operator picks a film type, for example "Color (Neg)" or "B/W Neg. (OB)" for black-and-white film on an orange base [N1][N2].
- **[published] Patent only: one offset and one gain per channel, from the whole roll.** Noritsu's patent on finding the film base: "the base concentration value of the film is measured and subtracted from the color image data". It works from the prescan of "one roll of 135 color negative film", builds a histogram for each channel, and slides and stretches the red and blue histograms over the green one until it "finds the shift rate and the stretch ratio that maximizes the relevant superimposed area" [N5]. It was written because reading the clear film between frames fails when "the intervals between frames are scarcely provided" [N5].
- **[published] Patent only: logarithm, then tables.** Another Noritsu patent: a "logarithmic conversion" turns "16-bit digital image data" into "12-bit digital image data for each color" using a table "storing therein an exposure density characteristics curve", so that "the shading of the image on the negative film can be caused to agree with the shading of the image on the print paper"; a density correction step then outputs "8-bit digital data" [N7].

### The same idea in both

Both makers describe a gain and an offset per channel in density, derived from the pictures on the roll, and neither describes a stored mask value per film stock **(my summary of [F8][F9][N5])**. A consequence is that the result for a frame depends on the other frames on its roll **(my reasoning)**.

### What the open tools model instead

- **[measured by others, tool documentation]** darktable's negadoctor says of itself that it inverts negatives "and simulate[s] their print on paper, based on Kodak Cineon densitometry algorithm" [M20]. It does not claim to model a lab scanner.
- **[measured by others, tool documentation]** RawTherapee's film negative tool raises each channel "to a different exponent, depending on the film type, age and possibly other factors", picked "only once per film roll" [M21].
- **[measured by others, developer's word]** Negative Lab Pro offers "Frontier" and "Noritsu" colour models "based on" those scanners, and a tone profile "modeled after the punchier, higher contrast look of lab scanners" [M18]. No method, target or measurement behind them is published [M18][M19].

## 3. The tone curve

### Fujifilm

- **[published] The starting point is the look of a print.** "肌とグレーの階調はネガ，ペーパー系の階調をベースに，肌はよりハイライトの色のりが良くなるように設計した。色再現は現シーンに忠実な再現となるように設計した" (the gradation of skin and gray is based on the gradation of the negative and paper system, with skin designed to hold more colour in the highlights; colour reproduction is designed to be faithful to the actual scene) [F2].
- **[published] Under- and over-exposed negatives get a different curve.** Patent only for the detail: brightness is passed through a curve that "is inverse to the exposure-color forming density characteristics of the negative film", placed according to how far the frame sits above the film base, and "the chroma on the low brightness side is decreased when the film is underexposed and the chroma on the high brightness side is increased when the film is overexposed" [F8].
- **[published] Hyper-Tone is automatic dodging.** Fujifilm's paper: "When a scene with wide dynamic range has been photographed, it is difficult to represent both the light and dark portions on prints simultaneously. We have solved this problem by implementing digital dodging (auto mask effect). In Hyper-Tone processing, the ultra-low frequency component of image brightness is extracted, and this value is used to compress the dynamic range" [F1]. The figure's caption says the slope on the light side and the slope on the dark side "are separately set" and that compression is applied toward a reference point [F1]. Because it works from a blurred copy of the picture, what it does to a tone depends on where that tone sits in the frame **(my reasoning)**.
- **[published] Faces get their own tone.** "the result of face extraction is also used for local tone control of the face in addition to simple density correction" [F1].
- **[published] The SP-3000's tone settings** [F6]:
  - "Correct Level" has four choices. "Full Correction": tone correction yes, colour and density correction yes, Hypertone on. "Tone Fixing": tone correction no, colour and density correction yes, Hypertone off. "L-CORR": "(Low Correction)", Hypertone off. "Condition Confirm": no tone correction, no colour and density correction, Hypertone off.
  - "Tone Adjustment": Standard, All Hard, All Soft, Highlight Hard, Highlight Soft, Shadow Hard, Shadow Soft.
  - "Hypertone": process yes or no; highlight level and shadow level each Lower, Low, Normal, High or Higher; "Mode 1 (Normal Hypertone Mode)" or "Mode 2 (Preceding acceptance rate by improving backlighting and increasing contrast)".
  - "Gradation Selection": Hard 2, Hard 1, Normal, Soft 1, Soft 2, Soft 3.
  - The manual's example screen shows Full Correction, Standard, Hypertone yes, Normal, Normal and Mode 1 selected. The manual does not call these the defaults.
- **[measured by others, operator documentation]** A film maker's scanning sheet, written with four labs, lists the same block as its starting point on the SP3000: "Hypertone = Yes / Full correction / Tone adjustment = Standard / Highlight level = Normal / Shadow level = Normal / Mode = 1" [M15].
- **[measured by others, lab's word]** A lab that runs both machines: Hyper-Tone is "heavy software tone-mapping technology that enabled it to expand its dynamic range and make it virtually impossible to burn highlights"; "on the highlight areas the Frontier tries harder to keep detail and so it flattens the image a bit" [M2][M1].

### Noritsu

- **[published] Scene-judged contrast is on by default for 35mm.** "Scanner Gradation Correction Switch (Negative Film except 120) … The default setting is ON." "ON: The scene is judged by each frame and the contrast is corrected." "OFF: The prints like the analog (optical) print will be made." For 120 film, "The default setting is OFF" [N1].
- **[published] DSA.** "DSA is the abbreviation for Digital Scene Adjustment. The Automatic Contrast, the Automatic Sharpness, the Chroma of the image and print quality (Graininess Suppression) of enlargements can be corrected. Correction can be carried out for each input media, print channel or frame" [N1]. Automatic Contrast has Overall, Shadow and Highlight values, each from -10 to 10 [N1].
- **[published] "Automatic Contrast 2".** "Excessive contrast in an image can be corrected automatically by the amount of correction judged necessary." "A value of 5 is recommended for effective normal correction." At 0 "the function is not used" [N1]. The example screen shows 0 [N1].
- **[published] A fixed preset as well.** "Gradation Characteristics": High Contrast 1 to 3, Standard, "Low Contrast 1 to Low Contrast 6" [N1].
- **[published] Patent only: keep the middle at the film's slope, bend the ends per frame.** A Noritsu patent fits contrast in five brightness bands and holds the middle band to a stored value: "the slope of the basic correction line is the slope of the latitude portion of the standard film characteristic curve" (machine translation) [N8]. Nothing ties it to a product setting.
- **[measured by others, lab's word]** "The Noritsu can enable some tone-mapping on the luminosity channel to save some hard contrast situations but is not as heavy as in the Frontier" [M2].

### Not known

- **[not known]** The shape of either maker's base curve as numbers: no table or graph of it is published.
- **[not known]** How strong Hyper-Tone is at "Normal", and what Noritsu's scene judgment looks for.

## 4. Automatic colour and density correction

### Fujifilm

- **[published] The order of work.** "The system sequence can be broadly classified into three steps; (a) a pre-scanning step for obtain an image to determine the scanning and image processing conditions, (b) an inspection step for checking and correcting print, and (c) a fine scanning step" [F1].
- **[published] Per frame, with the roll as context.** Colour: "色補正は 1 件情報をベースに，異種光源シーンなどでは適応的にコレクションを上げる処理を行っている" (colour correction is based on the information from the whole order, and for scenes such as those under a different kind of light the correction is raised adaptively) [F2]. A patent describes the same split: gray balance for the film from the group of frames, then a separate estimate, per frame, of "the extent of bias in the color balance of a film image caused by the light source" [F9]. Another states it as common practice: "an auto-setup algorithm is commonly employed to estimate the shooting light source from the characteristic quantities for each frame and perform optimal color adjustment" [F10].
- **[published] Density.** "濃度補正は，アナログ機で実績のある ACCS 方式に，顔抽出，背景除去の技術を取り入れた" (density correction takes the ACCS method proven on analogue machines and adds face extraction and background removal) [F2]. "The print yield can be improved by recognizing the face and by correcting the density based on face density. This is especially effective for scenes (e.g. shooting in flash mode)" [F1]. What ACCS stands for is not given in the sources I opened.
- **[published] What the roll-wide analysis measures.** The condition setting section builds "density histograms" and calculates "average density, LATD (large-area transmission density), highlights (minimum density) and shadows (maximum density)" from "the image data acquired by prescanning all frames" [F10]. Patent only.
- **[published] Film-type channels on the SP-3000.** "Printing is normally performed with condition of the Master “0” channel" [F6]. The "Special Film Channel Setting" menu, with 128 channels keyed by DX code, is "for setting up the automatic condition selection function for the special monotone film", meaning black-and-white film made for colour developer [F6]. The Frontier 330 reads the film's bar code with the imaging sensor itself [F4].
- **[measured by others, operator documentation]** The film maker's sheet says settings "can be assigned to a custom channel" and that "It is also possible to set a specific auto DX channel for the film, however the settings are more limited" [M15].

### Noritsu

- **[published] Colour: three choices.** "Scanner Color Correction Switch (Negative Film)": "Standard: The color is adjusted to the color between Frame and Order." "Frame: The color is corrected by each frame." "Order: All the frames in the negative will be corrected by applying the average correction value of the frames" [N1]. The example screen shows Standard; the text does not name a default [N1].
- **[published] Density: per frame, by scene.** "Basic Density Correction Switch … Especially, this function is valid at the scene which is taken under the electronic flash or against the sun. Select from 0 to 4. … The initial value is 1." "Minus correction of density is carried out when scanning a film with high density due to snow, ocean or sky background." A lab can scale it: at -100, "the density correction calculated by the scanner is ignored" [N1].
- **[published] Film-type corrections in three levels.** "Scanner Slope Correction": "Correct the color and density that vary depending on the type, size and manufacturer of films." "Master Data" is "Used when color and density are corrected in the same way for all types of negatives"; a size-level slope; and "DX Slope", "Used when color and density are corrected for the certain manufacturer's negative". Each holds separate values for under-, normally and over-exposed negatives. "If the DX code of the scanned film has not been registered, the registration display appears" [N1].
- **[published] One frame's reading can be locked onto others.** "Photometry Memory": "Memorizes the photometry of selected image and applies it to other images" [N1].
- **[published] Patent only: roll statistics, and a stated break with the older method.** Noritsu's colour patent describes the older large-area method's fault: "in the case of a scene in which a person is photographed against a background of the grass, the area of the grass is finished in gray, while in the area of the person, magenta which is a complementary color of the grass strongly appears". Its own method works "without using the LATD exposure method", and "it is preferable to create concentration histograms in accordance with the total image data for one roll of film images" [N6]. A further patent detects frames lit by tungsten or fluorescent light [N9]. How "Standard" blends frame and order is in no document found.

### What operators say

- **[measured by others, lab's word]** Of the Frontier: "it scans one image at a time and it shifts a bit the color and contrast on every frame. We work hard to correct it every time on the overall order but sometimes there is only so much we can do" [M1].
- **[measured by others, former operator's word]** "most labs often relied upon the automated software to do the color and density adjustments." The automation fails on "color failure from large areas of solid color" [M16].
- **[measured by others, opinion]** One blogger says the opposite, that a Frontier or Noritsu "will process all the images of a same roll in an identical fashion" [M23]. The makers' documents above contradict this.
- **[measured by others, developer's word]** The maker of Negative Lab Pro, describing his own single-frame analysis: it "freaked out with all the yellow and tried to remove it … causing the shadows to turn a strong blue tint" [M19]. This is not a lab scanner; it shows the same kind of failure in a tool built to imitate one.

## 5. What the operator sets

### Fujifilm SP-3000

- **[published] Every frame can be checked.** "this image is displayed on the screen and the operator is requested to confirm the image or correct it if required. The result of this manual key correction is reflected in the fine scanning conditions" [F1]. The keys are density, cyan, magenta and yellow: "the operator performs correction of the frame with DCMY keys" [F10].
- **[published] Key step sizes.** For negatives: "C, M, Y: Normally enter “8”. Dc, Dm, Dy: Normally enter “15”." For slides: 4 and 8 [F6]. The manual gives no unit. **[measured by others]** The film maker's sheet gives a different default for the same setting: "Default (CMY = 5, D=10)" [M15]. Whether that is a different software version is not known.
- **[published] Other settings, with the manual's "normal" values** [F6]:
  - Balance and slope ("BL/SL"): "Normally enter “0”. Change settings only when the whole slope condition is offset."
  - Saturation: "Range is –9 to +9. Normally enter “0”."
  - Sharpness: "Select “Hyper-sharpness” for “Sharpness process”"; level Low 3 to High 3 with Normal in the middle; a separate level for under-exposed film.
  - "Grain Control Process": Higher, Normal, Lower.
  - "Bright Mode" colour intensity -2 to 4; for slides a "Basic Color Mode" 0 or "1(Nature Mode)".
- **[published] A lab can store its own setups.** "The 65 (0 + 64) custom conditions can be set up for each input type", chosen on the scanning screen; "To change the finished image for a specific film, set up the condition previously" [F6].
- **[not known]** The factory default of each SP-3000 setting. The manual I could open says "normally" for some and shows examples for others. The separate "Operating Instructions" volume could not be opened.

### Noritsu EZ Controller

- **[published] Whether a person looks at all is a setting.** "There are three print methods, PJP, AUTO and PPI." In AUTO, "Read images are not displayed on the monitor. Other than the settings for number of prints, for example the color and density correction settings, are entrusted to the system" [N1].
- **[published] Keys.** Yellow, magenta, cyan and density per frame. "The initial value of the color difference ratio is 5.8% and that of the density difference ratio is 15.0%" per key press [N1].
- **[published] Per-frame DSA.** Automatic Contrast (Overall, Shadow, Highlight), Automatic Sharpness, Chroma, Graininess Suppression and others, from -10 to +10: "corrections of contrast, sharpness, chroma, and graininess suppression can be made for each frame" [N2]. They stack in three layers: per input type, per print channel, per frame [N1].
- **[published] Defaults stated in the manual's text** [N1]:

  | Setting | Default |
  |---|---|
  | Scanner Gradation Correction, negative film except 120 | ON |
  | Scanner Gradation Correction, 120 negative film | OFF |
  | Basic Density Correction Switch | 1, on a scale of 0 to 4 |
  | Colour key step and density key step | 5.8% and 15.0% |
  | CCD Noise Suppression | on, "correction rate of 10" |
  | Automatic Contrast 2 | "A value of 5 is recommended"; 0 turns it off |

- **[published] Values seen only on the manual's example screens** (not called defaults): colour correction "Standard"; Automatic Contrast 0, 0, 0; Automatic Sharpness 0; Chroma 100; Graininess Suppression 5; Automatic Contrast 2 at 0; Gradation Characteristics "Standard" [N1]. A sharpness of 0 means no change to the automatic amount, not no sharpening, since the control is named Automatic Sharpness and lower values blur **(my reasoning)**.
- **[measured by others, operator documentation]** The film maker's sheet lists, for the HS-1800 and LS scanners, a lab starting point of "Colour Correction = Std / Gradation Correction(135) = ON / Basic Dens Correction = 1" and notes "Many labs will have a preferred configuration" [M15].
- **[measured by others, former operator's word]** "The Noritsu allowed me to set up a custom channel for each [DX] code … a saved set of color, contrast, density, sharpness and saturation level for each film stock", balanced by eye on a gray patch [M16].

### How much labs use these

- **[measured by others, labs' word]** "our technicians have the opportunity to make tweaks to the colours, the contrast, and manage the levels of each frame. This is a subjective exercise" [M10]. "we work on your pictures frame by frame" [M3]. One lab takes "the names of photographers you love, so they can emulate the look for you" [M11].
- **[measured by others, lab's word]** The limit of the keys: "scanning machines can only control color balance across the entire image (and not specific color channels or selective masking/editing), that means all the other colors in an image just fall where they may" [M6].

## 6. Output

### Fujifilm

- **[published] sRGB was the design goal for files.** Among the aims of the Frontier 350/370's link to outside systems: "色空間 sRGB への統一とプリント色再現保証" (unifying on the sRGB colour space and guaranteeing print colour reproduction) and "当社固有の画像処理の隠蔽，共有利用" (hiding, and sharing the use of, the company's own image processing) [F2].
- **[published] Files and prints go through separate processing.** On the Frontier 390: "プリント系とデジタイズ系で独立の画像処理（画素数やシャープネスなどが違う）を実施する必要があり" (the print path and the digitising path need independent image processing: pixel count, sharpness and so on differ) [F3]. So a file from a Frontier is not simply the print data saved.
- **[published] A quality setting for files.** The SP-3000 has a "Scanning Condition Setup for Digital Image Export": "Image Quality" or "Performance" [F6].
- **[published] Sharpening and grain are one linked step.** "To emphasize sharpness, USM (un-sharp masking) is generally used. This processing involves emphasizing the grain of the film if degree of emphasis is increased." Hyper-Sharpness splits the picture into three bands of detail and tells edges from flat areas by whether the three colours agree: where they agree it raises the fine band, where they do not it lowers the middle band [F1]. Later models added a "morphology" grain method [F2] and a new edge detector [F4].
- **[not known] File format and bit depth, from the maker.** The SP-3000 manual's "Image Export Settings" section says only "See the “Operating Instructions” manual" [F6], which could not be opened.
- **[measured by others]** Labs and operators report: "8 bits" for the Frontier against "16 bits" for the Noritsu [M3]; 35mm maximum "5433x3637 pixels" [M8]; medium format "4096x4096px or for a 6x9 negative up to 4096x6144px" [M7]; "the size you scan is the size you print" [M4].
- **[measured by others, developer's word]** Negative Lab Pro's "Sharpen: Lab" setting "is based on the default output of Fuji Frontier lab scanners. The sharpening scheme focuses on edges, with a mask" [M18]. **[measured by others, lab's word]** "the sharpness (or feeling of an unsharp mask) can be noticed on the Frontier … the contrast on the edges is higher on the Frontier" [M1]. "The grain is always smooth and clean due it’s grain suppression algorithm" [M2].

### Noritsu

- **[published] Formats.** Saving: JPEG, bitmap, TIFF "(16 bit is also available.)" and FlashPix. "If TIFF(16bit) is selected, the maximum image size that can be saved is 5120 × 10920 pixels" [N1].
- **[published] Colour space.** "Auto conversion to sRGB Color Space — Select whether to convert the color space to sRGB or not when saving image data to storage media" [N1]. The manual does not name the colour space a film scan is in before that, nor the default of the checkbox.
- **[published] Corrections are written into the saved file.** The manual's table of what is saved with an image marks as saved the key corrections, every DSA item and tone curve correction [N1].
- **[published] Sizes.** HS-1800, 35mm: from "1037 x 1565" to "4492 x 6774" pixels; LS-600 and LS-1100: up to "4011 x 6048" [N4].
- **[published] Noise in thin and dense areas is smoothed by default.** "parts of an image that are extremely under- or over-exposed can look gritty on the print. This function corrects this. … The initial setting is (with check mark) and a CCD Noise Suppression correction rate of 10" [N1].
- **[published] A less processed route exists.** In stand-alone use, "48bit Image Capture — Select the check box to capture 48bit images", and the DSA and key buttons are "Not shown if 48bit Image Capture is selected" [N2]. Whether the automatic corrections still run in that mode is not stated.
- **[measured by others]** "Noritsu and Frontier scanners produce extremely similar levels of sharpness"; "The increment of sharpness used on Richard’s scans is in the middle" [M5]. "The grain is sharper and more noticeable on higher ISO emulsions" [M2].

## How repeatable is a lab scan of the same negative?

This is the question the map needs answered next. The evidence is laid out by case. **No source gives a number for colour or tone in any of the three cases.**

### What the makers say about their own machines

- **[published] Fujifilm, in a patent, lists three cases in which the same result cannot be had.** The setting is a customer wanting reprints to match first prints. "even if the parameters to the gray balance condition … are stored in a memory and accessed when reprints are ordered …, no two prints are guaranteed to have the same finish unless the scanner characteristics are identical between the two instances. Even if the same scanner is used, faithful reproduction of gray balance is impossible if the scanner characteristics change with time. Even if two scanners of the same model are used, the same problem occurs if they have instrumental error in their characteristics. Of course, gray balance cannot be reproduced faithfully if two different scanners are used" [F10]. The cause it names: "differences in the linearity and spectral sensitivity characteristics of the scanners" [F10]. The patent's remedy, gray patches exposed on the film itself, needs film made with them; I found nothing saying it shipped.
- **[published] Both makers treat light source drift as a thing to control.** Fujifilm: the task with an LED source "は，光量確保と光量波長変動を抑えることである" (is to secure the amount of light and to hold down changes in amount and wavelength), done with a ceramic board and Peltier temperature control [F4]. Noritsu: "The light source of the scanner fluctuates from day to day according to the environment. Therefore, perform the correction of light source on the Scanner Calibration display" [N2]; its LED units are held within 1 or 2 °C [N3].
- **[published] The correction is built to change with the frame and the roll** (parts 2 to 4). So the same negative frame gets a different correction if the frames around it differ, for example a strip rescanned alone and not with its roll **(my reasoning from [F1][F9][N1][N5])**. No source tests this.

### Same scanner, same negative, twice

- **[not known]** Nobody has published two scans of one frame made on the same Frontier or Noritsu, with or without the automatic corrections, with or without numbers [M-all].
- **[measured by others, mask maker's guide]** The frame does not land in the same place each time on the SP3000: "Not every frame is transported by exactly the same amount, meaning the position of the frames can vary slightly from image to image", and the standard masks crop "6-7%" [M14]. If the analysis sees slightly different pixels, a rescan could differ even if the arithmetic is fixed **(my reasoning)**.
- **[measured by others, lab's word]** The Frontier "shifts a bit the color and contrast on every frame" [M1]. This is frame to frame within a roll, not the same frame twice.

### Frontier against Noritsu, same negative

- **[measured by others] The only numbers are for size and format.**

  | Source | Frontier | Noritsu |
  |---|---|---|
  | Lab's table, maximum [M3] | "3500 x 5250 px", "8 bits" | "5000 x 7500 px", "16 bits" |
  | Former technician, 35mm maximum [M8] | "5433x3637 pixels", "19.8 Megapixels", "5 MB" | "6774x4492 pixels", "30.4 Megapixels", "15 MB" |
  | Photographer, 6x6 maximum [M7] | "4096x4096px" | "4700x4700px" |

- **[measured by others, same-negative comparisons and labs' word] What labs agree on.** The Frontier has more contrast in the middle tones and at edges, more saturation, smoother grain, and holds highlights by flattening them. The Noritsu is flatter, shows more grain, and gives the operator more control of contrast [M1][M2][M5][M7][M9][M12].
- **[measured by others] What labs do not agree on: which way the colour leans.**
  - One lab in 2021: Frontier "Overall cooler tones with cyan and blue shadows", Noritsu "warmer tones yet more flat" [M2].
  - The same lab in 2016: "The palette goes a bit reddish on the Noritsu side"; Frontier shadows show "some shades of magenta" [M1].
  - A photographer scanning at that lab: the Frontier gives "a noticeable boost in warmth" [M9].
  - Another comparison, one frame: the Frontier's colours are "more towards magenta" [M7].
  - Negative Lab Pro's guide: the Noritsu "is generally not as warm" [M18].
  - A second lab declines to say: "Richard can never say one machine produces definitively “warmer” or “greener” or “anything-er” tones", because each machine reads magenta tones differently and "these interpretations will then vary under different lighting conditions" [M4].
- **[measured by others] The published side-by-sides are weak evidence of the machines.** One lab says of its own: "these images are edited to match each other, as usually the tones will drift a little on each scanner" [M1]. The same lab, five years on: "we thought the Noritsu had to look like the Frontier and we worked towards that direction" [M2]. A former technician: "when film is exposed correctly, both scanners will produce near-identical results" [M8]. And: "there are are way to make the Frontier look soft and the Noritsu go punchy and vivid" [M2].
- **What the disagreement suggests (my reasoning).** If labs that run both machines cannot agree on the direction of the colour difference, the difference between the machines is either smaller than, or tangled up with, each lab's setup and each frame's correction.

### Different labs and different operators

- **[not known]** No measured comparison of one negative across labs was found.
- **[measured by others, labs' word] Labs say the person and the setup come first.** "what’s going to influence your scans more than the machine you choose is the communication you have with the lab doing the scanning and the skills of their staff" [M4]. "It can also be difficult to maintain full visual consistency through the entire roll, so you may notice slight variations in colour or contrast between images" [M10]. "many labs will have their own preferred workflow" [M15].
- **[measured by others, labs' word] Labs give different customers different looks on purpose.** One keeps "a detailed custom color profile" per customer [M4]; one emulates named photographers [M11].
- **[measured by others, lab's word] A lab cannot know which rendering is right.** "These images are just a sample of how a range of colors can be achieved from the same color negative… and without any guidance from you, we don’t know which one is right" [M6].
- **[measured by others, one comparison, weak]** Two labs returned files of the same pixel size, 2797 x 2048, that differed plainly in density and grain; but these were two rolls of the same scene, not one negative [M11].

### The nearest instrument evidence, from neighbouring machines

- **[measured by others, instrument, printer side]** A profiling service measured the printers in Frontier minilabs, not the film scanners: "Profiles from two randomly chosen Frontier printers in our database are compared … the color gamuts of the two printers do not match each other." Of the automatic correction on digital files: "the adjustments are image data specific; i.e. as the content of the image changes, so does the “correction” applied." With it off, "we are left with an exceptionally stable printing platform" [M13]. No colour difference figure is given in the text.
- **[measured by others, academic, cinema film scanners]** A university study had the same films scanned on archive scanners. Two operators on the same scanner model "followed different routes … As a result the two scans differ highly from each other", and across scanners "It was not possible to obtain a standardized tone range or histogram" [M22]. It also reports that narrow-band light gives more vivid colour than white light: "no processing would retrieve those colors from the image captured with white light" [M22]. These are not minilab scanners.

### Summary of the repeatability evidence

| Case | Is there a number? | Best evidence |
|---|---|---|
| Same scanner, same negative, twice | No | Maker's patent says not guaranteed over time [F10]; frame position varies [M14]; untested |
| Same model, two machines | No | Maker's patent says "instrumental error" [F10]; printer-side gamuts differ [M13] |
| Frontier against Noritsu | Size and bit depth only | Labs agree on contrast, grain and highlights; disagree on colour direction [M1][M2][M4][M9] |
| Two labs, or two operators | No | Labs say the operator and setup dominate [M4][M10][M15]; per-customer looks [M4][M11] |
| Same frame, different roll around it | No | Follows from roll-level correction [F1][F9][N1][N5] **(my reasoning)**; untested |

What this says about a reference made from community scans, kept to the evidence: such scans carry at least five sources of variation that the sources name (scanner generation and its light, the lab's stored setup, the rest of the roll, the content of the frame, the operator and any per-customer look), plus editing after the scan, which one former technician says is what "custom color" really is [M8]. None of the five has a published size.

## Not known

- **Numbers for repeatability**, in every case in the table above.
- **LED peak wavelengths** of the SP-3000, SP500, HS-1800, LS-600 and LS-1100. Only the Frontier 330 and 340E have a published figure [F5].
- **Converter bit depth** of every scanner here except the Frontier 330's 12 bits [F4].
- **The base tone curve** of either maker, as numbers.
- **The shipped algorithms.** For both makers the arithmetic is in patents only. Fujifilm's papers confirm the outline (roll prescan, setup from all frames, face-based density, Hyper-Tone, Hyper-Sharpness) [F1][F2]; Noritsu's manuals confirm the outline (frame, order or between; scene-judged density and gradation) [N1]. Neither confirms the detail.
- **How Noritsu's "Standard" blends frame and order**, and what its scene judgment tests.
- **Whether either maker ships stored data per film stock.** Fujifilm says it needs none [F2]; Noritsu's manuals document only the lab's own DX slope offsets [N1].
- **SP-3000 factory defaults, file formats and file bit depth from the maker.** They are in the "Operating Instructions" volume, not opened.
- **Whether Noritsu's 48-bit capture skips the automatic corrections**, and what encoding its 16-bit TIFF holds.
- **What ACCS stands for** and what its rules are.
- **Whether a rescan with identical settings gives an identical file.** One blogger says the machines are deterministic [M23]; nobody shows a test.
- **How Negative Lab Pro's "Frontier" and "Noritsu" models were made.**
- **Software versions.** The SP-3000 manual is MS11 Ver. 1.0 (2007); the EZ Controller manual is Ver. 3 (2008). Labs today may run other versions. The two different key-step defaults in part 5 may be a sign of this.
- **Black-and-white film.** This note is about colour negative. Both machines have a black-and-white input type [F6][N2]; one lab says "Frontier scans of black and white can appear to be muddy brown" [M4]. Not looked into further.
- **Slide film.** Both machines scan it with separate settings [F6][N1]. Not looked into further.

## Could not open

These were found but not read. Nothing above relies on them.

- **Fujifilm SP-3000 "Operating Instructions"** and the **Frontier 390 instruction manual**: manualslib.com, manualshive.com and manuals.online refused automated access (HTTP 403 or a bot wall); Scribd needs an account.
- **Fujifilm's press release for the Frontier 570E**, `http://www.fujifilm.co.jp/news_r/nrj1271.html`: gone from Fujifilm's site; the Wayback Machine refused the request. Its content is known only through the news report [F14].
- **Nakamura, "Digital Image Processing for the Frontier350 Digital Minilab", IS&T PICS 1999, pages 96 to 99**: cited by [F1]; no copy found online.
- **ISO 5-3**, the definition of Status M: sold, not free. A third-party transcription is used and marked as such [S2].
- **photrio.com**, where most operator threads on these scanners live: HTTP 403. Threads not read include `https://www.photrio.com/forum/threads/how-do-scanners-color-correct-c-41-negatives.169634/` and `https://www.photrio.com/forum/threads/fuji-frontier-sp3000-vs-mirrorless-scanning.204388/`.
- **Reddit threads** on lab scan differences: mirrors failed or were bot-walled.
- **Analog Notes, "Noritsu vs Frontier"**, `https://analognotes.substack.com/p/noritsu-vs-frontier`: one roll on both scanners, behind a paywall after the introduction.
- **CineStill's help article on lab scanners**, **Jim Kasson's blog post 33470**, and **PetaPixel's piece on Gelatin Labs**: HTTP 403.
- **Noritsu's tech tips pages on noritsu.com**: HTTP 406; the Canadian tech tips page did open and has nothing on film scanning.
- **Noritsu EZ Controller "Image Editing Operator's Manual"** (tone curves) and the **QSS-32 and QSS-37 manuals**: not found.
- **Not searched exhaustively:** patents. Numbers were found through web search, not a full search of each maker's filings.

## Sources

Fujifilm, first-party:

- [F1] F. Sonoda, T. Matama, H. Nakamura (Fuji Photo Film), "Image Processing of Digital Minilab System", *Journal of the Society of Photographic Science and Technology of Japan* 64(5), 316-321, 2001. In English. <https://www.jstage.jst.go.jp/article/photogrst1964/64/5/64_5_316/_pdf> (DOI 10.11454/photogrst1964.64.316)
- [F2] Y. Ozawa and others, "デジタルミニラボ Frontier 350/370 の開発" (Development of Digital Minilab Systems "Frontier 350/370"), *Fujifilm Research & Development* No. 45, 35-41, 2000. Sections 3.2, 3.3, 5.2 and 10.2. <https://asset.fujifilm.com/www/jp/files/2019-09/60505e3ff99249a79b3027b2817a867b/rd_report_ff_rd045_007.pdf>
- [F3] T. Yamamoto and others, "デジタルミニラボ Frontier390 の開発", *Fujifilm Research & Development* No. 47, 24-30, 2002. <https://asset.fujifilm.com/www/jp/files/2019-09/3762079d1dfc91190da88597f3804e21/rd_report_ff_rd047_005.pdf>
- [F4] Y. Nakamura and others, "小型デジタルミニラボ Frontier 330 の開発", *Fujifilm Research & Development* No. 48, 15-21, 2003. Sections 4.1.1, 4.1.2 and 4.1.6. <https://asset.fujifilm.com/www/jp/files/2019-09/8c4625b8347ee5db9da2f0bc77e1655a/rd_report_ff_rd048_004.pdf>
- [F5] F. Mogi and others, "小型迅速デジタルミニラボ Frontier 340E の開発", *Fujifilm Research & Development* No. 49, 19-25, 2004. Section 3.1 and Figs. 2 and 3. <https://asset.fujifilm.com/www/jp/files/2019-10/da0eca2de68480ca18c6c08713c5855c/rd_report_ff_rd049_004.pdf>
- [F6] Fujifilm, *Instruction Manual, Frontier Workflow Management Software, Film Scanner Connection Software for SP-3000: Condition Setup and Maintenance*, MS11 Ver. 1.0, Second Edition, reference PP3-B1271E2, 2007. Sections 2.2, 4.3.4, 4.3.6, 4.4.6 and 6.1. Copy hosted by a third party: <https://fotobrell.com/wp-content/uploads/pp3-b1271e2-1.pdf>
- [F7] Fujifilm (United States), "Frontier SP500: Specifications", marked discontinued. <https://www.fujifilm.com/us/en/business/photofinishing/digital-lab-solutions/frontier-sp500/specifications>
- [F8] US 5,781,315, "Image processing method for photographic printer", H. Yamaguchi, Fuji Photo Film, priority 1995, granted 1998. <https://patents.google.com/patent/US5781315/en>
- [F9] US 6,665,434 B1, "Device, method, and recording medium for correcting color imbalance of an image", H. Yamaguchi, Fuji Photo Film, priority 1999, granted 2003. <https://patents.google.com/patent/US6665434/en>
- [F10] US 6,683,981 B1, "Image processing method", T. Matama, Fuji Photo Film, priority 1998, granted 2004. <https://patents.google.com/patent/US6683981/en>
- [F11] US 6,791,721 B1, "Image reading device", T. Konagaya and Y. Nakamura, Fuji Photo Film, priority 1999, granted 2004. <https://patents.google.com/patent/US6791721/en>
- [F12] US 6,806,981 B1, "Image reading apparatus", M. Konno, Fuji Photo Film, priority 1999, granted 2004. Read for background; it argues for more blue LEDs than red, the reverse of the SP-3000's parts list [F6], a reminder that a patent is not a product. <https://patents.google.com/patent/US6806981/en>
- [F13] Fuji Photo Film, Fujicolor Pro colour negative film brochure, reference PB-410E, 2004. <https://asset.fujifilm.com/www/us/files/2020-03/14c3c3e650b41069b071bfd3180bd936/FUJICOLOR_PRO_NEG_FAMILY_BROCHURE_101305.pdf>
- [F14] Impress Digital Camera Watch, "富士フイルム、小さく速くなったデジタルミニラボ「フロンティア570E」", 5 October 2004. A news report of Fujifilm's press release, not first-party. <https://dc.watch.impress.co.jp/cda/other/2004/10/05/207.html>
- [F15] Fujifilm, Frontier LP7000 series brochure, which offers the SP-500 and SP-3000 as its film scanners. <https://www.fujifilm.co.il/wp-content/uploads/2012/07/frontier_700.pdf>

Noritsu, first-party:

- [N1] Noritsu Koki, *EZ Controller Operator's Manual*, English Ver. 3, issued June 2008. Sections 1.1.2, 3.3.2, 4.3.4, 5.1.5, 5.2, 5.4, 5.5, 5.6.4.1, 6.15.3 and the glossary; page 5-18 for the negative film switches. <https://archive.org/details/ez-controller-operators-manual>
- [N2] Noritsu Koki, *LS-600 Operator's Manual*, English Ver. 1, April 2007, and *LS-600 Starting Guide*, April 2007. Copies hosted by a third party: <https://www.gostreetphoto.com/wp-content/uploads/NORITSU-OPERATOR-MANUAL-APRIL-2007.pdf> and <https://www.gostreetphoto.com/wp-content/uploads/NORITSU-STARTING-GUIDE-APRIL-2007.pdf>
- [N3] Noritsu Koki, *Scanner Service Manual* for the LS-600, LS-1100 and HS-1800, April 2007. Hardware facts only. Copy hosted by a third party: <https://www.gostreetphoto.com/wp-content/uploads/NORITSU-SERVICE-MANUAL-APRIL-2007.pdf>
- [N4] Noritsu America product pages and brochures, saved by a reseller: HS-1800 <https://footprintsequipment.com/images/brochures/Noritsu/Scanners/HS-1800FilmScanner.pdf>, LS-600 <https://www.footprintsequipment.com/images/brochures/Noritsu/Scanners/LS-600FilmScanner.pdf>, LS-1100 <https://footprintsequipment.com/images/brochures/Noritsu/Scanners/LS-1100FilmScanner.pdf>, QSS-3001 <https://footprintsequipment.com/images/brochures/Noritsu/PrinterProcessors/3001.pdf>
- [N5] US 7,613,339 B2, "Method and an apparatus for detecting the base concentration of a photographic film", Noritsu Koki, priority 2004, granted 2009. <https://patents.google.com/patent/US7613339B2/en>
- [N6] EP 1 662 315 A2, "Photograph image-processing method and device thereof", Noritsu Koki, priority 2004, published 2006. <https://patents.google.com/patent/EP1662315A2/en>
- [N7] EP 1 411 714 A2, "Conversion correcting method of color image data and photographic processing apparatus implementing the method", Noritsu Koki, priority 2002, published 2004. <https://patents.google.com/patent/EP1411714A2/en>
- [N8] JP 4655211 B2, on generating the correction characteristic used for contrast correction, Noritsu Koki, filed 2005. Read in machine translation. <https://patents.google.com/patent/JP4655211B2/en>
- [N9] EP 1 471 383 A1, on judging whether a picture was taken under unusual light, Noritsu Koki, priority 2003. <https://patents.google.com/patent/EP1471383A1/en>
- [N10] US 7,204,609 B2, "Light-emitting diode light source unit", Noritsu Koki, priority 2003, granted 2007. <https://patents.google.com/patent/US7204609B2/en>
- [N11] Further Noritsu Koki patents read for background and not quoted: EP 1 443 459 A2 (noise in under- and over-exposed areas), EP 1 330 114 A2 (sharpening strength by grain), EP 1 176 801 A2 and EP 1 580 689 A2 (grain suppression), EP 1 530 154 A2 (sharpening by colour), JP 4591784 B2 and JP 4998794 B2 (learned correction curves). Each at `https://patents.google.com/patent/<number>/en`.

Measured or reported by others:

- [M1] Carmencita Film Lab, "New Film Scan Options: Noritsu HS-1800", 2016. A lab running both scanners; same frames on each. <https://carmencitafilmlab.com/blog/new-film-scan-options-noritsu-hs-1800/>
- [M2] Carmencita Film Lab, "Frontier vs Noritsu: Round 2 (5 years later)", 2021. <https://carmencitafilmlab.com/?p=35292>
- [M3] Carmencita Film Lab, scanning page with comparison table. <https://carmencitafilmlab.com/we-do/scanning/>
- [M4] Richard Photo Lab, "It's back… Noritsu vs Frontier!". <https://www.richardphotolab.com/blog/post/its-back-noritsu-vs-frontier>
- [M5] Richard Photo Lab, "Stay Sharp! Richard explores film scan sharpness". <https://richardphotolab.com/blogs/post/stay-sharp-richard-explores-film-scan-sharpness>
- [M6] Richard Photo Lab, "Scanning colors: detail shots and other images (no skin tones)". <https://richardphotolab.com/blogs/post/scanning-colors-detail-shots-and-other-images-no-skin-tones>
- [M7] Sebastian Schlüter, "The magic Fuji Frontier SP-3000", 2018. Same negatives scanned on both by one lab. <https://sebastian-schlueter.com/blog/2018/3/7/the-magic-fuji-frontier-sp-3000>
- [M8] David Cruz, former lab technician, "Noritsu vs Frontier". <https://thedrunkweddingphotographer.com/summerimperfect/noritsu-vs-frontier>
- [M9] JB Flanc, "The Art of Film Scanning: Frontier vs. Noritsu". Scans "straight from the scanners, unedited". <https://jbflanc.substack.com/p/the-art-of-film-scanning-frontier>
- [M10] Analogue Wonderland, "Editing film scans in the lab". <https://analoguewonderland.co.uk/blogs/film-photography-blog/editing-film-scans-in-the-lab>
- [M11] Anna Wu, "Oscar's Photo Lab vs Richard Photo Lab", 2011. <https://annawu.com/blog/2011/04/oscars-photo-lab-vs-richard-photo-lab/>
- [M12] Photovision, "Noritsu or Frontier" help article. <https://pv-site-astro.pages.dev/help/articles/noritsu-or-frontier>
- [M13] Dry Creek Photo, "Additional profile questions" and "Using printer profiles". Printer-side measurements of Frontier and Noritsu minilabs. <https://www.drycreekphoto.com/Learn/additional_profile_questions.htm> and <https://drycreekphoto.com/icc/using_printer_profiles.htm>
- [M14] BOBACH, mask installation guide for the SP3000. <https://cdn.shopify.com/s/files/1/0736/5119/2072/files/135_FFMS_SP3000_Guide.pdf>
- [M15] Harman Technology, "Recommended scanning parameters, Harman Phoenix 200", October 2024, written with four labs. <https://harmanphoto.co.uk/wp/wp-content/uploads/sites/3/2024/10/Phoenix-Scanning-Parameters-011024.pdf>
- [M16] Chris Tisinger, former lab operator, Color Craft Lab blog. <https://colorcraftlab.blogspot.com/>
- [M17] alchemycolor, "Working the color negative". <https://alchemycolor.com/working-the-color-negative/>
- [M18] Negative Lab Pro, guide, "Basics". <https://www.negativelabpro.com/guide/basics/>
- [M19] Negative Lab Pro forum, posts by the developer: "How to get the original film look" <https://forums.negativelabpro.com/t/3862>, version 2.2 <https://forums.negativelabpro.com/t/2513>, version 3.0 <https://forums.negativelabpro.com/t/6429>
- [M20] darktable, `negadoctor.c` source header and user manual. <https://raw.githubusercontent.com/darktable-org/darktable/master/src/iop/negadoctor.c> and <https://docs.darktable.org/usermanual/stable/en/module-reference/processing-modules/negadoctor/>
- [M21] RawTherapee, RawPedia, "Film Negative". <https://rawpedia.pixls.us/film_negative/>
- [M22] B. Flueckiger and others, "Investigation of Film Material–Scanner Interaction", DIASTOR, University of Zurich, 2018. Cinema film archive scanners. <https://diastor.ch/wp-content/uploads/2018/02/flueckigeretal_investigationfilmmaterialscannerinteraction_2018_v_1-1b.pdf>
- [M23] cameragx.com, posts tagged "frontier". <https://cameragx.com/tag/frontier/>
- [M-all] The whole set above, plus the searches that found nothing: no measured LED spectrum, no raw data dump, no colour difference figure and no same-frame-twice test for any Frontier or Noritsu film scanner was found in any source that could be opened.

Standards and related:

- [S1] SMPTE RP 180-1999, "Spectral Conditions Defining Printing Density in Motion-Picture Negative and Intermediate Films". <https://pub.smpte.org/pub/rp180/rp0180-1999_stable2006.pdf>
- [S2] Status M spectral products as transcribed in the open project `spectral_film_lut`, file `densiometry.py`, at commit `a15043f`. A third-party copy of the ISO 5-3 table, not the standard itself. <https://github.com/JanLohse/spectral_film_lut/blob/a15043f6fe2d365d0c359d22e0868076800916d9/src/spectral_film_lut/densiometry.py>
