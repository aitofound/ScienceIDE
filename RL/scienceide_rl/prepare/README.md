# Data preparation for SciAccel-RL

Turns an authored task bank into Harbor-runnable tasks and hinted training
parquets. Four stages, in a hard dependency order:

| Stage | What it does | Re-run when |
|---|---|---|
| `compile` | Densifies sparse task sources into Harbor task dirs under `build/<env>/` | The task bank changes |
| `lines` | Resolves each defect's source line from the pinned upstream tree | The task bank changes |
| `dataset` | Writes the L1/L2/L3 parquets and their splits | Hints or splits change |
| `warm` | Populates each node's buildkit cache so episodes do not cold build | A node is added or reimaged |

| File | Purpose |
|------|---------|
| [`prepare_all.sh`](prepare_all.sh) | Runs all four stages in order. Start here. |
| [`build_dataset.py`](build_dataset.py) | Hinted parquets with stratified train and eval splits |
| [`resolve_defect_lines.py`](resolve_defect_lines.py) | Locates defect lines in the pinned upstream source |
| [`warm_status.sh`](warm_status.sh) | Probes how warm each node's image cache already is |
| [`warm_repair.sh`](warm_repair.sh) | Retries only the tasks that failed a warm pass |
| [`internal/`](internal/) | Site-specific node provisioning, published as reference only |

Every command below is run from the repository root. `${SCIACCEL_REPO}` is your
checkout of the task bank, and `192.168.1.x` stands in for your own node
addresses.

---

## The one command

```bash
# See the plan first, touching nothing.
bash scienceide_rl/prepare/prepare_all.sh \
    --repo ${SCIACCEL_REPO} --envs mitgcm-biogeo --dry-run

bash scienceide_rl/prepare/prepare_all.sh \
    --repo ${SCIACCEL_REPO} --envs mitgcm-biogeo \
    --hosts 192.168.1.1,192.168.1.2
```

It skips already-compiled envs, probes each node's Docker before dispatching, and
warms envs sequentially per host so concurrency stays at the intended value
rather than that value times the env count.

Re-run a single stage after a failure instead of redoing slow work:

```bash
bash scienceide_rl/prepare/prepare_all.sh --repo ${SCIACCEL_REPO} \
    --envs mitgcm-biogeo --stages dataset
```

| Flag | Default | Meaning |
|---|---|---|
| `--repo` | required | Task bank checkout |
| `--envs` | `laps,mitgcm-biogeo,athena-gr` | Environments to prepare |
| `--hosts` | required for `warm` | Nodes that will host episodes |
| `--stages` | `compile,lines,dataset,warm` | Subset to run |
| `--difficulty` | `easy` | Tier to keep |
| `--categories` | `repair` | Taxonomy categories to keep |
| `--apt-mirror` | empty | Baked into images at compile time |

**The order is not cosmetic.** A dataset built before `compile` points at task
directories with no `environment/`, and every episode dies about two seconds in.
A dataset built before `lines` silently drops the line from every L1 hint for an
env that records only the file, quietly turning L1 into L2.

The rest of this file explains each stage for when you need to run one by hand.

---

## 1. Compile authored sources

An authored task under `envs/` is **sparse**: it holds `task.toml`,
`instruction.md`, `defect.json`, `fix.json`, and its provenance, but no
`environment/` directory. Harbor builds its image from exactly that directory, so
an uncompiled task fails at trial start with
`unable to prepare context: path .../environment not found`, after about two
seconds and with no other diagnostic.

One compiler handles every env. It reads the env's own templates and
`harbor_spec.py`, so a fix belongs in `envs/<env>/env/harbor/` rather than in the
compiler:

```bash
cd ${SCIACCEL_REPO}
python utils/harbor/to_harbor.py --env envs/<env>
```

It writes `build/<env>/<category>/<tier>/<task>/` with `environment/`, `tests/`,
and `solution/` added, plus a `build/<env>/index.jsonl` for samplers.
`build_dataset.py` reads only from `build/<env>` and refuses to emit a dataset
when it is missing, so this step cannot be skipped silently.

**If your route to `deb.debian.org` is slow, pass `--apt-mirror`.** It is baked
into the generated Dockerfiles at compile time, so it cannot be corrected later
without recompiling. A slow route does not fail the build, it crawls, so the
symptom is a warm pass stuck at 0 completed tasks with `docker compose build`
processes that look hung.

```bash
python utils/harbor/to_harbor.py --env envs/<env> --apt-mirror http://your-mirror.example.com
```

---

## 2. Resolve defect line numbers

The strongest hint level names the file **and line** of the defect. Envs disagree
on whether they record one, so this fills the gaps:

```bash
python scienceide_rl/prepare/resolve_defect_lines.py \
    --repo ${SCIACCEL_REPO} --env laps --env mitgcm-biogeo --env athena-gr
```

It downloads each env's pinned upstream source, verifies its sha256, and finds the
line by matching the provenance `old` text block literally. It writes
`envs/<env>/factory/DEFECT_LINES.json`.

A recorded line always wins and is never cached, so the cache holds only what an
env is missing. Where both exist they agree, so the reported offsets are expected
rather than errors: an env whose build patches a file before the agent sees it
has post-patch recorded lines, while the resolver reads the pristine tree. The
recorded line is kept in that case.

---

## 3. Build the hinted datasets

