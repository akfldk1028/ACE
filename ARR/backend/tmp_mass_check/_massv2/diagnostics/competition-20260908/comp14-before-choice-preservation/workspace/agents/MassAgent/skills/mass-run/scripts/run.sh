#!/usr/bin/env bash
# mass-run: one massv2 generation round. Thin wrapper - the backend owns
# every metre; paths and parcel facts come from config/massagent.env only.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
. "$ROOT/config/massagent.env" || { echo "FAIL: cannot source config"; exit 1; }

CORPUS="${1:?usage: run.sh <corpus.json> <run-name>}"
RUN="${2:?usage: run.sh <corpus.json> <run-name>}"

. "$ROOT/skills/lib.sh"
CORPUS="$(resolve_corpus "$CORPUS")"
[ -f "$CORPUS" ] || { echo "FAIL: corpus not found: $CORPUS"; exit 1; }

OUT="$MASSV2_WS/runs/$RUN"
ERR="$MASSV2_WS/runs/$RUN.err"
mkdir -p "$OUT"
$PY "$HERE/prepare_corpus.py" "$CORPUS" "$MASSV2_WS/inputs/gen-develop.json" \
  "$OUT/input-corpus.json" || exit 1
CORPUS="$OUT/input-corpus.json"
# A stale summary from an earlier run of the same name must not turn a
# failed run into a false pass - move it aside before we start.
[ -f "$OUT/massv2-summary.json" ] && mv "$OUT/massv2-summary.json" "$OUT/massv2-summary.prev.json"

cd "$ARR_BACKEND" || exit 1
$PY manage.py generate_massv2 \
  --pnu "$PNU" \
  --building-type "$BUILDING_TYPE" \
  --track "$TRACK" \
  --parti-json "$CORPUS" \
  --authored-only \
  --spread-coverage --spread-siting --per-cell 2 \
  --output-dir "$OUT" \
  > "$MASSV2_WS/runs/$RUN.out" 2> "$ERR"
status=$?
# The funnel lines are a courtesy view; success is judged on the artifact,
# never on whether grep matched the backend's current log phrasing.
grep -E "parti sentences|silent:|clipped:|refus|gaps that closed|coverage variants|siting variants|selected|compiled" \
  "$MASSV2_WS/runs/$RUN.out" || true
if [ $status -eq 0 ] && [ -f "$OUT/massv2-summary.json" ]; then
  echo "summary: $OUT/massv2-summary.json"
  [ -f "$OUT/massv2-sheet.png" ] && echo "sheet:   $OUT/massv2-sheet.png"
  exit 0
fi
echo "FAIL: run did not complete (exit $status) - read $ERR"
exit 1
