# Revised 24-check Docker calibration — 2026-09-07

**Calibration passed; final self-validation is still pending.** The current
suite contains 22 small numerical checks, one API check and one L20 XXZ
workload. All 24 ran once with nominal input (`-O2`), once with variant input
(`-O2`) and once with nominal input under the alternative build (`-O0`):
72 executions, not 72 different problems. Both sets of comparisons passed;
the official nominal/variant reward is **1.0**. No run failed, exceeded its
time limit or reported OOM. The only declared numerical-calibration exception
is the intentionally identical API check.

The [scalar summary](revision-calibration-20260907.json) preserves exact
per-check measurements, limiting gates, timings and record hashes.
The CLI-generated [current validation record](../pipeline/self-validation.json)
contains the full case-level grader results; it currently describes this
calibration, not a later final run.

## Two different margins

- **Independent scientific margin:** the acceptance bound divided by the
  discrepancy from an independently computed answer for the *same input*.
  The tightest is `wide-spectrum-defect / wide-single`, variant L2:
  error `2.874029768331123e-11`, bound `1e-8`, margin **347.9435×**.
- **Nominal/variant pair margin:** the comparison bound divided by the
  measured response to a two-ULP input perturbation. The tightest is
  `operator-dense-reference / scalar-shift-phase`: distance
  `3.679851863252633e-15`, bound `1e-10`, margin **27175.01×**.
  This is not an independent-reference error.

The tightest auxiliary gate is the norm of
`normalization-contract / nonunit-opt-in`, variant:
`4.440892098500626e-16` against `1e-12`, margin **2251.80×**.
For L20 there is **no independent oracle**: its pair distance is
`2.6854169361247645e-15` against `1e-9` (372381.65×).

All 24 nominal/altbuild comparisons measured zero state difference on this
host. There is consequently no finite limiting altbuild margin. This does
not make the algorithm error zero or establish a cross-platform error floor.

## Per-check measurements

N/V denote nominal/variant. State error is the maximum raw complex-component
error; L2 error is the maximum full-state error over a check's cases and times,
without global-phase alignment. Scientific margin is the minimum across all
independent scientific gates and N/V/altbuild runs; its limiting case need not
be the case with the largest absolute state error. The JSON identifies it.
All numerical rows passed their respective gates. Altbuild differences are
zero for every row and are not repeated in the table.

