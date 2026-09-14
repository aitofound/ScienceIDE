# Preserved Julia 1.12.5 calibration records

These two CLI-produced JSON files are byte-for-byte copies of the calibration
records preserved before the separately authorized final self-validation.
They belong to the preceding calibration, not the current final run.

- `self-validation.json`: calibration fingerprint
  `0fba6cb96cbac29d26aedbbdaa0cf957037f3e0493161d9a8ac3b59d422a4357`.
- `runtime-metadata.json`: runtime metadata from that same calibration.

See [the calibration report](../julia125-calibration-v1.md). After calibration,
23 check README runtime sentences were corrected; the exact earlier calibrated
Task and raw results remain archived outside the Task. That prose change is
recorded in `../julia125-documentation-followup.json`, without altering these
historical records. The final run covers the corrected documents and writes
the current records under `../../pipeline/`.

The original Julia 1.10 evidence remains separate under `../julia110-archive/`.
No record here was edited to impersonate the final Julia 1.12.5 run.
