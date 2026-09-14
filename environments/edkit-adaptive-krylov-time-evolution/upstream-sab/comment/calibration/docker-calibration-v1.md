# First Docker calibration

The completed CLI run recorded result `passed` and reward 1.0 (23/23 checks). This is the first nominal/variant calibration with the existing provisional bounds; the final tolerances remain unconfirmed.

Same-input errors below compare each run with its independently constructed ED answer for that exact input. Pair perturbation compares nominal with variant. These measurements have different meanings.

Scientific headroom is the reciprocal of the largest recorded bound fraction across that check's own case, metric and input combinations, including cross-case gates. Every fraction is associated with its actual case-specific bound. It is not an aggregate maximum error divided by an unrelated cap. Exact API outcomes have no numerical headroom.

22 of 22 numerical checks changed their complete-state outputs under the declared input perturbation. The `removed-hermitian-keyword` check has declared identical API inputs/outcomes and provides no numerical-noise calibration; its numerical errors and headroom are N/A.

## Observed container environment

The following observation comes from the separately recorded read-only environment probe. The running image IDs in JSON come from each CLI solve's oracle manifest, not from an earlier tag inspection.

- actual os: Debian GNU/Linux 13 (trixie), DEBIAN_VERSION_FULL=13.1
- julia: 1.10.12
- python: 3.13.5 (GCC 14.2.0)
- numpy: 2.2.4
- blas lapack: NumPy reports BLAS and LAPACK 3.12.1
- architecture: linux/arm64 (aarch64), local Apple Silicon CPU
- kernel: 7.0.12-linuxkit
- base label discrepancy: Both existing Dockerfiles say debian:bookworm-slim@sha256:1caf1c703c8f7e15dcf2e7769b35000c764e6f50e4d7401c355fb0248f3ddfdb, but the pinned digest actually contains Debian 13 trixie. The existing digest and Dockerfiles were not changed for this calibration.
- inspection note: Read-only version probe in the built oracle image used an overridden /bin/sh entrypoint, not the scientific suite. It exited 0. numpy.show_config emitted only an optional PyYAML formatting warning. Actual solve image IDs must be taken from CLI manifests, since cached rebuilds may change OCI attestation/index IDs.
- Initial image byte sizes are retained in JSON. Shared image layers mean these sizes cannot be added to infer total disk use.

The two saved solve-build logs contain the same platform manifest and image configuration digests. Their attestation and OCI index digests differ, which does not constitute an alternative scientific build. The runtime manifest records remain the authority for each solve's image ID.

## Per-check scientific and perturbation evidence

