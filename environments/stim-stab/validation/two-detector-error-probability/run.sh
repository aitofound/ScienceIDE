#!/usr/bin/env bash
# Check two-detector-error-probability: the TEST half of the check.
#   run.sh nominal | run.sh variant     run one initial condition (see ic/)
#   run.sh altbuild                     the nominal inputs on the alternative build (SIMD_WIDTH=128; see ALTBUILD)
#   run.sh --help                       list the runtime knobs below and the altbuild line
# Environment supplied by the produce driver: SOURCE_DIR (read-only source tree),
# OUT_DIR (empty directory for the graded files), CHECK_DIR (this directory).
# Reads only CHECK_DIR and SOURCE_DIR; no network; never modifies SOURCE_DIR.

KNOB_HELP=""
CHECK_DIR="${CHECK_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)}"
DEF() { python3 -c "import json,sys;print(json.load(open(sys.argv[1]))[sys.argv[2]])" "$CHECK_DIR/ic/nominal/params.json" "$1"; }
knob() { local name=$1 default=$2 desc=$3; [ -n "${!name:-}" ] || printf -v "$name" '%s' "$default"; export "$name"; KNOB_HELP+="$name=$default  $desc"$'\n'; }
# Parallel build jobs default to the CPUs this container may use (cgroup v2 cpu.max), not the host
# count. Ninja's own default is nproc+2 and nproc reports the HOST's cores even under
# `docker run --cpus`, so on a many-core grading host an unbounded build starts ~90 g++ processes
# inside the declared 4 GB and the container is OOM-killed before run.sh prints anything.
cpus_allowed() { local q p; if [ -r /sys/fs/cgroup/cpu.max ] && read -r q p < /sys/fs/cgroup/cpu.max && [ "$q" != max ]; then echo $(( (q + p - 1) / p )); else nproc 2>/dev/null || getconf _NPROCESSORS_ONLN; fi; }
knob SAB_SHOTS "$(DEF shots)" "shots sampled per error probability (default: ic params). The workload axis: the circuit is two qubits, so cost is entirely in the shot batch the frame simulator packs into words"
knob SAB_BUILD_JOBS "$(cpus_allowed)" "parallel jobs for this check's one build of the pinned source (default: the CPUs this container may use). Build time only; it does not touch the graded output"
# Alternative build. -DSIMD_WIDTH=128 is stim's own knob: CMakeLists.txt:25-35
# turns it into -mno-avx2 -msse2, so simd_word.h:28-34 resolves MAX_BITWORD_WIDTH
# to 128 and the build compiles bitword_128_sse instead of the host-native
# bitword_256_avx. Same compiler, same -O3 Release flags, same source, same
# nominal inputs - the alternative machine the codebase's own --seed CAUTION
# names ("a machine that supports AVX instructions and one that only supports
# SSE instructions may produce different simulation results").
ALTBUILD="the same pinned source configured with -DSIMD_WIDTH=128, which CMakeLists.txt:25-35 turns into -mno-avx2 -msse2 so stim compiles the SSE2 bitword_128 word backend instead of the host-native AVX2 bitword_256, with the same compiler, the same -O3 Release flags and ic/nominal unchanged: a build a correct candidate could plausibly be, and the one stim's own --seed CAUTION names. It takes effect only on x86_64, where stim's machine flags apply; off x86_64 run.sh altbuild refuses rather than report a floor that would mean nothing"
if [ "${1:-}" = "--help" ]; then printf '%s' "$KNOB_HELP"; [ -z "$ALTBUILD" ] || echo "altbuild: $ALTBUILD"; exit 0; fi

set -euo pipefail
IC="${1:?usage: run.sh <nominal|variant|altbuild> | run.sh --help}"
: "${SOURCE_DIR:?}" "${OUT_DIR:?}" "${CHECK_DIR:?}"
INPUTS="$IC"; CMAKE_EXTRA=()
if [ "$IC" = altbuild ]; then
  [ -n "$ALTBUILD" ] || { echo "run.sh: this check declares no alternative build" >&2; exit 2; }
  INPUTS=nominal; CMAKE_EXTRA=(-DSIMD_WIDTH=128)
