# vlasov-weibel-2x2v-p1

Upstream test: code/gkeyll/vlasov/creg/rt_vlasov_weibel_2x2v_p1.c. Policy: pointwise.

## The test

run.sh builds and executes the complete upstream driver at its original resolution and physical end time: Upstream P1 2x2v Weibel instability (8x8 configuration cells, 16x16 velocity cells) through t=80 with self-consistent Vlasov-Maxwell coupling. It grades the complete electron integrated-moment, distribution-L2 and field-energy histories. This configuration forces the four-dimensional (2x2v) Vlasov-Maxwell kernels at P1: two configuration dimensions of Maxwell coupling, absent from every 1x check. Runtime knobs expose the step count and every configuration and velocity grid dimension; defaults retain upstream values. The x86 survey of 2026-09-06 ran the driver in 35.5 s on one core with the source build excluded.

## The two initial conditions

The nominal input keeps alpha=1.18281106421231; the variant changes it to 1.1828110642123104, exactly two upward binary64 ULP. `alpha` is the amplitude of the seed perturbation, so calibration tests sensitivity without changing the physics problem. `run.sh altbuild` runs the same nominal inputs on a strict-IEEE build of the same source (gcc -O2, no -ffast-math, -ffp-contract=off, no -march=native); self-validation grades it against the default build and records the distance as this check's floor.

## The pass policy

Every payload value in the Gkeyll dynamic-vector histories `elc-imom.gkyl`, `elc-L2.gkyl`, `field-energy.gkyl` is compared pointwise; samples are matched on their recorded physical time (both time axes must be finite and non-decreasing, or the file fails) (within 1e-8 of the window), so neither the sample count nor the step sequence is graded; a reference time with no candidate sample fails. Every graded value must satisfy |err| <= atol + rtol*|ref| with `atol=1e-09, rtol=1e-09`. The bound is physical because a wrong 2x2v surface flux, a wrong two-dimensional Maxwell update or a wrong current coupling changes the graded values at order one, and achievable because the two-ULP variant and the strict-IEEE altbuild, the two legitimate perturbations measured below, stay under it.

## Evidence

The calibration selfcheck of 2026-09-06 on the x86 worker 136.114.2.6 (1 cpu, 4 GB, Docker) measured 67.4 s of run time with the driver build excluded. The two-ULP variant moved the graded values by at most `1.2e-10` absolute (worst file `elc-L2.gkyl`, using 3.7e-4 of its bound); the strict-IEEE altbuild (same source, gcc -O2 strict IEEE: no -ffast-math, -ffp-contract=off, no -march=native (build-ieee/)) by at most `7.4e-10` absolute (worst file `elc-L2.gkyl`, 2.3e-3 of its bound). Under the bound `atol=1e-09, rtol=1e-09` the largest fraction of any per-value bound used by either legitimate perturbation is 2.3e-3, a headroom of about 427x. Self-validation grades nominal against variant and nominal against altbuild with this validate.py and writes both numbers into rubric.json.
