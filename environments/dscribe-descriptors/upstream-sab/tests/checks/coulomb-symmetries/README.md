# coulomb-symmetries

This self-contained check is adapted from `code/dscribe/tests/test_coulombmatrix.py`. It computes rigid-motion matrices and atom-permutation eigenspectra with residuals.

Run `./run.sh nominal` or `./run.sh variant`; `SAB_REPEATS` scales repeated evaluation without changing the graded default. The variant moves one active binary64 coordinate by two ulps. The pointwise policy uses finalized atol 1e-8 and rtol 0.000001; Docker calibration evidence is recorded in `rubric.json`.
