# SciAccel-RL: Qwen3.5-9B baseline findings

Three full 144-task runs on 2026-08-30/31, plus what the trajectories and the harbor
source actually say. Written down because several plausible-sounding explanations in
here turned out to be wrong, and re-deriving them is expensive.

Artifacts under `outputs/sciaccel_rl/eval/`: `q35_v4_0830_2344` (baseline),
`q35_hardened_0831_0144` (hardened instructions), `q35_t50_0831_0244` (hardened +
50 turns + 98304 context on TP=4).

## Headline

| | baseline | hardened | **50t / 98k** |
|---|---|---|---|
| `max_turns` / `max_model_len` | 25 / 32768 | 25 / 32768 | **50 / 98304** |
| topology | 8 x TP=2 | 8 x TP=2 | **4 x TP=4** |
| delivered `.dat` | 3/144 (2%) | 13/144 (9%) | **52/144 (36%)** |
| solved (`equivalence_pass == 1`) | 1 | 2 | **7** |
| `reward_repair > 0` | 1 | 2 | **9** |
| mean `reward_repair` | 0.0069 | 0.0139 | **0.0497** (7.2x) |
| mean raw `reward` | 0.0139 | 0.0292 | **0.1528** |
| `prompt_overflow` | 44 (31%) | 49 (34%) | **0** |
| `timeout` | 1 | 1 | **0** |
| median turns | 25 (at cap) | 25 (at cap) | 50 (at cap) |

The third run reports `errors: {}`. Not one trial failed for any reason across 144.

Per category, `reward_repair`: acceleration 1.0 (1 task), repair 0.0516,
implementation 0.0239. Repair now scores 5x its baseline; implementation, which
requires writing a removed subroutine from scratch, remains much harder.

### What each change bought

- **Instruction hardening** (baseline -> hardened): delivery 2% -> 9%. The copy step
  is what it targets, and the copy-conversion rate among agents that ran the solver
  went 17/76 -> 28/58.
- **50 turns + 98304 context on TP=4** (hardened -> third run): delivery 9% -> 36%,
  solves 2 -> 7, and overflow 34% -> **0**.

**Caveat: the third run moved three variables at once** (turns, context, topology), so
the delivery and solve gains cannot be attributed between turns and context from this
data. The overflow elimination is clearly the context. A 25-turn run at 98304 would
isolate it.

### The reward distribution matters more than the mean

Raw `reward`, third run:

    below floor:  0.05->3  0.10->10  0.20->3  0.25->3  0.30->3  0.35->1   (23)
    floor:        0.50->20
    above floor:  0.60->1  0.65->1  1.00->7                               (9)
    zero:         0.00->92

The first two runs were essentially bimodal at {0, 0.5}: nothing delivered, or
delivered-but-unfixed at exactly the straw floor. Now 23 trials land strictly between
0 and the floor and 9 above it. For GRPO that is the difference between a flat reward
surface and a climbable one, and it matters more for training than the mean does.

Also note 9 clear the floor but only 7 reach full equivalence, so 2 sit in genuine
partial credit (0.60, 0.65), so the ladder is discriminating rather than pass/fail.

### Still turn-bound, with diminishing returns

Median turns is 50 with 106/124 at the cap, so the budget is still binding. But a
50-turn transcript already fills ~71k of the 98k window, so another doubling needs
another window increase, and the marginal turn is clearly worth less than the first 25
were. `mean_score` also peaked at 0.0676 around trial 74 and settled at 0.0497:
tasks are processed in sorted name order, so that is a difficulty gradient, not noise.

## Qwen3.5-9B vs Qwen3.5-35B-A3B

Same harness, same settings: hardened instructions, `max_turns` 50,
`max_model_len` 98304, 2 hosts x 2 replicas x TP=4. Artifacts in
`q35_t50_0831_0244` (9B) and `q35_35b_0831_0500` (35B).

| | 9B (144) | **35B-A3B (144)** | |
|---|---|---|---|
| delivered `.dat` | 52/144 (36%) | **99/144 (69%)** | 1.9x |
| **solved** (`equivalence_pass == 1`) | 7 (4.9%) | **40 (28%)** | **5.7x** |
| mean `reward_repair` | 0.0497 | **0.2807** | 5.6x |
| mean raw `reward` | 0.1528 | 0.4208 | 2.8x |
| errors | `{}` | `{prompt_overflow: 1}` | |
| mean turns | 48.7 | **42.5** | |
| mean seconds | 746 | 693 | |

