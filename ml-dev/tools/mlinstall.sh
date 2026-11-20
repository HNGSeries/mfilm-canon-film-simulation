#!/usr/bin/env bash
# mlinstall, for the 1300D's zip. Magic Lantern makes no ML-SETUP.FIR for the 1300D: the camera is set to
# start Magic Lantern from a computer, with mlinstall (petabyt, GPL-2.0), as Magic Lantern's developers say
# (magiclantern_simplified#325). So its owner doesn't have to find it, the 1300D's zip carries it.
#
#   bash ml-dev/tools/mlinstall.sh <folder>
#
# puts in <folder> the four programs of mlinstall's release 1.1.2, each checked against the SHA-256 below
# (a changed download stops the build), its licence, and its source at the same release with the libraries
# it is built from (GPL-2.0 section 3(a): the source goes with the programs).
set -euo pipefail

VERSION=1.1.2
COMMIT=1c78f2639ac8d98b63c296592b6492f6597b84af   # the tag 1.1.2
URL=https://github.com/petabyt/mlinstall/releases/download/$VERSION
SUMS="e356f4176adb77815453c2607a65ae96dc301128cf3ed8e0877144d1e41b3ae1  mlinstall.exe
71d78f452527586a9a3fc556359671fce7fe93ebd7d16531e070583a632796a1  mlinstall-osx-x86_64.tar.gz
3e0ec886a1e986003d323c0082ca0a407d2e89625e826ac91835af037e3f8849  mlinstall-x86_64.AppImage
35e8c2212024b49890aa61430f4482f2fce70d520900a89ebb19c8e3c8a4d4cc  mlinstall-aarch64.AppImage"

out=${1:?usage: mlinstall.sh <folder>}
mkdir -p "$out"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

echo "$SUMS" | while read -r _ f; do
  curl -sSfL --retry 3 -o "$work/$f" "$URL/$f"
done
sha=sha256sum; command -v sha256sum >/dev/null || sha="shasum -a 256"
(cd "$work" && echo "$SUMS" | $sha -c --quiet -) || { echo "mlinstall $VERSION: a download isn't what it was"; exit 1; }

cp "$work/mlinstall.exe" "$out/mlinstall-windows.exe"
tar xzf "$work/mlinstall-osx-x86_64.tar.gz" -C "$out"          # mlinstall.app
cp "$work/mlinstall-x86_64.AppImage" "$out/mlinstall-linux-x86_64.AppImage"
cp "$work/mlinstall-aarch64.AppImage" "$out/mlinstall-linux-arm64.AppImage"
chmod +x "$out"/mlinstall-linux-*.AppImage "$out/mlinstall.app/Contents/MacOS/mlinstall"

# the source, with its submodules (camlib, libwpd, libui-dev), at the tag's commit
git clone -q --recurse-submodules https://github.com/petabyt/mlinstall.git "$work/mlinstall-$VERSION"
git -C "$work/mlinstall-$VERSION" checkout -q "$COMMIT"
git -C "$work/mlinstall-$VERSION" submodule -q update --init --recursive
cp "$work/mlinstall-$VERSION/LICENSE" "$out/LICENSE.txt"
tar czf "$out/mlinstall-$VERSION-source.tar.gz" -C "$work" --exclude=.git "mlinstall-$VERSION"

cat > "$out/README.txt" <<EOF
mlinstall $VERSION, by petabyt, for your computer: it does not go on the card.
https://github.com/petabyt/mlinstall

The 1300D has no ML-SETUP.FIR: Magic Lantern doesn't make one for it. mlinstall sets the camera to start
Magic Lantern from the card instead, over USB. How: M-FILM-README.txt, next to this folder, under "1300D".

  Windows                 mlinstall-windows.exe
  Mac                     mlinstall.app (made for Intel Macs; on Apple silicon macOS runs it with Rosetta).
                          macOS can't check who made it: the first time, System Settings > Privacy &
                          Security > Open Anyway.
  Linux                   mlinstall-linux-x86_64.AppImage, or -arm64 on an ARM computer

mlinstall is free software under the GNU GPL version 2 (LICENSE.txt). Its source, at this release and with
the libraries it is built from, is mlinstall-$VERSION-source.tar.gz. It is passed on here unchanged, as
its author released it; M-Film didn't write it.
EOF
ls -la "$out"
