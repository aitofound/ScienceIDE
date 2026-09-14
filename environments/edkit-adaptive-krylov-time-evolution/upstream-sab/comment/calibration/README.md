# Native preparation validation

This is the historical native snapshot, recorded before container calibration.
The later [first Docker calibration](docker-calibration-v1.md) passed on
2026-09-05; final human tolerance confirmation is still pending. The native
measurements below are preserved as that earlier stage's evidence.

All 23 checks completed on both nominal and perturbed inputs (46 successful native runs), and every same-input independent oracle passed. The real task pair verifier returned 23/23, reward 1.0. These are native results; Docker calibration and final tolerance confirmation remain pending.

The 22 numerical checks changed their complete state outputs under the declared two-ULP input perturbation. The rejected-keyword API check had byte-identical inputs and outputs and supplies no numerical calibration.

The largest state-evolution L2 disagreement with an independent reference was 3.32422e-10. The unchanged density-matrix integration dependency reached 1.6419e-06 in its deliberately loose forced-restart case, whose upstream L2 cap is 5e-6. These are algorithm/reference errors, not repeat-run variation.

## Environment and measured time

julia version 1.10.12; Python 3.12.14; NumPy 2.3.5 (accelerate); Darwin arm64. Julia, OpenBLAS, OpenMP and Accelerate thread limits were 1. Two produce suites partially overlapped, with at most two checks running simultaneously and a 180-second per-check watchdog.

| Input | Total seconds | Build seconds | Run excluding build seconds |
|---|---:|---:|---:|
| nominal | 283.737 | 105.444 | 178.293 |
| variant | 291.264 | 107.830 | 183.434 |

These are sums of measured per-check times, not elapsed wall time of overlapping suites. Run time includes process startup, first-use JIT, independent oracle evaluation and output I/O. Solver-call timing is stored separately in the JSON and is not a warmed-kernel speed claim.

## Per-check evidence

L2 error below is the maximum across both independently referenced input modes. Perturbation response is the largest complex component difference between nominal and variant outputs; it is a different measurement.

| Check | Maximum same-input L2 error | Perturbation response | Native oracle / pair |
|---|---:|---:|---|
| basis-extension | 4.83164e-14 | 2.3282e-15 | pass / pass |
| basis-reuse | 5.10725e-15 | 1.41008e-15 | pass / pass |
| doc-getting-started | 1.14849e-14 | 4.57757e-16 | pass / pass |
| doc-manual-cache | 1.73947e-14 | 4.00297e-16 | pass / pass |
| doc-manual-full-quench | 2.02924e-14 | 4.74287e-16 | pass / pass |
| doc-manual-sector | 1.29703e-14 | 2.0321e-15 | pass / pass |
| doc-matrix-free-operator | 8.9951e-15 | 4.74287e-16 | pass / pass |
| doc-reference-api | 1.73947e-14 | 4.74287e-16 | pass / pass |
| doc-workflow-cache | 2.02924e-14 | 4.00297e-16 | pass / pass |
| doc-workflow-full-basis | 1.46682e-13 | 3.71927e-16 | pass / pass |
| doc-workflow-sector | 6.19595e-14 | 1.0887e-14 | pass / pass |
| doc-workflow-sector-product | 2.36856e-15 | 3.7238e-16 | pass / pass |
| docstring-timeevolve | 3.2216e-14 | 4.57757e-16 | pass / pass |
| explicit-cache-inplace | 4.63166e-15 | 1.00036e-15 | pass / pass |
| forward-time-rules | 5.35178e-15 | 8.5474e-16 | pass / pass |
| lindblad-unitary-integration | 1.6419e-06 | 6.3108e-14 | pass / pass |
| long-interval-restart | 3.32422e-10 | 3.59208e-15 | pass / pass |
| matrix-representations | 6.42956e-15 | 1.86588e-15 | pass / pass |
| normalization-contract | 1.02811e-14 | 1.79882e-15 | pass / pass |
| operator-dense-reference | 9.37754e-15 | 3.12805e-15 | pass / pass |
| removed-hermitian-keyword | N/A: exact API | N/A: identical API | pass / pass |
| symmetry-sector | 7.76782e-15 | 2.60961e-15 | pass / pass |
| wide-spectrum-defect | 2.87398e-11 | 1.22355e-14 | pass / pass |

## Same-input repeat observations

Earlier direct solver probes repeated the same nominal input three times for the four checks below. The result hashes were identical for all three samples, so zero output variation was observed on this build. This is not a zero algorithm error or a cross-build error floor; the final produce-run errors above remain nonzero.

| Check | Samples | Result files |
|---|---:|---|
| long-interval-restart | 3 | All byte-identical |
| wide-spectrum-defect | 3 | All byte-identical |
| doc-workflow-full-basis | 3 | All byte-identical |
| lindblad-unitary-integration | 3 | All byte-identical |

## Native reproduction

From the task directory, configure `SAB_JULIA_BIN`, `SAB_PYTHON_BIN` and `SAB_JULIA_DEPOT` for Julia 1.10.12, Python with NumPy, and the populated dependency depot. The `python3` found on `PATH` must also be Python >=3.11 with NumPy: `tests/test.sh` invokes it directly, so setting only `SAB_PYTHON_BIN` does not replace an older macOS system Python. Set `SAB_CHECK_TIMEOUT_S=180` and use fresh output directories. The actual task driver can rerun both inputs and the pair verifier:

```bash
bash tests/test.sh produce ../../../code/edkit /path/to/fresh-nominal nominal
bash tests/test.sh produce ../../../code/edkit /path/to/fresh-variant variant
HARBOR_REFERENCE_DIR=/path/to/fresh-nominal HARBOR_CANDIDATE_DIR=/path/to/fresh-variant HARBOR_REWARD_FILE=/path/to/reward.json bash tests/test.sh
```

The JSON retains all scalar case and cross-case oracle metrics, effective scientific policy, measured times, exact input/result/log hashes, science-script and environment-file hashes, source-tree hashes, and repeat-result hashes. It excludes full states, reference matrices/outputs and private absolute paths. Runtime estimates and other bookkeeping are excluded from contract hashes. No pipeline self-validation record is written by this report.

[Machine-readable native evidence](native-validation.json)
