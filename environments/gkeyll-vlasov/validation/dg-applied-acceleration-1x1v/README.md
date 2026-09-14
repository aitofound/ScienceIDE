# dg-applied-acceleration-1x1v

Upstream test: code/gkeyll/vlasov/creg/rt_dg_accel_1x1v.c. Policy: pointwise.

## The test

run.sh builds and executes the complete upstream driver at its original resolution and physical end time: Upstream P2 1x1v electron distribution under a prescribed sinusoidal applied acceleration with a static field (32x24 cells) through t=3. It grades the final electron distribution frame, its density, momentum and energy moment frames and the final field frame. This configuration forces the applied-acceleration source path (`app_accel`) of the Vlasov species with a static field. Runtime knobs expose the step count and every configuration and velocity grid dimension; defaults retain upstream values. The x86 survey of 2026-09-06 ran the driver in 0.5 s on one core with the source build excluded.

## The two initial conditions

The nominal input keeps Lvx=12.0; the variant changes it to 12.000000000000004, exactly two upward binary64 ULP. `Lvx` is the velocity-space extent, so the variant moves every cell centre and the graded grid extents by one part in 1e16 (the driver takes its mass, charge and initial distribution as fixed literals inside its functions, so no physics scalar reaches the species; the electron-mass literal left the output byte-identical), so calibration tests sensitivity without changing the physics problem. `run.sh altbuild` runs the same nominal inputs on a strict-IEEE build of the same source (gcc -O2, no -ffast-math, -ffp-contract=off, no -march=native); self-validation grades it against the default build and records the distance as this check's floor.

## The pass policy

Every payload value and the grid extents of the final frames `elc.gkyl`, `elc-m0.gkyl`, `elc-m1.gkyl`, `elc-m2.gkyl`, `field.gkyl` are compared pointwise with the cell count and element width required to match exactly. Every graded value must satisfy |err| <= atol + rtol*|ref| with `atol=1e-11, rtol=1e-11`. The bound is physical because a wrong applied-acceleration term or a wrong velocity-space flux changes the graded values at order one, and achievable because the two-ULP variant and the strict-IEEE altbuild, the two legitimate perturbations measured below, stay under it.

## Evidence

The calibration selfcheck of 2026-09-06 on the x86 worker 136.114.2.6 (1 cpu, 4 GB, Docker) measured 1.2 s of run time with the driver build excluded. The two-ULP variant moved the graded values by at most `2.7e-15` absolute (worst file `elc.gkyl`, using 1.4e-4 of its bound); the strict-IEEE altbuild (same source, gcc -O2 strict IEEE: no -ffast-math, -ffp-contract=off, no -march=native (build-ieee/)) by at most `4.6e-15` absolute (worst file `elc.gkyl`, 2.7e-4 of its bound). Under the bound `atol=1e-11, rtol=1e-11` the largest fraction of any per-value bound used by either legitimate perturbation is 2.7e-4, a headroom of about 3748x. Self-validation grades nominal against variant and nominal against altbuild with this validate.py and writes both numbers into rubric.json.
