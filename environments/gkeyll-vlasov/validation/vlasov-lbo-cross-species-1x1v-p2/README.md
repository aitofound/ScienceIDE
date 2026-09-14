# vlasov-lbo-cross-species-1x1v-p2

Upstream test: code/gkeyll/vlasov/creg/rt_vlasov_lbo_cross_1x1v_p2.c. Policy: pointwise.

## The test

run.sh builds and executes the complete upstream driver at its original resolution and physical end time: Upstream P2 1x1v relaxation of two neutral species with a 20:1 mass ratio (16x32 cells) through t=0.0025 with self and cross-species LBO collisions. It grades the complete integrated-moment and distribution-L2 histories of both species. This configuration forces the cross-species LBO operator (`cross_nu`, the Greene-weighted exchange of momentum and energy between species), untouched by the single-species LBO checks. Runtime knobs expose the step count and every configuration and velocity grid dimension; defaults retain upstream values. The x86 survey of 2026-09-06 ran the driver in 1.4 s on one core with the source build excluded.

## The two initial conditions

The nominal input keeps n0_neut1=1.0; the variant changes it to 1.0000000000000004, exactly two upward binary64 ULP. `n0_neut1` is the reference density of the heavy species, so calibration tests sensitivity without changing the physics problem. `run.sh altbuild` runs the same nominal inputs on a strict-IEEE build of the same source (gcc -O2, no -ffast-math, -ffp-contract=off, no -march=native); self-validation grades it against the default build and records the distance as this check's floor.

## The pass policy

Every payload value in the Gkeyll dynamic-vector histories `neut1-imom.gkyl`, `neut2-imom.gkyl`, `neut1-L2.gkyl`, `neut2-L2.gkyl` is compared pointwise; samples are matched on their recorded physical time (both time axes must be finite and non-decreasing, or the file fails) (within 1e-8 of the window), so neither the sample count nor the step sequence is graded; a reference time with no candidate sample fails. Every graded value must satisfy |err| <= atol + rtol*|ref| with `atol=1e-11, rtol=1e-11`. The bound is physical because a wrong cross-collision frequency, a wrong momentum or energy exchange or a wrong primitive-moment solve changes the graded values at order one, and achievable because the two-ULP variant and the strict-IEEE altbuild, the two legitimate perturbations measured below, stay under it.

## Evidence

The calibration selfcheck of 2026-09-06 on the x86 worker 136.114.2.6 (1 cpu, 4 GB, Docker) measured 3.7 s of run time with the driver build excluded. The two-ULP variant moved the graded values by at most `2.5e-14` absolute (worst file `neut2-imom.gkyl`, using 1.8e-4 of its bound); the strict-IEEE altbuild (same source, gcc -O2 strict IEEE: no -ffast-math, -ffp-contract=off, no -march=native (build-ieee/)) by at most `2.8e-14` absolute (worst file `neut2-imom.gkyl`, 1.7e-4 of its bound). Under the bound `atol=1e-11, rtol=1e-11` the largest fraction of any per-value bound used by either legitimate perturbation is 1.8e-4, a headroom of about 5545x. Self-validation grades nominal against variant and nominal against altbuild with this validate.py and writes both numbers into rubric.json.
