# acsf-analytic-features

This self-contained check is adapted from `code/dscribe/tests/test_acsf.py`. It computes g1 through g5 acsf arrays together with the distances and cutoff values that define their analytical formulas.

Run `./run.sh nominal` or `./run.sh variant`; `SAB_REPEATS` scales repeated evaluation without changing the graded default. The variant changes one active binary64 geometry value by two ulps. The candidate is compared pointwise with the hidden reference using the finalized bounds in `rubric.json`; calibration evidence is recorded in `rubric.json`.