fi
[ -d "$CHECK_DIR/ic/$INPUTS" ] || { echo "run.sh: no initial condition ic/$INPUTS" >&2; exit 2; }
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
cp -R "$SOURCE_DIR/." "$WORK/src"

# Upstream example this check reproduces: code/stim/doc/getting_started.ipynb,
# the X_ERROR two-detector circuit and its 1e6-shot detector rate.
BUILD_START=$(date +%s)
cmake -S "$WORK/src" -B "$WORK/b" -G Ninja -DCMAKE_BUILD_TYPE=Release "${CMAKE_EXTRA[@]}" >"$WORK/cmake.log" 2>&1

# The machine flag this configure resolved, read from the generated ninja file:
# ninja prints targets and not command lines, so the flags never reach cmake.log.
# `|| true`: grep exits 1 when it matches nothing, and under `set -o pipefail`
# that failed the assignment and killed run.sh silently, before it printed
# anything - on every host where stim resolves no machine flags, which is every
# non-x86_64 host. The empty case is legitimate and the guard below handles it.
MFLAG="$(grep -hoE -- '-march=native|-mno-avx2|-mavx2|-mno-sse2|-msse2' "$WORK/b/build.ninja" 2>/dev/null | sort -u | tr '\n' ' ' || true)"
# An altbuild that did not actually change the build would report a floor of 0 for
# every check and mean nothing, so it fails loudly instead. Stim guards its machine
# flags on CMAKE_SYSTEM_PROCESSOR (CMakeLists.txt:25) and every one of them is x86,
# so -DSIMD_WIDTH has no effect off x86_64.
case "$IC:$MFLAG" in
  altbuild:*-mno-avx2*) ;;
  altbuild:*) echo "run.sh: altbuild asked for -DSIMD_WIDTH=128 but this configure resolved machine flags '${MFLAG:-none}', so the alternative build is identical to the nominal one and its floor would be meaningless. Run the altbuild on an x86_64 host (the curator's ruling puts this leaf's official run on x86_64 with AVX2), or declare altbuild as \"none: <reason>\" for this host." >&2; exit 1 ;;
esac
cmake --build "$WORK/b" --target stim -j "$SAB_BUILD_JOBS" >>"$WORK/cmake.log" 2>&1
echo "SAB_BUILD_SECONDS=$(( $(date +%s) - BUILD_START ))"
STIM="$(find "$WORK/b" -type f -perm -111 -name stim | head -1)"
[ -x "$STIM" ] || { cp "$WORK/cmake.log" "$OUT_DIR/cmake-failed.log" 2>/dev/null; echo "run.sh: stim binary not built; see cmake-failed.log" >&2; exit 1; }

# Which vector word backend this build actually compiled, resolved exactly the
# way src/stim/mem/simd_word.h:28-34 resolves it: __AVX2__ -> bitword_256_avx,
# __SSE2__ -> bitword_128_sse, otherwise bitword_64. Stim's machine flags are
# guarded on CMAKE_SYSTEM_PROCESSOR (CMakeLists.txt:25) and its backends are
# x86-only, so the same source yields bitword_256_avx on an AVX2 host,
# bitword_128_sse under the altbuild's SIMD_WIDTH=128, and the portable
# bitword_64 where no flag applies. The incumbent is meaningless without this,
# so it is written beside the graded output rather than inferred.
{ echo "${MFLAG:-no-machine-flag}"
  ${CXX:-c++} ${MFLAG} -dM -E -x c++ /dev/null 2>/dev/null |
    awk '/define __AVX2__/{a=1} /define __SSE2__/{s=1} END{print (a ? "bitword_256_avx" : (s ? "bitword_128_sse" : "bitword_64"))}'
  uname -m; } > "$OUT_DIR/word_backend.txt"

