# coulomb-numerical-derivatives

This self-contained check is adapted from `code/dscribe/tests/test_coulombmatrix.py`. It computes numerical matrix and eigenspectrum derivative tensors with features.

Run `./run.sh nominal` or `./run.sh variant`; `SAB_REPEATS` scales repeated evaluation without changing the graded default. The variant moves one active binary64 coordinate by two ulps. The pointwise policy uses finalized atol 0.000001 and rtol 0.0005; Docker calibration evidence is recorded in `rubric.json`.
