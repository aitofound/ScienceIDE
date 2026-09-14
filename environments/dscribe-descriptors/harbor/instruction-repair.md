# Repair DScribe while preserving its numerical contracts

The pinned DScribe tree contains @DEFECT_SCOPE@. Diagnose and repair it so the
public checks @CHECKS_LIST@ pass without weakening their validators or changing
their inputs. The observed symptoms are:

@SYMPTOM@

Build and test locally from `/app/dscribe`. Deliver complete check artifacts under
`/logs/artifacts`; runtime network access is restricted by the task manifest.

Compile with `python3 /app/rowtool.py build /app/dscribe /app/site 2`.
For each named check, run
`python3 /app/rowtool.py run /app/dscribe /app/site /app/checks/CHECK /logs/artifacts/CHECK 1800`.
The runner writes both the scientific artifacts and required run status.
Only descriptor implementation changes are permitted; preserve check inputs,
validators, and the runner contract.