PARAMS="$CHECK_DIR/ic/$INPUTS/params.json" OUT="$OUT_DIR" SCRATCH="$WORK" STIM="$STIM" python3 - <<'PYEOF'
import json, os, subprocess
import numpy as np

p = json.load(open(os.environ["PARAMS"])); out = os.environ["OUT"]
scratch = os.environ["SCRATCH"]; stim = os.environ["STIM"]
shots = int(os.environ.get("SAB_SHOTS") or p["shots"])
probs = [float(x) for x in p["error_probabilities"]]

# The circuit is upstream's, written out verbatim per probability. H then CX
# prepares a Bell pair so the two Z measurements agree in the absence of noise;
# X_ERROR flips each independently; the DETECTOR compares the two.
def circuit_for(prob, path):
    with open(path, "w") as fh:
        fh.write("H 0\nTICK\nCX 0 1\nX_ERROR(%r) 0 1\nTICK\nM 0 1\nDETECTOR rec[-1] rec[-2]\n" % prob)

def readn(fh, n):
    """Read exactly n bytes unless EOF. A pipe may return short reads, and a
    partial shot would misalign every subsequent row of the bit table."""
    buf = bytearray()
    while len(buf) < n:
        b = fh.read(n - len(buf))
        if not b:
            break
        buf += b
    return bytes(buf)

# One detector, so b8 packs each shot into a single byte and the graded width is
# probed exactly rather than assumed: ceil(1/8)*8 would grade seven padding bits
# that are structurally zero in every run.
rates = np.zeros(len(probs), dtype=np.float64)
for i, prob in enumerate(probs):
    circ = os.path.join(scratch, "c%d.stim" % i)
    circuit_for(prob, circ)
    probe = os.path.join(scratch, "probe%d.01" % i)
    subprocess.run([stim, "detect", "--shots", "1", "--in", circ,
                    "--out", probe, "--out_format", "01", "--seed", "1"], check=True)
    with open(probe) as fh:
        n_det = len(fh.readline().strip())
    if n_det != 1:
        raise SystemExit("run.sh: expected 1 detector, probed %d" % n_det)
    width = (n_det + 7) // 8

    # Stream the sample from a pipe; nothing is written to disk.
    # Per-probability seeds are spaced by 1000, not by 1. With seed+i, two
    # initial conditions whose seeds differ by less than the number of
    # probabilities would share sampling streams - nominal at seed s would use
    # s, s+1, s+2 and a variant at s+1 would reuse s+1 and s+2 - so most of the
    # graded array would be identical between them and the variant would supply
    # almost no calibration evidence.
    proc = subprocess.Popen(
        [stim, "detect", "--shots", str(shots), "--in", circ,
         "--out_format", "b8", "--seed", str(int(p["seed"]) + 1000 * i)], stdout=subprocess.PIPE)
    fired = 0; nsh = 0
    while True:
        raw = readn(proc.stdout, 10000 * width)
        rows = len(raw) // width
        if rows == 0:
            break
        bits = np.unpackbits(np.frombuffer(raw[: rows * width], dtype=np.uint8).reshape(rows, width),
                             axis=1, bitorder="little")[:, :n_det]
        fired += int(bits.sum()); nsh += rows
    proc.stdout.close()
    if proc.wait() != 0:
        raise SystemExit("run.sh: stim detect exited nonzero at p=%r" % prob)
    if nsh != shots:
        raise SystemExit("run.sh: read %d shots, expected %d" % (nsh, shots))
    rates[i] = fired / float(nsh)

# Graded: the detector firing rate at each error probability. The mean, max and
# min of this array are the three invariants; with one detector per circuit
# there is no spread across detectors to grade, and the per-shot dispersion of a
# single Bernoulli bit is a function of the rate itself, so grading it would
# duplicate an already-graded quantity.
np.save(os.path.join(out, "detector_rates.npy"), rates)
print("shots=%d probabilities=%s" % (shots, probs))
PYEOF
