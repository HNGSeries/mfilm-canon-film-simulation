# Testing M-Film on your camera

M-Film was made on the **Canon EOS M**. The same code **builds** for 14 more cameras (100D, 650D,
700D, 6D, 70D, 5D Mark III on two firmwares, 550D, 600D, 60D, 1100D, 500D, 50D, 5D Mark II), and
testers have tried most of them: the [camera table](README.md#cameras) says how far each one got and
what's still wrong. If yours needs a first tester, or has a known problem you can check, you can help:
it takes about 20 minutes, and you can always go back.

> **Is it safe?** Magic Lantern runs from the card and changes nothing permanent in the camera.
> The worst that usually happens is that the camera doesn't start with the card in: take the
> battery and the card out, and it starts normally again. Still, this is untested software on your
> camera, at your own risk. Keep a fully charged battery and don't try it in the middle of a shoot.

## 1. Get the files

From the [latest release](../../releases/latest) (or the newest run under *Actions*), download
`M-Film-camera-<your camera>.zip`:

<!-- cameras:start -->
| Camera | Canon firmware it needs | File |
|---|---|---|
| Canon EOS M | 2.0.2 | `M-Film-camera-EOSM.202.zip` · `M-Film-camera-EOSM.202-module.zip` |
| Canon EOS 100D / Rebel SL1 / Kiss X7 | 1.0.1 | `M-Film-camera-100D.101.zip` |
| Canon EOS 650D / Rebel T4i / Kiss X6i | 1.0.4 | `M-Film-camera-650D.104.zip` |
| Canon EOS 700D / Rebel T5i / Kiss X7i | 1.1.5 | `M-Film-camera-700D.115.zip` |
| Canon EOS 6D | 1.1.6 | `M-Film-camera-6D.116.zip` · `M-Film-camera-6D.116-module.zip` |
| Canon EOS 70D | 1.1.2 | `M-Film-camera-70D.112.zip` |
| Canon EOS 5D Mark III (firmware 1.1.3) | 1.1.3 | `M-Film-camera-5D3.113.zip` · `M-Film-camera-5D3.113-module.zip` |
| Canon EOS 5D Mark III (firmware 1.2.3) | 1.2.3 | `M-Film-camera-5D3.123.zip` · `M-Film-camera-5D3.123-module.zip` |
| Canon EOS 550D / Rebel T2i / Kiss X4 | 1.0.9 | `M-Film-camera-550D.109.zip` |
| Canon EOS 600D / Rebel T3i / Kiss X5 | 1.0.2 | `M-Film-camera-600D.102.zip` |
| Canon EOS 60D | 1.1.1 | `M-Film-camera-60D.111.zip` · `M-Film-camera-60D.111-module.zip` |
| Canon EOS 1100D / Rebel T3 / Kiss X50 | 1.0.5 | `M-Film-camera-1100D.105.zip` |
| Canon EOS 500D / Rebel T1i / Kiss X3 | 1.1.1 | `M-Film-camera-500D.111.zip` · `M-Film-camera-500D.111-module.zip` |
| Canon EOS 50D | 1.0.9 | `M-Film-camera-50D.109.zip` · `M-Film-camera-50D.109-module.zip` |
| Canon EOS 5D Mark II | 2.1.2 | `M-Film-camera-5D2.212.zip` · `M-Film-camera-5D2.212-module.zip` |
<!-- cameras:end -->

The firmware must match exactly (MENU → last settings tab → *Firmware ver.*).

**Two files for most cameras (since 0.1.4).** `M-Film-camera-<camera>.zip` has the film OS built into
Magic Lantern, as before. `M-Film-camera-<camera>-module.zip` has it as a module that loads after the
camera has started, which takes about 180 KB less of the memory a camera can spare at power on
([MEMORY.md](ml-dev/MEMORY.md)). Please test it too, especially if the first one hangs at power on
(5D Mark II). Where the table has one zip, it is the module one: on the 100D, 70D, 550D, 600D and 1100D
the film OS only fits this way, and on the 650D and 700D it is the way it starts with the in-camera
darkroom (in 0.1.5 that is their `-module.zip`: the plain one there has no darkroom). If the film shelf
doesn't appear and you see Magic Lantern's own menu instead, the module didn't load: its line in the
*Modules* tab says why. Tell us what it says.

## 2. Install

1. Format a card **in the camera**, then copy everything from the zip to the card's root.
2. Camera off, card in, camera on. MENU → *Firmware ver.* → update (first time only: this lets the
   camera start Magic Lantern from the card).
3. Switch the camera off and on.
4. In Canon's menu set **Image quality** to **RAW** (RAW+JPEG works too) and **Image review** to
   **Off**. The in-camera darkroom develops the RAWs: frames shot as JPEG can't be developed.

## 3. What to try, and what to tell us

Go through these and note what happens (a photo of the screen helps a lot):

- [ ] The camera starts, and the **film shelf** appears (on a DSLR, from the normal shooting screen
      with LiveView off; give it up to 15 seconds).
- [ ] **Colours** look right (shelf canisters: Portra yellow, Ektar red; System → Screen colour has a chart).
- [ ] **Buttons**: the dial and arrows move along the shelf, SET loads a film, MENU goes back,
      half-shutter returns to the camera. Which buttons do nothing?
- [ ] **Trash** opens Home; **PLAY** opens the prints instead of Canon's playback.
- [ ] Load a roll and shoot a few frames **through the viewfinder**, and a few in **LiveView**.
      Does the frame count go up? Is the HUD drawn in LiveView?
- [ ] Rewind the roll and **develop it in the camera** (Darkroom). Do prints come out? How long per frame?
- [ ] Open the card in **Darkrooms** on a computer: are the rolls and films there?

Then [open an issue](../../issues/new/choose) with: your camera and firmware, what worked, what didn't,
and the file **`ML/FILMROLL.LOG`** from the card attached.

### If *Firmware ver.* says "Memory card containing firmware is required to update"

The camera found no update file it accepts on the card:
- The Canon firmware isn't exactly the one in the table: `ML-SETUP.FIR` only works on that version.
- `ML-SETUP.FIR` isn't at the top of the card. Unzipping on a Mac often makes a folder
  (`M-Film-camera-EOSM.202/`). The card's top level should show `autoexec.bin`, `ML-SETUP.FIR` and `ML`.
- On a Mac, hidden `._` files next to them can trip the camera. With the card in the reader, run
  `dot_clean -m /Volumes/EOS_DIGITAL` in *Terminal* (your card's name in place of `EOS_DIGITAL`),
  then eject the card before taking it out.

### If the camera says "ML directory not found"

Magic Lantern's installer (`ML-SETUP.FIR`, run by *Firmware ver.* → update) prints this, with
"Please copy all ML files.": it found `autoexec.bin` at the top of the card, but no `ML` folder next to
it ([#42](../../issues/42)). On a computer, the card's top level should look like this, with no folder
around it:

```
autoexec.bin
ML-SETUP.FIR
ML/
```

- Unzipping often makes a folder (`M-Film-camera-6D.116/`; Windows' *Extract All* does too). Copy what
  is inside it, the `ML` folder included, not the folder itself.
- Format the card **in the camera** first, not on the computer, then copy the files onto it.
- A card bigger than 32 GB is formatted as exFAT. If a big card keeps saying this, a card of 32 GB or
  less is a good second try.

### If you turned on Magic Lantern's console

The MENU button opens M-Film, so Magic Lantern's menu (where the console is switched off) can't be
reached while M-Film runs. On a computer, open `ML/SETTINGS/magic.cfg` on the card and change
`module.console = 1` to `module.console = 0`.

### If it doesn't start

Battery out, card out. Then please tell us, because it most likely means the program is too big for
that camera's memory (on the EOS M the limit is about 727 KB at boot; the built-in builds take 700–750 KB,
the module ones 490–575 KB, and most cameras' limits aren't known yet). Say
which camera and firmware, and whether the card light stayed on.

## 4. Remove it

Format the card in the camera. To stop the camera looking for Magic Lantern at all, run
`ML-SETUP.FIR` again from *Firmware ver.* and choose to remove the boot flag.

Thank you! Every camera someone tries moves it from *testing* to *working* in the
[list on the front page](README.md#cameras).
