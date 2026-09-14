# Julia 1.12.5 upstream-lock Docker recalibration

This is the first complete calibration after an authorized environment migration, not the final self-validation. Upstream source, scientific programs, fixtures, numerical tolerances and auxiliary gates are unchanged. Earlier Julia 1.10 validation is retained separately and is not evidence of final validation for this environment.

Result: passed; independent same-input oracle passes 46/46; pair reward 1.0 (23/23).

Each same-input L2 error compares a computed state with its independent dense reference for that actual input. Scientific headroom is the reciprocal of the largest bound fraction across the SAME case/metric/input and cross-case gates. API-only exact outcomes have no numerical headroom. Pair response instead compares nominal with variant; it is not an algorithm error or a same-input repeatability estimate.

## Old versus new (maximum over nominal and variant)

| Check | Old max L2 | New max L2 | Old min science headroom | New min science headroom | New limiting location | New pair response |
|---|---:|---:|---:|---:|---|---:|
| basis-extension | 4.77997e-14 | 4.77663e-14 | 20920.6 | 20935.3 | nominal / extended-grid / l2 | 3.48872e-15 |
| basis-reuse | 4.85766e-15 | 7.2605e-15 | 205861 | 137732 | variant / reused-grid / l2 | 3.21081e-15 |
| doc-getting-started | 1.30425e-14 | 1.23069e-14 | 76672.3 | 81254.9 | variant / getting-started-grid / l2 | 4.57757e-16 |
| doc-manual-cache | 1.7119e-14 | 1.58372e-14 | 58414.6 | 63142.4 | nominal / manual-cache / l2 | 4.00297e-16 |
| doc-manual-full-quench | 1.91759e-14 | 1.67028e-14 | 52148.9 | 59870.2 | nominal / manual-grid / l2 | 4.74287e-16 |
| doc-manual-sector | 1.35207e-14 | 2.32541e-14 | 73960.4 | 43003.1 | nominal / manual-sector / l2 | 1.19144e-14 |
| doc-matrix-free-operator | 9.19933e-15 | 9.8778e-15 | 108704 | 101237 | variant / matrix-free-grid / l2 | 4.74287e-16 |
| doc-reference-api | 1.7119e-14 | 1.58372e-14 | 58414.6 | 63142.4 | nominal / reference-grid / l2 | 4.74287e-16 |
| doc-workflow-cache | 1.91759e-14 | 1.65979e-14 | 52148.9 | 60248.7 | variant / workflow-cache / l2 | 4.00297e-16 |
| doc-workflow-full-basis | 1.46362e-13 | 1.46329e-13 | 6832.35 | 6833.92 | nominal / workflow-full-grid / l2 | 4.09924e-16 |
| doc-workflow-sector | 6.20835e-14 | 7.08327e-14 | 16107.3 | 14117.8 | variant / workflow-sector-grid / l2 | 2.07787e-14 |
| doc-workflow-sector-product | 2.8831e-15 | 3.67479e-15 | 346849 | 272124 | nominal / sector-product / l2 | 3.7238e-16 |
| docstring-timeevolve | 2.74843e-14 | 2.54937e-14 | 36384.4 | 39225.4 | nominal / docstring-grid / l2 | 4.57757e-16 |
| explicit-cache-inplace | 4.95313e-15 | 5.1179e-15 | 20189.3 | 19539.3 | nominal / cache-sequential / l2 | 5.84887e-16 |
| forward-time-rules | 5.1367e-15 | 4.47307e-15 | 194677 | 223560 | variant / sorted / l2 | 7.5758e-16 |
| lindblad-unitary-integration | 1.6419e-06 | 1.6419e-06 | 3.04525 | 3.04525 | variant / density-restart / l2 | 8.95346e-14 |
| long-interval-restart | 3.32422e-10 | 3.32422e-10 | 3008.23 | 3008.22 | nominal / long-grid / l2 | 4.21739e-15 |
| matrix-representations | 6.40624e-15 | 7.59913e-15 | 15609.8 | 13159.4 | nominal / hermitian / l2 | 3.13516e-15 |
| normalization-contract | 1.01112e-14 | 8.19575e-15 | 2251.8 | 2251.8 | variant / nonunit-opt-in / norm | 1.65251e-15 |
| operator-dense-reference | 9.42843e-15 | 1.28062e-14 | 10606.2 | 7808.72 | variant / time-grid / l2 | 3.67985e-15 |
| removed-hermitian-keyword | N/A | N/A | N/A | N/A | N/A | N/A |
| symmetry-sector | 7.75766e-15 | 7.80178e-15 | 128905 | 128176 | variant / sector-times / l2 | 1.35641e-15 |
| wide-spectrum-defect | 2.87398e-11 | 2.87403e-11 | 347.95 | 347.944 | variant / wide-single / l2 | 1.26666e-14 |

