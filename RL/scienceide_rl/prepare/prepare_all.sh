#!/usr/bin/env bash
# Run the SciAccel-RL preparation pipeline: compile, lines, dataset, warm, in order.
# Usage: `prepare_all.sh --repo PATH [--envs a,b,c] [--hosts ip1,ip2] [--stages ...] [--dry-run]`
#
# A dataset built before `compile` points at tasks with no `environment/`, and one
# built before `lines` silently turns L1 into L2.

set -euo pipefail

RL_ROOT=${RL_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}

# Path to the sciaccel-rl task bank checkout. No default: it lives outside this repo.
REPO=${REPO:-}
ENVS=${ENVS:-laps,mitgcm-biogeo,athena-gr}
# Nodes that will host Harbor episodes, comma separated. No default, because a wrong
# host silently warms the wrong machine and training then cold builds.
HOSTS=${HOSTS:-}
STAGES=${STAGES:-compile,lines,dataset,warm}
DIFFICULTY=${DIFFICULTY:-easy}
CATEGORIES=${CATEGORIES:-repair}
DATA_ROOT=${DATA_ROOT:-${RL_ROOT}/scienceide_rl/data}
# Baked into the generated Dockerfiles at compile time, so it cannot be corrected
# later without recompiling. Leave empty to use the upstream Debian mirrors.
APT_MIRROR=${APT_MIRROR:-}
DRY_RUN=0

# Concurrent warm episodes per host. Each compiles a full scientific codebase and fans
# out to 4 more processes, so a higher value oversubscribes the node and times out builds.
WARM_CONCURRENCY=${WARM_CONCURRENCY:-4}

usage() { sed -n '2,3p' "$0"; }

has_stage() { [[ ",${STAGES}," == *",$1,"* ]]; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo)        REPO="$2"; shift 2 ;;
        --envs)        ENVS="$2"; shift 2 ;;
        --hosts)       HOSTS="$2"; shift 2 ;;
        --stages)      STAGES="$2"; shift 2 ;;
        --difficulty)  DIFFICULTY="$2"; shift 2 ;;
        --categories)  CATEGORIES="$2"; shift 2 ;;
        --data-root)   DATA_ROOT="$2"; shift 2 ;;
        --apt-mirror)  APT_MIRROR="$2"; shift 2 ;;
        --dry-run)     DRY_RUN=1; shift ;;
        -h|--help)     usage; exit 0 ;;
        *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    esac
done

[[ -n "${REPO}" ]] || {
    echo "ERROR: set --repo (or REPO) to the sciaccel-rl task bank checkout." >&2
    exit 2
}
[[ -d "${REPO}" ]] || { echo "ERROR: repo not found: ${REPO}" >&2; exit 2; }
if has_stage warm && [[ -z "${HOSTS}" ]]; then
    echo "ERROR: set --hosts (or HOSTS) to the nodes that will run episodes." >&2
    exit 2
fi

IFS=',' read -r -a ENV_LIST <<< "${ENVS}"
IFS=',' read -r -a HOST_LIST <<< "${HOSTS}"

run() {
    echo "+ $*"
    if [[ "${DRY_RUN}" -eq 0 ]]; then "$@"; fi
}

# One directory per (env, category, tier), because a repair-only easy bank and a
# mixed one are different experiments that must not share a path.
env_out_dir() { echo "${DATA_ROOT}/$1/${CATEGORIES}_${DIFFICULTY}"; }

echo "=============================================================="
echo " repo    : ${REPO}"
echo " envs    : ${ENVS}"
echo " stages  : ${STAGES}"
echo " hosts   : ${HOSTS}"
echo "=============================================================="

# --- 1. Compile authored sources into Harbor tasks ---------------------------
# Skipped for an env whose `build/<env>/index.jsonl` already exists.
if has_stage compile; then
    echo; echo "### [1/4] compile"
    for env in "${ENV_LIST[@]}"; do
        if [[ -f "${REPO}/build/${env}/index.jsonl" ]]; then
            echo "  ${env}: already compiled at build/${env}, skipping"
            continue
        fi
        cmd=(python "${REPO}/utils/harbor/to_harbor.py" --env "${REPO}/envs/${env}")
        [[ -n "${APT_MIRROR}" ]] && cmd+=(--apt-mirror "${APT_MIRROR}")
        run "${cmd[@]}"
    done
