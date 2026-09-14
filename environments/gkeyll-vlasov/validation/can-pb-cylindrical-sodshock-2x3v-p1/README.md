# can-pb-cylindrical-sodshock-2x3v-p1

Upstream test: code/gkeyll/vlasov/creg/rt_can_pb_bgk_surf_cylindrical_sodshock_im_2x3v_p1.c. Policy: pointwise.

## The test

run.sh builds and executes the complete upstream driver at its original resolution and physical end time: Upstream P1 2x3v Sod shock on a cylindrical surface (32x1 configuration cells, 4x4x4 velocity cells) through t=0.1 with implicit BGK collisions at nu=15000 and reflecting radial boundaries. It grades the complete neutral integrated-moment and distribution-L2 histories plus the final energy-moment frame. This configuration forces the five-dimensional (2x3v) canonical Poisson-bracket kernels on a cylindrical metric, the P1 basis and the energy-moment diagnostic (the toroidal twin, rt_can_pb_bgk_surf_toroidal_sodshock_im_2x3v_p1, is numerically unstable at the pin and was not selected). Runtime knobs expose the step count and every configuration and velocity grid dimension; defaults retain upstream values. The x86 survey of 2026-09-06 ran the driver in 41.0 s on one core with the source build excluded.

## The two initial conditions

The nominal input keeps nl=1.0; the variant changes it to 1.0000000000000004, exactly two upward binary64 ULP. `nl` is the inner density of the discontinuity, so calibration tests sensitivity without changing the physics problem. `run.sh altbuild` runs the same nominal inputs on a strict-IEEE build of the same source (gcc -O2, no -ffast-math, -ffp-contract=off, no -march=native); self-validation grades it against the default build and records the distance as this check's floor.

## The pass policy

Every payload value in the Gkeyll dynamic-vector histories `neut-imom.gkyl`, `neut-L2.gkyl` is compared pointwise; samples are matched on their recorded physical time (both time axes must be finite and non-decreasing, or the file fails) (within 1e-8 of the window), so neither the sample count nor the step sequence is graded; a reference time with no candidate sample fails; every payload value and the grid extents of the final frame `neut-energy-moment.gkyl` are compared pointwise with the cell count and element width required to match exactly. Every graded value must satisfy |err| <= atol + rtol*|ref| with `atol=1e-11, rtol=1e-11`. The bound is physical because a wrong cylindrical metric, a wrong 2x3v surface term or a wrong implicit BGK step changes the graded values at order one, and achievable because the two-ULP variant and the strict-IEEE altbuild, the two legitimate perturbations measured below, stay under it.

## Evidence

The calibration selfcheck of 2026-09-06 on the x86 worker 136.114.2.6 (1 cpu, 4 GB, Docker) measured 45.1 s of run time with the driver build excluded. The two-ULP variant moved the graded values by at most `2.8e-14` absolute (worst file `neut-energy-moment.gkyl`, using 1.0e-3 of its bound); the strict-IEEE altbuild (same source, gcc -O2 strict IEEE: no -ffast-math, -ffp-contract=off, no -march=native (build-ieee/)) by at most `4.5e-14` absolute (worst file `neut-energy-moment.gkyl`, 1.7e-3 of its bound). Under the bound `atol=1e-11, rtol=1e-11` the largest fraction of any per-value bound used by either legitimate perturbation is 1.7e-3, a headroom of about 603x. Self-validation grades nominal against variant and nominal against altbuild with this validate.py and writes both numbers into rubric.json.
