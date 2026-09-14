# vp-emission-spectrum-1x1v-p2

Upstream test: code/gkeyll/vlasov/creg/rt_vlasov_poisson_emission_spectrum_1x1v_p2.c. Policy: pointwise.

## The test

run.sh builds and executes the complete upstream driver at its original resolution and physical end time: Upstream P2 1x1v electron emission problem through the Vlasov-Poisson app (128x32 cells, ten inverse plasma frequencies): a reflecting lower wall, an emitting upper electron boundary with a secondary-emission spectrum, an absorbing ion wall and a boundary-flux source, in SI units. It grades the electron and ion integrated-moment histories, the field energy and the final emitted-electron boundary frame. This configuration forces the emission boundary condition (`GKYL_SPECIES_EMISSION` with an emission spectrum model), the boundary-flux source and non-periodic Poisson boundary conditions. Runtime knobs expose the step count and every configuration and velocity grid dimension; defaults retain upstream values. The x86 survey of 2026-09-06 ran the driver in 1.1 s on one core with the source build excluded.

## The two initial conditions

The nominal input keeps n0=1.0e17; the variant changes it to 1.0000000000000003e17, exactly two upward binary64 ULP. `n0` is the reference density of both species, so calibration tests sensitivity without changing the physics problem. `run.sh altbuild` runs the same nominal inputs on a strict-IEEE build of the same source (gcc -O2, no -ffast-math, -ffp-contract=off, no -march=native); self-validation grades it against the default build and records the distance as this check's floor.

## The pass policy

Every payload value in the Gkeyll dynamic-vector histories `elc-imom.gkyl`, `ion-imom.gkyl`, `field-energy.gkyl` is compared pointwise; samples are matched on their recorded physical time (both time axes must be finite and non-decreasing, or the file fails) (within 1e-8 of the window), so neither the sample count nor the step sequence is graded; a reference time with no candidate sample fails; every payload value and the grid extents of the final frame `elc-bc-up.gkyl` are compared pointwise with the cell count and element width required to match exactly. Every graded value must satisfy |err| <= atol + rtol*|ref| with `atol=1e-09, rtol=1e-09`. In `elc-imom.gkyl` (3 values per sample) component 1 keeps atol=1e+10, rtol=1e-09, a residual-scale component graded on its own bound (see the rubric warrant). In `ion-imom.gkyl` (3 values per sample) component 1 keeps atol=1e+06, rtol=1e-09, a residual-scale component graded on its own bound (see the rubric warrant). The bound is physical because a wrong emission yield, a wrong boundary-flux accounting or a wrong Poisson boundary changes the graded values at order one, and achievable because the two-ULP variant and the strict-IEEE altbuild, the two legitimate perturbations measured below, stay under it.

## Evidence

The calibration selfcheck of 2026-09-06 on the x86 worker 136.114.2.6 (1 cpu, 4 GB, Docker) measured 4.3 s of run time with the driver build excluded. The two-ULP variant moved the graded values by at most `3.8e12` absolute (worst file `elc-imom.gkyl`, using 6.0e-3 of its bound); the strict-IEEE altbuild (same source, gcc -O2 strict IEEE: no -ffast-math, -ffp-contract=off, no -march=native (build-ieee/)) by at most `5.5e12` absolute (worst file `ion-imom.gkyl`, 3.9e-3 of its bound). Under the bound `atol=1e-09, rtol=1e-09` with the component overrides above the largest fraction of any per-value bound used by either legitimate perturbation is 6.0e-3, a headroom of about 168x. Self-validation grades nominal against variant and nominal against altbuild with this validate.py and writes both numbers into rubric.json.
