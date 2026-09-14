# numerical-derivatives

Upstream test: `code/dscribe/tests/test_soap.py`. Policy hypothesis: `pointwise`. This is the check labelled `acceleration` in `check.json`: its speed is the one measured.

## The test

Numerical derivatives. The check runs the independent, public `runner.py` against the DScribe source selected by `SOURCE_DIR` and writes finite-difference derivative tensors and paired SOAP features for four averaging and compression configurations, concatenated into one `output.npy`.

- Two per-center configurations (`average="off"` with compression `off` and `mu1nu1`) on the four-atom H2O-C molecule with atoms 0 and 1 as centers, at r_cut 3.5, n_max 3, l_max 3. These keep the breadth of the upstream test.
- Two averaged configurations (`average="inner"` with compression `off`, `average="outer"` with compression `crossover`) on a periodic cubic cell of 64 rotated copies of that molecule, 256 atoms in a 12.4 A cell, with every atom as a center, at r_cut 6.0, n_max 6, l_max 6. The graded quantity is the derivative of the global (averaged) descriptor with respect to every atom position and axis, the force-like quantity of a global-descriptor energy model. Its tensor is (1, 256, 3, features) per configuration, but each displaced atom re-evaluates the spectra of every center within the cutoff, so the work grows with the square of the atom count. This part is the acceleration workload.

Runtime scales linearly with `SAB_REPEATS`, whose graded default is 1; the two averaged configurations take about 65 s each on two CPU cores of an x86 host, the per-center ones under a second.

## The two initial conditions

Both inputs are JSON files. The nominal active value is binary64 1.0; the variant is 1.0000000000000004, two ulps higher. The runner applies it to one coordinate of the base molecule, which every copy in the periodic cell inherits, so the files differ byte-wise and every graded array differs.

## The pass policy

Every entry of `output.npy` has a fixed physical meaning for the declared species, basis, compression, center, and derivative metadata. The finalized pointwise rule is `|candidate-reference| <= 1e-6 + 5e-4*|reference|`, following the upstream derivative-equivalence scale. Finite-difference displacement, atom/center-axis, compression, periodic-image, averaging, or descriptor-evaluation faults cross that bound; the averaged derivatives are small numbers (one part in 256 of a per-center derivative), so the absolute term of the rule carries them.

## Evidence

The corresponding upstream definition passed in the native SOAP run at the pin. The Docker nominal/variant spread and the bound fraction of this configuration are recorded in `rubric.json` under `evidence` by the self-validation run; no alternative-build floor is declared.
