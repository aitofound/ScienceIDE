# Final Docker self-validation

The completed official CLI run recorded result `passed` and reward 1.0 (23/23 checks). This final nominal/variant selfcheck uses the human-confirmed tolerances and auxiliary gates. Their numerical policy is unchanged from the first calibration.

The current task fingerprint is `8b84b0b1757f53010faa59781adfaea7f61ffbe728f067ec587c624ac5e96b8c` and matches this final CLI record. The first-calibration numerical policy comparison passed for all 23 checks; this report does not overwrite historical calibration evidence.

Same-input errors below compare each run with its independently constructed ED answer for that exact input. Pair perturbation compares nominal with variant. These measurements have different meanings.

Scientific headroom is the reciprocal of the largest recorded bound fraction across that check's own case, metric and input combinations, including cross-case gates. Every fraction is associated with its actual case-specific bound. It is not an aggregate maximum error divided by an unrelated cap. Exact API outcomes have no numerical headroom.

22 of 22 numerical checks changed their complete-state outputs under the declared input perturbation. The `removed-hermitian-keyword` check has declared identical API inputs/outcomes and provides no numerical-noise calibration; its numerical errors and headroom are N/A.

## Observed container environment

The following software/base-environment information is inherited from the earlier read-only probe of the same pinned environment, not a new probe during this final run. The existing Bookworm label/digest mismatch was not edited. The running image IDs in JSON come from this final CLI run's new oracle manifests, not from the earlier image tags.

- actual os: Debian GNU/Linux 13 (trixie), DEBIAN_VERSION_FULL=13.1
- julia: 1.10.12
- python: 3.13.5 (GCC 14.2.0)
- numpy: 2.2.4
- blas lapack: NumPy reports BLAS and LAPACK 3.12.1
- architecture: linux/arm64 (aarch64), local Apple Silicon CPU
- kernel: 7.0.12-linuxkit
- base label discrepancy: Both existing Dockerfiles say debian:bookworm-slim@sha256:1caf1c703c8f7e15dcf2e7769b35000c764e6f50e4d7401c355fb0248f3ddfdb, but the pinned digest actually contains Debian 13 trixie. The existing digest and Dockerfiles were not changed for this calibration.
- inspection note: Read-only version probe in the built oracle image used an overridden /bin/sh entrypoint, not the scientific suite. It exited 0. numpy.show_config emitted only an optional PyYAML formatting warning. Actual solve image IDs must be taken from CLI manifests, since cached rebuilds may change OCI attestation/index IDs.

The final run's two saved solve-build logs contain the same platform manifest and image configuration digests. Any attestation/OCI index differences do not constitute an alternative scientific build. The runtime manifest records remain the authority for each solve's image ID.

## Per-check scientific and perturbation evidence

