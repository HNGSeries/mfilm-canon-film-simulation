# Easy install: what the spike found

The idea: on mfilm.app the visitor picks their camera, checks the firmware, puts the card in the
computer, lets the page into the card's folder and presses **Install**. The page downloads the camera's
zip, unzips it and writes it onto the card. Downloading and copying by hand stays as the fallback.

This page records the spike (stage 1) that tested the risky parts before any UI work. Verdict: **it
works as planned on Chromium desktop browsers**, as long as the zips are served from mfilm.app itself
and the page cleans up the `._` files macOS leaves behind.

Tested 2026-11-20 on the maintainer's Mac with Microsoft Edge 153 and Google Chrome 157, a throwaway
page served from `127.0.0.1`, the v0.2.3 650D zip, and two card images mounted the way a card is:
`EOS_DIGITAL` (FAT32, as the camera formats a card of 32 GB or less) and `EOS_EXFAT` (exFAT). Each had
`DCIM/100CANON` and no `._` files to start with. No real card was at hand. A card in a reader is a
different device from a disk image, so try it once on a real card in stage 2. The file system is the
same, though, so the `._`, quarantine and Safe Browsing results carry over.

## 1. Picking the card's root

`showDirectoryPicker({ mode: 'readwrite' })` exists only in Chromium desktop browsers (Chrome, Edge,
Opera, Brave). Safari, Firefox, and every browser on iOS get the manual steps. Android is out of scope.

| | Result |
|---|---|
| macOS, Edge 153: `/Volumes/EOS_DIGITAL`, `/Volumes/EOS_EXFAT` | Picked the volume root itself; `readwrite` granted; no "system files" dialog |
| macOS, Chrome 157: the same | The same |
| Windows, `E:\` | **Not tested.** Read from Chromium's source: allowed |

On Windows, Chromium refuses a folder only when it contains a blocked path. Blocked paths include
`C:\Windows`, `Program Files` and AppData, so `C:\` is refused. `GenerateBlockPaths` /
`ShouldBlockAccessToPath` in `chrome/browser/file_system_access/chrome_file_system_access_permission_context.cc`
list no volume or removable-drive root, so `E:\` should be pickable. Confirm it once on a Windows
machine before announcing it.

## 2. Getting the zip into the page

GitHub release downloads can't be fetched from mfilm.app. The spike tried both routes in the browser,
and both failed with `TypeError: Failed to fetch`:

- `github.com/<repo>/releases/download/...` answers with a 302 that has no `Access-Control-Allow-Origin`.
- `api.github.com/repos/<repo>/releases/assets/<id>` with `Accept: application/octet-stream` does send
  `Access-Control-Allow-Origin: *`. But it redirects to `release-assets.githubusercontent.com`, which
  sends no CORS headers at all.

**Choice: publish the camera zips on GitHub Pages, next to the site** (for example `site/dl/`, with a
`SHA256SUMS` beside them). The page then downloads them from its own origin, so no CORS is needed.

- **Size.** v0.2.3 has 16 zips, about 289 MB together. The site itself is about 5 MB. GitHub Pages
  allows a 1 GB site, so this fits. Publish only the latest release's zips, not older ones.
- **Bandwidth.** GitHub's soft limit is 100 GB a month, about 5,000 installs at 18.5 MB each. If it
  ever gets close: the zips are about 90% identical (mostly `ML/SAMPLES`). With files stored by
  content once, all 16 cameras together are about 28 MB compressed, and each camera adds only 1–1.6 MB
  of its own. That is plan B. It needs a manifest and checks each file instead of each zip, so it is
  not worth the complexity now.
- **Same bytes as the release.** Serving the release's own zips means the SHA-256 the page checks is
  the one anyone can check on the release.
- **Wiring.** `pages.yml` gets a step that runs `gh release download` for the newest `v*` release
  (`M-Film-*-camera-*.zip`) into `site/dl/` and writes `SHA256SUMS`. A release made by `camera.yml`
  uses `GITHUB_TOKEN`, so it does **not** trigger `pages.yml` through a `release` event. The release
  job should run `gh workflow run pages.yml` instead (`workflow_dispatch` is the exception GitHub
  allows), which needs `actions: write`.
- **Rejected:** another host (Cloudflare R2 or a CORS proxy). It means another account and secrets, for
  bytes GitHub Pages already serves.

## 3. Writing onto the card (macOS)

The 650D zip is 195 files, 36.3 MB:

| | FAT32 | exFAT |
|---|---|---|
| Edge 153 | 7.3 s, 0 failed | 5.5 s, 0 failed |
| Chrome 157 | 27.3 s, 0 failed | (not run) |

- **Safe Browsing / SmartScreen blocked nothing.** That includes `autoexec.bin`, `ML-SETUP.FIR`,
  `*.mo` and `*.sym`. Chrome runs a check after each file, which is why it is about 4× slower. Stage 2
  should write a few files at a time and show progress.
- **Contents are exact.** `diff -r` against the unzipped zip found every file identical. The one gap
  was the empty folder `ML/doc`, which the spike skipped. Stage 2 must create the zip's empty folders too.
- **No `.crswap` swap files were left behind.**
- **macOS quarantine leaves `._` files: one for every file and folder written, 205 in all.**
  `ls -l@` shows that every file got `com.apple.quarantine` (`0081;…;Edge;…`) and
  `com.apple.metadata:kMDItemWhereFroms`, and every folder got `com.apple.quarantine`. FAT32 and exFAT
  can't hold extended attributes, so macOS writes them into `._autoexec.bin`, `._ML`,
  `ML/modules/._*.mo`, and so on. The guide already warns that these can stop the camera.
- **The page can remove them itself.** It walks the tree after writing and calls `removeEntry()` on
  every `._*` name. That removed 205 of 205 files in Edge and in Chrome, and `xattr` afterwards showed
  nothing. With easy install, Mac users don't need `dot_clean`.
- **Windows is expected to be clean, not tested.** Chromium marks files with Mark-of-the-Web, which is
  a `Zone.Identifier` alternate data stream. FAT32 and exFAT have no alternate data streams, so the
  mark can't land on the card.

## 4. What stage 2 has to do (from the above)

- Show the button only where `showDirectoryPicker` exists. Everyone else gets the existing download
  steps unchanged.
- Fetch `dl/<zip>` from mfilm.app and check its SHA-256 against `dl/SHA256SUMS`. Unzip with fflate
  (pinned, for example `fflate@0.8.2` from jsDelivr).
- Skip `mlinstall-for-your-computer/`. Create empty folders.
- Write a few files at a time and show progress. Then remove every `._*` in the tree.
- Refuse or warn when the picked folder doesn't look like a card root, that is, it has no `DCIM/` and
  isn't empty (for example the user picked `DCIM` itself, or Desktop). Warn when an old `ML/` is there:
  the guide says to format in the camera first, and the web page can't format.
- Keep manual: step 6 (*Firmware ver.* → update), and mlinstall for the 1300D, which writes boot
  sectors that no web page can reach.
- Use English and Thai strings, the way `install.js` does.

## Still open

- `E:\` on Windows with Chrome or Edge: pick, write, and check that no `Zone.Identifier` files appear.
- One run on a real SD card in a reader. Then the camera: run *Firmware ver.* → update from a card the
  page wrote.
