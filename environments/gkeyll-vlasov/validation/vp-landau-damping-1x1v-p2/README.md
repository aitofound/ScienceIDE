# vp-landau-damping-1x1v-p2

Upstream test: code/gkeyll/vlasov/creg/rt_vp_landau_damping_1x1v_p2.c. Policy: pointwise.

## The test

run.sh builds and executes the complete upstream driver at its original resolution and physical end time: Upstream P2 1x1v Landau damping through the Vlasov-Poisson app (32x32 cells, 100 inverse plasma frequencies) with explicit Poisson boundary conditions. It grades the complete electron integrated-moment, distribution-L2 and field-energy histories. This configuration forces the Vlasov-Poisson application path with `poisson_bcs` (the periodic Poisson solve declared through the boundary-condition structure), distinct from the Vlasov-Maxwell field solve of the classic Landau check. Runtime knobs expose the step count and every configuration and velocity grid dimension; defaults retain upstream values. The x86 survey of 2026-09-06 ran the driver in 4.6 s on one core with the source build excluded.

## The two initial conditions

The nominal input keeps n0=1.0; the variant changes it to 1.0000000000000004, exactly two upward binary64 ULP. `n0` is the reference density, which sets the initial distribution and the plasma frequency (a two-ULP change of the 1e-4 perturbation amplitude alpha was found to vanish in the 1 + alpha cos(kx) sum and left the output byte-identical), so calibration tests sensitivity without changing the physics problem. `run.sh altbuild` runs the same nominal inputs on a strict-IEEE build of the same source (gcc -O2, no -ffast-math, -ffp-contract=off, no -march=native); self-validation grades it against the default build and records the distance as this check's floor.

## The pass policy

Every payload value in the Gkeyll dynamic-vector histories `elc-imom.gkyl`, `elc-L2.gkyl`, `field-energy.gkyl` is compared pointwise; samples are matched on their recorded physical time (both time axes must be finite and non-decreasing, or the file fails) (within 1e-8 of the window), so neither the sample count nor the step sequence is graded; a reference time with no candidate sample fails. Every graded value must satisfy |err| <= atol + rtol*|ref| with `atol=1e-11, rtol=1e-11`. The bound is physical because a wrong Poisson solve, a wrong periodic boundary or a wrong electrostatic acceleration changes the graded values at order one, and achievable because the two-ULP variant and the strict-IEEE altbuild, the two legitimate perturbations measured below, stay under it.

## Evidence

The calibration selfcheck of 2026-09-06 on the x86 worker 136.114.2.6 (1 cpu, 4 GB, Docker) measured 9.4 s of run time with the driver build excluded. The two-ULP variant moved the graded values by at most `1.8e-14` absolute (worst file `elc-imom.gkyl`, using 6.2e-4 of its bound); the strict-IEEE altbuild (same source, gcc -O2 strict IEEE: no -ffast-math, -ffp-contract=off, no -march=native (build-ieee/)) by at most `6.0e-14` absolute (worst file `elc-L2.gkyl`, 1.3e-3 of its bound). Under the bound `atol=1e-11, rtol=1e-11` the largest fraction of any per-value bound used by either legitimate perturbation is 1.3e-3, a headroom of about 758x. Self-validation grades nominal against variant and nominal against altbuild with this validate.py and writes both numbers into rubric.json.
