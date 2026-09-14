# Repair adaptive Krylov real-time evolution

The supplied EDKit tree contains one localized defect in its adaptive
Hermitian real-time propagation subsystem. Restore the scientific behavior
under the pinned validation cases. Preserve the public APIs and dependency pins.

The package is at `/app/edkit`; Julia 1.12.5 and the offline dependency depot
are installed. The immutable check drivers and their input files are under
`/app/checks`. The graded checks are: @CHECKS_LIST@.

For each check, build and produce complete results with:

```bash
python3 /app/rowtool.py /app/edkit /app/checks/CHECK /logs/artifacts/CHECK @ROW_TIMEOUT@
```

Each output directory must be fresh. The driver preserves the package's pinned
dependencies, executes the check, and emits both results and run status. Submit
all output directories under `/logs/artifacts`. Partial or failed runs do not
constitute valid measurements. The reference and straw floor are verifier-only.

The checker compares complete complex amplitudes, API behavior where declared,
and independent same-input scientific bounds from the upstream rubric. Repair
reward subtracts the measured defective baseline and reaches one on full pass.
Only source repair is allowed; do not replace the checks, grader, or run-status
protocol. Difficulty is unmeasured.

<!-- @CANARY@ -->
