# coulomb-random-permutation

This self-contained check is adapted from `code/dscribe/tests/test_coulombmatrix.py`. It computes seeded random-rank probability matrix and physical row norms.

Run `./run.sh nominal` or `./run.sh variant`; `SAB_REPEATS` scales repeated evaluation without changing the graded default. The variant moves one active binary64 coordinate by two ulps. The invariants policy uses finalized nine rank probabilities at atol 0.08 and three physical row norms at atol 1e-8, rtol 1e-6; Docker calibration evidence is recorded in `rubric.json`.