| Check | N / V independent state error | N / V independent L2 error | Minimum scientific margin | N/V pair distance | Pair margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| basis-extension | 1.567e-14 / 1.596e-14 | 4.831e-14 / 4.825e-14 | 2.070e4× | 3.489e-15 | 2.866e5× |
| basis-reuse | 9.018e-16 / 2.531e-15 | 2.936e-15 / 7.325e-15 | 1.365e5× | 3.211e-15 | 3.114e5× |
| doc-getting-started | 3.297e-15 / 3.316e-15 | 1.113e-14 / 1.115e-14 | 8.971e4× | 4.578e-16 | 2.185e6× |
| doc-manual-cache | 4.228e-15 / 4.228e-15 | 1.626e-14 / 1.627e-14 | 6.146e4× | 4.003e-16 | 2.498e6× |
| doc-manual-full-quench | 5.611e-15 / 5.571e-15 | 1.802e-14 / 1.801e-14 | 5.551e4× | 4.743e-16 | 2.108e6× |
| doc-manual-sector | 8.766e-15 / 4.177e-15 | 2.304e-14 / 1.345e-14 | 4.340e4× | 1.191e-14 | 8.393e4× |
| doc-matrix-free-operator | 2.968e-15 / 3.031e-15 | 9.134e-15 / 9.147e-15 | 1.093e5× | 4.743e-16 | 2.108e6× |
| doc-reference-api | 4.668e-15 / 4.638e-15 | 1.626e-14 / 1.627e-14 | 6.146e4× | 4.743e-16 | 2.108e6× |
| doc-workflow-cache | 5.539e-15 / 5.539e-15 | 1.783e-14 / 1.783e-14 | 5.608e4× | 4.003e-16 | 2.498e6× |
| doc-workflow-full-basis | 1.585e-14 / 1.573e-14 | 1.467e-13 / 1.466e-13 | 6819× | 4.099e-16 | 2.439e6× |
| doc-workflow-sector | 8.090e-15 / 2.502e-14 | 2.203e-14 / 7.066e-14 | 1.415e4× | 2.078e-14 | 4.813e4× |
| doc-workflow-sector-product | 1.729e-15 / 1.729e-15 | 3.519e-15 / 3.531e-15 | 2.832e5× | 3.724e-16 | 2.685e6× |
| docstring-timeevolve | 1.767e-14 / 1.763e-14 | 3.104e-14 / 3.106e-14 | 3.220e4× | 4.578e-16 | 2.185e6× |
| explicit-cache-inplace | 1.563e-15 / 1.195e-15 | 4.947e-15 / 4.110e-15 | 2.021e4× | 5.849e-16 | 1.710e5× |
| forward-time-rules | 1.248e-15 / 1.170e-15 | 4.577e-15 / 4.752e-15 | 2.104e5× | 7.576e-16 | 1.320e6× |
| lindblad-unitary-integration | 1.080e-15 / 1.043e-15 | 2.398e-15 / 1.308e-15 | 3.074e4× | 1.472e-15 | 6.795e4× |
| long-interval-restart | 6.006e-11 / 6.006e-11 | 3.324e-10 / 3.324e-10 | 3008× | 4.217e-15 | 3.704e8× |
| matrix-representations | 2.897e-15 / 1.945e-15 | 7.074e-15 / 6.471e-15 | 1.414e4× | 3.135e-15 | 3.190e4× |
| normalization-contract | 1.943e-15 / 2.283e-15 | 6.832e-15 / 8.186e-15 | 2252× | 1.653e-15 | 1.480e5× |
| operator-dense-reference | 2.843e-15 / 4.524e-15 | 8.440e-15 / 1.301e-14 | 7689× | 3.680e-15 | 2.718e4× |
| removed-hermitian-keyword | API only | API only | n/a | 0 (declared identical) | n/a |
| symmetry-sector | 3.264e-15 / 3.527e-15 | 7.395e-15 / 7.958e-15 | 1.257e5× | 1.356e-15 | 7.372e5× |
| wide-spectrum-defect | 7.884e-12 / 7.883e-12 | 2.874e-11 / 2.874e-11 | 347.9× | 1.267e-14 | 7.895e5× |
| xxz-quench-full-basis-l20 | no independent oracle | no independent oracle | n/a | 2.685e-15 | 3.724e5× |

All 23 numerical checks have changed active numeric inputs, changed graded
state bytes and nonzero pair distance. The small checks perturb an active
initial-state component by two ULP; L20 changes anisotropy from `0.7` to
`0.7000000000000002`. The API check intentionally has identical inputs and
does not supply numerical-noise evidence. These tiny perturbations calibrate
local numerical response, not robustness to macroscopically different inputs.

## Environment, resource enforcement and timing

Local Apple Silicon; Linux/ARM64 Docker; Julia 1.12.5 with the original
upstream Project/Manifest. All 72 runs confirmed the expected loaded source
copy and lock hashes. Julia compute/interactive threads were 1/0; BLAS used
one thread. Containers ran serially with 2 CPUs, 4 GiB memory, no extra swap
and network disabled. Python/NumPy verification ran single-threaded on the
macOS host, outside the container memory cap. The largest sampled container
memory usage was 1707 MiB, not an exact peak or a host-memory measurement.

The full controller window was **1166.807 s (19 min 26.807 s)**, including
startup, cached image builds, the three solves, host verification and record
consistency/freshness checks. This was one calibration cycle. Subsequent
report writing and read-only repository checks are not numerical run time.

