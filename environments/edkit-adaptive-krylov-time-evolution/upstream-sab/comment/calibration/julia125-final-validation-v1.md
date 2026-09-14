# Julia 1.12.5 upstream-lock final self-validation

Final result: **passed**, reward **1.0** (23/23 pair checks); independent same-input oracle passes **46/46**.

All existing scientific tolerances and auxiliary gates are retained, including the coarse density-restart cap of 5e-6. Upstream source, scientific programs and immutable inputs are unchanged. Julia 1.12.5 and the original upstream Project/Manifest are used in both solves.

The final CLI record and current Task files agree on fingerprint `7c7ad04861dbc00222b19759b7159c1934137760b395b465c623e699b84371ff`. The previous calibration and its raw outputs remain separate; this report does not replace them.

## Per-check final evidence

L2 error is measured against the independent dense answer for the SAME input. Scientific headroom is the reciprocal of the largest bound fraction across that check's case-specific metrics, inputs and cross-case gates. It is not the nominal/variant pair margin. The effective L2 caps below do not replace the other component, norm, energy, trace or cross-case gates retained in the JSON.

| Check | Nominal max L2 | Variant max L2 | Effective L2 cap(s) | Min science headroom | Limiting input / case / metric | Pair response | Runtime s N / V |
|---|---:|---:|---|---:|---|---:|---:|
| basis-extension | 4.77663e-14 | 4.76999e-14 | 1e-09 | 20935.3 | nominal / extended-grid / l2 | 3.48872e-15 | 14.929 / 14.1537 |
| basis-reuse | 2.92567e-15 | 7.2605e-15 | 1e-09 | 137732 | variant / reused-grid / l2 | 3.21081e-15 | 14.0318 / 13.1316 |
| doc-getting-started | 1.23059e-14 | 1.23069e-14 | 1e-09 | 81254.9 | variant / getting-started-grid / l2 | 4.57757e-16 | 14.0737 / 13.5591 |
| doc-manual-cache | 1.58372e-14 | 1.57995e-14 | 1e-09 | 63142.4 | nominal / manual-cache / l2 | 4.00297e-16 | 14.6825 / 14.6004 |
| doc-manual-full-quench | 1.67028e-14 | 1.67022e-14 | 1e-09 | 59870.2 | nominal / manual-grid / l2 | 4.74287e-16 | 18.1217 / 18.465 |
| doc-manual-sector | 2.32541e-14 | 1.34224e-14 | 1e-09 | 43003.1 | nominal / manual-sector / l2 | 1.19144e-14 | 13.3285 / 13.9876 |
| doc-matrix-free-operator | 9.87518e-15 | 9.8778e-15 | 1e-09 | 101237 | variant / matrix-free-grid / l2 | 4.74287e-16 | 15.1345 / 15.8505 |
| doc-reference-api | 1.58372e-14 | 1.57995e-14 | 1e-09 | 63142.4 | nominal / reference-grid / l2 | 4.74287e-16 | 17.2486 / 17.9986 |
| doc-workflow-cache | 1.65889e-14 | 1.65979e-14 | 1e-09 | 60248.7 | variant / workflow-cache / l2 | 4.00297e-16 | 14.9068 / 15.1959 |
| doc-workflow-full-basis | 1.46329e-13 | 1.46323e-13 | 1e-09 | 6833.92 | nominal / workflow-full-grid / l2 | 4.09924e-16 | 16.2094 / 16.4942 |
| doc-workflow-sector | 2.17881e-14 | 7.08327e-14 | 1e-09 | 14117.8 | variant / workflow-sector-grid / l2 | 2.07787e-14 | 13.9586 / 14.0156 |
| doc-workflow-sector-product | 3.67479e-15 | 3.65366e-15 | 1e-09 | 272124 | nominal / sector-product / l2 | 3.7238e-16 | 13.2727 / 14.4707 |
| docstring-timeevolve | 2.54937e-14 | 2.54556e-14 | 1e-09 | 39225.4 | nominal / docstring-grid / l2 | 4.57757e-16 | 17.5706 / 18.081 |
| explicit-cache-inplace | 5.1179e-15 | 4.45828e-15 | 1e-10 | 19539.3 | nominal / cache-sequential / l2 | 5.84887e-16 | 13.5491 / 13.4532 |
| forward-time-rules | 4.31794e-15 | 4.47307e-15 | 1e-09 | 223560 | variant / sorted / l2 | 7.5758e-16 | 13.7771 / 13.852 |
| lindblad-unitary-integration | 1.6419e-06 | 1.6419e-06 | density-single, unitary-state, density-grid: 1e-10; density-restart: 5e-06 | 3.04525 | variant / density-restart / l2 | 8.95346e-14 | 15.1617 / 15.1312 |
| long-interval-restart | 3.32422e-10 | 3.32422e-10 | long-grid: 1e-06; nonunit-restart: 2.5e-06 | 3008.22 | nominal / long-grid / l2 | 4.21739e-15 | 14.5236 / 14.3493 |
| matrix-representations | 7.59913e-15 | 6.75682e-15 | 1e-10 | 13159.4 | nominal / hermitian / l2 | 3.13516e-15 | 13.5646 / 13.8052 |
| normalization-contract | 6.90069e-15 | 8.19575e-15 | default-normalized-input, opt-in-normalized-input, nonunit-opt-in, analytic-diagonal: 1e-10; nonunit-default: 2.5e-10 | 2251.8 | variant / nonunit-opt-in / norm | 1.65251e-15 | 13.8333 / 14.2475 |
| operator-dense-reference | 8.56383e-15 | 1.28062e-14 | 1e-10 | 7808.72 | variant / time-grid / l2 | 3.67985e-15 | 13.3512 / 13.686 |
| removed-hermitian-keyword | N/A | N/A | N/A | N/A | N/A | N/A | 12.2576 / 12.3354 |
| symmetry-sector | 7.23455e-15 | 7.80178e-15 | 1e-09 | 128176 | variant / sector-times / l2 | 1.35641e-15 | 14.4204 / 13.8627 |
| wide-spectrum-defect | 2.87387e-11 | 2.87403e-11 | 1e-08 | 347.944 | variant / wide-single / l2 | 1.26666e-14 | 13.3651 / 13.8508 |

