# so-box-obcs-saphe

Upstream test: `code/mitgcm/verification/so_box_biogeo/input.saphe`. Policy: `pointwise`.

## The test

Southern Ocean box, open boundaries and the SolveSAPHE pH solver. `run.sh` builds one MITgcm executable for this
configuration with the tree's own `tools/genmake2` (the build configuration
under `mods/`: `SIZE.h`, `packages.conf` and the option headers of the
upstream experiment, gfortran optfile `linux_amd64_gfortran`, one process,
tiles only), then runs it on the deck under `ic/<ic>/`. Configuration:
verification/so_box_biogeo/input with the input.saphe overlay: a 42x20x15 Southern Ocean box cut out of the global 2.8-degree grid (six tiles of 14x10, exactly conserving free surface, ivdc_kappa=10, GM/Redi) started cold from the deck's T, S, eta, velocity and five tracer initial files, with pkg/obcs prescribing western, eastern and northern boundary values for temperature, salinity, both velocity components and all five DIC tracers from monthly files plus connect masks, and first-order upwind advection at the boundaries (OBCS_u1_adv_Tr); the overlay replaces data.dic so that pkg/dic runs with the Munhoven (2013) SolveSAPHE GENERAL total-alkalinity solver (selectPHsolver=1) and the alternative borate, fluoride, HF and K1/K2 constants (selectBTconst=1, selectFTconst=1, selectHFconst=1, selectK1K2const=6) that the experiment's DIC_OPTIONS.h enables with CARBONCHEM_SOLVESAPHE and CARBONCHEM_TOTALPHSCALE; run 60 tracer steps of 43200 s (30 days, the deck runs 10) so that both the 10-step dynDiag and the 60-step surfDiag averaging streams complete exactly at the final iteration..

The production path it forces: pkg/dic/dic_solvesaphe.F SOLVE_AT_GENERAL, the bracketed Newton iteration on total alkalinity with the safeguarded ANW_INFSUP bounds and AHINI_FOR_AT initial guess, called for every surface wet cell every step, together with EQUATION_AT and DIC_COEFFS_SURF; then pkg/obcs (obcs_apply_ptracer.F, obcs_prescribe_read.F and the per-tracer upwind boundary advection) and pkg/dic/dic_biotic_forcing.F with bio_export.F over the box..

Runtime knobs (`run.sh --help`): `SAB_STEPS` (default 60, the graded
value; the upstream deck runs 10 steps of 43200 s) scales the
run linearly, and `SAB_BUILD_JOBS` (default 4) only the build. Expected run
time on the declared resources, build excluded: about 3 s;
the per-check build (roughly 40 s on an x86_64 host) is reported by `run.sh`
as `SAB_BUILD_SECONDS` and does not count against the suite budget.

## The two initial conditions

