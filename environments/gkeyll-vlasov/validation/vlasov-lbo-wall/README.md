# vlasov-lbo-wall

Upstream test: code/gkeyll/vlasov/creg/rt_vlasov_neut_lbo_wall.c. Policy: pointwise.

## The test

run.sh builds and executes the complete upstream driver at its original resolution and physical end time: Upstream P2 1x1v drifting neutral gas hitting reflecting walls (128x16 cells) through t=0.3 with LBO collisions at nu=10. It grades the complete neutral integrated-moment and distribution-L2 histories. This configuration forces the reflecting species boundary in combination with the LBO operator: a wall-driven flow reversal and the collisional relaxation behind it. Runtime knobs expose the step count and every configuration and velocity grid dimension; defaults retain upstream values. The x86 survey of 2026-09-06 ran the driver in 3.8 s on one core with the source build excluded.

## The two initial conditions

The nominal input keeps u0=1.0; the variant changes it to 1.0000000000000004, exactly two upward binary64 ULP. `u0` is the initial drift velocity toward the wall, so calibration tests sensitivity without changing the physics problem. `run.sh altbuild` runs the same nominal inputs on a strict-IEEE build of the same source (gcc -O2, no -ffast-math, -ffp-contract=off, no -march=native); self-validation grades it against the default build and records the distance as this check's floor.

## The pass policy

Every payload value in the Gkeyll dynamic-vector histories `neut-imom.gkyl`, `neut-L2.gkyl` is compared pointwise; samples are matched on their recorded physical time (both time axes must be finite and non-decreasing, or the file fails) (within 1e-8 of the window), so neither the sample count nor the step sequence is graded; a reference time with no candidate sample fails. Every graded value must satisfy |err| <= atol + rtol*|ref| with `atol=1e-11, rtol=1e-11`. The bound is physical because a wrong reflecting boundary, a wrong LBO drag or diffusion coefficient changes the graded values at order one, and achievable because the two-ULP variant and the strict-IEEE altbuild, the two legitimate perturbations measured below, stay under it.

## Evidence

The calibration selfcheck of 2026-09-06 on the x86 worker 136.114.2.6 (1 cpu, 4 GB, Docker) measured 6.8 s of run time with the driver build excluded. The two-ULP variant moved the graded values by at most `6.2e-15` absolute (worst file `neut-imom.gkyl`, using 2.8e-4 of its bound); the strict-IEEE altbuild (same source, gcc -O2 strict IEEE: no -ffast-math, -ffp-contract=off, no -march=native (build-ieee/)) by at most `5.8e-15` absolute (worst file `neut-imom.gkyl`, 2.6e-4 of its bound). Under the bound `atol=1e-11, rtol=1e-11` the largest fraction of any per-value bound used by either legitimate perturbation is 2.8e-4, a headroom of about 3619x. Self-validation grades nominal against variant and nominal against altbuild with this validate.py and writes both numbers into rubric.json.
