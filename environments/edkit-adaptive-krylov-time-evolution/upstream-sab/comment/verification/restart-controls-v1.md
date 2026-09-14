# Targeted restart implementation controls

Three source versions, nominal input only, with the existing case-specific tolerances unchanged. The positive control changes projected propagation evaluation; the negative control introduces a stale restart anchor. This is neither a new nominal/variant calibration nor an optimal-tolerance study.

Same-input ED errors and baseline/candidate pair errors are separate quantities. Pair evaluation directly calls the unchanged validate.py pair_evaluate function with explicit nominal inputs; no run.ok marker is fabricated. Baseline pair self-comparison is N/A as independent evidence. Exit 1 is called a scientific rejection only when a complete finite trajectory, an observed restart, and a failed state/L2 gate are all present; crashes and timeouts are not scientific rejection evidence.

| Version | Case | L2 / component error | L2 / component caps | Science | Requirements | Pair component / pass / reason | Norm / energy error | Restarts | Check elapsed s | Classification |
|---|---|---:|---:|---|---|---|---:|---:|---:|---|
| baseline | long-grid | 3.32422e-10 / 6.00658e-11 | 1e-06 / 1e-06 | pass | pass | N/A / N/A / N/A: baseline self-comparison only, not independent agreement or repeat evidence | 1.02141e-14 / 7.96472e-14 | 1089 | 14.3634 | scientific_pass |
| baseline | nonunit-restart | 1.24424e-10 / 2.5351e-11 | 2.5e-06 / 2.5e-06 | pass | pass | N/A / N/A / N/A: baseline self-comparison only, not independent agreement or repeat evidence | 4.44089e-15 / 3.26072e-14 | 163 | 14.3634 | scientific_pass |
| positive-projected-exp | long-grid | 3.32422e-10 / 6.00576e-11 | 1e-06 / 1e-06 | pass | pass | 8.90528e-15 / pass / all components within original pair cap | 7.43849e-15 / 7.20419e-16 | 1089 | 14.6218 | scientific_pass |
| positive-projected-exp | nonunit-restart | 1.24424e-10 / 2.5343e-11 | 2.5e-06 / 2.5e-06 | pass | pass | 8.00243e-15 / pass / all components within original pair cap | 7.99361e-15 / 1.08398e-16 | 163 | 14.6218 | scientific_pass |
| negative-stale-anchor | long-grid | 1.53893 / 0.251575 | 1e-06 / 1e-06 | fail | pass | 0.251575 / fail / 2560 complex components exceed original pair cap | 3.33067e-16 / 9.63967e-16 | 1089 | 12.6442 | scientific_state_rejection |
| negative-stale-anchor | nonunit-restart | 3.48599 / 0.485526 | 2.5e-06 / 2.5e-06 | fail | pass | 0.485526 / fail / 512 complex components exceed original pair cap | 4.44089e-16 / 2.61958e-16 | 163 | 12.6442 | scientific_state_rejection |

Elapsed time is for the entire two-case check and is repeated in its two rows, not measured separately per case. The three execution times sum to 41.6294 s; the completed runner including pair verification took 41.9642 s. This is not a warmed-kernel benchmark.

The JSON also records norm/energy caps, original case-specific metrics, requirement failures, whole-check pair reasons, execution outcomes and artifact hashes. It contains no state trajectories or reference answers.

## Outcome

- Baseline passes both scientific cases: pass; pair is self-comparison only.
- Correct alternative passes both cases and pair checks: pass.
- Stale-anchor control scientifically rejected in both cases: pass.

## Limited recommendation

These targeted controls support retaining the existing L2/component caps of 1e-6 for long-grid and 2.5e-6 for nonunit-restart, with the current auxiliary gates unchanged, for human confirmation. They do not motivate tightening a tolerance and are not proof about all valid implementations or fault types.

## Scope limits

- Only nominal input was run; modified implementations' two-ULP sensitivity was not tested.
- The stale-anchor control does not establish rejection of a separate lost-amplitude bug.
- One accepted alternative and one rejected fault do not cover all valid implementations or all restart faults.
- Baseline pair data are self-comparison only, not an independent positive control or repeated-run observation.
- Only unchanged case-specific caps are reported; no optimal tolerance or new target is proposed.
- Reported restart counters come from the executed solver; source-change review is needed to establish their integrity.
- No final selfcheck, Docker repeat study, alternate build or pipeline record is produced by this summary.

[Machine-readable report](restart-controls-v1.json)