`ic/nominal` is the upstream deck, assembled as `testreport` assembles it
(the experiment's `input/`, the input.saphe/ overlay),
with these deck edits: `nTimeSteps` set to the graded window, `dumpFreq`,
`pChkptFreq` and `chkptFreq` set to zero and `dumpInitAndLast=.TRUE.` so that the only
state written is the initial and final dump, and
`writeBinaryPrec=64` so the dump is double precision and `useSingleCpuIO=.TRUE.` so the dump is one global file per field rather than one per tile.

`ic/variant` holds only the deck files that differ, laid over `ic/nominal` by
`run.sh`; the difference is `alphaUniform=9.700000000000003e-11` in `data.dic` instead of 9.7e-11:
two ulps of the graded precision (binary64) on a parameter that enters the
tendency from the first step, a distinct double, so the two runs differ at
round-off level from the first step. The
spread between them is the check's measured sensitivity under the pass policy
and must stay inside the bound.

## The pass policy

Every cell of every prognostic field in the final state dump must satisfy
|candidate - reference| <= 1e-10 + 1e-08 |reference|; inside `dynDiag` the records `PsiVEL`, `PhiVEL` are not graded (PsiVEL and PhiVEL are the streamfunction and velocity potential the diagnostics package computes with its own iterative Poisson solve (diagnostics_fill of the velocity decomposition); two legitimate builds of the same deck differ in PsiVEL by 2e-6 on values of order 1e7, which is 1.5e-13 of the field but above the absolute part of the rule in near-zero cells).
The relative part is the working bound because the fields span many orders of
magnitude; the absolute part covers cells at or near zero. The bound is physical for this check because the answer being graded is a converged root, not an arbitrary iterate: SOLVE_AT_GENERAL stops when the relative Newton increment on the hydrogen-ion concentration falls below pp_rdel_ah_target = 1e-8, so two correct runs can return values of [H+] that differ by as much as one part in 1e8 if a one-ulp perturbation changes the iteration count at the last step. That is the dominant round-off floor of this check, and it is worth stating plainly because it is larger than the floor of every other check here. It does not, however, reach the graded fields at that size: pH is package state written only into pickup_dic, which this configuration does not write, and the only route from [H+] to a graded field is the surface CO2 flux, which changes DIC in the top cell by roughly 1e-5 mol/m3 per step, so a 1e-8 relative wobble of the flux perturbs a 2.2 mol/m3 tracer by about 1e-13. The rest of the floor is the cg2d solve at 1e-13 and the prescribed boundary interpolation, both bit-identical between the runs since alphaUniform is a biological rate that cannot reach temperature, salinity or momentum. Thirty days is a long window for this module, and it is affordable precisely because of that decoupling: the dynamics, the convective adjustment switch and the open-boundary machinery all replay identically, and the perturbation lives only in five damped tracers advected by an identical flow. A reviewer should check the measured spread on PTRACER01 and PTRACER02 first, since alkalinity is the tracer the solver is most sensitive to.
Faults: Stopping SOLVE_AT_GENERAL early, replacing it with the cheaper Follows approximation, or dropping the phosphate, silicate, sulphate or fluoride terms of EQUATION_AT changes surface pH by 1e-3 or more and the resulting CO2 flux by percent, which reaches DIC in the top cell at parts in 1e-5 within a few steps. Losing the alkalinity-dependence of the initial bracket in AHINI_FOR_AT makes the iteration converge to the same root but with a different count, harmless; losing the bracket safeguard entirely makes it diverge, which the deck's error path reports. On the transport side, failing to apply the prescribed open-boundary tracer values (obcs_apply_ptracer.F) or applying them on the wrong index row changes PTRACER01 in the boundary columns by order one, and a wrong sign in the connect mask changes the interior within days.

## Evidence

input/ has no prepare_run, so the deck is self-contained; the prepare_run in inp_global/ belongs to a different, unused configuration and must not be run. The overlay input.saphe supplies data.dic, eedata and eedata.mth only, so the base data.obcs, data.ptracers, data.pkg and data.diagnostics stay in force. zeros_obX.bin is referenced only from commented-out lines in data.obcs and can be dropped. The obcs files are 2-D boundary sections sized to the box (20 rows west and east, 42 columns north) and are 32-bit like the rest of the deck, so readBinaryPrec must stay at 32. data.diagnostics sets frequency(2) twice; the second value (432000) wins, and 60 steps is a multiple of both 10 and 60 steps so both streams land on the final iteration; change the step count only in multiples of 60. DIC_OPTIONS.h in this experiment's code/ also defines DIC_CALCITE_SAT, but useCalciteSaturation is left false by the saphe overlay, so calcite_saturation.F is compiled and not called.

Floor: the optimised gfortran build and the IEEE -O0 build of the same source, run natively on the x86_64 host on 2026-09-02, differ on this deck by at most 2.4e-09 in absolute terms, 7.2e-02 of the bound (in dynDiag); the two builds pass each other under the rule. Faults, same build with one parameter changed: the cg2d target residual loosened to 1e-3 uses 4.3e+06 of the bound (FAIL), and the variant parameter off by five percent 1.6e+05 of the bound (FAIL). Measured run time of the nominal deck, build excluded: 2.3 s natively.
