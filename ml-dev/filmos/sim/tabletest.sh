#!/usr/bin/env bash
# The films' colour tables: every film on the shelf has one (tools/gentables.py
# fails otherwise), and a frame whose film has none on the card is not
# developed with a table the camera made up, but fails and says so (#124).
# And the Film-Luts LUTs they are baked from are pinned (#102), and so are the tables rendered from spektrafilm.
#   make out/devtest out/mkcr2 out/tables/TABLES.txt && ./tabletest.sh
set -euo pipefail
cd "$(dirname "$0")"
fail=0
ok()  { echo "ok    $1"; }
bad() { echo "FAIL  $1"; fail=1; }

make -s out/tables/TABLES.txt
films=$(grep -c '^LOOK' out/tables/TABLES.txt)
files=$(ls out/tables/LOOK*.LUT | wc -l | tr -d ' ')
[ "$films" = "$files" ] && [ "$films" -gt 8 ] && ok "every film has a table: $films" || bad "$films films listed, $files tables"

t=out/tabletest
rm -rf "$t" && mkdir -p "$t/full" "$t/part"
cp out/tables/LOOK*.LUT "$t/full/"
cp out/tables/LOOK*.LUT "$t/part/" && rm "$t/part/LOOK02.LUT"          # Ektar 100's
./out/mkcr2 "$t/frame.CR2" --small 2>/dev/null

# (devtest is run inside the directory: the darkroom keeps paths short, as on a card)
dev() { (cd "$t" && FOS_LUT_DIR=$1 ../devtest -f "$2" frame.CR2 "$1.fop" 2>&1) || true; }
dev full ektar100 > "$t/full.log"
grep -q "frame.CR2: [0-9]* ms" "$t/full.log" && ok "a film with its table develops" || bad "a film with its table did not develop: $(tail -1 "$t/full.log")"
dev part ektar100 > "$t/part.log"
grep -qF "no colour table for this film on the card" "$t/part.log" && ok "a film with no table: the frame says so" \
    || bad "a film with no table: $(tail -1 "$t/part.log")"
grep -qF "no colour table for ektar100: part/LOOK02.LUT" "$t/part.log" && ok "a film with no table: the log names the file" \
    || bad "a film with no table: the log does not name the file"
[ ! -e "$t/part/LOOK02.LUT" ] && ok "a film with no table: none was made" || bad "a table was made on the card"
# a table made for another look of the film (Portra 400's in Ektar 100's place)
cp "$t/full/LOOK00.LUT" "$t/part/LOOK02.LUT"
dev part ektar100 > "$t/other.log"
grep -qF "no colour table for this film on the card" "$t/other.log" && ok "another film's table in its place is not used" \
    || bad "another film's table was used: $(tail -1 "$t/other.log")"
dev part portra400 > "$t/first.log"
grep -q "frame.CR2: [0-9]* ms" "$t/first.log" && ok "the other films still develop" || bad "the other films: $(tail -1 "$t/first.log")"

# the Film-Luts LUTs are the ones of one commit (#102): a SHA-256 for each the film stocks use, and a LUT
# that is not that file, or is not there, is named. (No fetching here: --check only reads a folder.)
L=../../films
python3 - "$L" <<'PY' && ok "filmluts.sha256 has a line for each LUT the film stocks use, and no other" || bad "filmluts.sha256 and the film stocks' LUTs differ"
import sys
sys.path.insert(0, sys.argv[1])
import filmluts
sys.exit(set(filmluts.sums()) != filmluts.wanted() or len(filmluts.COMMIT) != 40 or filmluts.COMMIT not in filmluts.ZIP)
PY
mkdir -p "$t/luts/bw" && echo "not a LUT" > "$t/luts/bw/agfa_apx_100.cube"
if python3 "$L/getluts.py" --check "$t/luts" > "$t/luts.log" 2>&1; then
    bad "a folder with another file in a LUT's place passed"
elif grep -q "luts/bw/agfa_apx_100.cube: not the file Film-Luts has at" "$t/luts.log" \
        && grep -q "luts/bw/agfa_apx_25.cube: missing" "$t/luts.log"; then
    ok "a file that is not the pinned LUT is named, and so is a LUT that is not there"
else
    bad "the LUT check: $(head -3 "$t/luts.log")"
fi
if [ -d "$L/luts/filmluts" ]; then
    python3 "$L/getluts.py" --check > "$t/have.log" 2>&1 \
        && ok "the LUTs fetched here are the pinned ones: $(tail -1 "$t/have.log" | cut -d" " -f1) of them" \
        || bad "the LUTs in films/luts/filmluts: $(sed -n 2p "$t/have.log")"
    rm -rf "$t/copy" && cp -r "$L/luts/filmluts" "$t/copy"
    echo >> "$t/copy/bw/agfa_apx_100.cube"
    if python3 "$L/getluts.py" --check "$t/copy" > "$t/byte.log" 2>&1; then
        bad "a LUT changed by a byte passed"
    elif [ "$(grep -c "not the file" "$t/byte.log")" = 1 ] && ! grep -q missing "$t/byte.log"; then
        ok "a LUT changed by a byte is named, and no other: $(grep "not the file" "$t/byte.log" | sed "s/^ *//; s/:.*//")"
    else
        bad "a LUT changed by a byte: $(head -3 "$t/byte.log")"
    fi
else
    echo "      (the LUTs are not fetched here: the fetched ones are not checked)"
fi

# the tables rendered from spektrafilm: each film stock spektra.py names gets its own, as it is in films/spektra/,
# and one that is not the file spektra.sha256 names stops the build
python3 - "$L" out/tables <<'PY' && ok "the film stocks from spektrafilm have its tables: $(grep -c '^LOOK.* spektrafilm ' out/tables/TABLES.txt)" \
    || bad "the film stocks from spektrafilm: their tables are not the rendered ones"
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import spektra
listed = {line.split()[1]: line.split()[0] for line in Path(sys.argv[2], "TABLES.txt").read_text().splitlines()
          if line.startswith("LOOK") and line.split()[2] == "spektrafilm"}
sys.exit(spektra.problems() or set(listed) != set(spektra.KEYS)
         or any(Path(sys.argv[2], f).read_bytes()[8:] != spektra.body(k) for k, f in listed.items()))
PY
rm -rf "$t/sf" && cp -r "$L/spektra" "$t/sf"
printf '\001' | dd of="$L/spektra/gold200.tab" bs=1 seek=1000 conv=notrunc 2>/dev/null
if python3 ../tools/gentables.py "$t/sftables" --films out/FOSFILMS.BIN --devtest out/devtest --plain > "$t/sf.log" 2>&1; then
    bad "a rendered table changed by a byte was taken"
elif grep -q "gold200.tab: not the table spektra.sha256 names" "$t/sf.log"; then
    ok "a rendered table changed by a byte stops the build, and is named"
else
    bad "a rendered table changed by a byte: $(tail -2 "$t/sf.log")"
fi
cp "$t/sf/gold200.tab" "$L/spektra/gold200.tab"

[ "$fail" = 0 ] && echo "tabletest: all passed" || { echo "tabletest: failed (logs in sim/$t)"; exit 1; }
