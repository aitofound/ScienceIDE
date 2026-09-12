#!/usr/bin/env bash
# Re-run the tasks that errored in a warm pass, at low concurrency.
# Usage: `warm_repair.sh --results PATH [--host IP] [--concurrency N] [--dataset PATH] [--dry-run]`

set -euo pipefail

RL_ROOT=${RL_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}

RESULTS=""
HOST=""
CONCURRENCY=4
DATASET="${RL_ROOT}/scienceide_rl/data/mitgcm-biogeo/repair_easy/all/L1.parquet"
DRY_RUN=0

usage() { sed -n '2,3p' "$0"; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --results)      RESULTS="$2"; shift 2 ;;
        --host)         HOST="$2"; shift 2 ;;
        --concurrency)  CONCURRENCY="$2"; shift 2 ;;
        --dataset)      DATASET="$2"; shift 2 ;;
        --dry-run)      DRY_RUN=1; shift ;;
        -h|--help)      usage; exit 0 ;;
        *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    esac
done

[[ -n "${RESULTS}" ]] || { echo "ERROR: --results is required." >&2; usage >&2; exit 2; }
[[ -f "${RESULTS}" ]] || { echo "ERROR: results file not found: ${RESULTS}" >&2; exit 2; }

# Task names are read with python rather than grep/jq: the exception text in these
# records contains newlines and quotes, so line-oriented parsing mangles it.
mapfile -t FAILED < <(python3 -c "
import json, sys
seen = []
for line in open(sys.argv[1]):
    try:
        r = json.loads(line)
    except ValueError:
        continue
    if (r.get('error_class') or 'ok') != 'ok':
        name = r.get('task_name', '')
        if name and name not in seen:
            seen.append(name)
print('\n'.join(seen))
" "${RESULTS}")

if [[ ${#FAILED[@]} -eq 0 ]]; then
    echo "Nothing to repair: every task in ${RESULTS} has error_class=ok."
    exit 0
fi

echo "=== warm_repair ==="
echo "  results     : ${RESULTS}"
echo "  host        : ${HOST:-<local>}"
echo "  concurrency : ${CONCURRENCY}"
echo "  failed tasks: ${#FAILED[@]}"
for t in "${FAILED[@]}"; do echo "    ${t}"; done
echo

OUT_DIR="$(dirname "${RESULTS}")_repair_$(date +%m%d_%H%M%S)"

# Run each task separately so one failure cannot abort the remaining repairs.
run_one() {
    local task="$1" out="$2"
    cd "${RL_ROOT}"
    bash scienceide_rl/eval/run_eval.sh \
        --agent nop \
        --dataset "${DATASET}" \
        --task-glob "${task}" \
        --output-dir "${out}" \
        --skip-gpu-tasks \
        --max-per-instance "${CONCURRENCY}" \
        -n "${CONCURRENCY}"
}

if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "(dry-run) would run, one per task:"
    echo "  bash scienceide_rl/eval/run_eval.sh --agent nop \\"
    echo "      --dataset ${DATASET} --task-glob <task> \\"
    echo "      --output-dir ${OUT_DIR}/<n> --skip-gpu-tasks \\"
    echo "      --max-per-instance ${CONCURRENCY} -n ${CONCURRENCY}"
    exit 0
fi

n_ok=0
n_fail=0
mkdir -p "${OUT_DIR}"
for i in "${!FAILED[@]}"; do
    task="${FAILED[$i]}"
    out="${OUT_DIR}/$(printf '%02d' "$i")"
    echo "--- repairing ${task}"
    if [[ -n "${HOST}" ]]; then
        # Quoted once for ssh, which concatenates its arguments and lets the REMOTE
        # shell re-split them.
        cmd="cd ${RL_ROOT} && bash scienceide_rl/eval/run_eval.sh --agent nop \
--dataset ${DATASET} --task-glob $(printf '%q' "${task}") --output-dir ${out} \
--skip-gpu-tasks --max-per-instance ${CONCURRENCY} -n ${CONCURRENCY}"
        if ssh -o BatchMode=yes -o StrictHostKeyChecking=no "${HOST}" \
               bash -lc "$(printf '%q' "${cmd}")" >"${out}.log" 2>&1; then
            n_ok=$((n_ok + 1))
        else
            n_fail=$((n_fail + 1))
            echo "    FAILED, see ${out}.log"
        fi
    else
        mkdir -p "$(dirname "${out}")"
        if run_one "${task}" "${out}" >"${out}.log" 2>&1; then
            n_ok=$((n_ok + 1))
        else
            n_fail=$((n_fail + 1))
            echo "    FAILED, see ${out}.log"
        fi
    fi
done

echo
echo "=== done ==="
echo "  repaired : ${n_ok}/${#FAILED[@]}"
echo "  failed   : ${n_fail}"
echo "  logs     : ${OUT_DIR}"
[[ "${n_fail}" -eq 0 ]] || exit 1
