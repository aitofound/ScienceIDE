<!-- @CANARY@ -->
Find and repair @DEFECT_SCOPE@ in Stim, pinned at commit `@STIM_COMMIT@`.
The relevant subsystem is its packed stabilizer core: SIMD bit tables, Pauli
and Clifford tableau algebra, frame propagation, measurement-to-detection
reduction, and stochastic error-channel sampling. The root cause and source
location are yours to determine.

## Observed symptom

@SYMPTOM@

The graded checks are: @CHECKS_LIST@. Their public inputs, SAB rubrics, and
validators are under `/app/checks/<check>/`; concise row metadata is under
`/app/cases/<check>/row.json`.

## Build and delivery contract

Repair `/app/stim`, then build once and run every listed check:

    python3 /app/rowtool.py build /app/stim /app/build 2
    python3 /app/rowtool.py run /app/stim /app/build \
      /app/checks/<check> /logs/artifacts/<check> 900

The helper pins the Release toolchain and disables floating-point contraction.
Do not modify checks, validators, inputs, build helper, or generated outputs,
and do not fabricate or post-process results. Runtime network is restricted.

## Grading

An empty delivery earns 0.0; malformed output earns 0.1; a complete artifact
contract earns 0.5; satisfying the upstream SAB pass policy earns 1.0. The
verifier measures the unfixed floor (about @FLOOR@) and reports normalized
`reward_repair`.
