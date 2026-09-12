# Standalone SciAccel-RL Evaluation

Measures a model on the sciaccel-rl task bank **outside** the training loop:
serve a checkpoint with vLLM, let Harbor's own `terminus-2` harness drive it
through the containerized episodes, and report the per-category and per-family
reward. Use it for the pre-RL baseline and for evaluating saved checkpoints.

| File | Purpose |
|------|---------|
| [`eval_sciaccel.py`](eval_sciaccel.py) | Evaluation entry point. Reads a dataset Parquet, runs batched Harbor Jobs, aggregates metrics. |
| [`run_eval.sh`](run_eval.sh) | End-to-end wrapper: launch a vLLM fleet, run the eval, tear it down. Model-agnostic via `--model`. |

vLLM serving is **not** reimplemented here: the wrapper calls
[`psrl.eval.serve`](https://github.com/psrl-project/psrl), shared with `examples/mini_swe/eval/`. It
starts a fleet of independent replicas (`topology=fleet`) rather than one server
with `--data-parallel-size`, because DP is broken in this repo's patched vLLM and
`eval_sciaccel` spreads its work queue across every endpoint anyway.

The wrapper then reads `<output_dir>/serve/endpoints.json` to build `--api-base`,
so the eval is always pointed at exactly the replicas that came up healthy, with
no hand-maintained URL list.

---

## Prerequisite: build the dataset

```bash
python -m scienceide_rl.prepare.build_dataset \
    --repo ${SCIACCEL_REPO} \
    --out-dir scienceide_rl/data/mitgcm-biogeo/repair_easy \
    --env mitgcm-biogeo --categories repair --difficulty easy --hint-level all
```

See [`../prepare/build_dataset.py`](../prepare/build_dataset.py) for the schema,
and [`../README.md`](../../README.md) for the full preparation pipeline, including
the compile step this depends on.

---

## Anchor first: this is not optional

**`oracle` must score full marks and `nop` must score 0 on your machine before
any agent number means anything.** Neither needs a GPU or a model.

```bash
D=scienceide_rl/data/mitgcm-biogeo/repair_easy/all/L1.parquet
T=$(python -c "import pandas as pd,sys; print(pd.read_parquet(sys.argv[1])['task_name'][0])" $D)

# One task, fastest possible end-to-end signal
python -m scienceide_rl.eval.eval_sciaccel --dataset $D \
    --task-glob "$T" \
    --agent oracle --output-dir scienceide_rl/outputs/anchor_oracle
# expect: score 1.0 (reward_repair), raw reward 1.0

python -m scienceide_rl.eval.eval_sciaccel --dataset $D \
    --task-glob "$T" \
    --agent nop --output-dir scienceide_rl/outputs/anchor_nop
# expect: score 0.0, and `floor` reported matching the dataset's floor
```

If either anchor is off, stop and debug Harbor/Docker. A model number measured
against a broken verifier is worse than no number.

`summary.json` carries a `floor_mismatch` list for exactly this reason: the
verifier measures the straw floor in situ at image-build time, and it should
agree with what the task's provenance recorded. Drift means the compiled task tree and
the dataset disagree.

---

## Which key is the score

`score` in `results.jsonl` is **not** raw `reward`. It is the per-category
training signal, chosen by `build_dataset` and carried in
`extra_info["reward_key"]`:

| category | score key | why |
|---|---|---|
| repair, implementation | `reward_repair` | Floor-normalized. Delivering the unfixed build scores exactly 0; raw `reward` is inflated to the floor (0.1 to 0.65) by doing nothing. |
| acceleration / laps-accel-cuda | `reward_gpu` | `reward × gpu_active`. The CPU shortcut scores 0. |
| acceleration / laps-accel-cpu | `reward` | Carries no acceleration signal unless you tighten `[agent] timeout_sec` (budget forcing). |

`mean_raw_reward` is reported alongside so the gap is visible.

---

## Docker images: what gets built, and how much it costs

Every task ships its own `environment/Dockerfile` and `tests/Dockerfile` and
**no task declares a prebuilt `docker_image`**. Harbor builds from the task's
build context and tags the result `hb__<content-hash>`. Prebuilt images cannot be
shared across tasks here, because each repair environment must contain its own
injected defect.

That means one image tag per task, but **not** one independent build per task.
A bank shares only a handful of distinct Dockerfile bodies, and everything before
`COPY defect/` is byte-identical within a group. The expensive layers are built
once and cached: the apt toolchain, the upstream clone at the pin, the patches,
and the verifier's whole `reference` stage. Only the defect specs are genuinely
per-task input.

What is irreducibly per-task is the verifier's `straw` stage: recompile with
*this* task's defect, rerun the graded decks, and grade the result to produce
`floor.json`. That is by design, because the floor is a per-defect quantity.
Budget roughly 1 to 2 min per task for it, once.

**Warm-up strategy:** run the full `nop` pass. `nop` does nothing inside the
container but still walks env-build, verifier-build, grade, so it warms every
image *and* serves as the full-bank nop anchor. One cost, two results.

```bash
bash scienceide_rl/eval/run_eval.sh --agent nop \
    --dataset scienceide_rl/data/mitgcm-biogeo/repair_easy/all/L1.parquet \
    --output-dir scienceide_rl/outputs/warm_biogeo \
    --skip-gpu-tasks -n 4
# expect: every by_category mean score ~= 0, errors empty
```

Keep `-n` low for the MITgcm and Athena++ envs: each episode compiles a full
scientific codebase and fans out to 4 more processes, so a high value starves the
containers' own reference runs past their timeout. See the warm section of
[`../README.md`](../../README.md).

`harbor` has no standalone build command; `--install-only` only warms the agent
environment, not the verifier, so it is not enough here.

---

## Evaluating a model

```bash
# Full baseline: 4 replicas x TP=2 over 8 GPUs, 3 attempts per task
bash scienceide_rl/eval/run_eval.sh \
    --model ${PSRL_WORKSPACE}/models/Qwen3.5-9B \
    --served-model-name qwen35-9b \
    --dataset scienceide_rl/data/mitgcm-biogeo/repair_easy/eval/L1.parquet \
    --output-dir scienceide_rl/outputs/eval_biogeo_9b \
    --replicas 4 --tp 2 -k 3 -n 4
```

`--replicas` is the endpoint count, and the eval's work queue is spread across
all of them. Endpoints come from `endpoints.json`, so `--api-base` is only needed when
pointing at a server this wrapper did not start (with `--reuse-server`).

**Set `--max-model-len` to match the checkpoint.** A window wider than the model
supports makes trials die `ContextLengthExceededError`, which is *ungraded* and so
not even a zero. Keep `--max-turns` capped (default 25) for the same reason: every
turn resends the whole transcript, so cumulative prompt tokens grow quadratically.

Thinking is left **enabled** (Qwen3's default): no `chat_template_kwargs` is
passed, so the model reasons as it would out of the box. Note this differs from
the current training script, which disables thinking, so compare curves with
that in mind.

Smoke a small slice first:

```bash
bash scienceide_rl/eval/run_eval.sh \
    --model ${PSRL_WORKSPACE}/models/Qwen3.5-9B \
    --dataset scienceide_rl/data/mitgcm-biogeo/repair_easy/eval/L1.parquet \
    --output-dir scienceide_rl/outputs/eval_smoke \
    --per-family 1 -n 3
```

### Filters

`--categories`, `--families`, `--task-glob`, `--per-family`, `--limit`. Prefer
`--per-family` over `--limit` for representative subsets: families are very
unevenly sized, so a flat head of the list is dominated by one debugging shape.
`--per-family 1` covers every (category, family, tree) group in as many tasks as
there are groups.

### Image builds behind a slow mirror

`--apt-mirror` redirects apt to the URL in
[`../config/apt-mirror-override.yaml`](../config/apt-mirror-override.yaml) during
image builds. It is **off** by default. Edit that file to point at your own mirror
before using it, and only bother where the route to `deb.debian.org` is slow: the
symptom is builds that crawl rather than fail.

---

## Where terminus-2 actually runs

The agent process runs **on the host**, in this Python process: Harbor
constructs `LiteLLM(api_base=...)` in `harbor/agents/terminus_2/terminus_2.py`
and calls it directly. Only shell commands cross into the container, through
tmux and `environment.exec()`.

This is why `network_mode = "no-network"` on every repair and implementation
task does **not** block the agent from reaching a vLLM server on the host. The
policy exists to stop the agent from `git clone`-ing the public upstream and
diffing out the answer. It constrains the container, not the harness.

---

## Output artefacts

```
<output-dir>/
  results.jsonl   one JSON per trial, appended as each batch finishes
  summary.json    overall / by_category / by_family / errors / floor_mismatch / config
  eval.log        stdout of the run
  vllm.log        server log (when the wrapper launched it)
  jobs/batch_NNN/ Harbor job dirs: agent trajectory, verifier/reward.json
```

Tasks run in batches (`--tasks-per-job`, default `n_concurrent × 4`) rather than
as one giant Job so `results.jsonl` grows incrementally. A multi-hour run that
dies partway still leaves every finished trial on disk.

`summary.json` separates model failure from harness failure. `errors` buckets
trials by `error_class`:

| bucket | meaning |
|---|---|
| `prompt_overflow` | The policy talked itself past the context window. A model-side outcome, classified with `psrl.utils.rollout.overflow.is_prompt_overflow` because neither litellm nor Harbor recognizes vLLM's wording. |
| `timeout` | The task's agent timeout fired. Harbor enforces it from outside the container. |
| `other` | Everything else, usually environment or image trouble. |

Report `by_family` and `errors` together. A baseline that cannot distinguish
"the model does not know how" from "the environment fell over" is not a baseline.