Pair response is the maximum complex-component difference between nominal and perturbed outputs, after changing one active input component by the declared two binary64 ULP. It measures input sensitivity, not error against the exact solution and not same-input roundoff noise. All 22 numerical checks respond; the one declared identical API check has no numerical L2 error, cap or scientific headroom.

The stock review renderer may display a dash for spread because its dictionary reader expects a different field name for a stamped override. The final record retains the numerical spread under value; the table above recomputes it from raw outputs and verifies it against the reward record. The only override is the 180 s watchdog, not a scientific parameter.

## Case-level L2 bounds and errors

| Check / case | Nominal L2 | Variant L2 | Absolute cap | Relative cap | Case min science headroom | Limiting input / metric |
|---|---:|---:|---:|---:|---:|---|
| basis-extension / extended-grid | 4.77663e-14 | 4.76999e-14 | 1e-09 | 0 | 20935.3 | nominal / extended-grid / l2 |
| basis-reuse / reused-grid | 2.92567e-15 | 7.2605e-15 | 1e-09 | 0 | 137732 | variant / reused-grid / l2 |
| doc-getting-started / getting-started-grid | 1.23059e-14 | 1.23069e-14 | 1e-09 | 0 | 81254.9 | variant / getting-started-grid / l2 |
| doc-getting-started / getting-started-single | 6.17007e-15 | 6.15949e-15 | 1e-09 | 0 | 162073 | nominal / getting-started-single / l2 |
| doc-manual-cache / manual-cache | 1.58372e-14 | 1.57995e-14 | 1e-09 | 0 | 63142.4 | nominal / manual-cache / l2 |
| doc-manual-full-quench / manual-grid | 1.67028e-14 | 1.67022e-14 | 1e-09 | 0 | 59870.2 | nominal / manual-grid / l2 |
| doc-manual-full-quench / manual-single | 7.42216e-15 | 7.45921e-15 | 1e-09 | 0 | 134062 | variant / manual-single / l2 |
| doc-manual-sector / manual-sector | 2.32541e-14 | 1.34224e-14 | 1e-09 | 0 | 43003.1 | nominal / manual-sector / l2 |
| doc-matrix-free-operator / matrix-free-grid | 9.87518e-15 | 9.8778e-15 | 1e-09 | 0 | 101237 | variant / matrix-free-grid / l2 |
| doc-reference-api / reference-grid | 1.58372e-14 | 1.57995e-14 | 1e-09 | 0 | 63142.4 | nominal / reference-grid / l2 |
| doc-reference-api / reference-single | 7.42216e-15 | 7.45921e-15 | 1e-09 | 0 | 134062 | variant / reference-single / l2 |
| doc-workflow-cache / workflow-cache | 1.65889e-14 | 1.65979e-14 | 1e-09 | 0 | 60248.7 | variant / workflow-cache / l2 |
| doc-workflow-full-basis / workflow-full-grid | 1.46329e-13 | 1.46323e-13 | 1e-09 | 0 | 6833.92 | nominal / workflow-full-grid / l2 |
| doc-workflow-sector / workflow-sector-grid | 2.17881e-14 | 7.08327e-14 | 1e-09 | 0 | 14117.8 | variant / workflow-sector-grid / l2 |
| doc-workflow-sector-product / sector-product | 3.67479e-15 | 3.65366e-15 | 1e-09 | 0 | 272124 | nominal / sector-product / l2 |
| docstring-timeevolve / docstring-grid | 2.54937e-14 | 2.54556e-14 | 1e-09 | 0 | 39225.4 | nominal / docstring-grid / l2 |
| docstring-timeevolve / docstring-single | 9.78128e-15 | 9.81316e-15 | 1e-09 | 0 | 101904 | variant / docstring-single / l2 |
| explicit-cache-inplace / cache-sequential | 5.1179e-15 | 4.45828e-15 | 1e-10 | 0 | 19539.3 | nominal / cache-sequential / l2 |
| explicit-cache-inplace / inplace-single | 3.67589e-15 | 2.70193e-15 | 1e-10 | 0 | 27204.3 | nominal / inplace-single / l2 |
| forward-time-rules / cache-duplicates | 2.12313e-15 | 2.43423e-15 | 1e-09 | 0 | 410807 | variant / cache-duplicates / l2 |
| forward-time-rules / duplicate-times | 2.12313e-15 | 2.43423e-15 | 1e-09 | 0 | 410807 | variant / duplicate-times / l2 |
| forward-time-rules / rejections | N/A | N/A | N/A | N/A | N/A | N/A |
| forward-time-rules / shuffled | 4.31794e-15 | 4.47307e-15 | 1e-09 | 0 | 223560 | variant / shuffled / l2 |
| forward-time-rules / sorted | 4.31794e-15 | 4.47307e-15 | 1e-09 | 0 | 223560 | variant / sorted / l2 |
| lindblad-unitary-integration / density-grid | 2.52154e-15 | 1.48351e-15 | 1e-10 | 0 | 39658.3 | nominal / density-grid / l2 |
| lindblad-unitary-integration / density-restart | 1.6419e-06 | 1.6419e-06 | 5e-06 | 0 | 3.04525 | variant / density-restart / l2 |
| lindblad-unitary-integration / density-single | 2.52274e-15 | 1.27094e-15 | 1e-10 | 0 | 39639.4 | nominal / density-single / l2 |
| lindblad-unitary-integration / unitary-state | 1.38833e-15 | 1.29056e-15 | 1e-10 | 0 | 72028.8 | nominal / unitary-state / l2 |
| long-interval-restart / long-grid | 3.32422e-10 | 3.32422e-10 | 1e-06 | 0 | 3008.22 | nominal / long-grid / l2 |
| long-interval-restart / nonunit-restart | 1.24424e-10 | 1.24424e-10 | 2.5e-06 | 0 | 20092.5 | variant / nonunit-restart / l2 |
| matrix-representations / dense | 5.89607e-15 | 6.75682e-15 | 1e-10 | 0 | 14799.9 | variant / dense / l2 |
| matrix-representations / hermitian | 7.59913e-15 | 6.26271e-15 | 1e-10 | 0 | 13159.4 | nominal / hermitian / l2 |
| matrix-representations / sparse | 6.60232e-15 | 6.34493e-15 | 1e-10 | 0 | 15146.2 | nominal / sparse / l2 |
| normalization-contract / analytic-diagonal | 2.42365e-16 | 2.83052e-16 | 1e-10 | 0 | 300240 | variant / analytic-diagonal / norm |
| normalization-contract / default-normalized-input | 3.20892e-15 | 2.75415e-15 | 1e-10 | 0 | 31163.2 | nominal / default-normalized-input / l2 |
| normalization-contract / nonunit-default | 6.90069e-15 | 8.19575e-15 | 2.5e-10 | 0 | 30503.6 | variant / nonunit-default / l2 |
| normalization-contract / nonunit-opt-in | 2.59406e-15 | 3.27686e-15 | 1e-10 | 0 | 2251.8 | variant / nonunit-opt-in / norm |
| normalization-contract / opt-in-normalized-input | 3.05779e-15 | 2.75415e-15 | 1e-10 | 0 | 9007.2 | nominal / opt-in-normalized-input / norm |
| operator-dense-reference / scalar-shift-phase | 8.14964e-15 | 6.30671e-15 | 1e-10 | 0 | 12270.5 | nominal / scalar-shift-phase / l2 |
| operator-dense-reference / single-times | 6.96679e-15 | 1.19284e-14 | 1e-10 | 0 | 8383.38 | variant / single-times / l2 |
| operator-dense-reference / time-grid | 8.56383e-15 | 1.28062e-14 | 1e-10 | 0 | 7808.72 | variant / time-grid / l2 |
| removed-hermitian-keyword / removed-keyword | N/A | N/A | N/A | N/A | N/A | N/A |
| symmetry-sector / sector-times | 7.23455e-15 | 7.80178e-15 | 1e-09 | 0 | 128176 | variant / sector-times / l2 |
| wide-spectrum-defect / wide-grid | 2.04825e-11 | 2.04827e-11 | 1e-08 | 0 | 488.217 | variant / wide-grid / l2 |
| wide-spectrum-defect / wide-single | 2.87387e-11 | 2.87403e-11 | 1e-08 | 0 | 347.944 | variant / wide-single / l2 |

