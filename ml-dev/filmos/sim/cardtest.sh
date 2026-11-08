#!/usr/bin/env bash
# The darkroom on a card of problem rolls (mkcard.sh --problems): it develops
# what it can, and says why it can't the rest; Delete roll takes exactly
# what it says, and what it couldn't is still there to delete again; a card
# that can't take long folder names keeps no empty ones (#65); a roll
# developed again keeps its folder. Fails if a line is missing or a file is
# wrong.
#   make && ./cardtest.sh
set -euo pipefail
cd "$(dirname "$0")"
CARD=out/cardp ./mkcard.sh --problems >/dev/null
rm -rf out/frames/problems && mkdir -p out/frames/problems
log=out/cardtest.log
FOS_CARD=out/cardp/ ./out/sim scenes/darkroom_problems.txt out/frames/problems > "$log" 2>&1

fail=0
expect() {
    if grep -qF -- "$2" "$log"; then echo "ok    $1"
    else echo "FAIL  $1: no \"$2\""; fail=1; fi
}
reject() {        # an extended regex
    if grep -qE -- "$2" "$log"; then echo "FAIL  $1: \"$2\""; fail=1
    else echo "ok    $1"; fi
}

# a roll shot as JPEG: each frame says so, and names the JPEG
expect "JPEG roll: frame 1 is a JPEG"       "roll 006 frame 1: shot as JPEG, no RAW: out/cardp/DCIM/100CANON/IMG_0501.JPG"
expect "JPEG roll: frame 4 is a JPEG"       "roll 006 frame 4: shot as JPEG, no RAW: out/cardp/DCIM/100CANON/IMG_0504.JPG"
# Adobe RGB (_MG_): found by Canon's name; the deleted one is named that way too
expect "Adobe RGB: frame 1 found"           "roll 007 frame 1 developed"
expect "Adobe RGB: deleted, by Canon's name" "roll 007 frame 2: no RAW file out/cardp/DCIM/100CANON/_MG_0506.CR2"
expect "Adobe RGB: frame 4 found"           "roll 007 frame 4 developed"
# across IMG_9999 -> IMG_0001: each frame in its own folder's log
expect "9999 wrap: all four RAWs"           "roll 008 (gold200): 4 frames, 4 RAW files"
reject "9999 wrap: nothing missing"         "roll 008 frame [0-9]+: (no RAW|shot as JPEG)"
for f in 1 2 3 4; do expect "9999 wrap: frame $f developed" "roll 008 frame $f developed"; done

# Delete roll, on the card just developed: the files that go are exactly
# the ones listed, and nothing else changes
listing() { (cd "$1" && find . | grep -v '/LOOK[0-9]*\.LUT$' | sort); }
dcard=out/cardp
deletes() {     # deletes <what> <scene> <path that goes>...   (on $dcard)
    local what=$1 scene=$2; shift 2
    listing $dcard > out/del-before.txt
    FOS_CARD=$dcard/ ./out/sim "scenes/$scene.txt" - >> "$log" 2>&1
    listing $dcard > out/del-after.txt
    printf '%s\n' "$@" | sed '/^$/d' | sort > out/del-want.txt
    comm -23 out/del-before.txt out/del-after.txt > out/del-gone.txt
    comm -13 out/del-before.txt out/del-after.txt > out/del-new.txt
    if cmp -s out/del-want.txt out/del-gone.txt && [ ! -s out/del-new.txt ]; then echo "ok    $what"
    else
        echo "FAIL  $what"; fail=1
        diff out/del-want.txt out/del-gone.txt | sed 's/^</  should have gone:/; s/^>/  shouldn'"'"'t have gone:/' | grep '^ ' || true
        sed 's/^/  new: /' out/del-new.txt
    fi
}
# asked, then not confirmed: nothing goes
deletes "Delete roll: not confirmed" delete_cancel ""
# prints only (007, Adobe RGB, frame 2 deleted): its JPEG folder and the darkroom's prints
deletes "Delete roll: prints only" delete_prints \
    "./DCIM/Oct1002 Ektar100" "./DCIM/Oct1002 Ektar100/ROLL007.TXT" "./DCIM/Oct1002 Ektar100/_MG_0505.JPG" \
    "./DCIM/Oct1002 Ektar100/_MG_0507.JPG" "./DCIM/Oct1002 Ektar100/_MG_0508.JPG" \
    ./ML/DARKROOM/R007 ./ML/DARKROOM/R007/F01.BMP ./ML/DARKROOM/R007/F03.BMP ./ML/DARKROOM/R007/F04.BMP \
    ./ML/DARKROOM/R007/SHEET.BMP
