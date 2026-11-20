# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Owners of Canon DSLRs and the EOS M that run Magic Lantern (DIGIC 4 and 5: the EOS M, 100D, 650D, 700D, 6D,
5D Mark II and III, 60D, 70D, 50D, 500D, 550D, 600D, 1100D, 1300D) who want their digital camera to shoot like
a film camera, whether or not they have installed Magic Lantern before. They read the site in English or
Thai; they install with the camera and its card beside them.

## Product Purpose

M-Film turns the camera into a film camera: load a roll of a film stock from a shelf of 68, shoot it without
seeing the pictures, then develop the roll, in the camera or on a computer with Darkrooms. mfilm.app is
where people try it and get it. A first-time visitor should play with the camera in the browser first (load
a roll, shoot, develop), then download M-Film for their own camera and put it on the card. Success is a
visitor who leaves with M-Film on their card.

## Positioning

The site's camera is the real thing: the film OS on the page is compiled from the same code that runs on the
camera, so the menus, the shelf and the darkroom a visitor plays with are the ones they will get. No preset
pack or filter app can show that.

## Operating Context

- The home page leads with a working EOS M (other bodies selectable) whose screen runs the film OS in
  WebAssembly, with the camera's buttons, dial and keyboard keys.
- The install guide (install.html) is followed step by step with the camera and card at hand; in Chrome,
  Edge and Opera on a computer it can write M-Film onto the card itself.
- Downloads are pay what you want, $0 included, through Stripe; the zips are GitHub releases.
- Darkrooms, the desktop developer, is a separate app (Windows, Mac): free for one roll a day, US$2.99 a month
  or US$14.99 once.

## Capabilities and Constraints

- Static site on GitHub Pages (`site/`), plain HTML, CSS and JavaScript modules, no build step for the page
  itself; the film OS is built to WebAssembly by `ml-dev/filmos/web/build.sh` and checked in CI by
  `pagetest.mjs` and `installtest.mjs`.
- Every string exists in English and Thai (`js/i18n.js` and each page's `addStrings`).
- The film OS screens are shared with the camera; page design and motion must not change them.
- Camera status words come from GLOSSARY.md: Working, Issues, Testing. Film stocks are "in the style of"
  their film unless measured; none is measured yet.

## Brand Commitments

- The M-Film logo (`site/img/mfilm.png`) and the M·FILM wordmark.
- The amber accent, `#eca834`, shared with the README and the camera.
- The playable camera stays at the top of the home page.
- Tagline: "Your Canon, shot like film."

## Evidence on Hand

- The playable camera and its film OS (canister art, shelf, darkroom, prints) in `site/fos/` after a build.
- Camera backs for every body: `site/img/eosm-back.svg`, `site/img/backs/*.webp`.
- One RAW developed with every film (`fos/films/`, from `ml-dev/films/sample/SAMPLE.CR2`).
- Darkrooms screenshots: `docs/images/app-*.jpg`, `fos/app/`.
- The camera table and testers' notes (`ml-dev/cameras.txt`).
- No testimonials, user counts or press: do not invent them.

## Product Principles

- Show the camera working before saying anything about it.
- Say plainly how far each camera has got; never call a camera supported that nobody has tried.
- Free and open on the camera side; paying is a choice, never a gate.
- English and Thai are equals.
