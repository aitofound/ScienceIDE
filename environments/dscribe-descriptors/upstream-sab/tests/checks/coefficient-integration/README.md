# coefficient-integration

Upstream test: `code/dscribe/tests/test_soap.py`. Policy hypothesis: `pointwise`.

## The test

High-angular-order integration. The check runs the independent, public `runner.py` against the DScribe source selected by `SOURCE_DIR` and writes high-l GTO and polynomial SOAP spectra on the deterministic upstream coefficient-integration geometry. Runtime scales linearly with `SAB_REPEATS`, whose graded default is 1; the current pre-Docker estimate is 0.3 seconds on at most two CPU cores.

## The two initial conditions

Both inputs are JSON files. The nominal active value is binary64 1.0; the variant is 1.0000000000000004, two ulps higher. The runner applies it to a geometry coordinate, so the files differ byte-wise and native probes confirmed that the graded arrays differ.

## The pass policy

Every entry of `output.npy` has a fixed physical meaning for the declared species, basis, compression, center, and derivative metadata. The finalized pointwise rule is `|candidate-reference| <= 1e-10 + 1e-2*|reference|`, following the upstream coefficient-level relative scale and the Docker calibration. High-angular-order basis or power-spectrum contraction faults should cross that bound.

## Evidence

The corresponding upstream definition passed in the native 122-item SOAP run. An independent nominal/variant execution of this check completed locally and produced byte-different arrays. Docker floor, calibration spread, final margin, and a wrong-implementation rejection probe are pending the calibration stage and will be recorded before submission.
