#!/usr/bin/env bash
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
. "$ROOT/config/massagent.env"
export ARR_BACKEND MASSV2_WS PNU BUILDING_TYPE TRACK BOOK_COUNT GROUND_CAPACITY_M2 JUROR_MODEL
export PYTHONUNBUFFERED=1
if command -v cygpath >/dev/null 2>&1; then
  export MASS_BASH="$(cygpath -w "$(command -v bash)")"
fi
$PY "$HERE/cycle.py" "$@"
