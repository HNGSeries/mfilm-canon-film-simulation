#!/usr/bin/env bash
# The film OS for the browser (mfilm.app): site/fos/mfilm.wasm, mkcr2.wasm and
# the card's data files. Needs clang and wasm-ld with a WASI sysroot, and
# Binaryen's wasm-opt (Ubuntu: clang lld wasi-libc libclang-rt-18-dev-wasm32 binaryen).
#   ml-dev/filmos/web/build.sh [out dir]          default: site/fos
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=$(realpath -m "${1:-$HERE/../../../site/fos}")   # relative to where it is run from
cd "$HERE"
mkdir -p "$OUT" out
SYSROOT=${WASI_SYSROOT:-/usr}
CC=${CC:-clang}
VERSION=$(tr -d ' \r\n' < ../../../VERSION)
CFLAGS="--target=wasm32-wasi --sysroot=$SYSROOT -O2 -std=gnu99 -Wall -Wno-unused-parameter -DMFILM_VERSION=\"$VERSION\""

# the fonts and the films, as the camera finds them on its card (sim's Makefile)
make -C ../sim out/FOSFONT.BIN out/FOSFILMS.BIN >/dev/null
cp ../sim/out/FOSFONT.BIN ../sim/out/FOSFILMS.BIN "$OUT/"

SRC="web.c ../sim/port_files.c ../sim/fonts.c ../sim/films.c ../fos_gfx.c ../fos_film.c ../fos_ui.c ../fos_shelf.c \
     ../fos_pages.c ../fos_hud.c ../fos_print.c ../fos_dark.c ../fos_dev.c ../fos_lab.c ../fos_looks.c ../fos_jpeg.c"
$CC $CFLAGS -mexec-model=reactor -Wl,--export=malloc -Wl,--export=free -Wl,-z,stack-size=1048576 \
    -o out/mfilm.raw.wasm $SRC -lm
# fos_port_sleep waits on the page: Asyncify lets web.sleep return later
wasm-opt -O2 --asyncify --pass-arg=asyncify-imports@web.sleep out/mfilm.raw.wasm -o "$OUT/mfilm.wasm"

# the shutter: a CR2 from what LiveView shows
$CC $CFLAGS -o out/mkcr2.raw.wasm ../sim/tools/mkcr2.c -lm
wasm-opt -O2 out/mkcr2.raw.wasm -o "$OUT/mkcr2.wasm"
ls -la "$OUT"
