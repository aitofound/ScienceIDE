<!-- @CANARY@ -->
Find and repair @DEFECT_SCOPE@ in Athena++, pinned at commit
`@ATHENA_COMMIT@`. The relevant surface is fixed-metric GR hydro/MHD:
coordinate/frame bookkeeping, spatial four-velocity conventions,
conserved-to-primitive recovery, and floor/fallback sequencing. Determine the
root cause and affected source locations yourself.

## Observed symptom

@SYMPTOM@

Authoritative graded cases live under `/app/cases/`; each `row.json` identifies
its official decks, checksums, build variant, and native final `.tab` frames.
Build each named variant in a fresh source copy using the corresponding `-g`,
optional `-b`/`-t`, `--prob=gr_shock_tube`, `--coord=minkowski`, and named
`--flux` switches, always adding `--cflag='-O2 -g0 -ffp-contract=off'`.
Keep object/bin directories disjoint.

Run every listed deck as `<athena> -i <deck>.athinput -d .`. Deliver only the
named native final frames under `/logs/artifacts/<check>/`; logs, diagnostics,
and reconstructed outputs are excluded.

The ladder is 0.2 conformance + 0.5 final-frame fraction + 0.3 exact canonical
bytes. Physical time/cycle headers are scored and no wall timestamp is masked.
The verifier measures an unfixed floor (crash/hang means floor zero) and reports
floor-normalized repair reward. Network access and the pristine archive are
absent. Do not alter or post-process the frozen scientific inputs or outputs.
