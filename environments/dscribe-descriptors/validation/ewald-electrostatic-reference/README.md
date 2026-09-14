# ewald-electrostatic-reference

This self-contained check is adapted from `code/dscribe/tests/test_ewaldsummatrix.py`. It computes converged Ewald matrix, reconstructed total energy, and all two-particle energies.

Run `./run.sh nominal` or `./run.sh variant`; `SAB_REPEATS` scales repeated evaluation without changing the graded default. The variant moves one active binary64 coordinate by two ulps. The pointwise policy uses finalized atol 0.00001 and rtol 0.00001; Docker calibration evidence is recorded in `rubric.json`.