| Check | L2 error | Component error | Norm error | Energy error | Min science headroom | Pair perturbation | Pair headroom |
|---|---:|---:|---:|---:|---:|---:|---:|
| basis-extension | 4.77997e-14 | 1.5006e-14 | 8.88178e-16 | 3.17801e-15 | 20920.6 | 2.3282e-15 | 429516 |
| basis-reuse | 4.85766e-15 | 1.69602e-15 | 1.77636e-15 | 1.66543e-15 | 205861 | 1.41008e-15 | 709179 |
| doc-getting-started | 1.30425e-14 | 4.72569e-15 | 1.9984e-15 | 9.11182e-15 | 76672.3 | 4.57757e-16 | 2.18457e+06 |
| doc-manual-cache | 1.7119e-14 | 6.84233e-15 | 4.44089e-15 | 7.10545e-15 | 58414.6 | 4.00297e-16 | 2.49815e+06 |
| doc-manual-full-quench | 1.91759e-14 | 6.92926e-15 | 4.66294e-15 | 8.88329e-15 | 52148.9 | 4.74287e-16 | 2.10843e+06 |
| doc-manual-sector | 1.35207e-14 | 3.45376e-15 | 8.88178e-16 | 1.28248e-14 | 73960.4 | 2.0321e-15 | 492102 |
| doc-matrix-free-operator | 9.19933e-15 | 2.1339e-15 | 6.66134e-16 | 6.88426e-15 | 108704 | 4.74287e-16 | 2.10843e+06 |
| doc-reference-api | 1.7119e-14 | 6.92926e-15 | 4.66294e-15 | 8.88329e-15 | 58414.6 | 4.74287e-16 | 2.10843e+06 |
| doc-workflow-cache | 1.91759e-14 | 4.02293e-15 | 4.44089e-15 | 8.22423e-15 | 52148.9 | 4.00297e-16 | 2.49815e+06 |
| doc-workflow-full-basis | 1.46362e-13 | 1.6053e-14 | 1.11022e-15 | 2.05392e-15 | 6832.35 | 3.71927e-16 | 2.6887e+06 |
| doc-workflow-sector | 6.20835e-14 | 2.24174e-14 | 1.05471e-14 | 8.51541e-14 | 16107.3 | 1.0887e-14 | 91852.7 |
| doc-workflow-sector-product | 2.8831e-15 | 1.44755e-15 | 3.33067e-16 | 6.69623e-16 | 346849 | 3.7238e-16 | 2.68543e+06 |
| docstring-timeevolve | 2.74843e-14 | 1.31164e-14 | 6.66134e-16 | 7.9937e-15 | 36384.4 | 4.57757e-16 | 2.18457e+06 |
| explicit-cache-inplace | 4.95313e-15 | 1.4524e-15 | 8.88178e-16 | 1.32937e-15 | 20189.3 | 1.00036e-15 | 99963.8 |
| forward-time-rules | 5.1367e-15 | 1.46647e-15 | 6.66134e-16 | 2.25516e-15 | 194677 | 8.5474e-16 | 1.16995e+06 |
| lindblad-unitary-integration | 1.6419e-06 | 8.19169e-07 | 6.63913e-13 | 1.53727e-14 | 3.04525 | 1.0289e-13 | 55259.7 |
| long-interval-restart | 3.32422e-10 | 6.00658e-11 | 1.02141e-14 | 1.01711e-13 | 3008.23 | 3.59208e-15 | 2.87266e+08 |
| matrix-representations | 6.40624e-15 | 2.06182e-15 | 1.77636e-15 | 7.43931e-15 | 15609.8 | 1.86588e-15 | 53594.1 |
| normalization-contract | 1.01112e-14 | 3.33096e-15 | 1.77636e-15 | 1.19402e-15 | 2251.8 | 1.79882e-15 | 132521 |
| operator-dense-reference | 9.42843e-15 | 3.46924e-15 | 1.9984e-15 | 6.34215e-15 | 10606.2 | 3.12805e-15 | 31968.8 |
| removed-hermitian-keyword | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| symmetry-sector | 7.75766e-15 | 3.81589e-15 | 3.55271e-15 | 4.02494e-15 | 128905 | 2.60961e-15 | 383198 |
| wide-spectrum-defect | 2.87398e-11 | 7.88639e-12 | 7.10543e-15 | 5.35129e-14 | 347.95 | 1.22355e-14 | 817293 |

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
| basis-extension | 4.91944 | 8.55346 | 4.89483 | 8.57907 |
| basis-reuse | 4.55604 | 8.54846 | 4.4097 | 8.5208 |
| doc-getting-started | 4.56067 | 8.91983 | 4.41875 | 8.58735 |
| doc-manual-cache | 4.55869 | 10.1606 | 4.45661 | 10.3815 |
| doc-manual-full-quench | 4.76232 | 13.5124 | 4.47191 | 12.5244 |
| doc-manual-sector | 4.53145 | 8.78225 | 4.08308 | 8.33472 |
| doc-matrix-free-operator | 4.51221 | 10.8358 | 4.14516 | 10.1918 |
| doc-reference-api | 4.41842 | 13.2058 | 4.12769 | 12.3098 |
| doc-workflow-cache | 4.83646 | 9.73264 | 3.95085 | 8.71315 |
| doc-workflow-full-basis | 4.40957 | 11.4955 | 3.97835 | 10.3199 |
| doc-workflow-sector | 4.52438 | 8.64702 | 4.02534 | 7.58956 |
| doc-workflow-sector-product | 4.3859 | 8.314 | 3.89233 | 7.12787 |
| docstring-timeevolve | 4.39712 | 13.0498 | 3.89478 | 11.3255 |
| explicit-cache-inplace | 4.45391 | 8.18139 | 3.82843 | 6.92737 |
| forward-time-rules | 4.45342 | 8.59898 | 3.83185 | 7.17325 |
| lindblad-unitary-integration | 4.39373 | 10.5827 | 3.73598 | 9.00672 |
| long-interval-restart | 4.32995 | 9.16885 | 3.71252 | 8.46308 |
| matrix-representations | 4.35755 | 7.36085 | 3.72021 | 6.83649 |
| normalization-contract | 4.46133 | 8.65457 | 4.40626 | 8.33814 |
| operator-dense-reference | 4.66145 | 8.33465 | 4.20698 | 8.10182 |
| removed-hermitian-keyword | 4.36605 | 7.05075 | 4.20442 | 6.73648 |
| symmetry-sector | 4.32036 | 8.73044 | 4.19121 | 8.43409 |
| wide-spectrum-defect | 4.44455 | 7.06115 | 4.24566 | 6.73704 |

nominal: recorded per-check builds 103.615 s, runs excluding build 217.482 s; complete solve wall time 324.869 s. Image-build time is not separately isolated from complete solve overhead.

variant: recorded per-check builds 94.8329 s, runs excluding build 201.26 s; complete solve wall time 297.617 s. Image-build time is not separately isolated from complete solve overhead.

Before selfcheck, the two-image build command was separately timed at 164.22 s. Its log SHA-256 is retained in JSON; this separate command time is not counted again as per-check build time.

The complete first selfcheck command took 627.00 s according to its `time -p` real measurement. This includes both solves, the verifier and CLI overhead; it is not inferred by subtracting whole-second timestamps.

## Optional offline tolerance arithmetic

The following only divides an explicitly requested hypothetical L2 cap by already recorded same-input L2 errors. No policy was changed and no experiment was run. These are proposals, not human-finalized tolerances or evidence that wrong implementations would be rejected.

- long-interval-restart / long-grid: hypothetical L2 cap 1e-8, recorded max L2 error 3.32422e-10, projected headroom 30.0823.
- long-interval-restart / nonunit-restart: hypothetical L2 cap 1e-8, recorded max L2 error 1.24424e-10, projected headroom 80.3702.

No alternate-build floor or same-input Docker repeat experiment was performed by this run. No fault-injection experiment or final self-validation was added. The JSON retains scalar evidence, effective bounds, limiting locations, timings and artifact hashes; it does not contain reference-state arrays or private absolute paths.

[Machine-readable calibration](docker-calibration-v1.json)
