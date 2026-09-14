# dg-advection-2x-p2

Upstream test: code/gkeyll/vlasov/creg/rt_dg_advect_2x_p2.c. Policy: pointwise.

## The test

run.sh builds and executes the complete upstream driver at its original resolution and physical end time: Upstream P2 two-dimensional DG scalar advection of a cylinder (16x16 cells) through one rotation period as a fluid species of the vlasov app. It grades the final scalar frame. This configuration forces the DG advection fluid species with a prescribed velocity field in two dimensions. Runtime knobs expose the step count and every configuration and velocity grid dimension; defaults retain upstream values. The x86 survey of 2026-09-06 ran the driver in 0.6 s on one core with the source build excluded.

## The two initial conditions

The nominal input keeps r0=0.2; the variant changes it to 0.20000000000000007, exactly two upward binary64 ULP. `r0` is the radius of the advected cylinder, so calibration tests sensitivity without changing the physics problem. `run.sh altbuild` runs the same nominal inputs on a strict-IEEE build of the same source (gcc -O2, no -ffast-math, -ffp-contract=off, no -march=native); self-validation grades it against the default build and records the distance as this check's floor.

## The pass policy

Every payload value and the grid extents of the final frame `q.gkyl` are compared pointwise with the cell count and element width required to match exactly. Every graded value must satisfy |err| <= atol + rtol*|ref| with `atol=1e-11, rtol=1e-11`. The bound is physical because a wrong upwind advection flux or a wrong two-dimensional modal update changes the graded values at order one, and achievable because the two-ULP variant and the strict-IEEE altbuild, the two legitimate perturbations measured below, stay under it.

## Evidence

The calibration selfcheck of 2026-09-06 on the x86 worker 136.114.2.6 (1 cpu, 4 GB, Docker) measured 1.1 s of run time with the driver build excluded. The two-ULP variant moved the graded values by at most `1.8e-15` absolute (worst file `q.gkyl`, using 1.2e-4 of its bound); the strict-IEEE altbuild (same source, gcc -O2 strict IEEE: no -ffast-math, -ffp-contract=off, no -march=native (build-ieee/)) by at most `3.0e-15` absolute (worst file `q.gkyl`, 1.6e-4 of its bound). Under the bound `atol=1e-11, rtol=1e-11` the largest fraction of any per-value bound used by either legitimate perturbation is 1.6e-4, a headroom of about 6197x. Self-validation grades nominal against variant and nominal against altbuild with this validate.py and writes both numbers into rubric.json.