| Check | Nominal L2 error | Variant L2 error | Component error (max) | Norm error (max) | Energy error (max) | Min science headroom | Pair perturbation | Pair headroom |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| basis-extension | 4.77997e-14 | 4.77673e-14 | 1.5006e-14 | 8.88178e-16 | 3.17801e-15 | 20920.6 | 2.3282e-15 | 429516 |
| basis-reuse | 4.85766e-15 | 3.61674e-15 | 1.69602e-15 | 1.77636e-15 | 1.66543e-15 | 205861 | 1.41008e-15 | 709179 |
| doc-getting-started | 1.30425e-14 | 1.30347e-14 | 4.72569e-15 | 1.9984e-15 | 9.11182e-15 | 76672.3 | 4.57757e-16 | 2.18457e+06 |
| doc-manual-cache | 1.7119e-14 | 1.71168e-14 | 6.84233e-15 | 4.44089e-15 | 7.10545e-15 | 58414.6 | 4.00297e-16 | 2.49815e+06 |
| doc-manual-full-quench | 1.91244e-14 | 1.91759e-14 | 6.92926e-15 | 4.66294e-15 | 8.88329e-15 | 52148.9 | 4.74287e-16 | 2.10843e+06 |
| doc-manual-sector | 1.25863e-14 | 1.35207e-14 | 3.45376e-15 | 8.88178e-16 | 1.28248e-14 | 73960.4 | 2.0321e-15 | 492102 |
| doc-matrix-free-operator | 9.19832e-15 | 9.19933e-15 | 2.1339e-15 | 6.66134e-16 | 6.88426e-15 | 108704 | 4.74287e-16 | 2.10843e+06 |
| doc-reference-api | 1.7119e-14 | 1.71168e-14 | 6.92926e-15 | 4.66294e-15 | 8.88329e-15 | 58414.6 | 4.74287e-16 | 2.10843e+06 |
| doc-workflow-cache | 1.91244e-14 | 1.91759e-14 | 4.02293e-15 | 4.44089e-15 | 8.22423e-15 | 52148.9 | 4.00297e-16 | 2.49815e+06 |
| doc-workflow-full-basis | 1.46362e-13 | 1.46309e-13 | 1.6053e-14 | 1.11022e-15 | 2.05392e-15 | 6832.35 | 3.71927e-16 | 2.6887e+06 |
| doc-workflow-sector | 3.36675e-14 | 6.20835e-14 | 2.24174e-14 | 1.05471e-14 | 8.51541e-14 | 16107.3 | 1.0887e-14 | 91852.7 |
| doc-workflow-sector-product | 2.8831e-15 | 2.78162e-15 | 1.44755e-15 | 3.33067e-16 | 6.69623e-16 | 346849 | 3.7238e-16 | 2.68543e+06 |
| docstring-timeevolve | 2.74843e-14 | 2.74602e-14 | 1.31164e-14 | 6.66134e-16 | 7.9937e-15 | 36384.4 | 4.57757e-16 | 2.18457e+06 |
| explicit-cache-inplace | 4.12659e-15 | 4.95313e-15 | 1.4524e-15 | 8.88178e-16 | 1.32937e-15 | 20189.3 | 1.00036e-15 | 99963.8 |
| forward-time-rules | 4.59229e-15 | 5.1367e-15 | 1.46647e-15 | 6.66134e-16 | 2.25516e-15 | 194677 | 8.5474e-16 | 1.16995e+06 |
| lindblad-unitary-integration | 1.6419e-06 | 1.6419e-06 | 8.19169e-07 | 6.63913e-13 | 1.53727e-14 | 3.04525 | 1.0289e-13 | 55259.7 |
| long-interval-restart | 3.32422e-10 | 3.32422e-10 | 6.00658e-11 | 1.02141e-14 | 1.01711e-13 | 3008.23 | 3.59208e-15 | 2.87266e+08 |
| matrix-representations | 6.40624e-15 | 6.4061e-15 | 2.06182e-15 | 1.77636e-15 | 7.43931e-15 | 15609.8 | 1.86588e-15 | 53594.1 |
| normalization-contract | 1.01112e-14 | 9.40887e-15 | 3.33096e-15 | 1.77636e-15 | 1.19402e-15 | 2251.8 | 1.79882e-15 | 132521 |
| operator-dense-reference | 9.42843e-15 | 7.33311e-15 | 3.46924e-15 | 1.9984e-15 | 6.34215e-15 | 10606.2 | 3.12805e-15 | 31968.8 |
| removed-hermitian-keyword | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| symmetry-sector | 5.69854e-15 | 7.75766e-15 | 3.81589e-15 | 3.55271e-15 | 4.02494e-15 | 128905 | 2.60961e-15 | 383198 |
| wide-spectrum-defect | 2.87398e-11 | 2.87396e-11 | 7.88639e-12 | 7.10543e-15 | 5.35129e-14 | 347.95 | 1.22355e-14 | 817293 |

## Case-level scientific margins

The fixed density-matrix integration cases remain separate here. In particular, the deliberately loose `density-restart` case does not set the bounds of the accurate unitary-state cases.

