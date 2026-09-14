# can-pb-implicit-bgk-flat

Upstream test: code/gkeyll/vlasov/creg/rt_can_pb_im_bgk_surf_flat.c. Policy: pointwise.

## The test

run.sh builds and executes the complete upstream driver at its original resolution and physical end time: The implicit twin of can-pb-explicit-bgk-flat: the same P2 2x2v flat-metric relaxation through t=0.1 with the implicit BGK scheme, which takes far fewer steps at nu=15000. It grades the complete neutral integrated-moment and distribution-L2 histories. This configuration forces the implicit BGK collision scheme on the canonical Poisson-bracket model, whose step count differs from the explicit twin by two orders of magnitude. Runtime knobs expose the step count and every configuration and velocity grid dimension; defaults retain upstream values. The x86 survey of 2026-09-06 ran the driver in 0.5 s on one core with the source build excluded.

## The two initial conditions

The nominal input keeps n0=1.0; the variant changes it to 1.0000000000000004, exactly two upward binary64 ULP. `n0` is the reference density of the initial distribution, so calibration tests sensitivity without changing the physics problem. `run.sh altbuild` runs the same nominal inputs on a strict-IEEE build of the same source (gcc -O2, no -ffast-math, -ffp-contract=off, no -march=native); self-validation grades it against the default build and records the distance as this check's floor.

## The pass policy

Every payload value in the Gkeyll dynamic-vector histories `neut-imom.gkyl`, `neut-L2.gkyl` is compared pointwise; samples are matched on their recorded physical time (both time axes must be finite and non-decreasing, or the file fails) (within 1e-8 of the window), so neither the sample count nor the step sequence is graded; a reference time with no candidate sample fails. Every graded value must satisfy |err| <= atol + rtol*|ref| with `atol=1e-11, rtol=1e-11`. The bound is physical because a wrong implicit relaxation factor or a wrong LTE projection changes the graded values at order one, and achievable because the two-ULP variant and the strict-IEEE altbuild, the two legitimate perturbations measured below, stay under it.

## Evidence

The calibration selfcheck of 2026-09-06 on the x86 worker 136.114.2.6 (1 cpu, 4 GB, Docker) measured 2.2 s of run time with the driver build excluded. The two-ULP variant moved the graded values by at most `8.9e-16` absolute (worst file `neut-imom.gkyl`, using 4.4e-5 of its bound); the strict-IEEE altbuild (same source, gcc -O2 strict IEEE: no -ffast-math, -ffp-contract=off, no -march=native (build-ieee/)) by at most `1.8e-15` absolute (worst file `neut-imom.gkyl`, 8.9e-5 of its bound). Under the bound `atol=1e-11, rtol=1e-11` the largest fraction of any per-value bound used by either legitimate perturbation is 8.9e-5, a headroom of about 11259x. Self-validation grades nominal against variant and nominal against altbuild with this validate.py and writes both numbers into rubric.json.
