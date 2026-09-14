#!/usr/bin/env bash
# Reproduce execNEST and reduce unordered stochastic events to ensemble observables.
KNOB_HELP=""
knob() { local name=$1 default=$2 desc=$3; [ -n "${!name:-}" ] || printf -v "$name" '%s' "$default"; export "$name"; KNOB_HELP+="$name=$default  $desc"$'\n'; }
knob SAB_EVENTS 2000 "number of detector-response events; run time scales linearly"
ALTBUILD=""
if [ "${1:-}" = "--help" ]; then printf '%s' "$KNOB_HELP"; exit 0; fi
set -euo pipefail
IC="${1:?usage: run.sh <nominal|variant> | run.sh --help}"
: "${SOURCE_DIR:?}" "${OUT_DIR:?}" "${CHECK_DIR:?}"
[ "$IC" = nominal ] || [ "$IC" = variant ] || { echo "run.sh: unsupported initial condition $IC" >&2; exit 2; }
[ -f "$CHECK_DIR/ic/$IC/config.env" ] || { echo "run.sh: missing ic/$IC/config.env" >&2; exit 2; }
. "$CHECK_DIR/ic/$IC/config.env"
: "${SEED:?}"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
cp -R "$SOURCE_DIR/." "$WORK/src"
BUILD_START=$(date +%s)
cmake -S "$WORK/src" -B "$WORK/build" -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_EXAMPLES=OFF -DBUILD_GARFIELD=OFF -DBUILD_ROOT=OFF -DG4=OFF \
  -DFETCHCONTENT_BASE_DIR=/opt/nest-fetch -DFETCHCONTENT_FULLY_DISCONNECTED=ON >/dev/null
cmake --build "$WORK/build" --target execNEST --parallel 1 >/dev/null
echo "SAB_BUILD_SECONDS=$(( $(date +%s) - BUILD_START ))"
mkdir "$WORK/run"
(cd "$WORK/run" && "$WORK/build/execNEST" "$SAB_EVENTS" ER 10 10 200 0,0,0 "$SEED" > events.txt 2> diagnostics.txt)
tr ',' ' ' < "$WORK/run/events.txt" | awk '
  NF >= 14 && $1 ~ /^-?[0-9]/ { n++; nph += $7; ne += $8; s1c += $10; s2c += $14 }
  END { if (!n) exit 2; printf "%d %.17g %.17g %.17g %.17g\n", n, nph/n, ne/n, s1c/n, s2c/n }
' > "$OUT_DIR/summary.dat" || { echo "run.sh: execNEST produced no parseable event rows" >&2; exit 1; }
