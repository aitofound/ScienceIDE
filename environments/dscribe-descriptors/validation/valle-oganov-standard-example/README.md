# valle-oganov-standard-example

This self-contained check is adapted from `code/dscribe/examples/valle_oganov.py`. It computes end-to-end distance and angle Valle–Oganov vectors adapted from the official example.

Run `./run.sh nominal` or `./run.sh variant`; `SAB_REPEATS` scales repeated evaluation without changing the graded default. The variant changes one active binary64 geometry value by two ulps. The candidate is compared pointwise with the hidden reference using finalized atol 1e-8 and rtol 0.000001; calibration evidence is recorded in `rubric.json`.
