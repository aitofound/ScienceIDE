# mbtr-valle-oganov-derivatives

This self-contained check is adapted from `code/dscribe/tests/test_mbtr.py`. It computes numerical and analytical derivatives of periodic Valle–Oganov-normalized MBTR.

Run `./run.sh nominal` or `./run.sh variant`; `SAB_REPEATS` scales repeated evaluation without changing the graded default. The variant changes one active binary64 geometry value by two ulps. The candidate is compared pointwise with the hidden reference using finalized atol 0.000001 and rtol 0.0005; calibration evidence is recorded in `rubric.json`.