| Check / case | L2 error | Component error | Min science headroom | Limiting input / metric |
|---|---:|---:|---:|---|
| basis-extension / extended-grid | 4.77997e-14 | 1.5006e-14 | 20920.6 | nominal / l2 |
| basis-reuse / reused-grid | 4.85766e-15 | 1.69602e-15 | 205861 | nominal / l2 |
| doc-getting-started / getting-started-grid | 1.30425e-14 | 4.72569e-15 | 76672.3 | nominal / l2 |
| doc-getting-started / getting-started-single | 6.18315e-15 | 2.56409e-15 | 161730 | nominal / l2 |
| doc-manual-cache / manual-cache | 1.7119e-14 | 6.84233e-15 | 58414.6 | nominal / l2 |
| doc-manual-full-quench / manual-grid | 1.91759e-14 | 6.92926e-15 | 52148.9 | variant / l2 |
| doc-manual-full-quench / manual-single | 6.92407e-15 | 1.8312e-15 | 144424 | variant / l2 |
| doc-manual-sector / manual-sector | 1.35207e-14 | 3.45376e-15 | 73960.4 | variant / l2 |
| doc-matrix-free-operator / matrix-free-grid | 9.19933e-15 | 2.1339e-15 | 108704 | variant / l2 |
| doc-reference-api / reference-grid | 1.7119e-14 | 6.92926e-15 | 58414.6 | nominal / l2 |
| doc-reference-api / reference-single | 6.92407e-15 | 1.8312e-15 | 144424 | variant / l2 |
| doc-workflow-cache / workflow-cache | 1.91759e-14 | 4.02293e-15 | 52148.9 | variant / l2 |
| doc-workflow-full-basis / workflow-full-grid | 1.46362e-13 | 1.6053e-14 | 6832.35 | nominal / l2 |
| doc-workflow-sector / workflow-sector-grid | 6.20835e-14 | 2.24174e-14 | 16107.3 | variant / l2 |
| doc-workflow-sector-product / sector-product | 2.8831e-15 | 1.44755e-15 | 346849 | nominal / l2 |
| docstring-timeevolve / docstring-grid | 2.74843e-14 | 1.31164e-14 | 36384.4 | nominal / l2 |
| docstring-timeevolve / docstring-single | 1.02466e-14 | 4.4086e-15 | 97593.4 | variant / l2 |
| explicit-cache-inplace / cache-sequential | 4.95313e-15 | 1.4524e-15 | 20189.3 | variant / l2 |
| explicit-cache-inplace / inplace-single | 3.54878e-15 | 9.56763e-16 | 28178.7 | variant / l2 |
| forward-time-rules / cache-duplicates | 2.9066e-15 | 8.27156e-16 | 344044 | variant / l2 |
| forward-time-rules / duplicate-times | 2.9066e-15 | 8.27156e-16 | 344044 | variant / l2 |
| forward-time-rules / rejections | N/A | N/A | N/A | N/A |
| forward-time-rules / shuffled | 5.1367e-15 | 1.46647e-15 | 194677 | variant / l2 |
| forward-time-rules / sorted | 5.1367e-15 | 1.46647e-15 | 194677 | variant / l2 |
| lindblad-unitary-integration / density-grid | 2.60053e-15 | 1.45265e-15 | 38453.7 | nominal / l2 |
| lindblad-unitary-integration / density-restart | 1.6419e-06 | 8.19169e-07 | 3.04525 | variant / l2 |
| lindblad-unitary-integration / density-single | 2.78211e-15 | 1.67396e-15 | 35944 | nominal / l2 |
| lindblad-unitary-integration / unitary-state | 1.38833e-15 | 1.01032e-15 | 72028.8 | nominal / l2 |
| long-interval-restart / long-grid | 3.32422e-10 | 6.00658e-11 | 3008.23 | variant / l2 |
| long-interval-restart / nonunit-restart | 1.24424e-10 | 2.5351e-11 | 20092.5 | nominal / l2 |
| matrix-representations / dense | 6.40624e-15 | 2.06182e-15 | 15609.8 | nominal / l2 |
| matrix-representations / hermitian | 6.40527e-15 | 1.72226e-15 | 15612.1 | variant / l2 |
| matrix-representations / sparse | 6.4061e-15 | 1.99416e-15 | 15610.1 | variant / l2 |
| normalization-contract / analytic-diagonal | 2.83052e-16 | 2.22045e-16 | 300240 | variant / norm |
| normalization-contract / default-normalized-input | 2.8461e-15 | 8.44267e-16 | 35135.9 | variant / l2 |
| normalization-contract / nonunit-default | 1.01112e-14 | 3.33096e-15 | 24725.1 | nominal / l2 |
| normalization-contract / nonunit-opt-in | 4.06185e-15 | 1.33359e-15 | 2251.8 | nominal / norm |
| normalization-contract / opt-in-normalized-input | 2.76858e-15 | 8.44267e-16 | 3002.4 | nominal / norm |
| operator-dense-reference / scalar-shift-phase | 7.33311e-15 | 2.8593e-15 | 13636.8 | variant / l2 |
| operator-dense-reference / single-times | 7.62019e-15 | 2.67323e-15 | 13123 | nominal / l2 |
| operator-dense-reference / time-grid | 9.42843e-15 | 3.46924e-15 | 10606.2 | nominal / l2 |
| removed-hermitian-keyword / removed-keyword | N/A | N/A | N/A | N/A |
| symmetry-sector / sector-times | 7.75766e-15 | 3.81589e-15 | 128905 | variant / l2 |
| wide-spectrum-defect / wide-grid | 2.04823e-11 | 5.45167e-12 | 488.227 | variant / l2 |
| wide-spectrum-defect / wide-single | 2.87398e-11 | 7.88639e-12 | 347.95 | nominal / l2 |