## Effective case-specific bounds and errors

Density-matrix integration is kept separate from state evolution. The coarse density-restart case keeps its original settings and its own original cap.

| Check / case | Nominal L2 | Variant L2 | Case min science headroom | Limiting input / metric |
|---|---:|---:|---:|---|
| basis-extension / extended-grid | 4.77663e-14 | 4.76999e-14 | 20935.3 | nominal / extended-grid / l2 |
| basis-reuse / reused-grid | 2.92567e-15 | 7.2605e-15 | 137732 | variant / reused-grid / l2 |
| doc-getting-started / getting-started-grid | 1.23059e-14 | 1.23069e-14 | 81254.9 | variant / getting-started-grid / l2 |
| doc-getting-started / getting-started-single | 6.17007e-15 | 6.15949e-15 | 162073 | nominal / getting-started-single / l2 |
| doc-manual-cache / manual-cache | 1.58372e-14 | 1.57995e-14 | 63142.4 | nominal / manual-cache / l2 |
| doc-manual-full-quench / manual-grid | 1.67028e-14 | 1.67022e-14 | 59870.2 | nominal / manual-grid / l2 |
| doc-manual-full-quench / manual-single | 7.42216e-15 | 7.45921e-15 | 134062 | variant / manual-single / l2 |
| doc-manual-sector / manual-sector | 2.32541e-14 | 1.34224e-14 | 43003.1 | nominal / manual-sector / l2 |
| doc-matrix-free-operator / matrix-free-grid | 9.87518e-15 | 9.8778e-15 | 101237 | variant / matrix-free-grid / l2 |
| doc-reference-api / reference-grid | 1.58372e-14 | 1.57995e-14 | 63142.4 | nominal / reference-grid / l2 |
| doc-reference-api / reference-single | 7.42216e-15 | 7.45921e-15 | 134062 | variant / reference-single / l2 |
| doc-workflow-cache / workflow-cache | 1.65889e-14 | 1.65979e-14 | 60248.7 | variant / workflow-cache / l2 |
| doc-workflow-full-basis / workflow-full-grid | 1.46329e-13 | 1.46323e-13 | 6833.92 | nominal / workflow-full-grid / l2 |
| doc-workflow-sector / workflow-sector-grid | 2.17881e-14 | 7.08327e-14 | 14117.8 | variant / workflow-sector-grid / l2 |
| doc-workflow-sector-product / sector-product | 3.67479e-15 | 3.65366e-15 | 272124 | nominal / sector-product / l2 |
| docstring-timeevolve / docstring-grid | 2.54937e-14 | 2.54556e-14 | 39225.4 | nominal / docstring-grid / l2 |
| docstring-timeevolve / docstring-single | 9.78128e-15 | 9.81316e-15 | 101904 | variant / docstring-single / l2 |
| explicit-cache-inplace / cache-sequential | 5.1179e-15 | 4.45828e-15 | 19539.3 | nominal / cache-sequential / l2 |
| explicit-cache-inplace / inplace-single | 3.67589e-15 | 2.70193e-15 | 27204.3 | nominal / inplace-single / l2 |
| forward-time-rules / cache-duplicates | 2.12313e-15 | 2.43423e-15 | 410807 | variant / cache-duplicates / l2 |
| forward-time-rules / duplicate-times | 2.12313e-15 | 2.43423e-15 | 410807 | variant / duplicate-times / l2 |
| forward-time-rules / rejections | N/A | N/A | N/A | N/A |
| forward-time-rules / shuffled | 4.31794e-15 | 4.47307e-15 | 223560 | variant / shuffled / l2 |
| forward-time-rules / sorted | 4.31794e-15 | 4.47307e-15 | 223560 | variant / sorted / l2 |
| lindblad-unitary-integration / density-grid | 2.52154e-15 | 1.48351e-15 | 39658.3 | nominal / density-grid / l2 |
| lindblad-unitary-integration / density-restart | 1.6419e-06 | 1.6419e-06 | 3.04525 | variant / density-restart / l2 |
| lindblad-unitary-integration / density-single | 2.52274e-15 | 1.27094e-15 | 39639.4 | nominal / density-single / l2 |
| lindblad-unitary-integration / unitary-state | 1.38833e-15 | 1.29056e-15 | 72028.8 | nominal / unitary-state / l2 |
| long-interval-restart / long-grid | 3.32422e-10 | 3.32422e-10 | 3008.22 | nominal / long-grid / l2 |
| long-interval-restart / nonunit-restart | 1.24424e-10 | 1.24424e-10 | 20092.5 | variant / nonunit-restart / l2 |
| matrix-representations / dense | 5.89607e-15 | 6.75682e-15 | 14799.9 | variant / dense / l2 |
| matrix-representations / hermitian | 7.59913e-15 | 6.26271e-15 | 13159.4 | nominal / hermitian / l2 |
| matrix-representations / sparse | 6.60232e-15 | 6.34493e-15 | 15146.2 | nominal / sparse / l2 |
| normalization-contract / analytic-diagonal | 2.42365e-16 | 2.83052e-16 | 300240 | variant / analytic-diagonal / norm |
| normalization-contract / default-normalized-input | 3.20892e-15 | 2.75415e-15 | 31163.2 | nominal / default-normalized-input / l2 |
| normalization-contract / nonunit-default | 6.90069e-15 | 8.19575e-15 | 30503.6 | variant / nonunit-default / l2 |
| normalization-contract / nonunit-opt-in | 2.59406e-15 | 3.27686e-15 | 2251.8 | variant / nonunit-opt-in / norm |
| normalization-contract / opt-in-normalized-input | 3.05779e-15 | 2.75415e-15 | 9007.2 | nominal / opt-in-normalized-input / norm |
| operator-dense-reference / scalar-shift-phase | 8.14964e-15 | 6.30671e-15 | 12270.5 | nominal / scalar-shift-phase / l2 |
| operator-dense-reference / single-times | 6.96679e-15 | 1.19284e-14 | 8383.38 | variant / single-times / l2 |
| operator-dense-reference / time-grid | 8.56383e-15 | 1.28062e-14 | 7808.72 | variant / time-grid / l2 |
| removed-hermitian-keyword / removed-keyword | N/A | N/A | N/A | N/A |
| symmetry-sector / sector-times | 7.23455e-15 | 7.80178e-15 | 128176 | variant / sector-times / l2 |
| wide-spectrum-defect / wide-grid | 2.04825e-11 | 2.04827e-11 | 488.217 | variant / wide-grid / l2 |
| wide-spectrum-defect / wide-single | 2.87387e-11 | 2.87403e-11 | 347.944 | variant / wide-single / l2 |

