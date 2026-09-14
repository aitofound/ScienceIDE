# dg-euler-sodshock-p2

Upstream test: code/gkeyll/vlasov/creg/rt_dg_euler_sodshock_p2.c. Policy: pointwise.

## The test

run.sh builds and executes the complete upstream driver at its original resolution and physical end time: Upstream P2 DG Euler Sod shock (512 cells) through t=0.1 as a fluid species of the vlasov app. It grades the final conserved-variable and primitive-variable frames of the fluid species. This configuration forces the DG fluid-species path of the vlasov app: the modal Euler flux, the primitive-variable recovery and the fluid time stepper (`gkyl_vlasov_fluid_species`), used by 24 drivers and by no other check. Runtime knobs expose the step count and every configuration and velocity grid dimension; defaults retain upstream values. The x86 survey of 2026-09-06 ran the driver in 1.7 s on one core with the source build excluded.

## The two initial conditions

The nominal input keeps rhol=3.0; the variant changes it to 3.000000000000001, exactly two upward binary64 ULP. `rhol` is the left-state density of the Riemann problem, so calibration tests sensitivity without changing the physics problem. `run.sh altbuild` runs the same nominal inputs on a strict-IEEE build of the same source (gcc -O2, no -ffast-math, -ffp-contract=off, no -march=native); self-validation grades it against the default build and records the distance as this check's floor.

## The pass policy

Every payload value and the grid extents of the final frames `euler.gkyl`, `euler-prim-vars.gkyl` are compared pointwise with the cell count and element width required to match exactly. Every graded value must satisfy |err| <= atol + rtol*|ref| with `atol=1e-07, rtol=1e-07`. The bound is physical because a wrong Euler flux, a wrong primitive-variable recovery or a wrong limiter changes the graded values at order one, and achievable because the two-ULP variant and the strict-IEEE altbuild, the two legitimate perturbations measured below, stay under it.

## Evidence

The calibration selfcheck of 2026-09-06 on the x86 worker 136.114.2.6 (1 cpu, 4 GB, Docker) measured 4.3 s of run time with the driver build excluded. The two-ULP variant moved the graded values by at most `8.2e-10` absolute (worst file `euler.gkyl`, using 3.1e-3 of its bound); the strict-IEEE altbuild (same source, gcc -O2 strict IEEE: no -ffast-math, -ffp-contract=off, no -march=native (build-ieee/)) by at most `3.4e-10` absolute (worst file `euler.gkyl`, 1.1e-3 of its bound). Under the bound `atol=1e-07, rtol=1e-07` the largest fraction of any per-value bound used by either legitimate perturbation is 3.1e-3, a headroom of about 324x. Self-validation grades nominal against variant and nominal against altbuild with this validate.py and writes both numbers into rubric.json.
