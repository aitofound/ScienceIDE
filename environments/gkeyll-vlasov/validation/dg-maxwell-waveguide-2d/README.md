# dg-maxwell-waveguide-2d

Upstream test: code/gkeyll/vlasov/creg/rt_dg_maxwell_wg_2d.c. Policy: pointwise.

## The test

run.sh builds and executes the complete upstream driver at its original resolution and physical end time: Upstream P2 two-dimensional DG Maxwell waveguide mode (70x50 cells) through ten periods with no kinetic species. It grades the final field frame and the complete field-energy history. This configuration forces the standalone DG Maxwell solver of the vlasov app in two dimensions, a blind spot the module's previous check set named. Runtime knobs expose the step count and every configuration and velocity grid dimension; defaults retain upstream values. The x86 survey of 2026-09-06 ran the driver in 7.7 s on one core with the source build excluded.

## The two initial conditions

The nominal input keeps epsilon0=1.0; the variant changes it to 1.0000000000000004, exactly two upward binary64 ULP. `epsilon0` is the permittivity, which sets the wave speed, so calibration tests sensitivity without changing the physics problem. `run.sh altbuild` runs the same nominal inputs on a strict-IEEE build of the same source (gcc -O2, no -ffast-math, -ffp-contract=off, no -march=native); self-validation grades it against the default build and records the distance as this check's floor.

## The pass policy

Every payload value in the Gkeyll dynamic-vector histories `field-energy.gkyl` is compared pointwise; samples are matched on their recorded physical time (both time axes must be finite and non-decreasing, or the file fails) (within 1e-8 of the window), so neither the sample count nor the step sequence is graded; a reference time with no candidate sample fails; every payload value and the grid extents of the final frame `field.gkyl` are compared pointwise with the cell count and element width required to match exactly. Every graded value must satisfy |err| <= atol + rtol*|ref| with `atol=1e-11, rtol=1e-11`. The bound is physical because a wrong Maxwell flux, a wrong divergence-cleaning potential or a wrong two-dimensional field update changes the graded values at order one, and achievable because the two-ULP variant and the strict-IEEE altbuild, the two legitimate perturbations measured below, stay under it.

## Evidence

The calibration selfcheck of 2026-09-06 on the x86 worker 136.114.2.6 (1 cpu, 4 GB, Docker) measured 13.4 s of run time with the driver build excluded. The two-ULP variant moved the graded values by at most `2.5e-13` absolute (worst file `field-energy.gkyl`, using 3.7e-3 of its bound); the strict-IEEE altbuild (same source, gcc -O2 strict IEEE: no -ffast-math, -ffp-contract=off, no -march=native (build-ieee/)) by at most `1.9e-13` absolute (worst file `field-energy.gkyl`, 4.0e-3 of its bound). Under the bound `atol=1e-11, rtol=1e-11` the largest fraction of any per-value bound used by either legitimate perturbation is 4.0e-3, a headroom of about 252x. Self-validation grades nominal against variant and nominal against altbuild with this validate.py and writes both numbers into rubric.json.
