# can-pb-newtonian-orbits-2x2v-p2

Upstream test: code/gkeyll/vlasov/creg/rt_can_pb_newtonian_orbits_2x2v_p2.c. Policy: pointwise.

## The test

run.sh builds and executes the complete upstream driver at its original resolution and physical end time: Upstream P2 2x2v collisionless Newtonian orbits around a point mass in polar coordinates (16x32 configuration cells, 8x32 velocity cells) through t=0.001 with absorbing radial boundaries. It grades the neutral integrated-moment and distribution-L2 histories plus the final density and Hamiltonian-derived momentum frames. This configuration forces the canonical Poisson-bracket model with a gravitational Hamiltonian in polar geometry, absorbing boundaries and the `M1_from_H` moment. Runtime knobs expose the step count and every configuration and velocity grid dimension; defaults retain upstream values. The x86 survey of 2026-09-06 ran the driver in 8.1 s on one core with the source build excluded.

## The two initial conditions

The nominal input keeps vt=1.0; the variant changes it to 1.0000000000000004, exactly two upward binary64 ULP. `vt` is the thermal velocity of the initial orbiting distribution, so calibration tests sensitivity without changing the physics problem. `run.sh altbuild` runs the same nominal inputs on a strict-IEEE build of the same source (gcc -O2, no -ffast-math, -ffp-contract=off, no -march=native); self-validation grades it against the default build and records the distance as this check's floor.

## The pass policy

Every payload value in the Gkeyll dynamic-vector histories `neut-imom.gkyl`, `neut-L2.gkyl` is compared pointwise; samples are matched on their recorded physical time (both time axes must be finite and non-decreasing, or the file fails) (within 1e-8 of the window), so neither the sample count nor the step sequence is graded; a reference time with no candidate sample fails; every payload value and the grid extents of the final frames `neut-m0.gkyl`, `neut-m1-from-h.gkyl` are compared pointwise with the cell count and element width required to match exactly. Every graded value must satisfy |err| <= atol + rtol*|ref| with `atol=1e-11, rtol=1e-11`. The bound is physical because a wrong Hamiltonian gradient, a wrong polar metric or a wrong absorbing boundary changes the graded values at order one, and achievable because the two-ULP variant and the strict-IEEE altbuild, the two legitimate perturbations measured below, stay under it.

## Evidence

The calibration selfcheck of 2026-09-06 on the x86 worker 136.114.2.6 (1 cpu, 4 GB, Docker) measured 14.2 s of run time with the driver build excluded. The two-ULP variant moved the graded values by at most `2.4e-16` absolute (worst file `neut-imom.gkyl`, using 2.3e-5 of its bound); the strict-IEEE altbuild (same source, gcc -O2 strict IEEE: no -ffast-math, -ffp-contract=off, no -march=native (build-ieee/)) by at most `9.7e-17` absolute (worst file `neut-imom.gkyl`, 8.9e-6 of its bound). Under the bound `atol=1e-11, rtol=1e-11` the largest fraction of any per-value bound used by either legitimate perturbation is 2.3e-5, a headroom of about 43130x. Self-validation grades nominal against variant and nominal against altbuild with this validate.py and writes both numbers into rubric.json.
