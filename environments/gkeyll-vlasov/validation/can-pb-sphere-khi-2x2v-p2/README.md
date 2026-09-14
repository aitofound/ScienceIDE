# can-pb-sphere-khi-2x2v-p2

Upstream test: code/gkeyll/vlasov/creg/rt_can_pb_bgk_surf_sphere_khi_im_2x2v_p2.c. Policy: pointwise.

## The test

run.sh builds and executes the complete upstream driver at its original resolution and physical end time: Upstream P2 2x2v Kelvin-Helmholtz shear on a spherical surface (32x32 angular cells, 8x8 velocity cells) through t=0.01 with implicit BGK collisions at nu=15000. It grades the complete neutral integrated-moment and distribution-L2 histories. This configuration forces the 2x2v canonical Poisson-bracket kernels on a spherical metric with counter-streaming shear layers, the largest kernel family of the module in its two-configuration-dimension form. Runtime knobs expose the step count and every configuration and velocity grid dimension; defaults retain upstream values. The x86 survey of 2026-09-06 ran the driver in 48.9 s on one core with the source build excluded.

## The two initial conditions

The nominal input keeps nl=2.0; the variant changes it to 2.000000000000001, exactly two upward binary64 ULP. `nl` is the density of the inner shear layer, so calibration tests sensitivity without changing the physics problem. `run.sh altbuild` runs the same nominal inputs on a strict-IEEE build of the same source (gcc -O2, no -ffast-math, -ffp-contract=off, no -march=native); self-validation grades it against the default build and records the distance as this check's floor.

## The pass policy

Every payload value in the Gkeyll dynamic-vector histories `neut-imom.gkyl`, `neut-L2.gkyl` is compared pointwise; samples are matched on their recorded physical time (both time axes must be finite and non-decreasing, or the file fails) (within 1e-8 of the window), so neither the sample count nor the step sequence is graded; a reference time with no candidate sample fails. Every graded value must satisfy |err| <= atol + rtol*|ref| with `atol=1e-11, rtol=1e-11`. The bound is physical because a wrong spherical metric, a wrong 2x2v surface flux or a wrong implicit BGK update changes the graded values at order one, and achievable because the two-ULP variant and the strict-IEEE altbuild, the two legitimate perturbations measured below, stay under it.

## Evidence

The calibration selfcheck of 2026-09-06 on the x86 worker 136.114.2.6 (1 cpu, 4 GB, Docker) measured 59.6 s of run time with the driver build excluded. The two-ULP variant moved the graded values by at most `2.3e-14` absolute (worst file `neut-imom.gkyl`, using 1.9e-4 of its bound); the strict-IEEE altbuild (same source, gcc -O2 strict IEEE: no -ffast-math, -ffp-contract=off, no -march=native (build-ieee/)) by at most `2.1e-14` absolute (worst file `neut-imom.gkyl`, 1.0e-4 of its bound). Under the bound `atol=1e-11, rtol=1e-11` the largest fraction of any per-value bound used by either legitimate perturbation is 1.9e-4, a headroom of about 5329x. Self-validation grades nominal against variant and nominal against altbuild with this validate.py and writes both numbers into rubric.json.
