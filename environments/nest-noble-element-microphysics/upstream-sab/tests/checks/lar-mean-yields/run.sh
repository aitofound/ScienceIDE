#!/usr/bin/env bash
KNOB_HELP=""
knob() { local name=$1 default=$2 desc=$3; [ -n "${!name:-}" ] || printf -v "$name" '%s' "$default"; export "$name"; KNOB_HELP+="$name=$default  $desc"$'\n'; }
knob SAB_ENERGY_STEPS 512 "energy-grid resolution across every upstream interaction/field family; run time scales linearly"
ALTBUILD="GNU C++ Debug build at -O0 instead of the nominal Release optimization"
if [ "${1:-}" = "--help" ]; then printf '%s' "$KNOB_HELP"; echo "altbuild: $ALTBUILD"; exit 0; fi
set -euo pipefail
IC="${1:?usage: run.sh <nominal|variant> | run.sh --help}"
: "${SOURCE_DIR:?}" "${OUT_DIR:?}" "${CHECK_DIR:?}"
INPUTS="$IC"; BUILD_TYPE=Release
if [ "$IC" = altbuild ]; then INPUTS=nominal; BUILD_TYPE=Debug; fi
[ "$IC" = nominal ] || [ "$IC" = variant ] || [ "$IC" = altbuild ] || { echo "run.sh: unsupported initial condition $IC" >&2; exit 2; }
[ -f "$CHECK_DIR/ic/$INPUTS/config.env" ] || { echo "run.sh: missing ic/$INPUTS/config.env" >&2; exit 2; }
. "$CHECK_DIR/ic/$INPUTS/config.env"; : "${DENSITY:?}" "${SEED:?}"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT; cp -R "$SOURCE_DIR/." "$WORK/src"
src="$WORK/src/examples/LArNEST/LArNESTMeanYieldsBenchmarks.cpp"
n=$(grep -c 'int num_energy_steps = 50000;' "$src" || true); [ "$n" -eq 1 ] || { echo "run.sh: upstream energy-step declaration changed" >&2; exit 1; }
sed -i "s/int num_energy_steps = 50000;/int num_energy_steps = $SAB_ENERGY_STEPS;/" "$src"
BUILD_START=$(date +%s)
cmake -S "$WORK/src" -B "$WORK/build" -DCMAKE_BUILD_TYPE="$BUILD_TYPE" -DBUILD_EXAMPLES=ON -DBUILD_GARFIELD=OFF -DBUILD_ROOT=OFF -DG4=OFF -DFETCHCONTENT_BASE_DIR=/opt/nest-fetch -DFETCHCONTENT_FULLY_DISCONNECTED=ON >/dev/null
cmake --build "$WORK/build" --target LArNESTMeanYieldsBenchmarks --parallel 1 >/dev/null
echo "SAB_BUILD_SECONDS=$(( $(date +%s) - BUILD_START ))"
mkdir "$WORK/run"; (cd "$WORK/run" && "$WORK/build/examples/LArNEST/LArNESTMeanYieldsBenchmarks" "$DENSITY" "$SEED")
awk -F, 'NR>1 { t=($1=="NR"?0:($1=="ER"?1:2)); print t,$2,$3,$4,$5,$6,$7,$8,$9,$10 }' "$WORK/run/mean_yields_benchmarks.csv" \
  | sort -k1,1n -k2,2n -k3,3n \
  | awk '{ if (NR == 1 || $1 != kind) rank = 0; else rank++; kind=$1; printf "%d %d", kind, rank; for (i=4; i<=NF; i++) printf " %s", $i; print "" }' \
  > "$OUT_DIR/yields.dat"
[ -s "$OUT_DIR/yields.dat" ] || { echo "run.sh: mean-yield table is empty" >&2; exit 1; }
