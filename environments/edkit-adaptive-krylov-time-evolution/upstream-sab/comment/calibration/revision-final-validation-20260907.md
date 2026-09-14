# Revised 24-check final self-validation — 2026-09-07

**Final self-validation passed: reward 1.0.** The suite consists of 22 small numerical checks, one API check, and one L20 XXZ workload. Each ran once with nominal input (`-O2`), once with variant input (`-O2`), and once with nominal input under `-O0`: **72 executions of 24 checks**, not 72 distinct problems. All 24 nominal/variant comparisons and all 24 nominal/altbuild comparisons passed.

This report is extracted from the completed official run. The [scalar evidence](revision-final-validation-20260907.json) retains exact per-check values, limiting metrics, timings, source/lock confirmations, record hashes, and graded-state fingerprints. The [CLI validation record](../pipeline/self-validation.json) contains official results and nominal/variant case-level details.

## Independent accuracy versus run-to-run margins

**Independent scientific margin** compares a result to an independently computed reference for the same input. The limiting gate is `wide-spectrum-defect / wide-single` (variant, l2): 2.874e-11, margin **347.9×**.

**Nominal/variant pair margin** compares the nominal output with its two-ULP input perturbation; it is not an independent-reference error. The limiting pair is `operator-dense-reference / all states` (pair, state distance): 3.68e-15, margin **2.718e+04×**.

State errors below are maximum raw complex-component errors; L2 errors are maximum full-state errors over cases and times, without global-phase alignment. The science margin is the minimum over all independent scientific gates and all three modes; its limiting case need not have the largest absolute state error. N/V mean nominal/variant. The JSON also retains `-O0` independent errors.

| Check | N / V independent state error | N / V independent L2 error | Minimum science margin (N/V/O0) | N/V pair distance | Pair margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| basis-extension | 1.567e-14 / 1.596e-14 | 4.831e-14 / 4.825e-14 | 2.07e+04× | 3.489e-15 | 2.866e+05× |
| basis-reuse | 9.018e-16 / 2.531e-15 | 2.936e-15 / 7.325e-15 | 1.365e+05× | 3.211e-15 | 3.114e+05× |
| doc-getting-started | 3.297e-15 / 3.316e-15 | 1.113e-14 / 1.115e-14 | 8.971e+04× | 4.578e-16 | 2.185e+06× |
| doc-manual-cache | 4.228e-15 / 4.228e-15 | 1.626e-14 / 1.627e-14 | 6.146e+04× | 4.003e-16 | 2.498e+06× |
| doc-manual-full-quench | 5.611e-15 / 5.571e-15 | 1.802e-14 / 1.801e-14 | 5.551e+04× | 4.743e-16 | 2.108e+06× |
| doc-manual-sector | 8.766e-15 / 4.177e-15 | 2.304e-14 / 1.345e-14 | 4.34e+04× | 1.191e-14 | 8.393e+04× |
| doc-matrix-free-operator | 2.968e-15 / 3.031e-15 | 9.134e-15 / 9.147e-15 | 1.093e+05× | 4.743e-16 | 2.108e+06× |
| doc-reference-api | 4.668e-15 / 4.638e-15 | 1.626e-14 / 1.627e-14 | 6.146e+04× | 4.743e-16 | 2.108e+06× |
| doc-workflow-cache | 5.539e-15 / 5.539e-15 | 1.783e-14 / 1.783e-14 | 5.608e+04× | 4.003e-16 | 2.498e+06× |
| doc-workflow-full-basis | 1.585e-14 / 1.573e-14 | 1.467e-13 / 1.466e-13 | 6819× | 4.099e-16 | 2.439e+06× |
| doc-workflow-sector | 8.09e-15 / 2.502e-14 | 2.203e-14 / 7.066e-14 | 1.415e+04× | 2.078e-14 | 4.813e+04× |
| doc-workflow-sector-product | 1.729e-15 / 1.729e-15 | 3.519e-15 / 3.531e-15 | 2.832e+05× | 3.724e-16 | 2.685e+06× |
| docstring-timeevolve | 1.767e-14 / 1.763e-14 | 3.104e-14 / 3.106e-14 | 3.22e+04× | 4.578e-16 | 2.185e+06× |
| explicit-cache-inplace | 1.563e-15 / 1.195e-15 | 4.947e-15 / 4.11e-15 | 2.021e+04× | 5.849e-16 | 1.71e+05× |
| forward-time-rules | 1.248e-15 / 1.17e-15 | 4.577e-15 / 4.752e-15 | 2.104e+05× | 7.576e-16 | 1.32e+06× |
| lindblad-unitary-integration | 1.08e-15 / 1.043e-15 | 2.398e-15 / 1.308e-15 | 3.074e+04× | 1.472e-15 | 6.795e+04× |
| long-interval-restart | 6.006e-11 / 6.006e-11 | 3.324e-10 / 3.324e-10 | 3008× | 4.217e-15 | 3.704e+08× |
| matrix-representations | 2.897e-15 / 1.945e-15 | 7.074e-15 / 6.471e-15 | 1.414e+04× | 3.135e-15 | 3.19e+04× |
| normalization-contract | 1.943e-15 / 2.283e-15 | 6.832e-15 / 8.186e-15 | 2252× | 1.653e-15 | 1.48e+05× |
| operator-dense-reference | 2.843e-15 / 4.524e-15 | 8.44e-15 / 1.301e-14 | 7689× | 3.68e-15 | 2.718e+04× |
| removed-hermitian-keyword | API only | API only | n/a | 0 (declared identical) | n/a |
| symmetry-sector | 3.264e-15 / 3.527e-15 | 7.395e-15 / 7.958e-15 | 1.257e+05× | 1.356e-15 | 7.372e+05× |
| wide-spectrum-defect | 7.884e-12 / 7.883e-12 | 2.874e-11 / 2.874e-11 | 347.9× | 1.267e-14 | 7.895e+05× |
| xxz-quench-full-basis-l20 | no independent oracle | no independent oracle | n/a | 2.685e-15 | 3.724e+05× |