| Mode | Source preparation inside checks (s) | Remaining run/JIT/output (s) | Complete solve.sh (s) |
| --- | ---: | ---: | ---: |
| nominal, `-O2` | 145.726 | 215.167 | 362.223 |
| variant, `-O2` | 138.037 | 206.893 | 346.406 |
| nominal, `-O0` | 135.071 | 247.247 | 384.365 |

The first two columns are components of the third; do not add all three.
Complete solves additionally include each round's cached image build and
driver/container overhead. L20's check
elapsed times, including its own source preparation, were 45.728 s,
45.601 s and 128.148 s respectively.

An additive accounting of the full controller window is:

| Component | Seconds |
| --- | ---: |
| Both cached image build commands | 2.524 |
| Three complete solve.sh invocations (including their cached builds) | 1092.994 |
| Official nominal/variant host verifier | 34.024 |
| Remaining selfcheck work, including altbuild host verification and record bookkeeping | 34.123 |
| Startup, image preservation, consent, consistency/freshness and controller overhead | 3.142 |
| **Total** | **1166.807** |

The stock CLI does not separately time every altbuild validator. The 34.123 s
row is the measured selfcheck total minus the recorded solves and pair
verifier, not a fabricated exact altbuild-validator duration. Sampled process
lifetimes remain in the external supervisor log. The longest recorded
nominal/variant per-check host validation was 6.500 s.

An external controller enforced a 2400 s total limit, 180 s per small check,
300 s for L20 nominal/variant, 600 s for L20 altbuild, and 60 s per host
validator. `SAB_CHECK_TIMEOUT_S=600` was only the stock driver's fallback;
the controller enforced the tighter individual limits. No scientific knob
was overridden. No container from this calibration remains running.

## Consistency and interpretation

Compared with the snapshot taken before this calibration, fixed upstream
source, inputs, check programs, Dockerfiles, locks and all acceptance settings
are unchanged. The official CLI updated only the 24 rubrics' measured
evidence fields and the two current pipeline records. The former leaf and
source copies remain preserved externally; historical reports are unchanged.
The run-root and Task copies of the CLI record match byte-for-byte. Lint,
record freshness, regenerated registry, repository validation, vendor integrity
and Harbor structure checks passed locally.

Relative to the [historical Julia 1.12.5 final scalar summary](julia125-final-validation-v1.json),
the 41 retained small numerical cases have identical N/V pair errors. Across
332 comparable independent-oracle scalar metrics, the largest absolute
change was `5.63e-15`; no material accuracy regression was observed. Oracle
evaluation has moved from the container to host NumPy, so last-bit differences
are not solely measurements of solver variation. The removed
`density-restart` case and its historical 3.05× margin are not comparable
metrics of this revision.

**Recommendation: retain all current candidate bounds and auxiliary gates.**
This calibration supports the existing packaging/accuracy objective; it does
not optimize tolerances. Earlier positive/negative restart controls remain
historical evidence, not a new faulty-solver experiment in this run. L20
continues to use the pinned implementation as reference; no independent
large-system exact solution, x86_64 execution or GPU execution was tested.
The `-O0` run changes Julia optimization level on the same host and dependency
stack; it is not a different BLAS or architecture.

The repository skill's calibration review precedes the separate final
self-validation. No final run has been performed for this revision yet.

<details>
<summary>Local evidence identifiers</summary>

- Contract fingerprint: `d2f958d38523cecc6194cc945fd4d3e96049763632eab82049f58f29f855b2cd`.
- Full external run and snapshot directory:
  `/Users/gaoqucheng/Documents/Codex_my/202609_GPU_work/revision-calibration.SU6iAku6`.
- `official-run/`: genuine driver outputs, nominal/variant reward and 24
  altbuild verifier reports; `before/`: immutable prior copies;
  `events.jsonl` and `execution.json`: controller timing/resource audit;
  `summary/summary.json`: full read-only extraction including all scalar gates.
- Portable scalar summary above records image IDs and official record hashes.

</details>
