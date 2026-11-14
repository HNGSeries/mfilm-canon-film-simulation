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
# every film's colour table, as a camera's card has them in ML/DARKROOM: the darkroom makes none
# itself and stops with "no colour table" without one (#124), so the page's card needs them too.
# camera.js puts a film's table on the card when a roll of it is loaded. The same bytes as in a
# camera's zip, with the notices that go with them (THIRD_PARTY.md).
# MFILM_PLAIN=1: on a computer that can't fetch the Film-Luts LUTs (films/getluts.py), those films
# get the table of their look. Never for the page that is published.
make -C ../sim out/devtest >/dev/null
[ -n "${MFILM_PLAIN:-}" ] || [ -d ../../films/luts/filmluts ] || python3 ../../films/getluts.py
rm -rf "$OUT/tables"
python3 ../tools/gentables.py "$OUT/tables" --films ../sim/out/FOSFILMS.BIN --devtest ../sim/out/devtest ${MFILM_PLAIN:+--plain}
cp ../../../LICENSE "$OUT/tables/LICENSE.txt"
cp ../../../THIRD_PARTY.md "$OUT/tables/THIRD_PARTY.txt"
# the page's cameras and films, from cameras.txt and FILMS.md as the README's are
python3 sitedata.py "$OUT"

SRC="web.c out/port_files.o ../sim/fonts.c ../sim/films.c ../fos_gfx.c ../fos_film.c ../fos_ui.c ../fos_shelf.c \
     ../fos_pages.c ../fos_hud.c ../fos_print.c ../fos_dark.c ../fos_dev.c ../fos_lab.c ../fos_looks.c ../fos_jpeg.c"
# the simulator's card (stdio) as it is, but its fos_port_model (always the EOS M) out of the way:
# web.c says which camera the page is playing
$CC $CFLAGS -Dfos_port_model=sim_port_model -c -o out/port_files.o ../sim/port_files.c
$CC $CFLAGS -mexec-model=reactor -Wl,--export=malloc -Wl,--export=free -Wl,-z,stack-size=1048576 \
    -o out/mfilm.raw.wasm $SRC -lm
# fos_port_sleep waits on the page: Asyncify lets web.sleep return later
wasm-opt -O2 --asyncify --pass-arg=asyncify-imports@web.sleep out/mfilm.raw.wasm -o "$OUT/mfilm.wasm"

# the shutter: a CR2 from what LiveView shows
$CC $CFLAGS -o out/mkcr2.raw.wasm ../sim/tools/mkcr2.c -lm
wasm-opt -O2 out/mkcr2.raw.wasm -o "$OUT/mkcr2.wasm"
ls -la "$OUT"
