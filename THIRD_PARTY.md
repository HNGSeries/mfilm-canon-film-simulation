# Third-party software

- **Magic Lantern** (GPL-2.0): the camera side builds on it. https://magiclantern.fm
- **The colour tables of 59 film stocks** are adapted from film emulation tables by **Pat David**
  (https://patdavid.net), shared under **CC BY-SA 4.0**.
  See [The film colour tables](#the-film-colour-tables-cc-by-sa-40) below: they are not under GPL-2.0.
- **Film-Luts** by Yahia Angelo (MIT License, below): the export of G'MIC's built-in film tables that the
  build downloads those tables from, https://github.com/YahiaAngelo/Film-Luts. Its `.cube` files are *not*
  in this repository: the camera build (`ml-dev/films/getluts.py`) and Darkrooms download them.
- **Barlow** font family (SIL Open Font License 1.1): `ml-dev/filmos/fonts/OFL.txt`.
- Film names and box art are descriptive and made for this project; they are not affiliated with or endorsed
  by Kodak, Fujifilm, CineStill, Ilford, Agfa or others. "Canon" and "EOS M" are trademarks of Canon Inc.;
  this project is not affiliated with Canon. Canon firmware is not included.

## The film colour tables (CC BY-SA 4.0)

**What they are.** For the 59 film stocks listed in `ml-dev/films/filmluts.py`, the colour comes from a film
emulation table that G'MIC credits to Pat David, who published them in 2013
(https://patdavid.net/2013/08/film-emulation-presets-in-gmic-gimp/). His site states: "Unless otherwise noted,
this work by Pat David is licensed under a Creative Commons Attribution-ShareAlike 4.0 International License",
which he explains as "you are free to share and adapt my works in any way you'd like (even commercially),
provided you give me credit and that any changes you make to my works will be licensed under the same
conditions", and asks: "Please attribute me as: 'Pat David' with a link to this site, https://patdavid.net"
(https://patdavid.net/about/). The same tables are in the RawTherapee Film Simulation Collection, which its
README gives as CC BY-SA 4.0 and which credits Pat David, Pavlov Dmitry and Michael Ezra without saying who
made which table.

**How they reach M-Film, and what was changed.** G'MIC has the tables built in, compressed. Film-Luts is an
export of G'MIC's tables as `.cube` files, 13 points a side. M-Film's build resamples each one to 33 points a
side over Cineon code and gives its input the tone curve of a finished photo (`ml-dev/films/lut.py`,
`ml-dev/filmos/tools/genfilms.py`, `ml-dev/filmos/tools/gentables.py`).

**Which files.** The tables made that way: `ML/DARKROOM/LOOKnn.LUT` on the card for those 59 film stocks, and the
same files in `M-Film-tables.zip`. `TABLES.txt` in that zip lists every table and marks these ones `lut`. The
other tables there are mixed from M-Film's own film model and are part of M-Film.

**Their licence.** Those table files are licensed under the Creative Commons Attribution-ShareAlike 4.0
International licence, https://creativecommons.org/licenses/by-sa/4.0/, and not under GPL-2.0. They are data
the program reads, kept apart from it, and they are not encrypted or locked. You may copy, share and change
them, for any purpose, if you credit Pat David as above, link the licence, say what you changed, and share
your version under the same licence. Credit: "Pat David", https://patdavid.net.

**What they are not.** Pat David describes these tables as his approximations, made by eye from examples
online, of "a very popular set of film emulation presets that are available commercially", and has said that
some "were likely also reverse-generated from other color curve packages". They are looks, not measurements
of the films they are named after. A Creative Commons licence passes on only the rights its licensor has.

The pictures developed with these tables (`ML/SAMPLES` on the card, `docs/films` and `docs/samples` here) are
M-Film's own prints of M-Film's own photo, made through them.

## Film-Luts licence

Film-Luts' own notice. Its maintainer writes that he "does not claim ownership of the LUTs", so this covers his
export and packaging, and the terms above apply to the tables.

```
MIT License

Copyright (c) 2024 Yahia

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