## Execution and integrity

Measured build plus complete calibration: 961.239 s (limit 1200 s). Each check had a 180 s timeout. Measured stages: build 275 s; calibration 686.091 s.

The recorded solve containers use 2 CPUs, 4 GiB and network none. All 46 scientific processes report Julia 1.12.5, one computation thread, zero interactive threads, one BLAS thread, their fresh source copy and the original Project/Manifest SHA-256 hashes. Each uses a fresh writable depot overlay followed by the image-baked Julia 1.12.5 depot.

Numerical checks with changed nominal/variant states: 22/22. The declared identical API check is not counted as numerical-noise evidence.

## Limits and next decision

The CLI recorded `SAB_CHECK_TIMEOUT_S=180` as the sole execution override;
this is a safety watchdog, not a changed scientific input or numerical knob.
Its stamped override metadata was retained rather than erased.

After this completed calibration, the 23 check READMEs received only a
runtime-version sentence correction from Julia 1.10.12 to Julia 1.12.5 with
the upstream lock files. The calibrated tree is preserved separately.
The JSON and original CLI record bind the calibration-time contract;
current freshness is therefore stale due only to those prose corrections,
pending the separately approved final selfcheck. Source, runtime scripts,
inputs, scientific code, tolerances and auxiliary gates were not changed
after this calibration.

Only one nominal and one variant solve were run. This is no repeated-run noise study, alternative-build floor, fault-injection extension, speedup measurement, or tolerance optimization. Old-versus-new state differences include Julia and locked dependency changes; tiny roundoff-level changes should not be interpreted as improved accuracy. Passing these checks is not a proof of all inputs or all valid implementations.

Retain the existing tolerances and auxiliary gates as the candidate policy, pending the user decision. A separate final self-validation must wait for that confirmation. No final-validation claim is made here.

[Machine-readable calibration](julia125-calibration-v1.json)
