# What's new in M-Film

The camera side, version by version. The files for each are in the
[releases](https://github.com/HNGSeries/mfilm-canon-film-simulation/releases); Darkrooms has
[its own](https://github.com/HNGSeries/Darkrooms-app/releases). [ภาษาไทย](CHANGELOG.th.md)

## 0.2.4

- **Nine film stocks take their colour from [spektrafilm](https://github.com/andreavolpato/spektrafilm)**, by
  Andrea Volpato, which builds each film from its maker's data, layer by layer, and develops, prints and scans it:
  Kodak Portra 160, 400 and 800, Ektar 100, Gold 200 and Kodachrome 64, and Fujifilm Pro 400H, Velvia 100 and
  Provia 100F. Each keeps the brightness it had; its colour and contrast change, so these nine won't match what
  0.2.3 developed ([how they compare](docs/spektrafilm.md)). The shelf is still 68 film stocks, and none is
  measured against the real film yet. The tables are CC BY-SA 4.0: every zip carries `SPEKTRAFILM_LICENSE.txt`.
- **Finer grain** for Portra 400, Pro 400H and the Portra 400 NC, VC and UC ([#80](../../issues/80)).
- **The 1300D no longer freezes at power on** ([#85](../../issues/85)): its first tester found the bug and fixed it.
  With the fix the film shelf, shooting and the in-camera darkroom worked on their camera. Its zip has no
  `ML-SETUP.FIR` (Magic Lantern makes none for it): it now carries **mlinstall**, which sets the camera up
  from a computer instead, in the folder `mlinstall-for-your-computer` (it doesn't go on the card), and
  M-FILM-README.txt in the zip says how.
- Every zip's name says which M-Film it is: `M-Film-0.2.4-camera-EOSM.202.zip`.

**Copy the whole `ML` folder of the zip to the card** again: the nine new colour tables are in `ML/DARKROOM`.

## 0.2.3

0.2.3 is about colour, on every camera:

- A roll comes out the same colour in the camera and in **Darkrooms 0.2.0**: the two develop the same way and
  read the same colour tables ([#132](../../issues/132); [how the darkroom develops](ml-dev/DEVELOPING.md)).
  From this version on, Darkrooms updates itself.
- The darkroom develops a frame with the white balance the camera was on, and cuts it where that frame's own
  samples clip: blown highlights are no longer pink.
- The 59 films whose colour comes from Pat David's tables are fed a finished photo's tone, as those tables
  expect. Every colour film changes; pictures will not match the ones 0.2.1 developed.
- The glow round highlights is fainter on every film, and a highlight no longer goes red from its own light.
- The four cinema print films left the shelf: 68 film stocks.
- Every film stock says whether it is measured against the real film or only in its style
  ([FILMS.md](FILMS.md)). None is measured yet: [how a paired shot is made](docs/paired-shot.md).

**Copy the whole `ML` folder of the zip to the card**, not only `autoexec.bin`: the films' colour tables are
files in `ML/DARKROOM` now, and without them the darkroom stops with "no colour table".

## 0.2.1

Adds the [Canon EOS 1300D](TESTING.md#canon-eos-1300d), for testers. Nothing changes on the other cameras: they don't need to update.

## 0.2: everything since 0.1.6

- **Bigger prints.** Small, Medium or Large, asked before the darkroom starts: up to 2592 × 1728 from an 18 MP camera.
- **Zoom.** In the prints, turn the wheel to go into a frame and the arrows to move about.
- **Four viewfinders.** Classic (the SLR's), Minimal, Rangefinder and Clean: *Settings → Viewfinder*.
- **A shorter Home.** What to do next on top, then Darkroom and Settings. The battery is on every page.
- **Print sizes and zoom**: [how big the prints are](README.md#how-big-the-prints-are).
- **A quieter darkroom.** The developing screen keeps the safelight, the tray and the paper, and draws again
  only when a print is done: the camera's one processor develops instead of animating. INFO dims the screen
  while it works.
- **The camera's white balance.** The darkroom develops each frame with the white balance the camera was on
  when it was shot. Loading a roll sets it to the light the film is made for: 5500 K, or 3200 K for a tungsten
  film. Change it by hand and the print follows. Daylight pictures come out cooler than they used to: the old
  fixed balance was too warm.
- **The 59 films whose colour comes from Film-Luts have more contrast and darker shadows.** Their tables were
  made by eye on finished photos, and the darkroom was giving them a flatter picture than any camera's own
  JPEG: about 88 % of its contrast. They now get the tone of a finished photo (Canon's Standard picture
  style), with the middle tones where they were. The eight films with M-Film's own model have not changed.
- **Four films have left the shelf:** the cinema print films Kodak Vision 2383 and 2393 and Fujifilm Eterna 3510
  and 3513. Their colour tables came with no licence, they were made for a film scan and not for a photo, and a
  print film is never loaded in a camera, so they could not be checked against the real thing. A roll already
  shot on one is listed in the darkroom under its name and is not developed as some other film; its RAWs stay
  on the card. If one of them is loaded when you update, rewind it first.
- **Date stamp** (*Settings → Date stamp*): the day in the corner of each print, in orange, like a compact's data back.
- **The battery** beside the clock on every page and in the viewfinder: in percent on the 60D, 6D, 70D,
  5D Mark II and 5D Mark III, whose battery reports it; as an icon with three levels on the others, where
  Canon knows no more.
- **The films you loaded last** have a shelf of their own, where the film shelf opens: the same film again is one press.
- **Settings** is one page (viewfinder, exposure simulation, print size, date stamp, film mode); the rest is
  under *Manual lens* and *Advanced*. The wind lever no longer locks the shutter: it reminds, or is off.
- **Menus that are simply there.** Going into a menu and back no longer slides; the fade between the shelf,
  the darkroom and the prints is shorter, and *Advanced → Page fade* turns it off.
- **The readout lights when you turn a dial**, not only on a half-press. On cameras with two dials (50D, 60D,
  70D, 5D Mark II, 5D Mark III, 6D) the top one changes shelves on the film shelf and the rear one picks the film.
- **EOS M: *Advanced → Hide Canon's graphics*** keeps Canon's exposure scale and icons off the viewfinder
  (its focus frame goes too, so it is off unless you turn it on).
- **One build.** The film OS now loads as a module after the camera starts on every camera, so Magic Lantern
  takes no more memory at power on than it does alone ([why](ml-dev/MEMORY.md)). On the cameras that had it
  built in until 0.1.6 (EOS M, 6D, 5D Mark III, 60D, 500D, 50D, 5D Mark II) this is new: see [Cameras](README.md#cameras).
