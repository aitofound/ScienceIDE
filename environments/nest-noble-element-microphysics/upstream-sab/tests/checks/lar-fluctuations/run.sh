#!/usr/bin/env bash
KNOB_HELP=""
knob() { local name=$1 default=$2 desc=$3; [ -n "${!name:-}" ] || printf -v "$name" '%s' "$default"; export "$name"; KNOB_HELP+="$name=$default  $desc"$'\n'; }
knob SAB_ENERGY_STEPS 512 "energy-grid resolution across every upstream interaction/field family; run time scales linearly"
knob SAB_EVENTS_PER_POINT 100 "random samples per energy/field point; run time scales linearly"
ALTBUILD=""
if [ "${1:-}" = "--help" ]; then printf '%s' "$KNOB_HELP"; exit 0; fi
set -euo pipefail
IC="${1:?usage: run.sh <nominal|variant> | run.sh --help}"
: "${SOURCE_DIR:?}" "${OUT_DIR:?}" "${CHECK_DIR:?}"
[ "$IC" = nominal ] || [ "$IC" = variant ] || { echo "run.sh: unsupported initial condition $IC" >&2; exit 2; }
[ -f "$CHECK_DIR/ic/$IC/config.env" ] || { echo "run.sh: missing ic/$IC/config.env" >&2; exit 2; }
. "$CHECK_DIR/ic/$IC/config.env"; : "${DENSITY:?}" "${SEED:?}"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT; cp -R "$SOURCE_DIR/." "$WORK/src"
src="$WORK/src/examples/LArNEST/LArNESTFluctuationBenchmarks.cpp"
n=$(grep -c 'int num_energy_steps = 50000;' "$src" || true); [ "$n" -eq 1 ] || { echo "run.sh: upstream energy-step declaration changed" >&2; exit 1; }
sed -i "s/int num_energy_steps = 50000;/int num_energy_steps = $SAB_ENERGY_STEPS;/" "$src"
sed -i "s/uint64_t num_events = 100;/uint64_t num_events = $SAB_EVENTS_PER_POINT;/" "$src"
BUILD_START=$(date +%s)
cmake -S "$WORK/src" -B "$WORK/build" -DCMAKE_BUILD_TYPE=Release -DBUILD_EXAMPLES=ON -DBUILD_GARFIELD=OFF -DBUILD_ROOT=OFF -DG4=OFF -DFETCHCONTENT_BASE_DIR=/opt/nest-fetch -DFETCHCONTENT_FULLY_DISCONNECTED=ON >/dev/null
cmake --build "$WORK/build" --target LArNESTFluctuationBenchmarks --parallel 1 >/dev/null
echo "SAB_BUILD_SECONDS=$(( $(date +%s) - BUILD_START ))"
mkdir "$WORK/run"; (cd "$WORK/run" && "$WORK/build/examples/LArNEST/LArNESTFluctuationBenchmarks" "$DENSITY" "$SEED" "$SAB_EVENTS_PER_POINT")
awk -F, 'NR>1 { n++; a+=$4; b+=$5; c+=$6; d+=$11; e+=$12; f+=$13 } END { if(!n) exit 2; printf "%d %.17g %.17g %.17g %.17g %.17g %.17g\n",n,a/n,b/n,c/n,d/n,e/n,f/n }' "$WORK/run/fluctuation_benchmarks.csv" > "$OUT_DIR/summary.dat" || { echo "run.sh: fluctuation table is empty" >&2; exit 1; }