## Measured time

Build is the per-check build/preparation time recorded by the driver. Run excluding build includes fresh process startup, first-use JIT, independent-oracle work and I/O. Solver-call timing is retained separately in JSON. These are not warmed-kernel speed measurements.

| Check | Nominal build s | Nominal run s | Variant build s | Variant run s |
|---|---:|---:|---:|---:|
| basis-extension | 4.66131 | 8.08239 | 4.09582 | 7.88868 |
| basis-reuse | 4.28463 | 7.80557 | 4.18922 | 7.92718 |
| doc-getting-started | 4.01508 | 7.78122 | 4.15909 | 7.95381 |
| doc-manual-cache | 3.87181 | 8.97329 | 4.09925 | 8.91785 |
| doc-manual-full-quench | 3.84731 | 12.1836 | 3.99644 | 12.5151 |
| doc-manual-sector | 3.93693 | 7.70347 | 4.29081 | 8.03799 |
| doc-matrix-free-operator | 4.00102 | 10.0536 | 4.11049 | 10.043 |
| doc-reference-api | 3.99195 | 12.0635 | 4.12518 | 12.2091 |
| doc-workflow-cache | 4.19553 | 9.25807 | 4.15073 | 9.16157 |
| doc-workflow-full-basis | 3.95876 | 10.6512 | 4.11661 | 10.7845 |
| doc-workflow-sector | 3.96861 | 8.07239 | 4.23707 | 7.90193 |
| doc-workflow-sector-product | 4.05451 | 7.70119 | 4.14426 | 7.68144 |
| docstring-timeevolve | 4.09739 | 12.1648 | 3.98694 | 12.0782 |
| explicit-cache-inplace | 4.00962 | 7.64438 | 4.37201 | 7.69199 |
| forward-time-rules | 4.11309 | 8.15311 | 4.2432 | 8.0251 |
| lindblad-unitary-integration | 4.15914 | 9.91446 | 4.14206 | 9.88224 |
| long-interval-restart | 4.25621 | 8.91449 | 4.00798 | 8.60152 |
| matrix-representations | 4.28149 | 6.74101 | 4.08434 | 6.83456 |
| normalization-contract | 4.04702 | 8.04638 | 4.10895 | 8.40475 |
| operator-dense-reference | 4.11351 | 8.09629 | 4.08695 | 7.91405 |
| removed-hermitian-keyword | 3.94512 | 6.15968 | 3.97251 | 6.27359 |
| symmetry-sector | 3.95114 | 7.99856 | 4.04772 | 7.81438 |
| wide-spectrum-defect | 4.20827 | 6.46533 | 3.9777 | 6.4668 |

nominal: recorded per-check builds 93.9695 s, runs excluding build 200.628 s; complete solve wall time 295.908 s. Image-build time is not separately isolated from complete solve overhead.

variant: recorded per-check builds 94.7453 s, runs excluding build 201.009 s; complete solve wall time 297.264 s. Image-build time is not separately isolated from complete solve overhead.

The complete final selfcheck command took 597.23 s according to its `time -p` real measurement. This includes both solves, the verifier and CLI overhead; it is not inferred by subtracting whole-second timestamps.

This final selfcheck adds no alternate-build floor, dedicated same-input repeat study, fault injection, or tolerance optimization. The earlier targeted restart controls remain separate evidence. Passing this suite does not establish correctness for every implementation, input or fault type. The JSON retains scalar evidence, effective bounds, limiting locations, timings and artifact hashes; it does not contain reference-state arrays or private absolute paths. No pipeline record is authored by this summarizer.

[Machine-readable final validation](final-validation-v1.json)