expect "Delete roll: prints only, logged"   "lab: roll 007: deleted prints, 0 left"
# the whole roll (008, across IMG_9999) where IMG_9999's RAW and its print
# in DCIM can't be removed: the rest of it goes; its logs and the print
# folder's tag stay, so it is still there to delete again
FOS_KEEP=IMG_9999 deletes "Delete roll: whole roll, files that can't go" delete_whole \
    ./DCIM/100CANON/IMG_9998.CR2 ./DCIM/101CANON/IMG_0001.CR2 ./DCIM/101CANON/IMG_0002.CR2 \
    "./DCIM/Oct1003 Gold200/IMG_0001.JPG" "./DCIM/Oct1003 Gold200/IMG_0002.JPG" "./DCIM/Oct1003 Gold200/IMG_9998.JPG" \
    ./ML/DARKROOM/R008 ./ML/DARKROOM/R008/F01.BMP ./ML/DARKROOM/R008/F02.BMP ./ML/DARKROOM/R008/F03.BMP \
    ./ML/DARKROOM/R008/F04.BMP ./ML/DARKROOM/R008/SHEET.BMP
expect "Delete roll: the RAW that can't go is said" "lab: can't remove out/cardp/DCIM/100CANON/IMG_9999.CR2"
expect "Delete roll: ... and counted"       "lab: roll 008: deleted all, 3 left"
# deleted again: the rest of it, the print folder and its tag, the RAW and
# its logs in both DCIM folders
deletes "Delete roll: whole roll across IMG_9999, again" delete_whole \
    "./DCIM/Oct1003 Gold200" "./DCIM/Oct1003 Gold200/IMG_9999.JPG" "./DCIM/Oct1003 Gold200/ROLL008.TXT" \
    ./DCIM/100CANON/IMG_9999.CR2 ./DCIM/100CANON/ROLL_008.TXT ./DCIM/101CANON/ROLL_008.TXT
# the roll in the camera (006 here): nothing goes
deletes "Delete roll: never the roll in the camera" delete_loaded ""
# the whole roll (007) once its prints are gone: straight to "sure?"; Canon's _MG_ names
deletes "Delete roll: whole roll in Adobe RGB" delete_whole \
    ./DCIM/100CANON/_MG_0505.CR2 ./DCIM/100CANON/_MG_0507.CR2 ./DCIM/100CANON/_MG_0508.CR2 ./DCIM/100CANON/ROLL_007.TXT
# the whole roll shot as JPEG (006): Canon's JPEGs are its frames
deletes "Delete roll: whole roll shot as JPEG" delete_whole \
    ./DCIM/100CANON/IMG_0501.JPG ./DCIM/100CANON/IMG_0502.JPG ./DCIM/100CANON/IMG_0503.JPG \
    ./DCIM/100CANON/IMG_0504.JPG ./DCIM/100CANON/ROLL_006.TXT \
    "./DCIM/Oct1001 Portra400" "./DCIM/Oct1001 Portra400/ROLL006.TXT" ./ML/DARKROOM/R006 ./ML/DARKROOM/R006/SHEET.BMP
n=$(grep -c "lab: can't remove" "$log" || true)
[ "$n" = 2 ] && echo "ok    Delete roll: nothing else it couldn't" || { echo "FAIL  Delete roll: $n \"can't remove\" lines, not 2"; fail=1; }

