<!-- @CANARY@ -->
Find and repair @DEFECT_SCOPE@ in Athena++, pinned at commit
`@ATHENA_COMMIT@`. The relevant surface is SR hydro/MHD: Lorentz-factor versus
velocity storage, conserved-to-primitive iteration/fallback protocols,
transverse coupling, Riemann states, and relativistic EOS bookkeeping.
Determine the root cause and affected source locations yourself.

## Observed symptom

@SYMPTOM@

Authoritative graded cases live under `/app/cases/`; each `row.json` identifies
its selected official deck, checksum, build variant, and native final `.tab`
frames. Build each named variant in a fresh source copy using `-s`, optional
`-b`, the row's `gr_shock_tube` or `gr_linear_wave` problem,
`--coord=cartesian`, and its named `--flux` switch, always adding
`--cflag='-O2 -g0 -ffp-contract=off'`. Keep object/bin directories disjoint.

Run every listed deck as `<athena> -i <deck>.athinput -d .`. Deliver only the
named native final frames under `/logs/artifacts/<check>/`; logs, diagnostics,
and reconstructed outputs are excluded.

The ladder is 0.2 conformance + 0.5 final-frame fraction + 0.3 exact canonical
bytes. Physical time/cycle headers are scored and no wall timestamp is masked.
The verifier measures an unfixed floor (crash/hang means floor zero) and reports
floor-normalized repair reward. Network access and the pristine archive are
absent. Do not alter or post-process the frozen scientific inputs or outputs.
