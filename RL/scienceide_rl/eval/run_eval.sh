#!/usr/bin/env bash
# Serve a model as a vLLM fleet, run the eval against it, then tear it down.
# Usage: `run_eval.sh [--model PATH] [--dataset PATH] [--agent nop|oracle|terminus-2] [--replicas N] [-n N]`
set -euo pipefail

# The `nop` and `oracle` anchors need no model, so they skip serving entirely.
usage() { sed -n '2,3p' "$0"; }

PSRL_PATH=${PSRL_PATH:-$(python3 -c "import os, psrl; print(os.path.dirname(os.path.dirname(psrl.__file__)))")}
RL_ROOT=${RL_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}
ENV_SCRIPT=${ENV_SCRIPT:-${PSRL_WORKSPACE:-}/env/psrl.sh}

MODEL=${HF_MODEL_PATH:-${PSRL_WORKSPACE:-}/models/Qwen3.5-9B}
SERVED_NAME="qwen35-9b"
AGENT="terminus-2"
DATASET="${RL_ROOT}/scienceide_rl/data/mitgcm-biogeo/repair_easy/all/L1.parquet"
OUTPUT_DIR=""
PORT=8000
TP=2
PP=1
REPLICAS=4
MAX_MODEL_LEN=32768
MAX_OUTPUT_TOKENS=8192
MAX_TURNS=25
MAX_PER_INSTANCE=32
API_BASE=""
N_ATTEMPTS=1
N_CONCURRENT=8
TEMPERATURE=1.0
TIMEOUT_MULTIPLIER=1.0
BUILD_TIMEOUT_MULTIPLIER=2.0
APT_MIRROR=0
SKIP_GPU_TASKS=1
KEEP_SERVER=0
REUSE_SERVER=0
CATEGORIES=()
FAMILIES=()
TASK_GLOB=""
PER_FAMILY=0
LIMIT=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --model)               MODEL="$2"; shift 2 ;;
        --served-model-name)   SERVED_NAME="$2"; shift 2 ;;
        --agent)               AGENT="$2"; shift 2 ;;
        --dataset)             DATASET="$2"; shift 2 ;;
        --output-dir)          OUTPUT_DIR="$2"; shift 2 ;;
        --port)                PORT="$2"; shift 2 ;;
        --tp)                  TP="$2"; shift 2 ;;
        --pp)                  PP="$2"; shift 2 ;;
        --replicas)            REPLICAS="$2"; shift 2 ;;
        --max-model-len)       MAX_MODEL_LEN="$2"; shift 2 ;;
        --max-output-tokens)   MAX_OUTPUT_TOKENS="$2"; shift 2 ;;
        --max-turns)           MAX_TURNS="$2"; shift 2 ;;
        --max-per-instance)    MAX_PER_INSTANCE="$2"; shift 2 ;;
        --api-base)            API_BASE="$2"; shift 2 ;;
        -k|--n-attempts)       N_ATTEMPTS="$2"; shift 2 ;;
        -n|--n-concurrent)     N_CONCURRENT="$2"; shift 2 ;;
        --temperature)         TEMPERATURE="$2"; shift 2 ;;
        --timeout-multiplier)  TIMEOUT_MULTIPLIER="$2"; shift 2 ;;
        --build-timeout-multiplier) BUILD_TIMEOUT_MULTIPLIER="$2"; shift 2 ;;
        --apt-mirror)          APT_MIRROR=1; shift ;;
        --skip-gpu-tasks)      SKIP_GPU_TASKS=1; shift ;;
        --with-gpu-tasks)      SKIP_GPU_TASKS=0; shift ;;
        --keep-server)         KEEP_SERVER=1; shift ;;
        --reuse-server)        REUSE_SERVER=1; shift ;;
        --task-glob)           TASK_GLOB="$2"; shift 2 ;;
        --per-family)          PER_FAMILY="$2"; shift 2 ;;
        --limit)               LIMIT="$2"; shift 2 ;;
        --categories)
            shift
            while [[ $# -gt 0 && "$1" != --* ]]; do CATEGORIES+=("$1"); shift; done ;;
        --families)
            shift
            while [[ $# -gt 0 && "$1" != --* ]]; do FAMILIES+=("$1"); shift; done ;;
        -h|--help)             usage; exit 0 ;;
        *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    esac
done

[[ -f "${DATASET}" ]] || {
    echo "ERROR: dataset not found: ${DATASET}" >&2
    echo "Build it first: python -m scienceide_rl.prepare.build_dataset --repo <task-bank> --out-dir $(dirname "${DATASET}")" >&2
    exit 2
}

if [[ -z "${OUTPUT_DIR}" ]]; then
    OUTPUT_DIR="${RL_ROOT}/outputs/scienceide_rl/eval/${AGENT}_$(date +%Y%m%d_%H%M%S)"
fi
mkdir -p "${OUTPUT_DIR}"

# Anchor agents play the policy without an endpoint.
NEEDS_MODEL=1
if [[ "${AGENT}" == "oracle" || "${AGENT}" == "nop" ]]; then
    NEEDS_MODEL=0
fi

LAUNCHED_SERVER=0
SERVE_DIR="${OUTPUT_DIR}/serve"

# Signal each replica process group so worker children release their GPUs.
cleanup() {
    if [[ "${LAUNCHED_SERVER}" -eq 1 && "${KEEP_SERVER}" -eq 0 && -f "${SERVE_DIR}/endpoints.json" ]]; then
        echo "[run_eval] Stopping the vLLM fleet..."
        python3 -c "
import json, os, signal, sys, time

pids = [e['pid'] for e in json.load(open(sys.argv[1]))['endpoints'] if e.get('pid')]
groups = []
for pid in pids:
    try:
        groups.append(os.getpgid(pid))
    except ProcessLookupError:
        pass
for gid in groups:
    try:
        os.killpg(gid, signal.SIGTERM)
        print(f'  SIGTERM -> process group {gid}')
    except (ProcessLookupError, PermissionError):
        pass
time.sleep(15)
for gid in groups:
    try:
        os.killpg(gid, signal.SIGKILL)
        print(f'  SIGKILL -> process group {gid} (ignored SIGTERM)')
    except (ProcessLookupError, PermissionError):
        pass
" "${SERVE_DIR}/endpoints.json" || true
    fi
}
trap cleanup EXIT

# Optional shared env script, absent on a machine already in the right environment.
set +u
if [[ -f "${ENV_SCRIPT}" ]]; then
    # shellcheck disable=SC1090
    source "${ENV_SCRIPT}"
else
    echo "[run_eval] No env script at ${ENV_SCRIPT}, using the current environment."
fi
set -u

if [[ "${NEEDS_MODEL}" -eq 1 && "${REUSE_SERVER}" -eq 0 ]]; then
    [[ -d "${MODEL}" ]] || { echo "ERROR: model directory not found: ${MODEL}" >&2; exit 2; }
    echo "[run_eval] Serving ${MODEL} as ${SERVED_NAME}: ${REPLICAS} replica(s) x TP=${TP} from port ${PORT}..."
    # Use independent servers because evaluation distributes work across endpoints.
    (cd "${PSRL_PATH}" && python3 -m psrl.eval.serve \
        topology=fleet \
        topology.replicas="${REPLICAS}" \
        topology.tp="${TP}" \
        topology.pp="${PP}" \
        topology.base_port="${PORT}" \
        server.checkpoint="${MODEL}" \
        server.served_model_name="${SERVED_NAME}" \
        server.max_model_len="${MAX_MODEL_LEN}" \
        env_script="${ENV_SCRIPT}" \
        output_dir="${SERVE_DIR}")
    LAUNCHED_SERVER=1
fi

# Discover endpoints from whatever the fleet actually brought up healthy, so the
# eval can never be pointed at a replica that failed to load.
if [[ "${NEEDS_MODEL}" -eq 1 && -z "${API_BASE}" && -f "${SERVE_DIR}/endpoints.json" ]]; then
    API_BASE="$(python3 -c "
import json, sys
payload = json.load(open(sys.argv[1]))
print(','.join(e['url'] for e in payload['endpoints']))
" "${SERVE_DIR}/endpoints.json")"
    echo "[run_eval] Discovered endpoints: ${API_BASE}"
fi

EVAL_ARGS=(
    --dataset "${DATASET}"
    --output-dir "${OUTPUT_DIR}"
    --agent "${AGENT}"
    --n-attempts "${N_ATTEMPTS}"
    --n-concurrent "${N_CONCURRENT}"
    --timeout-multiplier "${TIMEOUT_MULTIPLIER}"
    --build-timeout-multiplier "${BUILD_TIMEOUT_MULTIPLIER}"
    --max-per-instance "${MAX_PER_INSTANCE}"
)
if [[ "${NEEDS_MODEL}" -eq 1 ]]; then
    EVAL_ARGS+=(
        --served-model-name "${SERVED_NAME}"
        --api-base "${API_BASE:-http://127.0.0.1:${PORT}/v1}"
        --temperature "${TEMPERATURE}"
        --max-model-len "${MAX_MODEL_LEN}"
        --max-output-tokens "${MAX_OUTPUT_TOKENS}"
        --max-turns "${MAX_TURNS}"
    )
fi
[[ ${#CATEGORIES[@]} -gt 0 ]] && EVAL_ARGS+=(--categories "${CATEGORIES[@]}")
[[ "${APT_MIRROR}" -eq 1 ]]     && EVAL_ARGS+=(--apt-mirror)
[[ "${SKIP_GPU_TASKS}" -eq 1 ]] && EVAL_ARGS+=(--skip-gpu-tasks)
[[ ${#FAMILIES[@]} -gt 0 ]]   && EVAL_ARGS+=(--families "${FAMILIES[@]}")
[[ -n "${TASK_GLOB}" ]]       && EVAL_ARGS+=(--task-glob "${TASK_GLOB}")
[[ "${PER_FAMILY}" -gt 0 ]]   && EVAL_ARGS+=(--per-family "${PER_FAMILY}")
[[ "${LIMIT}" -gt 0 ]]        && EVAL_ARGS+=(--limit "${LIMIT}")

cd "${RL_ROOT}"
PYTHONUNBUFFERED=1 python3 -m scienceide_rl.eval.eval_tasks "${EVAL_ARGS[@]}" \
    2>&1 | tee "${OUTPUT_DIR}/eval.log"
