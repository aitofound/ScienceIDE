# mbtr-geometry-peaks

This self-contained check is adapted from `code/dscribe/tests/test_mbtr.py`. It computes k1, K2-distance, and K3-angle distributions on fixed grids.

Run `./run.sh nominal` or `./run.sh variant`; `SAB_REPEATS` scales repeated evaluation without changing the graded default. The variant changes one active binary64 geometry value by two ulps. The candidate is compared pointwise with the hidden reference using finalized atol 1e-8 and rtol 0.000001; calibration evidence is recorded in `rubric.json`.