# A card that makes a long-named folder but can't write into it (a 550D's
# exFAT card, #65): the prints go in SEP0906-style folders, and no empty
# long-named one is left, however often the rolls are developed (6 and 7
# are developed again: they have frames that can't be)
long_dirs() { find "$1/DCIM" -mindepth 1 -maxdepth 1 -type d -name '* *' | wc -l; }
CARD=out/cardl ./mkcard.sh --problems >/dev/null
for i in 1 2; do FOS_CARD=out/cardl/ FOS_LONG_DIRS_EMPTY=1 ./out/sim scenes/darkroom_problems.txt - >> "$log" 2>&1; done
expect "Long names fail: short folder"      "darkroom: JPEGs in out/cardl/DCIM/OCT1003"
n=$(find out/cardl/DCIM/OCT1003 -name '*.JPG' | wc -l)
[ "$n" = 4 ] && echo "ok    Long names fail: 4 JPEGs in OCT1003" || { echo "FAIL  Long names fail: $n JPEGs in OCT1003"; fail=1; }
n=$(long_dirs out/cardl)
[ "$n" = 0 ] && echo "ok    Long names fail: no empty long folders" || { echo "FAIL  Long names fail: $n long folders left"; fail=1; }
# and a camera that can't remove a folder either: one left for each roll, not one more each time
CARD=out/cardl ./mkcard.sh --problems >/dev/null
for i in 1 2; do FOS_CARD=out/cardl/ FOS_LONG_DIRS_EMPTY=1 FOS_NO_RMDIR=1 ./out/sim scenes/darkroom_problems.txt - >> "$log" 2>&1; done
n=$(long_dirs out/cardl)
[ "$n" = 3 ] && echo "ok    Long names fail, no folder removal: 3 left" || { echo "FAIL  Long names fail, no folder removal: $n left, not 3"; fail=1; }
# there, Delete roll still takes every file of the whole roll (008) and its
# logs: only the folders stay, empty
dcard=out/cardl FOS_NO_RMDIR=1 deletes "Delete roll, no folder removal: every file" delete_whole \
    ./DCIM/100CANON/IMG_9998.CR2 ./DCIM/100CANON/IMG_9999.CR2 ./DCIM/100CANON/ROLL_008.TXT \
    ./DCIM/101CANON/IMG_0001.CR2 ./DCIM/101CANON/IMG_0002.CR2 ./DCIM/101CANON/ROLL_008.TXT \
    ./DCIM/OCT1003/IMG_0001.JPG ./DCIM/OCT1003/IMG_0002.JPG ./DCIM/OCT1003/IMG_9998.JPG ./DCIM/OCT1003/IMG_9999.JPG \
    ./DCIM/OCT1003/ROLL008.TXT ./ML/DARKROOM/R008/F01.BMP ./ML/DARKROOM/R008/F02.BMP ./ML/DARKROOM/R008/F03.BMP \
    ./ML/DARKROOM/R008/F04.BMP ./ML/DARKROOM/R008/SHEET.BMP
expect "Delete roll, no folder removal: the folders counted" "lab: roll 008: deleted all, 2 left"

# A roll developed again finds its folder whichever of the day's names it
# has: here "Oct1002 Ektar100 2", the first name free again (another roll
# of that day deleted since). No second folder, no frame developed again.
CARD=out/cardg ./mkcard.sh --problems >/dev/null
FOS_CARD=out/cardg/ ./out/sim scenes/darkroom_problems.txt - >> "$log" 2>&1
mv "out/cardg/DCIM/Oct1002 Ektar100" "out/cardg/DCIM/Oct1002 Ektar100 2"
FOS_CARD=out/cardg/ ./out/sim scenes/darkroom_problems.txt - > out/cardtest-gap.log 2>&1
cat out/cardtest-gap.log >> "$log"
grep -qF "darkroom: JPEGs in out/cardg/DCIM/Oct1002 Ektar100 2" out/cardtest-gap.log && [ ! -e "out/cardg/DCIM/Oct1002 Ektar100" ] \
    && echo "ok    A gap in the day's names: its own folder" || { echo "FAIL  A gap in the day's names: not its own folder"; fail=1; }
grep -qE "roll 007 frame [0-9]+ developed" out/cardtest-gap.log \
    && { echo "FAIL  A gap in the day's names: frames developed again"; fail=1; } || echo "ok    A gap in the day's names: nothing developed again"

[ $fail = 0 ] && echo "cardtest: all passed" || { echo "cardtest: failed (log: sim/$log)"; exit 1; }
