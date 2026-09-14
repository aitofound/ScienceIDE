#!/usr/bin/env bash
# Parameterize the seed in upstream bareNEST and run an ensemble of its event path.
KNOB_HELP=""
knob() { local name=$1 default=$2 desc=$3; [ -n "${!name:-}" ] || printf -v "$name" '%s' "$default"; export "$name"; KNOB_HELP+="$name=$default  $desc"$'\n'; }
knob SAB_SAMPLES 128 "number of independent bareNEST events; run time scales linearly"
ALTBUILD=""
if [ "${1:-}" = "--help" ]; then printf '%s' "$KNOB_HELP"; exit 0; fi
set -euo pipefail
IC="${1:?usage: run.sh <nominal|variant> | run.sh --help}"
: "${SOURCE_DIR:?}" "${OUT_DIR:?}" "${CHECK_DIR:?}"
[ "$IC" = nominal ] || [ "$IC" = variant ] || { echo "run.sh: unsupported initial condition $IC" >&2; exit 2; }
[ -f "$CHECK_DIR/ic/$IC/config.env" ] || { echo "run.sh: missing ic/$IC/config.env" >&2; exit 2; }
. "$CHECK_DIR/ic/$IC/config.env"
: "${SEED_START:?}"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
cp -R "$SOURCE_DIR/." "$WORK/src"
seed_line_count=$(grep -c 'RandomGen::rndm()->SetSeed(0);' "$WORK/src/examples/bareNEST.cpp" || true)
[ "$seed_line_count" -eq 1 ] || { echo "run.sh: expected exactly one upstream bareNEST seed line" >&2; exit 1; }
sed -i 's/RandomGen::rndm()->SetSeed(0);/RandomGen::rndm()->SetSeed(static_cast<unsigned long>(std::strtoul(argv[1], nullptr, 10)));/' "$WORK/src/examples/bareNEST.cpp"
sed -i '/#include <algorithm>/a #include <cstdlib>' "$WORK/src/examples/bareNEST.cpp"
BUILD_START=$(date +%s)
cmake -S "$WORK/src" -B "$WORK/build" -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_EXAMPLES=ON -DBUILD_GARFIELD=OFF -DBUILD_ROOT=OFF -DG4=OFF \
  -DFETCHCONTENT_BASE_DIR=/opt/nest-fetch -DFETCHCONTENT_FULLY_DISCONNECTED=ON >/dev/null
cmake --build "$WORK/build" --target bareNEST --parallel 1 >/dev/null
echo "SAB_BUILD_SECONDS=$(( $(date +%s) - BUILD_START ))"
: > "$WORK/events.txt"
for ((i=0; i<SAB_SAMPLES; i++)); do
  "$WORK/build/examples/bareNEST" "$((SEED_START + i))" >> "$WORK/events.txt" 2>/dev/null
done
tr ',' ' ' < "$WORK/events.txt" | awk '
  NF >= 14 && $1 ~ /^-?[0-9]/ { n++; nph += $7; ne += $8; s1c += $10; s2c += $14 }
  END { if (!n) exit 2; printf "%d %.17g %.17g %.17g %.17g\n", n, nph/n, ne/n, s1c/n, s2c/n }
' > "$OUT_DIR/summary.dat" || { echo "run.sh: bareNEST produced no parseable event rows" >&2; exit 1; }
