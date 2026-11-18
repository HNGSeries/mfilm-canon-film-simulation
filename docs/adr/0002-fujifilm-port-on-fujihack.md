# The Fujifilm port runs on FujiHack, with only a new port file

M-Film on Fujifilm cameras keeps the film OS's sources as they are and adds one port file, `ml-dev/fuji/fujiport.c`, that gives the film OS its `fos_port_*` functions over [FujiHack](https://github.com/fujihack/fujihack), pinned at one commit (`3f14615`). The first camera is the X-A2 on firmware 1.30: of the bodies FujiHack has notes for, it is the one whose screen is the film OS's own 720 × 480 and whose header names the file, key, screen and timer places the port needs. The XF1 follows, with the canvas squeezed to its 640-wide screen. We decided this in November 2026, when the Fujifilm port was started.

The film OS already reaches the camera only through `fos_port_*` (PORTING.md), so a second camera family is a second implementation of those functions, as the simulator is a third. A fake camera on a PC (`fakefuji.c`) plays FujiHack's firmware functions and memory from a script, so the port is built and run in `make check` long before it runs on a camera.

## Considered Options

- **Magic Lantern-style fork of FujiHack.** Rejected: FujiHack has no menu or module system to hook into the way `ml-dev/fork/` hooks Magic Lantern, and nothing in the film OS needs one.
- **The XF1 first.** It is the one model where running code is confirmed. Rejected for now: its screen is 640 wide, and its screen memory is not the layers FujiHack draws on elsewhere. It stays second.
- **An X-Trans body (X-T10, X-T20).** Rejected: FujiHack has little more than addresses for them, and their RAW would need a developer of its own.

## Consequences

- The screens name Canon's buttons in their hints; a build with `FOS_KEYS_FUJI` names them as a Fujifilm prints them (OK, BACK, FN), in one place, `ui_keycap`.
- Fujifilm builds are not in the camera table (`ml-dev/cameras.txt`) until one runs on a camera.
- FujiHack is GPL-3.0 and M-Film's camera side GPL-2.0, from Magic Lantern. The Fujifilm build contains no Magic Lantern code, only the film OS and FujiHack, but a binary of both can only be given out under GPL-3.0, and only if the film OS's authors allow its sources to be used under it. That decision is needed before the first Fujifilm release.
- FujiHack changes how the camera's firmware starts; Magic Lantern doesn't. Every test build carries a higher risk than on a Canon.