The hint is a localization aid appended to the instruction:

```
## Where to look

The defect is a single edit confined to:

    pkg/bling/bling_bio_nitrogen.F, line 1037

The change made there: clip a loop upper bound by one. No other file has been modified.
```

Three levels: **L1** file and line, **L2** file only, **L3** no hint (control).
Hints exist because an unhinted 4B model scored near zero: the task became
*finding* the defect in a large repository rather than *fixing* it.

```bash
python -m scienceide_rl.prepare.build_dataset \
    --repo ${SCIACCEL_REPO} \
    --out-dir scienceide_rl/data/mitgcm-biogeo/repair_easy \
    --env mitgcm-biogeo --categories repair --difficulty easy --hint-level all
```

One file per role per level, so a launch script names a split by path rather than
by decoding a filename prefix:

```
data/<env>/<category>_<tier>/
├── train/L1.parquet        hinted train split
├── eval/L1.parquet         hinted eval split, in-distribution
├── eval/unhinted.parquet   unhinted eval split, shared by every level
├── all/L1.parquet          every task at this level, unsplit
├── stats/L1.json           per-group counts and floor ranges
└── split.json              the partition, and how it was chosen
```

Sizes for the `repair` category at the `easy` tier, to check your own build against:

| Dataset | all | train | eval |
|---|---|---|---|
| `laps/repair_easy` | 32 | 24 | 8 |
| `mitgcm-biogeo/repair_easy` | 87 | 66 | 21 |
| `athena-gr/repair_easy` | 104 | 87 | 17 |
| `mitgcm-atmos/repair_easy` | 123 | 93 | 30 |

Two eval files exist on purpose. `eval/L1.parquet` is **hinted**, matching the
training distribution, and is what you want for measuring training progress.
`eval/unhinted.parquet` measures unaided localization, which a hint-trained model
was never asked to do. Comparing a hinted checkpoint against it will look like a
catastrophic regression that is really a task change.

The split is stratified by `(category, family, tree)` and chosen by sorted task
name, so it is reproducible without a seed and identical across hint levels. It
is capped at 25% of the bank, because one task per group is only proportionate
when groups are large. An env with many singleton groups would otherwise hold
out most of its tasks.

---

## 4. Warm the image cache, on every node that runs episodes

Harbor containers run wherever the agent-loop process runs, and the buildkit
cache is node-local (`/var/lib/docker/buildkit`). A cold node spends 8 to 15
minutes per task on its first build. Warm each node with the `nop` agent, which
builds and tears down without needing a GPU or a model:

```bash
for H in 192.168.1.1 192.168.1.2; do
  ssh -o BatchMode=yes "$H" "cd $PWD && nohup setsid bash scienceide_rl/eval/run_eval.sh \
      --agent nop \
      --dataset scienceide_rl/data/mitgcm-biogeo/repair_easy/all/L1.parquet \
      --output-dir /tmp/nop_warm_${H//./_} \
      --skip-gpu-tasks --max-per-instance 4 -n 4 \
      > /tmp/nop_warm.log 2>&1 < /dev/null &"
  sleep 2   # staggering matters: launching all at once has silently dropped a host
done
```

**Keep warm concurrency low.** Each episode compiles a full scientific codebase
and fans out to 4 more processes, so a high value oversubscribes even a
many-core node. The containers' own reference runs then starve past their 120 s
timeout and fail, which looks like broken tasks rather than contention.

`warm_status.sh` probes how warm each node already is, and `warm_repair.sh`
retries only the tasks that failed.

### Check Docker health first

A degraded daemon is the single most common cause of a stalled run, and it does
not announce itself. Before launching anything:

```bash
timeout 20 docker ps -q | wc -l      # hangs => daemon is wedged, do not launch
ps -eo comm | grep -c fuse-overlayfs # hundreds => orphaned mounts
uptime                               # load >> core count
```

If `docker ps` times out, that node cannot host episodes. Exclude it with
`AGENT_NODE_IPS` rather than waiting for it to recover. See
[`internal/`](internal/) for the node provisioning this was developed against,
including why buildkit ignores your shell's proxy.

---

## Adding an environment

Every env is prepared identically, so adding one is a task-bank change rather
than a change here. What decides whether a new env trains well:

| Property | Why it decides success |
|---|---|
| native `candidate.meta.line` | L1 degrades to L2 without it, and resolving needs a reachable pinned source. |
| single-file defects | multi-file hints cost 400+ chars and cannot name a line, so they localize worse. |
| bundled source tarball | no network at compile time, and no digest surprises. |
| low measured check wall | the 120 s reference-run cap is the top source of wasted episodes. Compare the funnel's *measured* wall, not the declared `expected_runtime_sec`. |

Check the env's `env/harbor/` templates carry `tmux` in the agent image and an
apt-mirror slot in the verifier's final stage. terminus-2 drives the container
through a tmux pane, and the agent allowlist contains only model API hosts, so a
missing `tmux` produces a flood of `Failed to install tmux from source` followed
by `rollout_error` on every episode.

```bash
grep -c tmux envs/<env>/env/harbor/agent.Dockerfile   # must be >= 1
```

After compiling, prove one task builds and runs before committing a training run:

```bash
T=$(ls -d build/<env>/repair/easy/*/environment | head -1)
docker build -t probe -f $T/Dockerfile $T && docker run --rm probe tmux -V
```
