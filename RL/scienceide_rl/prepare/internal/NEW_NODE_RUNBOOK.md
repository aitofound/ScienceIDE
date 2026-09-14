# Preparing a new node for ScienceIDE RL

Run this on any fresh IP before it can serve rollout or training. Two independent
things have to be true: Docker must be able to build (step 2) and the task images
must already be in that node's build cache (step 4). A node that passes step 2 but
skips step 4 still works, it just pays ~1 min per task on first touch instead of
~16 s.

Everything below was verified against five fresh nodes on 2026-08-31.

## 0. Prerequisites you should check first

```bash
# From any node that can reach the others.
cat > /tmp/newhosts <<'EOF'
192.168.1.1
192.168.1.2
192.168.1.3
192.168.1.4
192.168.1.5
EOF

pssh -h /tmp/newhosts -t 30 -i '
  hostname -s
  nvidia-smi --query-gpu=count --format=csv,noheader | head -1
  test -d ${RL_ROOT} && echo REPO_OK || echo REPO_MISSING
  test -f ${PSRL_WORKSPACE}/env/psrl.sh && echo ENV_OK || echo ENV_MISSING
  test -d ${TASK_BANK_REPO}/envs/laps/tasks \
    && echo TASKS_OK || echo TASKS_MISSING'
```

You need `SUCCESS` for every host plus `REPO_OK` / `ENV_OK` / `TASKS_OK`. The repo,
the env script, and the compiled task directories all live on the shared FS, so
nothing is copied per node. If the mount is missing, later steps fail in
confusing ways rather than cleanly.

Passwordless ssh is assumed (`pssh` and plain `ssh` both need it).

## 1. Audit before changing anything

```bash
cd ${RL_ROOT}

bash scienceide_rl/prepare/internal/provision_docker_nodes.sh \
    --hosts /tmp/newhosts --check
```

`--check` is read-only. It exits 3 if any host needs work, so it doubles as a gate in
a larger script. Per-host detail lands in the printed `logs:` directory:

```
DAEMON_NEEDS: registry-mirrors=[]; default-address-pools gives ~31 networks
CLIENT_NEEDS_PROXY (has nothing)
LIVE_POOL_NARROW (probe subnet 192.168.0.0/20; needs dockerd RESTART)
RESULT: needs provisioning
```

## 2. Provision Docker

```bash
bash scienceide_rl/prepare/internal/provision_docker_nodes.sh --hosts /tmp/newhosts
```

Runs all hosts in parallel, is idempotent, and fixes three independent things. Each
one alone is enough to stop image builds:

| what | why it matters |
|---|---|
| `registry-mirrors` in `/etc/docker/daemon.json` | no direct route to Docker Hub |
| `proxies.default` in `/root/.docker/config.json` | **buildkit does not inherit the shell's `http_proxy`**, so a build fails at `apt-get update` even when `curl` works in the same shell |
| `default-address-pools` = /24 slices of 172.16/12 and 10.128/9 | Docker's stock pool is ~31 networks and every Harbor trial needs TWO (task + egress sidecar), so concurrency above ~15 trials dies with `could not find an available, non-overlapping IPv4 address pool` |

Two behaviours worth knowing:

- **dockerd is restarted, not just reloaded.** Address pools are read when the network
  controller initializes, so `SIGHUP` is not enough. The script refuses to restart while
  containers are running, and on these non-systemd hosts it relaunches dockerd itself.
- **The build probe retries once.** A dockerd that has just restarted answers
  `docker pull` fine while buildkit's registry client still fails with a bare `EOF`.
  Reporting that as a config error sends you hunting a proxy bug that is not there.

Expected result:

```
192.168.1.1        OK    provisioned (dockerd reloaded)
...
ok: 5   needs-provisioning: 0   failed: 0
```

Re-run `--check` afterwards; every host should say `already provisioned`.

## 3. Build the dataset (once, not per node)

The task directories and the parquet live on the shared FS, so this is a one-time
step for the whole cluster:

```bash
source ${PSRL_WORKSPACE}/env/psrl.sh
cd ${RL_ROOT}

python -m scienceide_rl.prepare.build_dataset \
    --repo ${TASK_BANK_REPO} \
    --out-dir scienceide_rl/data/mitgcm-biogeo/repair_easy \
    --env mitgcm-biogeo --categories repair --difficulty easy --hint-level all
```

Produces `train/`, `eval/`, `all/`, and `stats/` under the output directory, plus
`split.json`.

## 4. Warm the image cache, on EVERY node

This is the step people skip. **Harbor containers run wherever the agent-loop process
runs**, and rollout is spread across the cluster, so any node can be asked to build a
task environment. The cache lives in that node's `/var/lib/docker/buildkit` and does
not transfer.

```bash
R=${RL_ROOT}

for H in $(grep -Ev '^\s*(#|$)' /tmp/newhosts); do
  OUT=$R/outputs/scienceide_rl/eval/nop_warm_${H//./_}
  ssh -o BatchMode=yes "$H" "cd $R && nohup setsid bash scienceide_rl/eval/run_eval.sh \
      --agent nop \
      --dataset scienceide_rl/data/mitgcm-biogeo/repair_easy/all/L1.parquet \
      --output-dir $OUT \
      --skip-gpu-tasks --max-per-instance 4 -n 4 \
      > /tmp/nop_warm.log 2>&1 < /dev/null &"
  sleep 2   # stagger; launching all at once has raced and silently dropped a host
done
```

