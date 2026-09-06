#!/usr/bin/env bash
# mass-cycle: one complete massing cycle, in order, stopping at the first
# failure. Calling the step skills by hand is how steps go missing - three
# rounds shipped without the BOOK exploration, without the development
# verdict applied and without the brief regenerated, because a person was
# typing the commands.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
. "$ROOT/config/massagent.env" || { echo "FAIL: cannot source config"; exit 1; }

ROUND="${1:?usage: cycle.sh <round-name> [sentence-count] [--from N]}"
COUNT="${2:-18}"
# Resume. A cycle that dies at step 7 has already spent an authoring round, a
# pipeline run and a BOOK exploration; re-running from the top re-stages, and
# staging deletes the juror files the jury just wrote. `--from 8` picks up
# where it stopped.
FROM=1
for arg in "$@"; do
  case "$arg" in
    --from=*) FROM="${arg#--from=}" ;;
  esac
done
BOOK_RUN="book-$ROUND"
STEP=0

say() { STEP=$((STEP + 1)); echo; echo "=== $STEP. $* ==="; }
skip() { [ "$STEP" -lt "$FROM" ] && { echo "   (skipped, resuming from $FROM)"; return 0; } || return 1; }
die() { echo "FAIL at step $STEP: $*"; exit 1; }

say "brief - the author writes knowing what the last jury said"
bash "$ROOT/skills/mass-author/scripts/brief.sh" || die "brief"

say "author - $COUNT sentences into inputs/gen-$ROUND.json"
if [ -f "$MASSV2_WS/inputs/gen-$ROUND.json" ]; then
  echo "inputs/gen-$ROUND.json exists - riding the book that is already there"
else
  node "$ROOT/dist/index.js" --dir "$ROOT" --prompt \
"Author one massing round. Read $MASSV2_WS/brief.md end to end, then \
$MASSV2_WS/inputs/VOCABULARY.md. Write $COUNT English parti sentences into \
$MASSV2_WS/inputs/gen-$ROUND.json (format: read inputs/gen-agent07.json). \
Every sentence: one dominant move carried by quiet support, a named site \
pressure as the why's input, storeys declared, a designed top, and a \
formal_principle a juror could remember. No two sentences may share opener, \
dominant move family and stature - the validator refuses a book that says the \
same thing twice. Spread across the six part-to-whole positions: single body, \
stacked tiers, body and parts, paired bodies, field of parts, lifted body. \
Then run: bash skills/mass-validate/scripts/validate.sh $ROUND and fix every \
fault until zero. Print the sentence list and stop - do not run the pipeline." \
    || die "author"
fi

say "validate - unknown words, out-of-range parameters, duplicate ideas"
# The validator takes the corpus, not the round: `validate.sh agent08` looks
# for inputs/agent08 and dies. The authoring step above calls it correctly,
# which is why the cycle got this far before failing.
bash "$ROOT/skills/mass-validate/scripts/validate.sh" "gen-$ROUND.json" || die "validate"

say "run - execute, vary, grow, fit, gate, select"
bash "$ROOT/skills/mass-run/scripts/run.sh" "gen-$ROUND.json" "$ROUND" || die "run"

say "BOOK - the catalogue graph explores, and its masses come to this parcel"
BOOK_DIR="$ARR_BACKEND/tmp_mass_check/c260-book"
rm -rf "$BOOK_DIR/$BOOK_RUN"
(cd "$ARR_BACKEND" && $PY manage.py generate_maas_creative_100 \
   --count "${BOOK_COUNT:-120}" --pnu "$PNU" --capacity-ceiling-m2 "${GROUND_CAPACITY_M2:-1497.877}" \
   --output-root tmp_mass_check/c260-book --run-id "$BOOK_RUN" \
   --author-mode recipe_fixture > "$MASSV2_WS/runs/$BOOK_RUN.out" 2>&1) \
  || die "BOOK exploration - read runs/$BOOK_RUN.out"
(cd "$MASSV2_WS" && $PY tools/book_import.py "$BOOK_DIR/$BOOK_RUN" "$BOOK_RUN" \
   > "runs/$BOOK_RUN-import.out" 2>&1) || die "BOOK import - read runs/$BOOK_RUN-import.out"
tail -1 "$MASSV2_WS/runs/$BOOK_RUN-import.out"

say "stage - anonymous tiles for both rounds"
bash "$ROOT/skills/mass-judge/scripts/stage.sh" "$ROUND" 14 || die "stage $ROUND"

say "jury - three blind jurors per round"
bash "$ROOT/skills/mass-judge/scripts/judge.sh" "$ROUND" || die "jury $ROUND"
bash "$ROOT/skills/mass-judge/scripts/judge.sh" "$BOOK_RUN" || die "jury $BOOK_RUN"

say "score - anchors correct session drift"
bash "$ROOT/skills/mass-judge/scripts/score.sh" "$ROUND" || die "score $ROUND"
bash "$ROOT/skills/mass-judge/scripts/score.sh" "$BOOK_RUN" || die "score $BOOK_RUN"

say "curate - one seat per family, one reserved per part-to-whole position"
bash "$ROOT/skills/mass-curate/scripts/curate.sh" || die "curate"

say "bake - the board is redrawn from the seats"
bash "$ROOT/skills/mass-board/scripts/bake.sh" || die "bake"

say "sheet - three schemes with their arguments"
(cd "$MASSV2_WS" && $PY tools/study_sheet.py "$ROUND" "study-$ROUND" \
   > "runs/study-$ROUND.out" 2>&1) || die "study sheet - read runs/study-$ROUND.out"
tail -1 "$MASSV2_WS/runs/study-$ROUND.out"

say "develop - the top seat is grown, not replaced"
TOP="$($PY -c "import json,sys; k=json.load(open(sys.argv[1],encoding='utf-8')); \
print(next((r['name'] for r in k if str(r['label']).startswith('O')), ''))" \
  "$MASSV2_WS/runs/board/board-key.json" 2>/dev/null)"
if [ -n "$TOP" ] && [ "${TOP#book:}" = "$TOP" ]; then
  (cd "$MASSV2_WS" && $PY tools/develop.py "$ROUND" "$TOP" 16 \
     > "runs/develop-$ROUND.out" 2>&1) || die "develop - read runs/develop-$ROUND.out"
  tail -2 "$MASSV2_WS/runs/develop-$ROUND.out"
  echo "next: judge the pairs in runs/develop-*/pairs, then tools/develop.py --score"
else
  echo "top seat is a BOOK mass ($TOP) - development mutates authored sentences only"
fi

echo
echo "=== cycle complete ==="
echo "board:  $MASSV2_WS/runs/board/board.html"
echo "sheet:  $MASSV2_WS/runs/study-$ROUND/study.html"
echo "publish the sheet yourself; a cycle that republishes would overwrite a"
echo "sheet somebody is reading."