Per category, `reward_repair`:

| | 9B | 35B-A3B |
|---|---|---|
| repair (99) | 0.0516 | **0.2850** |
| implementation (44) | 0.0239 | **0.2775** |

The 35B is ~12x better on `implementation`, which requires writing a removed
subroutine from scratch. That was the category the 9B was worst at, and it is the one
where the gap is largest.

### The distribution inverts

    raw reward     9B    35B
    0.00           92     46
    0.05-0.35      23     28
    0.50 (floor)   20     26
    0.55-0.65       2      4
    1.00            7     40

For the 9B the modal non-zero outcome is the straw floor: delivered, unfixed. For the
35B full credit (40) beats the floor (25). Both models produce a dense middle, so both
give a trainable gradient, but the 35B's mass sits at the top.

### It is not running out of budget

The 9B pinned the 50-turn cap on 85% of trials. It never finished, mean 48.7 of a
possible 50. The 35B averages 42.5 and hits the cap on roughly half its trials, so a
substantial share of its episodes terminate because the work is done. Same cap,
different relationship to it.

One 35B trial did overflow (`prompt_overflow: 1`, `n_unmeasured: 1`) against zero for
the 9B, expected, since the 35B is served with 0.66x the KV headroom. Regrade did not
recover it (`n_regraded: 0`), meaning that trial had delivered nothing before dying.

### Serving cost, measured not assumed

    Qwen3.5-9B       TP=4   18,743 blocks   299,888 KV tokens
    Qwen3.5-35B-A3B  TP=4   12,448 blocks   199,168 KV tokens   (0.66x)

The 35B has **less** KV headroom, and the reason is not what it looks like. KV per
token scales with `layers x kv_heads x head_dim`, not `hidden_size`:

    9B       layers=32  kv_heads=4  head_dim=256  ->  128 KiB/token
    35B-A3B  layers=40  kv_heads=2  head_dim=256  ->   80 KiB/token

So the 35B's cache is *cheaper* per token. The smaller budget is its MoE weights
(67 GB, 256 experts) consuming the memory the cache would otherwise use. At 98304 that
is 2.0 concurrent sequences per replica against the 9B's 3.1, the 35B wins on
capability while being served worse.

### Operational cost of MoE

First launch on a node spends ~27 minutes in flashinfer's JIT build of the CUTLASS
fused-MoE kernel: 166 nvcc processes, all TP workers serialized behind one filelock
(`flashinfer/jit/core.py:313 _poll_until_acquired`). It caches under
`~/.cache/flashinfer`, so only the first launch per node pays it, but a 1800s
readiness deadline kills the load mid-compile, which is why `wait_ready_sec` is now
4500.

## The finding that dominates everything else

Of 144 baseline trials, **141 delivered only `manifest.json`**. The reward ladder's
bottom rung is `0.0 = nothing usable`, so those scored zero for **submitting nothing**,
not for a wrong fix. The 3 that delivered are exactly the 3 that scored
`raw_reward > 0`.

So `mean_score = 0.0069` measures almost nothing about physics-repair ability. It
measures whether the agent remembered to copy files to `/logs/artifacts/`.

Stage funnel, hardened run, 143 trajectories:

| stage reached | n | |
|---|---|---|
| never ran `make` | 21 | 15% |
| built, never ran the solver | 59 | **41%** |
| ran solver, never copied | 30 | 21% |
| copied to artifacts | 33 | 23% |

In the baseline, 58 trials edited the source, compiled it, AND ran the solver, then
stopped one `cp` short of a score.

### What the instruction change did