The `-O0`/nominal comparison measured zero state difference in **23/23 numerical checks** on this host; the API comparison passed separately. A zero measured difference is **not zero algorithm error**, and does not establish an error floor on another platform. Per-check alternative-build differences and margins are retained in the JSON.

All 23 numerical checks have changed active numeric inputs, changed graded-state bytes, and nonzero N/V pair distance. The small checks perturb an active initial-state component by two ULP; L20 perturbs anisotropy from `0.7` to `0.7000000000000002`. The intentionally identical API check supplies no numerical-noise evidence. Tiny perturbations measure local numerical response, not robustness to macroscopically different inputs.

## Comparison with the preceding calibration

Of 69 numerical run groups (23 checks × three modes), **69 have identical graded-state fingerprints** and **0 differ** from the [calibration](revision-calibration-20260907.md). The three API run groups are non-numerical exceptions, not evidence of numerical repeatability.

All retained independent-science and pair/altbuild comparison fields are identical to calibration. This is observed repeatability on the same host and stack, not cross-platform evidence.

## Environment and measured time

Local Apple Silicon, Linux/ARM64 Docker, Julia 1.12.5 with the original upstream Project/Manifest. All 72 runs confirmed the expected fresh source copy, unchanged lock hashes, Julia compute/interactive threads 1/0, and one BLAS thread. Containers ran serially with 2 CPUs, 4 GiB memory, no extra swap, and network disabled. Python/NumPy verification ran single-threaded on the macOS host, **outside the container's 4 GiB cap**.

The final controller window was **1215.289 s**. This is one final self-validation cycle; it does not include the preceding calibration or subsequent prose/Git work.

| Mode | Source preparation within checks (s) | Remaining run/JIT/output (s) | Complete solve.sh (s) |
| --- | ---: | ---: | ---: |
| nominal | 148.376 | 221.170 | 370.908 |
| variant | 147.929 | 221.554 | 371.067 |
| altbuild | 141.240 | 253.978 | 396.687 |

The first two columns are components of the third, not additional totals. `solve.sh` includes each round's cached image build and driver/container overhead; these are **not pure kernel timings**.

An additive accounting of the entire final controller window:

| Component | Seconds |
| --- | ---: |
| Two cached image-build commands before selfcheck | 4.524 |
| Three complete solve.sh invocations (including their cached builds) | 1138.662 |
| Official nominal/variant host verifier | 35.106 |
| Remaining selfcheck: altbuild grading and record bookkeeping | 33.866 |
| Startup, consent, consistency/freshness and outer controller overhead | 3.131 |
| **Total** | **1215.289** |

Remaining selfcheck is the measured `final-selfcheck` stage minus the three official solve times and the official host pair-verifier time. It is not a separately measured exact altbuild-validator duration. The controller enforced a 2400 s total ceiling, 180 s per small check, 300 s for L20 nominal/variant, 600 s for L20 altbuild, and 60 s per host validator; no failure, timeout, or OOM triggered a stop.

## Consistency and validation scope

Final self-validation started from the exact contract-file inventory at the end of calibration. Scientific settings remained unchanged: the controller confirmed unchanged upstream source, inputs, check programs, environment files, and acceptance gates, allowing only CLI-owned measured evidence/current-record updates. CLI measurement timestamps can change the raw contract fingerprint between runs. The final record matches the final Task files: the external record matches the Task copy byte-for-byte, and the controller's final freshness check passed. Earlier calibration and historical records remain separate.

L20 is compared to the pinned implementation and has **no independent large-system oracle**. Validation covers Linux/ARM64 Docker on Apple Silicon with Julia 1.12.5; **x86_64, GPU execution, and compatibility after installing additional GPU dependencies have not been validated**. `-O0` changes optimization level on the same host and dependency/BLAS stack, not architecture. The pinned upstream source is unchanged; the contribution is the runnable environment, scientific checks, and reproducible verification packaging.

Full record hashes, graded-state fingerprints, and exact limiting metrics are in the linked scalar evidence.