## One same-environment confirmation

Compared with the preceding Julia 1.12.5 calibration, the maximum same-input full-state L2 difference over all recorded states is 0. Maximum L2-error changes and per-case state differences are retained in JSON. This compares the prior calibration with this final run: one confirmation pair per input, not a repeated-run ensemble or an estimate of general numerical fluctuations.

## Time and identity

Build plus final selfcheck took 685.796 s against the 1200 s limit. build: 4.52258 s; final: 681.13 s.

Slowest recorded check: doc-manual-full-quench / variant, 18.465 s, below the 180 s watchdog. Check time includes fresh-process startup, source preparation, JIT, oracle work and I/O; it is not a warmed solver benchmark.

Both actual solve containers were inspected as network none, 2 CPUs, 4 GiB memory and 4 GiB total memory-plus-swap (no extra swap). All 46 logs verify Julia 1.12.5, one Julia compute thread, zero interactive threads, one BLAS thread, a fresh source/Project/depot overlay, and the original Project/Manifest hashes. Raw records, logs and results are checksum-bound in JSON.

## Contribution and limits

The contribution is a reproducible environment and verification package for one existing upstream module: 23 official-test/example-derived checks, immutable nominal/perturbed fixtures, full-state independent dense-reference gates, auxiliary physical checks and auditable runtime evidence. EDKit's adaptive Krylov algorithm and existing tests are upstream work, not a new algorithm or new scientific result from this package.

This final validation establishes that the pinned reference implementation passes this suite in the tested local CPU arm64 environment. It adds no alternate build, cross-platform or GPU validation, candidate optimization, fault-injection expansion, broad perturbation survey, speedup measurement or tolerance optimization. Previous limited positive/negative controls remain separate historical evidence. Passing does not establish every input, implementation or failure mode.

[Machine-readable final evidence](julia125-final-validation-v1.json)