fi

# --- 2. Resolve defect line numbers -----------------------------------------
# Writes DEFECT_LINES.json, filling only the gaps a recorded line leaves.
if has_stage lines; then
    echo; echo "### [2/4] resolve defect lines"
    args=()
    for env in "${ENV_LIST[@]}"; do args+=(--env "${env}"); done
    run python "${RL_ROOT}/scienceide_rl/prepare/resolve_defect_lines.py" \
        --repo "${REPO}" "${args[@]}"
fi

# --- 3. Build the hinted datasets -------------------------------------------
if has_stage dataset; then
    echo; echo "### [3/4] build datasets"
    for env in "${ENV_LIST[@]}"; do
        out=$(env_out_dir "${env}")
        cmd=(python -m scienceide_rl.prepare.build_dataset
             --repo "${REPO}" --out-dir "${out}"
             --env "${env}" --categories "${CATEGORIES}" --hint-level all
             --difficulty "${DIFFICULTY}")
        ( cd "${RL_ROOT}" && run "${cmd[@]}" )
    done
fi

# --- 4. Warm each node's image cache ----------------------------------------
# The cache is node-local, so every node that hosts episodes needs its own pass.
if has_stage warm; then
    echo; echo "### [4/4] warm image caches"
    # Datasets are checked up front so a missing one fails before any host is touched.
    datasets=()
    for env in "${ENV_LIST[@]}"; do
        dataset="$(env_out_dir "${env}")/all/L1.parquet"
        if [[ ! -f "${dataset}" ]]; then
            echo "  ${env}: no dataset at ${dataset}, run the dataset stage first" >&2
            exit 2
        fi
        datasets+=("${env}:${dataset}")
    done

    for host in "${HOST_LIST[@]}"; do
        # A wedged daemon accepts the ssh and then hangs every build, so probe before
        # dispatching rather than discovering it 40 minutes later.
        if ! timeout 40 ssh -o BatchMode=yes -o StrictHostKeyChecking=no "${host}" \
             'timeout 25 docker ps -q > /dev/null 2>&1'; then
            echo "  ${host}: docker is unresponsive, skipping (exclude it via AGENT_NODE_IPS)" >&2
            continue
        fi
        # One background shell per host walking the envs SEQUENTIALLY. Launching an
        # env per host in parallel would multiply the concurrency by the env count.
        remote_script=""
        for entry in "${datasets[@]}"; do
            env="${entry%%:*}"
            dataset="${entry#*:}"
            outdir="${RL_ROOT}/scienceide_rl/outputs/warm/${env}_${host//./_}"
            conc=${WARM_CONCURRENCY}
            remote_script+="echo \"[warm] ${env} start \$(date +%T) conc=${conc}\"; "
            remote_script+="bash scienceide_rl/eval/run_eval.sh --agent nop "
            remote_script+="--dataset ${dataset} --output-dir ${outdir} "
            remote_script+="--skip-gpu-tasks --max-per-instance ${conc} -n ${conc} || true; "
        done
        remote_script+="echo \"[warm] all envs done \$(date +%T)\";"
        echo "  ${host}: ${#datasets[@]} envs, sequential"
        if [[ "${DRY_RUN}" -eq 0 ]]; then
            # `-n` and the redirects matter: without them ssh waits on the remote's
            # inherited stdout, so this loop blocks on the first host.
            ssh -n -o BatchMode=yes -o StrictHostKeyChecking=no "${host}" \
                "cd ${RL_ROOT} && nohup setsid bash -c '${remote_script}' > /tmp/warm_all.log 2>&1 < /dev/null & disown" \
                > /dev/null 2>&1 </dev/null
        fi
        # Staggered on purpose: launching every host at once has raced and silently
        # dropped one, which then cold builds during training.
        sleep 2
    done
    echo
    echo "Warm runs in the background, roughly 40 to 60 minutes per env per host. Watch with:"
    for host in "${HOST_LIST[@]}"; do
        echo "  ssh ${host} 'tail -2 /tmp/warm_all.log; timeout 20 docker ps -q | wc -l'"
    done
fi

echo; echo "Done: ${STAGES}"
