#!/usr/bin/env bash
# Preflight the three-node cluster before distributed training.
# Usage: `start_distributed_training.sh [options]`
set -euo pipefail

RL_ROOT=${RL_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}
HOSTS_FILE="${PSRL_WORKSPACE:-}/hosts/24GPUs"
CHECK_ONLY=0
FORCE=0

usage() { sed -n '2,20p' "$0"; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --hosts)      HOSTS_FILE="$2"; shift 2 ;;
        --check-only) CHECK_ONLY=1; shift ;;
        --force)      FORCE=1; shift ;;
        -h|--help)    usage; exit 0 ;;
        *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    esac
done

[[ -f "${HOSTS_FILE}" ]] || { echo "ERROR: hostfile not found: ${HOSTS_FILE}" >&2; exit 2; }
mapfile -t HOSTS < <(grep -Ev '^[[:space:]]*(#|$)' "${HOSTS_FILE}")
[[ ${#HOSTS[@]} -eq 3 ]] || {
    echo "ERROR: expected 3 hosts for the 8-gen + 16-train layout, got ${#HOSTS[@]}." >&2
    echo "For a 2-node run edit fsdp_qwen35_9b.sh: NNODES=2, TRAIN_NNODES=1, TRAIN_FSDP=8." >&2
    exit 2
}

echo "=== preflight: ${#HOSTS[@]} hosts from ${HOSTS_FILE} ==="
FAIL=0

# All GPUs must be free because placement commits all 24 devices.
echo "-- free GPUs"
for host in "${HOSTS[@]}"; do
    used="$(ssh -o BatchMode=yes -o ConnectTimeout=15 "${host}" \
        'nvidia-smi --query-gpu=memory.used --format=csv,noheader | awk "{s+=\$1} END {print s+0}"' 2>/dev/null || echo -1)"
    if [[ "${used}" -lt 0 ]]; then
        printf '   %-18s UNREACHABLE\n' "${host}"; FAIL=1
    elif [[ "${used}" -gt 2048 ]]; then
        printf '   %-18s BUSY (%s MiB in use)\n' "${host}" "${used}"
        [[ "${FORCE}" -eq 1 ]] || FAIL=1
    else
        printf '   %-18s free\n' "${host}"
    fi
done

# Refuse to stop Ray processes that may belong to another cluster.
echo "-- no foreign Ray processes"
for host in "${HOSTS[@]}"; do
    n="$(ssh -o BatchMode=yes -o ConnectTimeout=15 "${host}" \
        'pgrep -af "gcs_server|raylet" 2>/dev/null | grep -v "bash -c" | wc -l' 2>/dev/null || echo -1)"
    if [[ "${n}" -gt 0 ]]; then
        printf '   %-18s %s Ray process(es) present, CONFIRM THEY ARE YOURS\n' "${host}" "${n}"
        ssh -o BatchMode=yes "${host}" \
            'pgrep -af "gcs_server|raylet" 2>/dev/null | grep -v "bash -c" | sed "s|/lib/python3.*||" | head -3' 2>/dev/null | sed 's/^/       /'
        FAIL=1
    else
        printf '   %-18s clean\n' "${host}"
    fi
done

# Probe image availability directly on each node.
echo "-- image cache (base images present = the expensive layers are local)"
for host in "${HOSTS[@]}"; do
    n="$(ssh -o BatchMode=yes -o ConnectTimeout=15 "${host}" \
        'c=0; for i in python:3.13-slim debian:bookworm-slim alpine:3.19; do docker image inspect $i >/dev/null 2>&1 && c=$((c+1)); done; echo $c' 2>/dev/null || echo -1)"
    layers="$(ssh -o BatchMode=yes -o ConnectTimeout=15 "${host}" \
        'docker images -q 2>/dev/null | wc -l' 2>/dev/null || echo 0)"
    if [[ "${n}" -lt 0 ]]; then
        printf '   %-18s UNREACHABLE\n' "${host}"; FAIL=1
    elif [[ "${n}" -lt 3 ]]; then
        printf '   %-18s only %s/3 base images, run provision_docker_nodes.sh\n' "${host}" "${n}"; FAIL=1
    elif [[ "${layers}" -lt 50 ]]; then
        printf '   %-18s base images ok but only %s images cached, run a nop warm pass\n' "${host}" "${layers}"; FAIL=1
    else
        printf '   %-18s warm (3/3 base images, %s images cached)\n' "${host}" "${layers}"
    fi
done

echo
if [[ "${FAIL}" -ne 0 ]]; then
    echo "PREFLIGHT FAILED, not starting. Fix the items above, or pass --force for the GPU check only."
    exit 1
fi
echo "PREFLIGHT OK"

[[ "${CHECK_ONLY}" -eq 0 ]] || exit 0

echo
echo "=== starting Ray (head = ${HOSTS[0]}) ==="
cd "${RL_ROOT}"
bash examples/ray/ray_start.sh "${HOSTS_FILE}"

# Wait for asynchronous GPU registration before trainer placement.
echo
echo "=== waiting for 24 GPUs to register ==="
for _ in $(seq 1 30); do
    sleep 10
    n="$(python3 -c "
import ray
ray.init(address='auto', log_to_driver=False)
print(int(ray.cluster_resources().get('GPU', 0)))
" 2>/dev/null || echo 0)"
    echo "   GPUs visible to Ray: ${n}/24"
    [[ "${n}" -ge 24 ]] && break
done
[[ "${n}" -ge 24 ]] || { echo "ERROR: only ${n}/24 GPUs registered. Not launching." >&2; exit 1; }

LOG_DIR="${RL_ROOT}/scienceide_rl/psrl_logs/GRPO-sciaccel-v2-Qwen35-9B"
mkdir -p "${LOG_DIR}"
LOG="${LOG_DIR}/train_$(date +%m%d_%H%M%S).log"
echo "${LOG}" > /tmp/train_log

echo
echo "=== launching training ==="
echo "  log: ${LOG}"
nohup setsid bash scienceide_rl/fsdp_qwen35_9b.sh > "${LOG}" 2>&1 < /dev/null &
echo "  pid: $!"
echo
echo "Watch with:  tail -f ${LOG}"
echo "Baseline to beat (Qwen3.5-9B, same settings): 7/144 solved, mean reward_repair 0.0497"
