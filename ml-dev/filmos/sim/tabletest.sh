#!/usr/bin/env bash
# The films' colour tables: every film on the shelf has one (tools/gentables.py
# fails otherwise), and a frame whose film has none on the card is not
# developed with a table the camera made up, but fails and says so (#124).
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

[ "$fail" = 0 ] && echo "tabletest: all passed" || { echo "tabletest: failed (logs in sim/$t)"; exit 1; }
