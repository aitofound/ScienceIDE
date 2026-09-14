#!/usr/bin/env bash
# Probe each host's task image cache, and optionally warm the cold ones.
# Usage: `warm_status.sh (--hosts FILE | --hosts-list IP,IP) [--warm] [--threshold N] [--dataset PATH]`

set -euo pipefail

RL_ROOT=${RL_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}

HOSTS_FILE=""
HOSTS_LIST=""
DO_WARM=0
THRESHOLD=40
DATASET="${RL_ROOT}/scienceide_rl/data/mitgcm-biogeo/repair_easy/all/L1.parquet"
CONCURRENCY=8

usage() { sed -n '2,3p' "$0"; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --hosts)        HOSTS_FILE="$2"; shift 2 ;;
        --hosts-list)   HOSTS_LIST="$2"; shift 2 ;;
        --warm)         DO_WARM=1; shift ;;
        --threshold)    THRESHOLD="$2"; shift 2 ;;
        --dataset)      DATASET="$2"; shift 2 ;;
        --concurrency)  CONCURRENCY="$2"; shift 2 ;;
        -h|--help)      usage; exit 0 ;;
        *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    esac
done

if [[ -n "${HOSTS_FILE}" ]]; then
    [[ -f "${HOSTS_FILE}" ]] || { echo "ERROR: hosts file not found: ${HOSTS_FILE}" >&2; exit 2; }
    mapfile -t HOSTS < <(grep -Ev '^[[:space:]]*(#|$)' "${HOSTS_FILE}")
elif [[ -n "${HOSTS_LIST}" ]]; then
    IFS=',' read -r -a HOSTS <<< "${HOSTS_LIST}"
else
    echo "ERROR: pass --hosts FILE or --hosts-list LIST." >&2
    usage >&2
    exit 2
fi
[[ ${#HOSTS[@]} -gt 0 ]] || { echo "ERROR: no hosts." >&2; exit 2; }

# One representative task measures whether shared expensive layers are cached.
PROBE_TASK='scienceide/laps-repair-bounds-2d-mhdrhs-l264'

echo "=== warm_status ==="
echo "  hosts     : ${#HOSTS[@]}"
echo "  probe task: ${PROBE_TASK}"
echo "  threshold : ${THRESHOLD}s (under this = warm)"
echo

PROBE_ROOT="${RL_ROOT}/outputs/scienceide_rl/eval/warm_probe"
mkdir -p "${PROBE_ROOT}"
declare -a COLD=()
declare -a WARM=()

for host in "${HOSTS[@]}"; do
    out="${PROBE_ROOT}/${host//./_}_$(date +%H%M%S)"
    cmd="cd ${RL_ROOT} && bash scienceide_rl/eval/run_eval.sh --agent nop \
--dataset ${DATASET} --task-glob $(printf '%q' "${PROBE_TASK}") --output-dir ${out} \
--skip-gpu-tasks --max-per-instance 1 -n 1"

    printf '  %-18s probing... ' "${host}"
    if ! ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=15 \
            "${host}" bash -lc "$(printf '%q' "${cmd}")" >"${out}.log" 2>&1; then
        echo "PROBE FAILED (see ${out}.log)"
        COLD+=("${host}")
        continue
    fi

    secs="$(python3 -c "
import json, sys
try:
    rows = [json.loads(l) for l in open(sys.argv[1])]
except OSError:
    print(-1); raise SystemExit
vals = [r.get('env_setup_seconds') for r in rows if r.get('env_setup_seconds')]
print(int(vals[0]) if vals else -1)
" "${out}/results.jsonl" 2>/dev/null || echo -1)"

    if [[ "${secs}" -lt 0 ]]; then
        echo "no timing recorded -> treating as cold"
        COLD+=("${host}")
    elif [[ "${secs}" -le "${THRESHOLD}" ]]; then
        echo "env_setup ${secs}s -> WARM"
        WARM+=("${host}")
    else
        echo "env_setup ${secs}s -> COLD"
        COLD+=("${host}")
    fi
done

echo
echo "  warm: ${#WARM[@]} ${WARM[*]:-}"
echo "  cold: ${#COLD[@]} ${COLD[*]:-}"

if [[ "${DO_WARM}" -eq 0 ]]; then
    echo
    echo "Re-run with --warm to warm the cold nodes, or warm them by hand:"
    for host in "${COLD[@]:-}"; do
        [[ -n "${host}" ]] && echo "  ssh ${host} 'cd ${RL_ROOT} && bash scienceide_rl/eval/run_eval.sh --agent nop --dataset ${DATASET} --output-dir <out> --skip-gpu-tasks --max-per-instance ${CONCURRENCY} -n ${CONCURRENCY}'"
    done
    exit 0
fi

if [[ ${#COLD[@]} -eq 0 ]]; then
    echo
    echo "Every node is already warm. Nothing to do."
    exit 0
fi

echo
echo "=== warming ${#COLD[@]} cold node(s) ==="
for host in "${COLD[@]}"; do
    # Avoid concurrent warm passes that could truncate the same results file.
    if ssh -o BatchMode=yes -o ConnectTimeout=15 "${host}" \
           'pgrep -f "run_eval.sh --agent nop" >/dev/null 2>&1'; then
        echo "  SKIP ${host}: a nop pass is already running there"
        continue
    fi
    # Timestamped, so re-running never overwrites an earlier pass's results.
    out="${RL_ROOT}/outputs/scienceide_rl/eval/nop_warm_${host//./_}_$(date +%m%d_%H%M%S)"
    cmd="cd ${RL_ROOT} && nohup setsid bash scienceide_rl/eval/run_eval.sh \
--agent nop --dataset ${DATASET} --output-dir ${out} --skip-gpu-tasks \
--max-per-instance ${CONCURRENCY} -n ${CONCURRENCY} > /tmp/nop_warm.log 2>&1 < /dev/null &"
    ssh -o BatchMode=yes -o StrictHostKeyChecking=no "${host}" \
        bash -lc "$(printf '%q' "${cmd}")" >/dev/null 2>&1 || true
    echo "  launched on ${host} -> ${out}"
    # Stagger: launching several at once has raced and silently dropped a host.
    sleep 3
done

echo
echo "Watch progress with (output dirs are timestamped, so glob them):"
echo "  for D in ${RL_ROOT}/outputs/scienceide_rl/eval/nop_warm_*/results.jsonl; do"
echo "    echo \"\$(dirname \$D | xargs basename): \$(wc -l < \$D)/144\""
echo "  done"
echo
echo "Then repair the transient registry failures and check the anchor:"
echo "  bash scienceide_rl/prepare/warm_repair.sh --results <out>/results.jsonl --host <host>"
