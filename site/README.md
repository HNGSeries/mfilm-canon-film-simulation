# mfilm.app

The website, with the camera in it: M-Film's film OS compiled to WebAssembly
(`ml-dev/filmos/web/`), running on a drawing of an EOS M. The menus, the HUD,
the darkroom and the prints are the camera's own code; the shutter writes a
CR2 from what LiveView shows (`sim/tools/mkcr2.c`), and the darkroom develops it.

Published by `.github/workflows/pages.yml` on a push to `main`
(Settings → Pages → Source: **GitHub Actions**) at
https://hngseries.github.io/mfilm-canon-film-simulation/. A domain of its own
goes in Settings → Pages → Custom domain (with Actions, a CNAME file is not
read), and in the licence server's `DONATE_PAGES` so Stripe may send people back to it.

## Run it here

```bash
ml-dev/filmos/web/build.sh
```

```bash
python3 -m http.server -d site 8000
```

then open http://localhost:8000. Building needs clang, lld, `wasi-libc`,
`libclang-rt-18-dev-wasm32` and `binaryen` (Ubuntu packages).

## What to replace

- **The cameras**: every camera M-Film runs on is in `js/bodies.js`: its body
  (the EOS M is `img/eosm-back.svg`; the DSLRs are drawn from their family's
  shape: Rebel, 60D/70D/6D, 5D/50D), its screen, and each control where it
  sits. Give a body an `image` (a photo of its back) and it replaces the
  drawing; the controls stay where its numbers put them. `web_config` tells
  the film OS which camera it is: its name, a DSLR (top plate until the LV
  button), a swivel screen, exposure simulation.
- **The EOS M's body**: `img/eosm-back.svg` is a drawing. A photo of the back
  (1100 × 740, or the same proportions, the screen's glass at x 60–740,
  y 140–593) can take its place in `index.html`. The buttons sit over it in
  `css/site.css` (`.ctl.info`, `.dial`, …), each at its centre in % of the
  body: x / 1100, y / 740.
- **LiveView**: `media/liveview.mp4`, a short loop, plays under the screen if
  it is there. Without it, the stills in `img/samples/` drift by instead.
- **Developing pace**: the browser develops far faster than the camera; the
  film OS is held to about a second a frame (`web_dev_pace` in `web.c`).

## Files

- `js/camera.js` runs `fos/mfilm.wasm`: its screen onto a canvas, the keys
  into it, the shutter. `fos_port_sleep` waits on the page through Binaryen's
  Asyncify, so the film OS's own loop runs as on the camera.
- `js/wasi.js` is the memory card: an in-memory file system behind the WASI
  calls of `mfilm.wasm` and `mkcr2.wasm`. Everything shot is lost on reload.
- `js/liveview.js` is what the sensor sees, and the photo each frame is made from.
- `js/download.js` is the download: camera, pay what you want (US$0–99). Over $0 it asks the Darkrooms
  licence server (`/v1/donate`) for a Stripe Checkout page of that amount; Stripe comes back with `?thanks=1`.
  Its camera list follows `ml-dev/cameras.txt`.
- `install.html` / `js/install.js`: installing, step by step, for the camera picked there.
- `js/main.js` wires the buttons, the dial, the keyboard and the guide; `js/i18n.js` has the English and Thai.