`INSTRUCTION_REPAIR` / `INSTRUCTION_RESTORE` in
`sciaccel-rl/utils/adapters/to_harbor.py` stated the delivery contract accurately but
passively, as a location description. Now it opens with the consequence ("a correct
one-line fix that is never copied there scores 0.0, identical to no attempt"), gives
literal `mkdir`/`cp` commands per graded check, says `mkdir` alone delivers nothing,
and requires an `ls -la /logs/artifacts/*/` check before finishing.

Measured effect on the step it targets:

    ran solver -> then copied
    BASELINE   17 / 76   (22%)
    HARDENED   28 / 58   (48%)

The copy-conversion rate more than doubled. Cost: the longer instruction eats prompt
budget, so fewer agents reached the solver at all (76 -> 58) and `prompt_overflow`
rose 44 -> 49. Net positive, not free.

**Remaining gap: 31 trials ran `mkdir` and never ran `cp`** (median `mkdir` at step 16
of 26). They reserve the directory early, then die before producing output to fill it.
Delivery is still an all-or-nothing final step; copying incrementally after each check
would bank partial work, and the ladder already pays for it (`0.2 conforming` plus
per-frame credit).

## Four explanations that were wrong

Recorded because each was plausible, and three of them I asserted before checking.

**1. "Binary `.dat` dumps fill the context."** `env_chars` maxes at 84 MB and the
agent does run `head -10` on binary files. But terminus-2 caps every observation at
10,000 bytes (`_limit_output_length`, applied at all 5 call sites). Measured across
3,386 observations: max 10,201 bytes, nothing above it, 9.5% truncated. The 84 MB is
the raw tmux recording; the model never saw it.

**2. "`max_output_tokens=4096` truncated 27 trials."** `model_info.max_output_tokens`
is **never sent as a per-request `max_tokens`** on the litellm chat path. Grep across
`harbor/llms/` finds zero such call sites; it is read only by
`get_model_output_limit()` for the Responses API and by cost accounting. Measured
per-turn output was 219-549 tokens against the nominal 4096 cap, i.e. never binding.
`finish_reason == "length"` was vLLM's own `--max-model-len` boundary.

**3. "`parser_name='xml'` would salvage truncated replies."**
`salvage_truncated_response` (`terminus_xml_plain_parser.py:528`) requires **both**
`</commands>` and `</response>` in the truncated text. All 44 overflow trials end
mid-reasoning before any command block opens (e.g. `...then search for all usages of
these arrays.`), so salvage returns `None` in 44/44. Switching parsers changes nothing.

**4. "~30% of rollouts become false zeros, poisoning the RL gradient."** The
mechanism is real (see below) but the rate is not:

    BASELINE  44 overflow trials, 0 had .dat  -> regrade recovers 0
    HARDENED  49 overflow trials, 4 had .dat  -> regrade recovers 4

`reward = 0.0` for an episode that delivered nothing is the **correct** label. The
real false-zero rate is 0/144 baseline, 4/144 hardened.

## Output truncation: what actually happens

`OutputLengthExceededError` does **not** end the episode. `terminus_2.py:1113-1150`
appends the truncated text as an assistant message, appends "ERROR!! NONE of the
actions you just requested were performed because you exceeded N tokens... break it
into chunks", and recurses into `_query_llm`. So the behaviour is
truncate-inform-continue.

Two costs remain: both the truncated text and the scold stay in the transcript, so
every truncation permanently inflates context; and that recursion has no depth guard.

What *does* end the episode is `ContextLengthExceededError` (`terminus_2.py:1014`),
which re-raises immediately when `enable_summarize=False`.

## The verifier-skip gap, and regrade

Harbor's trial body is a bare sequence (`harbor/trial/single_step.py:41-52`):

    await self._run_agent()          # raises here
    await self._collect_artifacts(...)
    await self._run_verifier()       # never reached

No try/except between them, so any agent-side exception skips verification and the
trial reports an empty reward dict, no measurement at all, which `reward.py:48`
then floors to 0.0.

But `_recover_outputs()` collects artifacts even on the failure path, and harbor
supports grading exactly those via a `regrade` source job (no agent, no live
container). LAPS tasks qualify because they declare
`[verifier] environment_mode = "separate"`.

Verified end-to-end on a hardened-run trial that delivered `.dat` but had no rewards:
recovered `reward=0.5` on both checks in 39 s. (`reward_repair` stays 0.0 because 0.5
is exactly the straw floor, the ladder behaving correctly.)

Wired into both paths, on by default, skipping instantly when no `.dat` exists so no
verifier build is wasted confirming a zero:

- eval: `_regrade_unverified` in `eval/eval_sciaccel.py`, off with `--no-regrade`
- training: `_regrade_from_artifacts` in `runner.py`, off with
  `regrade_unverified=False`

Worth ~4 trials today. Its value scales with the delivery rate, so it is correctness
insurance rather than a score fix.

## Trajectory composition

Characters, hardened run. Do not read `n_input_tokens` as a length: it is the
per-turn prompt summed over turns, so it grows quadratically in turn count.

|  | graded (99) | overflow (44) |
|---|---|---|
| `prompt_chars` | 6,863 | 7,072 |
| `agent_chars` | 9,765 | 9,204 |
| `env_chars` | 169,533 | 137,323 |
| **env share** | **99.5%** | **98.3%** |

The model writes ~10 KB across 25 turns; the container returns ~170 KB. Context
pressure has essentially nothing to do with the model's verbosity.

## Turn budget and context are coupled

Estimated final-turn prompt (cumulative input is roughly linear per turn, so
final ~= 2 x mean), trials with >= 20 turns:

    median 35,537 tokens   p90 39,311   window 32,768

So at turn 25 the transcript **already exceeds** the window: the median run ends at
~108% of it. Raising `max_turns` alone just moves the overflow a couple of turns
later. The two knobs have to move together.

## Measured serving capacity

`num_gpu_blocks` read from `/metrics`, `block_size` 16, `gpu_memory_utilization` 0.9,
Qwen3.5-9B on H20:

| topology | KV tokens/replica | |
|---|---|---|
| TP=2 | 140,736 | 8,796 blocks |
| TP=4 | **299,888** | 18,743 blocks, **2.13x** |

TP=4 more than doubles KV per replica because per-GPU weights and activation reserve
halve. Fleet-wide concurrency over 16 GPUs across 2 hosts:

| topology | ctx | conc/replica | endpoints | fleet |
|---|---|---|---|---|
| 4 x TP=2 | 32768 | 4.3 | 8 | 34.4 |
| 4 x TP=2 | 65536 | 2.1 | 8 | 17.2 |
| 2 x TP=4 | 65536 | 4.6 | 4 | 18.3 |
| 2 x TP=4 | 98304 | 3.1 | 4 | 12.2 |

At small context TP=2 wins on endpoint count; at large context TP=4 wins on both
axes. Since a 50-turn run needs ~71k of window, 2 x TP=4 @ 98304 is the configuration
that makes a higher turn cap meaningful.

Note the driver of the 9B's tight budget is multimodality, not parameter count:
weights are 13.7 GiB/GPU but 89.7 of 97.9 GiB is consumed, so the vision tower and
activation reserve take most of it.

## Reward key

Use `reward_repair`, never raw `reward`. Two hardened trials scored `raw_reward = 0.5`
,  exactly the straw floor, which `reward_repair` correctly normalizes to 0. Reporting
raw would have claimed 3 successes where there was 1. `floor_mismatch` was empty in
both runs, so the ladder is wired correctly.

## Open levers, ranked

1. ~~`max_turns` 25 -> 50 with `max_model_len` 98304 on 2 x TP=4~~ **DONE.** Delivery
   9% -> 36%, solves 2 -> 7, overflow 34% -> 0. Still turn-bound at 50, but with
   diminishing returns: the transcript now fills ~71k of the 98k window, so a further
   increase needs another window increase.
2. **Copy incrementally, per check, instead of at the end.** Still the clearest
   remaining lever: 92 of 144 trials score exactly 0, and delivery is still an
   all-or-nothing final step. The ladder already pays for a partial delivery
   (`0.2 conforming` plus per-frame credit).
3. **Give the build+run recipe as one pasteable block per check.** Agents burn turns
   rediscovering `mpirun --allow-run-as-root --oversubscribe -np 4` and which deck to
   use. Cheap generator change; helps the population that builds but never runs.
4. **Isolate turns from context.** A 25-turn run at 98304 would separate the two
   contributions that the third run confounded.
5. **Larger models.** Qwen3.5-35B-A3B is MoE (256 experts, 8 active, 40 layers,
   hidden 2048). Hidden 2048 vs the 9B's 4096 means smaller KV per token, so it may
   afford *more* context despite being larger. Measure `num_gpu_blocks` before
   choosing a window.
