# acsf-environment-basis

This self-contained check is adapted from `code/dscribe/tests/test_acsf.py`. It computes center-averaged acsf vectors and normalized environment-overlap values across species environments and a supercell.

Run `./run.sh nominal` or `./run.sh variant`; `SAB_REPEATS` scales repeated evaluation without changing the graded default. The variant changes one active binary64 geometry value by two ulps. The candidate is compared pointwise with the hidden reference using the finalized bounds in `rubric.json`; calibration evidence is recorded in `rubric.json`.
