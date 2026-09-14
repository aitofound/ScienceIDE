# dg-five-moment-beach-p2

Upstream test: code/gkeyll/vlasov/creg/rt_dg_5m_mom_beach_p2.c. Policy: pointwise.

## The test

run.sh builds and executes the complete upstream driver at its original resolution and physical end time: Upstream P2 plasma-beach problem (200 cells, 5 ns, SI units): a DG five-moment electron fluid driven by an applied current against a density ramp, coupled to the Maxwell field. It grades the final electron five-moment frame, the final field frame and the complete field-energy history. This configuration forces the DG five-moment fluid species with an applied current source coupled to the DG Maxwell solver, the fluid-field coupling of the vlasov app. Runtime knobs expose the step count and every configuration and velocity grid dimension; defaults retain upstream values. The x86 survey of 2026-09-06 ran the driver in 3.4 s on one core with the source build excluded.

## The two initial conditions

The nominal input keeps J0=1.0e-12; the variant changes it to 1.0000000000000004e-12, exactly two upward binary64 ULP. `J0` is the amplitude of the applied current, so calibration tests sensitivity without changing the physics problem. `run.sh altbuild` runs the same nominal inputs on a strict-IEEE build of the same source (gcc -O2, no -ffast-math, -ffp-contract=off, no -march=native); self-validation grades it against the default build and records the distance as this check's floor.

## The pass policy

Every payload value in the Gkeyll dynamic-vector histories `field-energy.gkyl` is compared pointwise; samples are matched on their recorded physical time (both time axes must be finite and non-decreasing, or the file fails) (within 1e-8 of the window), so neither the sample count nor the step sequence is graded; a reference time with no candidate sample fails; every payload value and the grid extents of the final frames `elc.gkyl`, `field.gkyl` are compared pointwise with the cell count and element width required to match exactly. Every graded value must satisfy |err| <= atol + rtol*|ref| with `atol=1e-08, rtol=1e-08`. The bound is physical because a wrong applied-current source, a wrong fluid-Maxwell coupling or a wrong five-moment flux changes the graded values at order one, and achievable because the two-ULP variant and the strict-IEEE altbuild, the two legitimate perturbations measured below, stay under it.

## Evidence

The calibration selfcheck of 2026-09-06 on the x86 worker 136.114.2.6 (1 cpu, 4 GB, Docker) measured 9.4 s of run time with the driver build excluded. The two-ULP variant moved the graded values by at most `2.4e-12` absolute (worst file `field.gkyl`, using 2.4e-4 of its bound); the strict-IEEE altbuild (same source, gcc -O2 strict IEEE: no -ffast-math, -ffp-contract=off, no -march=native (build-ieee/)) by at most `5.4e-11` absolute (worst file `field.gkyl`, 4.5e-3 of its bound). Under the bound `atol=1e-08, rtol=1e-08` the largest fraction of any per-value bound used by either legitimate perturbation is 4.5e-3, a headroom of about 223x. Self-validation grades nominal against variant and nominal against altbuild with this validate.py and writes both numbers into rubric.json.
