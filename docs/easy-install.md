# Easy install

On mfilm.app's install page, a visitor in Chrome, Edge or Opera on a computer can let the page write
M-Film onto the card: pick the camera, check the firmware, put the card in, choose it, press Install.
The page downloads the camera's zip, checks it, unzips it and copies it onto the card. Every other
browser gets the steps by hand, as before. The code is `site/js/easyinstall.js`; the test is
`ml-dev/filmos/web/installtest.mjs`.

Before any of it was built, a spike checked the parts that could have sunk the idea. It works in
Chromium browsers on a computer, provided the zips come from mfilm.app itself and the page removes the
`._` files macOS leaves on the card.

The spike ran on 2026-11-20 on the maintainer's Mac, in Microsoft Edge 153 and Google Chrome 157, with
the v0.2.3 650D zip. No spare card was at hand, so it used two disk images mounted as cards would be:
`EOS_DIGITAL` (FAT32, as the camera formats a card of 32 GB or less) and `EOS_EXFAT` (exFAT). Each had
`DCIM/100CANON` and no `._` files to start with. A card in a reader is a different device from a disk
image, so the first install onto a real card is still to do. The file system is the same, so what
follows about `._` files, quarantine and Safe Browsing should hold.

## Choosing the card

`showDirectoryPicker({ mode: 'readwrite' })` exists only in Chromium browsers on a computer (Chrome,
Edge, Opera, Brave). Safari, Firefox and every browser on iOS don't have it. Android is out of scope.

On the Mac, both Edge and Chrome let the visitor choose `/Volumes/EOS_DIGITAL` and `/Volumes/EOS_EXFAT`
themselves, gave write access, and showed no "system files" warning.

Windows hasn't been tried. Chromium refuses a folder only when a blocked path is inside it: `C:\` is
refused because `C:\Windows`, Program Files and AppData are in it. `GenerateBlockPaths` and
`ShouldBlockAccessToPath` in `chrome/browser/file_system_access/chrome_file_system_access_permission_context.cc`
list no drive root, so `E:\` should be allowed. Someone should try it once on Windows.

## Where the zip comes from

A page on mfilm.app can't download GitHub's release files. The spike tried two ways in the browser and
both failed with `TypeError: Failed to fetch`. `github.com/<repo>/releases/download/...` answers with a
302 that has no `Access-Control-Allow-Origin` header. `api.github.com/repos/<repo>/releases/assets/<id>`
with `Accept: application/octet-stream` does send `Access-Control-Allow-Origin: *`, but it redirects to
`release-assets.githubusercontent.com`, which sends no CORS headers.

So `pages.yml` copies the newest `v*` release's camera zips into `site/dl/`, and
`ml-dev/filmos/web/dl.py` writes `dl/index.json` beside them with each zip's name, size and SHA-256.
The page downloads from its own site, so CORS doesn't come into it, and the SHA-256 it checks is that of
the zip anyone can download from the release.

v0.2.3 has 16 camera zips, about 289 MB together, and the site is about 5 MB. GitHub Pages allows 1 GB,
and only the newest release is published. Pages' soft limit of 100 GB a month is about 5,000 installs at
18.5 MB each. If that gets close, there is room to shrink: the zips are about 90% the same files (mostly
`ML/SAMPLES`), and stored once each, all 16 cameras come to about 28 MB compressed, 1 to 1.6 MB of it
each camera's own. The page would then fetch files listed in a manifest and check each one, which isn't
worth doing yet.

A release made by `camera.yml` uses `GITHUB_TOKEN`, and GitHub doesn't start other workflows from events
that token causes. The release job therefore runs `gh workflow run pages.yml` itself
(`workflow_dispatch` is allowed), which needs `actions: write`.

Another host, such as Cloudflare R2 or a CORS proxy, would have meant another account and its secrets,
for files GitHub Pages can serve.

## Writing onto the card

The 650D zip is 195 files, 36.3 MB. Edge wrote it in 7.3 s on FAT32 and 5.5 s on exFAT; Chrome took
27.3 s on FAT32 (exFAT wasn't tried in Chrome). No file failed in either browser. Safe Browsing and
SmartScreen let everything through, `autoexec.bin`, `ML-SETUP.FIR`, `*.mo` and `*.sym` included.
Chrome checks each file after it is written, which is why it is about four times slower, so the page
writes four files at a time.

`diff -r` against the unzipped zip found every file identical. The spike missed the empty folder
`ML/doc`; the page creates the zip's empty folders too. No `.crswap` swap files were left behind.

macOS marks everything the browser writes as downloaded. `ls -l@` showed `com.apple.quarantine`
(`0081;…;Edge;…`) and `com.apple.metadata:kMDItemWhereFroms` on every file, and `com.apple.quarantine`
on every folder. FAT32 and exFAT can't hold extended attributes, so macOS writes each one into a `._`
file beside it: `._autoexec.bin`, `._ML`, `ML/modules/._*.mo` and so on, 205 of them. These are the
files the guide's `dot_clean` step is for, since they can stop the camera's installer.

The page can delete them itself. After writing, it walks what it wrote and calls `removeEntry()` on
every `._` name there. In the spike that removed all 205, in Edge and in Chrome, and `xattr` showed
nothing left. Visitors who install from the page don't need `dot_clean`. The page leaves `DCIM` and
anything else it didn't write alone.

On Windows, Chromium's mark is a `Zone.Identifier` alternate data stream. FAT32 and exFAT have no
alternate data streams, so nothing should land on the card. This hasn't been tried.

## What the page does

- It shows the box only where `showDirectoryPicker` exists. Other browsers see the guide as before.
- It downloads `dl/<zip>`, checks its SHA-256 against `dl/index.json`, and unzips it with fflate 0.8.2
  from jsDelivr.
- It skips `mlinstall-for-your-computer/` and creates empty folders.
- It writes four files at a time with a progress bar, then removes the `._` files in what it wrote.
- It refuses a folder with files but no `DCIM/` (the visitor chose a folder on the computer) and the
  `DCIM` folder itself. It warns when `ML/` or `autoexec.bin` is already there: the guide says to
  format in the camera first, and a web page can't format a card.
- Step 6 (*Firmware ver.* → update) stays by hand, and so does mlinstall on the 1300D, which writes
  boot sectors no web page can reach.

## Not tried yet

- `E:\` on Windows in Chrome or Edge: choosing it, writing, and whether any `Zone.Identifier` files
  appear.
- A real SD card in a reader, then the camera: *Firmware ver.* → update from a card the page wrote.
