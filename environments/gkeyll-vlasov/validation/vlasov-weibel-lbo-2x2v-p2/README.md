# vlasov-weibel-lbo-2x2v-p2

Upstream test: code/gkeyll/vlasov/creg/rt_vlasov_weibel_lbo_2x2v_p2.c. Policy: pointwise.

## The test

run.sh builds and executes the complete upstream driver at its original resolution and physical end time: Upstream P2 2x2v Weibel instability with LBO collisions (8x8 configuration cells, 16x16 velocity cells) through t=5. It grades the complete electron integrated-moment, distribution-L2 and field-energy histories. This configuration forces the 2x2v Vlasov-Maxwell kernels at P2 together with the 2x2v LBO collision kernels. Runtime knobs expose the step count and every configuration and velocity grid dimension; defaults retain upstream values. The x86 survey of 2026-09-06 ran the driver in 22.0 s on one core with the source build excluded.

## The two initial conditions

The nominal input keeps alpha=1.18281106421231; the variant changes it to 1.1828110642123104, exactly two upward binary64 ULP. `alpha` is the amplitude of the seed perturbation, so calibration tests sensitivity without changing the physics problem. `run.sh altbuild` runs the same nominal inputs on a strict-IEEE build of the same source (gcc -O2, no -ffast-math, -ffp-contract=off, no -march=native); self-validation grades it against the default build and records the distance as this check's floor.

## The pass policy

Every payload value in the Gkeyll dynamic-vector histories `elc-imom.gkyl`, `elc-L2.gkyl`, `field-energy.gkyl` is compared pointwise; samples are matched on their recorded physical time (both time axes must be finite and non-decreasing, or the file fails) (within 1e-8 of the window), so neither the sample count nor the step sequence is graded; a reference time with no candidate sample fails. Every graded value must satisfy |err| <= atol + rtol*|ref| with `atol=1e-11, rtol=1e-11`. The bound is physical because a wrong 2x2v P2 flux, a wrong 2x2v LBO diffusion or a wrong Maxwell coupling changes the graded values at order one, and achievable because the two-ULP variant and the strict-IEEE altbuild, the two legitimate perturbations measured below, stay under it.

## Evidence

The calibration selfcheck of 2026-09-06 on the x86 worker 136.114.2.6 (1 cpu, 4 GB, Docker) measured 37.5 s of run time with the driver build excluded. The two-ULP variant moved the graded values by at most `1.1e-13` absolute (worst file `elc-imom.gkyl`, using 4.5e-5 of its bound); the strict-IEEE altbuild (same source, gcc -O2 strict IEEE: no -ffast-math, -ffp-contract=off, no -march=native (build-ieee/)) by at most `5.1e-13` absolute (worst file `elc-imom.gkyl`, 1.1e-3 of its bound). Under the bound `atol=1e-11, rtol=1e-11` the largest fraction of any per-value bound used by either legitimate perturbation is 1.1e-3, a headroom of about 952x. Self-validation grades nominal against variant and nominal against altbuild with this validate.py and writes both numbers into rubric.json.
