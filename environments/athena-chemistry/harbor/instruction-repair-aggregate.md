<!-- @CANARY@ -->
Find and repair @DEFECT_SCOPE@ in Athena++, pinned at commit
`@ATHENA_COMMIT@`. The relevant numerical surface is the chemistry ODE layer,
reaction networks and thermodynamics, chemistry-radiation coupling, six-ray
column exchange, and chemistry initialization. Root cause and location are
yours to determine.

## Observed symptom

@SYMPTOM@

Discover the graded rows under `/app/cases`; each `row.json` declares its
profile and native output contract. Build every needed profile with
`python3 /app/rowtool.py build /app/athena <profile> <build-dir> 4 /usr`, then
run it with `python3 /app/rowtool.py run <builds-root> <case-dir>
/logs/artifacts/<row> <timeout>`. Exact arguments live in
`/app/build_profiles.json` and pin `-O2 -g0 -ffp-contract=off`.

The verifier grades only native history and full-precision final primitive /
species frames: 0.2 conformance + 0.5 pointwise frame credit + 0.3 canonical
exact bytes, floor-normalized in situ. Physical time/cycle fields remain exact.

Documentation, regression answer keys, ungraded chemistry pgen siblings,
backup variants, Git metadata, and pristine source are absent; network access
is disabled. Do not modify cases, validators, compiler settings, or outputs,
and do not fabricate/post-process results.