Runs in parallel across nodes, ~40-60 min each, no GPU needed. Watch it:

```bash
for H in $(grep -Ev '^\s*(#|$)' /tmp/newhosts); do
  echo "$H: $(wc -l < $R/outputs/scienceide_rl/eval/nop_warm_${H//./_}/results.jsonl 2>/dev/null || echo 0)"
done
```

`--skip-gpu-tasks` drops any task declaring `gpus > 0`, which the local Docker
provider cannot host, so the total is below the bank size.

### What "warm" actually means

There is no explicit `docker build`. Harbor runs

```bash
docker compose --project-name <task>__<trial>__env \
  --project-directory <task>/environment \
  -f docker-compose-build.yaml ... up --detach --wait
```

and harbor's `docker-compose-build.yaml` carries a `build:` stanza, so `compose up`
builds first and runs second. Warming is that build happening once per task; `nop` is
an agent that does nothing inside the container but still walks
env-build -> verifier-build -> grade.

It pays off because a task's Dockerfiles are nearly identical across the bank. Docker
hashes each instruction plus everything before it, so the apt toolchain, the upstream
clone, and the build are byte-identical across tasks and get reused. Only the final
`COPY defect/` layer is per-task.

Cost per task environment, which is why step 4 is worth the wall time:

| state | time |
|---|---|
| cold, no registry mirror / build proxy | ~3.5 h (apt at ~17 kB/s through the proxy) |
| cold, provisioned | ~1 min |
| **warm** | **~16 s** |

The cache is in `/var/lib/docker/buildkit`. What `docker images` shows is *not* the
cache. Those are Harbor's per-trial tags, which become `<none>` when the trial ends
which accumulate in the thousands. So:

- `docker image prune` clears the `<none>` tags and does **not** hurt the cache
- `docker builder prune` **destroys** the cache

Do not judge the cache by directory size. Buildkit's own GC shrinks it without
slowing builds. Judge it by `env_setup_seconds`.

## 5. Confirm the nop anchor, do not skip this

The warm pass doubles as the anchor, and it is the one check that says whether a
training run can mean anything.

```bash
python3 -c "
import json, sys
p = sys.argv[1]
s = json.load(open(p)); o = s['overall']
ok = (o['mean_score'] == 0 and o['mean_raw_reward'] == 0 and o['n_success'] == 0
      and not s['errors'] and not s.get('floor_mismatch'))
print('by_category:', {k: v['mean_score'] for k, v in s['by_category'].items()})
print('errors:', s['errors'], '| floor_mismatch:', s.get('floor_mismatch'))
print('ANCHOR HELD:', ok)
" $R/outputs/scienceide_rl/eval/nop_warm_<host>/summary.json
```

`nop` does nothing inside the container, so it MUST score a strict 0. A non-zero score
means the reward ladder credits a non-delivery, and every reward the policy sees would
be inflated, so training on it is meaningless. `floor_mismatch` must be empty too: it is
the denominator of `reward_repair = max(0, reward - floor) / (1 - floor)`.

Verified on this cluster:

```
by_category: {'acceleration': 0.0, 'implementation': 0.0, 'repair': 0.0}
errors: {} | floor_mismatch: []
ANCHOR HELD: True
```

## 6. Start Ray, then train

```bash
cat > ${PSRL_WORKSPACE}/hosts/<N>GPUs <<'EOF'
<head ip first>
<worker ip>
...
EOF

bash examples/ray/ray_start.sh ${PSRL_WORKSPACE}/hosts/<N>GPUs
```

The first line of the hostfile becomes the Ray head. The script force-stops leftover
Ray on every node first, which matters: a stale GCS makes the next launch hang
retrying `Failed to connect to GCS at <ip>:8887`.

**Watch out for `--num-cpus=32` in that script.** Each Harbor container runs 4 MPI
ranks, so 32 advertised CPUs caps concurrent episodes at ~8 per node no matter how many
physical cores exist (these boxes have 384). Raise it if rollout throughput is
CPU-bound.

Then, from the head node:

```bash
bash scienceide_rl/fsdp_qwen35_9b.sh
```

## Gotchas that cost real time here

- **`TMPDIR` length breaks Ray.** Ray's plasma socket goes under `tempfile.gettempdir()`
  and AF_UNIX paths cannot exceed 107 bytes. A 62-char inherited `TMPDIR` projects to
  ~129 and Ray dies with `validate_socket_filename failed`. `fsdp_qwen35_9b.sh` pins
  `TMPDIR=/tmp`. Note Ray does **not** read `RAY_TMPDIR`; the knobs are `TMPDIR` or
  `ray.init(_temp_dir=...)`.
- **Do not put scratch on the shared FUSE mount.** It does not report free inodes, and
  writes fail with `ENOSPC` under load even with terabytes free.
- **A first MoE launch costs ~27 min of kernel compilation.** flashinfer JIT-builds the
  CUTLASS fused-MoE kernel with all TP workers serialized behind one filelock (166 nvcc
  processes at peak). It caches in `~/.cache/flashinfer`, so only the first launch per
  node pays it. Relevant if you serve a MoE checkpoint such as Qwen3.5-35B-A3B.
