# dg-hyperdiffusion4-3x

Upstream test: code/gkeyll/vlasov/creg/rt_dg_diffusion4_const_3x.c. Policy: pointwise.

## The test

run.sh builds and executes the complete upstream driver at its original resolution and physical end time: Upstream P2 three-dimensional fourth-order (hyper-)diffusion with a constant coefficient (4x4x4 cells) through t=0.1 as a fluid species of the vlasov app. It grades the final scalar frame. This configuration forces the fourth-order constant-coefficient DG diffusion kernels (`dg_diffusion` order 4), a different recovery stencil from second-order diffusion. Runtime knobs expose the step count and every configuration and velocity grid dimension; defaults retain upstream values. The x86 survey of 2026-09-06 ran the driver in 0.5 s on one core with the source build excluded.

## The two initial conditions

The nominal input keeps diffusion_coeff=1.0; the variant changes it to 1.0000000000000004, exactly two upward binary64 ULP. `diffusion_coeff` scales the hyper-diffusion coefficient, so calibration tests sensitivity without changing the physics problem. `run.sh altbuild` runs the same nominal inputs on a strict-IEEE build of the same source (gcc -O2, no -ffast-math, -ffp-contract=off, no -march=native); self-validation grades it against the default build and records the distance as this check's floor.

## The pass policy

Every payload value and the grid extents of the final frame `q.gkyl` are compared pointwise with the cell count and element width required to match exactly. Every graded value must satisfy |err| <= atol + rtol*|ref| with `atol=1e-11, rtol=1e-11`. The bound is physical because a wrong fourth-order recovery or a wrong sign of the hyper-diffusion term changes the graded values at order one, and achievable because the two-ULP variant and the strict-IEEE altbuild, the two legitimate perturbations measured below, stay under it.

## Evidence

The calibration selfcheck of 2026-09-06 on the x86 worker 136.114.2.6 (1 cpu, 4 GB, Docker) measured 4.0 s of run time with the driver build excluded. The two-ULP variant moved the graded values by at most `2.2e-16` absolute (worst file `q.gkyl`, using 1.4e-5 of its bound); the strict-IEEE altbuild (same source, gcc -O2 strict IEEE: no -ffast-math, -ffp-contract=off, no -march=native (build-ieee/)) by at most `1.1e-15` absolute (worst file `q.gkyl`, 7.2e-5 of its bound). Under the bound `atol=1e-11, rtol=1e-11` the largest fraction of any per-value bound used by either legitimate perturbation is 7.2e-5, a headroom of about 13842x. Self-validation grades nominal against variant and nominal against altbuild with this validate.py and writes both numbers into rubric.json.
