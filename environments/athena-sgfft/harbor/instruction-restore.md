<!-- @CANARY@ -->
Restore the missing body of `@SUB@` in Athena++, pinned at commit
`@ATHENA_COMMIT@`, so native self-gravitating Jeans evolution matches the
unmodified incumbent. Restore any retained implementation twins as well.

Observed behavior:

@SYMPTOM@

Rows: @CHECKS_LIST@. Read each `/app/cases/<check>/row.json` and its
`athinput.jeans`. Build the row's `mg_serial`, `mg_mpi`, or `fft_mpi` variant
with the gravity, MPI, FFTW, Cartesian, and compiler arguments documented in
the row/instructions; use separate source, object, and binary trees.

Run every row with its ordered overrides and MPI rank prefix. Deliver its
native history and only the final-numbered conserved VTK block group under
`/logs/artifacts/<check>/`. The ladder is 0.2 conformance + 0.5 evolved-frame
fraction + 0.3 exact scored bytes, normalized above floor @FLOOR@. Network,
docs/tests, backup variants, Git metadata, and the pristine archive are absent.
Do not alter cases, validators, numerical/build contracts, or output bytes.
