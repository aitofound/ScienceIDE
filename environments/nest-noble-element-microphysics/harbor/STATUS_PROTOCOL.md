# NEST delivery and status protocol

The verifier grades only the task's compiled `CHECKS`. The normal delivery is
`/logs/artifacts/<check>/`, containing the rowtool's `_run_status.json`, `run.ok`,
and the output tables named by the pinned rubric. Extra files and directories,
including saved baseline runs with their own `_run_status.json`, are ignored.
The verifier never recursively discovers submitted checks.

Without a manifest, each check's `_run_status.json` is either the rowtool object
or a list of status objects. An optional `/logs/artifacts/manifest.json` can
instead supply the authoritative status list:

```json
{
  "checks": [
    {"check": "legacy-larnest-yields", "status": "ok", "exit": 0}
  ]
}
```

A bare list of these objects is also accepted. Output paths always remain
`<delivery>/<check>/`; manifest records cannot redirect a check to other files.
Entries must be objects with nonempty string check names. Other fields are
metadata. `status: "ok"` with an integer `exit: 0` permits validation; the
validator must still pass before the check receives 1.0. A completed, readable
but divergent numerical output retains the existing 0.5 ladder score.

- An unknown status, failed run, invalid exit code, missing check/status/output,
  or unreadable output receives 0 for that check, with a reason in the report.
- Duplicate check entries keep the last entry in list order and record a
  warning. Duplicate JSON object keys also keep the last value with a warning.
- Unknown check names are ignored with a warning; they do not change the
  denominator or provide another source of output for a graded check.
- Malformed JSON or manifest structure makes the entire delivery
  `nonconforming`: every check receives 0 and `grader_error` remains 0.
  Malformed per-check status files affect only their own check.
- Status/manifest JSON is limited to 1 MiB. Symlink and nonregular status/data
  files are rejected as nonconforming output. Unrelated files are not opened.

For local replay, `--candidate` also accepts Harbor's exported `artifacts/`
directory. Its transport manifest is a list with the `/logs/artifacts` source,
`artifacts/logs/artifacts` destination, `directory` type, and `ok` status.
The payload is read at the fixed `logs/artifacts/` location. Duplicate transport
entries keep the last record with a warning. Invalid transport manifests score
all checks 0. A transport manifest is distinct from the optional check manifest
inside its payload.

`grading_report.json` contains per-check reasons and `protocol.warnings` /
`protocol.errors`; `reward.json` includes a numeric `nonconforming` flag and
numeric raw and repair rewards. The measured floor and repair normalization
remain verifier-owned. `--floor-file` is a local replay option; Harbor continues
to load `/tests/floor.json`.

Missing or corrupt reference/validator/floor assets and failed validator
processes are verifier faults: they produce a numeric zero reward with
`grader_error: 1`, a diagnostic report, and a failing exit code. The shell wrapper
also supplies a numeric fault reward if the grader is killed or runs out of
memory. Ordinary agent delivery problems do not take this path.

Floor calibration remains strict in `grade_floor.py`: unexpected, incomplete,
malformed, or timed-out straw status records fail calibration. A completed
ordinary crash is allowed only with the preexisting explicit successful-build
evidence. A nonconforming straw cannot become a measured zero floor.

Regression evidence is produced by `factory/robustness_anchor.py`; fresh
oracle/nop waves are run by `factory/reanchor_hardened.py`.
