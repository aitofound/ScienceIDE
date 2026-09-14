#!/usr/bin/env bash
# Run one self-contained DScribe SOAP observable. The copied runner dispatches
# from this check directory's name and reads only this check plus SOURCE_DIR.
KNOB_HELP=""
knob() { local name=$1 default=$2 desc=$3; [ -n "${!name:-}" ] || printf -v "$name" '%s' "$default"; export "$name"; KNOB_HELP+="$name=$default  $desc"$'\n'; }
knob SAB_REPEATS "1" "number of repeated observable evaluations; runtime scales linearly"
if [ "${1:-}" = "--help" ]; then printf '%s' "$KNOB_HELP"; exit 0; fi

set -euo pipefail
IC="${1:?usage: run.sh <nominal|variant> | run.sh --help}"
case "$IC" in nominal|variant) ;; *) echo "run.sh: initial condition must be nominal or variant" >&2; exit 2 ;; esac
: "${SOURCE_DIR:?}" "${OUT_DIR:?}" "${CHECK_DIR:?}"
[ -f "$CHECK_DIR/ic/$IC/input.json" ] || { echo "missing ic/$IC/input.json" >&2; exit 2; }

echo "SAB_BUILD_SECONDS=0"
PYTHONPATH="$SOURCE_DIR" python3 "$CHECK_DIR/runner.py" \
  --input "$CHECK_DIR/ic/$IC/input.json" \
  --out "$OUT_DIR/output.npy" \
  --repeats "$SAB_REPEATS"
