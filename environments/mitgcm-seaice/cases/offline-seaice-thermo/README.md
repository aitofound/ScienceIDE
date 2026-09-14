# offline-seaice-thermo

Upstream test: `code/mitgcm/verification/offline_exf_seaice/input.thermo`. Policy: `pointwise`.

## The test

Ice-only channel, zero-layer (Hibler) thermodynamics with dynamics switched off. `run.sh` builds one MITgcm executable for this
configuration with the tree's own `tools/genmake2` (the build configuration
under `mods/`: `SIZE.h`, `packages.conf` and the option headers of the
upstream experiment, gfortran optfile `linux_amd64_gfortran`, one process,
tiles only), then runs it on the deck under `ic/<ic>/`. Configuration:
verification/offline_exf_seaice/input.thermo: the same 80x42 channel with SEAICEuseDYNAMICS=.FALSE., so the momentum solver never runs and the check is a pure test of the pkg/seaice thermodynamics: growth and melt of single-category zero-layer (Hibler) ice: SEAICE_ITD is undefined in the check's SEAICE_OPTIONS.h, so seaice_readparms.F sets SEAICE_multDim = 1, which is also what upstream's reference log for this deck records, the McPhee ocean-to-ice turbulent flux (SEAICE_mcPheePiston=8.7854425e-5), lead closing with HO=0.2, area loss formula 2, growth and melt by convergence, open-water melt, flooding, and the surface temperature solve; exf forcing from tair_4x.bin, qa70_4x.bin, dlw_250.bin, dsw_100.bin with a restoring SST from tocn.bin, the ice started from ice0_area.bin and ice0_heff.bin, advection scheme 77 with snow advection, ocean temperature stepped but not advected; the deck's own window of 120 steps of 3600 s (five days) is kept.

The production path it forces: seaice_growth.F (the whole growth and melt budget on the single ice category), seaice_solve4temp.F with its Newton iteration on the surface temperature, seaice_budget_ice.F and seaice_budget_ocean.F, and seaice_advdiff.F for AREA, HEFF and HSNOW.

Runtime knobs (`run.sh --help`): `SAB_STEPS` (default 120, the graded
value; the upstream deck runs 120 steps of 3600 s) scales the
run linearly, and `SAB_BUILD_JOBS` (default 4) only the build. Expected run
time on the declared resources, build excluded: about 3 s;
the per-check build (roughly 40 s on an x86_64 host) is reported by `run.sh`
as `SAB_BUILD_SECONDS` and does not count against the suite budget.

## The two initial conditions

`ic/nominal` is the upstream deck, assembled as `testreport` assembles it
(the experiment's `input/`, the input.thermo/ overlay),
with these deck edits: `nTimeSteps` set to the graded window, `dumpFreq`,
`pChkptFreq` and `chkptFreq` set to zero and `dumpInitAndLast=.TRUE.` so that the only
state written is the initial and final dump, and
`writeBinaryPrec=64` so the dump is double precision and `useSingleCpuIO=.TRUE.` so the dump is one global file per field rather than one per tile; `SEAICEwriteState=.TRUE.` in `data.seaice`.

`ic/variant` holds only the deck files that differ, laid over `ic/nominal` by
`run.sh`; the difference is `SEAICE_mcPheePiston=8.785442500000003e-05` in `data.seaice` instead of 8.78544e-05:
two ulps of the graded precision (binary64) on a parameter that enters the
tendency from the first step, a distinct double, so the two runs differ at
round-off level from the first step. The
spread between them is the check's measured sensitivity under the pass policy
and must stay inside the bound.

## The pass policy

Every cell of every prognostic field in the final state dump must satisfy
|candidate - reference| <= 1e-10 + 1e-08 |reference|; the fields `UWIND`, `VWIND` are not graded.
The relative part is the working bound because the fields span many orders of
magnitude; the absolute part covers cells at or near zero. The observable is every cell of AREA, HEFF, HSNOW, the ocean T and S and the flux fields of the final dump under |c - r| <= 1e-10 + 1e-8|r|; UICE and VICE are written but identically zero because the dynamics is off. The relative part of the bound is what is actually tested because the graded fields span ten orders of magnitude (ice area of order one, ice and ocean velocities of order 1e-2 to 1 m/s, ice enthalpies of order 1e5 J/kg, heat fluxes of order 1e2 W/m2), so a single absolute number would be either unreachable for the enthalpies or vacuous for the velocities; the absolute part only covers cells at or near zero. The bound is physical because the thermodynamic step is an explicit budget plus one Newton solve for the surface temperature, with no global reduction and no iterative linear solve, so the round-off floor is the floor of a few hundred floating-point operations per cell, far below 1e-10 relative; nothing here amplifies. The window is the deck's own five days, which upstream verifies, and the deck's albedos are all set to 0.6 (dry ice, wet ice, dry snow and wet snow alike), which removes the temperature-triggered albedo switch that would otherwise be the main discrete hazard of a thermodynamics-only run. The residual hazard is a cell whose ice disappears or appears during the window; that is what the calibration measures. It is achievable because the run is one process with the tiles swept in a fixed order (GLOBAL_SUM_ORDER_TILES), so every reduction and every solver sweep is deterministic and two correct builds of the same source differ only by round-off amplified through the iterations of the solve; the nominal-versus-variant spread that selfcheck records is the measurement of that amplification under this exact rule, and the bound is finalised against it with the human.
Faults: A wrong latent or sublimation heat, a wrong emissivity, or a mis-ported saturation vapour pressure in seaice_solve4temp.F moves the surface temperature by tenths of a kelvin and the ice thickness by per cent within a day. Truncating the Newton iteration on the surface temperature (IMAX_TICE / postSolvTempIter) leaves a residual in the surface energy balance that shows up directly in SItices and HEFF. A wrong SEAICE_mcPheePiston, the parameter the variant perturbs, changes the ocean-to-ice heat flux and therefore the basal melt rate linearly.

## Evidence

Hazard: this is the one deck of the module whose graded state is decided entirely by threshold-rich thermodynamics (ice appearing and disappearing in marginal cells, lead closing at HO=0.2, the SEAICE_areaLossFormula=2 branch). The window is the deck's own 120 steps, so it is exactly what upstream verifies; if the calibration finds the two-ulp variant crossing a switch, shorten to 48 steps (two days) rather than changing the deck. usePW79thermodynamics is left at its default .TRUE. here, unlike the dynamics overlays. 64-bit inputs, no pickup, no prepare_run links; the sibling deck seaice_itd/input.thermo is excluded from the module because it fails to reproduce the upstream digits.

Floor: the optimised gfortran build and the IEEE -O0 build of the same source, run natively on the x86_64 host on 2026-09-02, differ on this deck by at most 0.0e+00 in absolute terms, 0.0e+00 of the bound (in no field); the two builds pass each other under the rule. Faults, same build with one parameter changed: the cg2d target residual loosened to 1e-3 uses 0.0e+00 of the bound (NO EFFECT (no cg2d in this configuration)), and the variant parameter off by five percent 3.8e+08 of the bound (FAIL). Measured run time of the nominal deck, build excluded: 0.5 s natively.
