# vp-sheath-1x1v-p2

Upstream test: code/gkeyll/vlasov/creg/rt_vp_sheath_1x1v_p2.c. Policy: pointwise.

## The test

run.sh builds and executes the complete upstream driver at its original resolution and physical end time: Upstream P2 1x1v electron-ion sheath through the Vlasov-Poisson app (64x16 cells, 100 inverse plasma frequencies) with absorbing lower and reflecting upper species boundaries and Dirichlet/Neumann Poisson boundary conditions, in SI units. It grades the complete electron and ion integrated-moment and distribution-L2 histories plus the electrostatic field energy. This configuration forces the Vlasov-Poisson sheath path: non-periodic Poisson boundary conditions, absorbing and reflecting species boundaries and the LTE projection of two species. Runtime knobs expose the step count and every configuration and velocity grid dimension; defaults retain upstream values. The x86 survey of 2026-09-06 ran the driver in 2.7 s on one core with the source build excluded.

## The two initial conditions

The nominal input keeps n0=1.0e18; the variant changes it to 1.0000000000000003e18, exactly two upward binary64 ULP. `n0` is the reference density that sets both initial Maxwellians and, through the Debye length, the domain, so calibration tests sensitivity without changing the physics problem. `run.sh altbuild` runs the same nominal inputs on a strict-IEEE build of the same source (gcc -O2, no -ffast-math, -ffp-contract=off, no -march=native); self-validation grades it against the default build and records the distance as this check's floor.

## The pass policy

Every payload value in the Gkeyll dynamic-vector histories `elc-imom.gkyl`, `ion-imom.gkyl`, `elc-L2.gkyl`, `ion-L2.gkyl`, `field-energy.gkyl` is compared pointwise; samples are matched on their recorded physical time (both time axes must be finite and non-decreasing, or the file fails) (within 1e-8 of the window), so neither the sample count nor the step sequence is graded; a reference time with no candidate sample fails. Every graded value must satisfy |err| <= atol + rtol*|ref| with `atol=1e-10, rtol=1e-10`. In `elc-imom.gkyl` (3 values per sample) component 1 keeps atol=1e+11, rtol=1e-10, a residual-scale component graded on its own bound (see the rubric warrant). In `ion-imom.gkyl` (3 values per sample) component 1 keeps atol=1e+07, rtol=1e-10, a residual-scale component graded on its own bound (see the rubric warrant). The bound is physical because a wrong Poisson boundary condition, a wrong wall flux or a wrong charge sign changes the graded values at order one, and achievable because the two-ULP variant and the strict-IEEE altbuild, the two legitimate perturbations measured below, stay under it.

## Evidence

The calibration selfcheck of 2026-09-06 on the x86 worker 136.114.2.6 (1 cpu, 4 GB, Docker) measured 6.8 s of run time with the driver build excluded. The two-ULP variant moved the graded values by at most `7.4e13` absolute (worst file `elc-imom.gkyl`, using 9.0e-3 of its bound); the strict-IEEE altbuild (same source, gcc -O2 strict IEEE: no -ffast-math, -ffp-contract=off, no -march=native (build-ieee/)) by at most `2.2e14` absolute (worst file `field-energy.gkyl`, 6.8e-3 of its bound). Under the bound `atol=1e-10, rtol=1e-10` with the component overrides above the largest fraction of any per-value bound used by either legitimate perturbation is 9.0e-3, a headroom of about 112x. Self-validation grades nominal against variant and nominal against altbuild with this validate.py and writes both numbers into rubric.json.
