# isomip-shelfice-gammafrict

Upstream test: `code/mitgcm/verification/isomip/input.htd`. Policy: `pointwise`.

## The test

Three-equation melt with velocity-dependent transfer coefficients. `run.sh` builds one MITgcm executable for this
configuration with the tree's own `tools/genmake2` (the build configuration
under `mods/`: `SIZE.h`, `packages.conf` and the option headers of the
upstream experiment, gfortran optfile `linux_amd64_gfortran`, one process,
tiles only), then runs it on the deck under `ic/<ic>/`. Configuration:
verification/isomip/input.htd laid over input: the same 50x100x30 ISOMIP cavity but restarted from the deck's pickup at iteration 8640 (six months of spin-up, so the cavity circulation is developed and the water column is no longer degenerate) and switched to the Holland and Jenkins three-equation formulation, SHELFICEuseGammaFrict=.TRUE. with SHI_ALLOW_GAMMAFRICT compiled in, SHELFICEselectDragQuadr=1, SHELFICEadvDiffHeatFlux=.TRUE., SHELFICEconserve=.TRUE. and a prescribed ice mass from iceShelf_Mass.bin instead of a load-anomaly file, together with the non-linear free surface (nonlinFreeSurf=4, hFacInf=0.02, hFacSup=2.0), implicit vertical viscosity and diffusion with ivdc_kappa=1, thin-top-cell mixing (pCellMix_select=20 with pCellMix_viscAr=4e-4 and pCellMix_diffKr=2e-4), Jamart wet points and viscAh=1000; graded window 60 steps of 1800 s from iteration 8640 to 8700, three times the deck's 20 steps. The two active diagnostics streams (surfDiag with the friction velocity, the two transfer coefficients, the melt and heat fluxes, the shelfice forcing terms and the top stresses; dynDiag with the velocities, hydrostatic pressure, theta and salt) are retimed to the run length so they land at the final iteration..

The production path it forces: pkg/shelfice/shelfice_thermodynamics.F, whose gamma-friction block (the SHELFICEuseGammaFrict branches near lines 301-500) recomputes the friction velocity from the top-cell velocities and then solves the Holland and Jenkins stability relation for shiTransCoeffT and shiTransCoeffS at every ice-covered column before the three-equation quadratic (eps1 through eps8, bqe, cqe, discrim) is solved for the interface salinity; pkg/shelfice/shelfice_u_drag_coeff.F and shelfice_v_drag_coeff.F for the quadratic top drag; model/src/cg2d.F at about 178 iterations per step; the non-linear free-surface bookkeeping in model/src/calc_surf_dr.F and update_surf_dr.F, which rescales hFac every step; and the implicit vertical solves in model/src/solve_tridiagonal.F reached through impldiff.F with the pCellMix enhancement..

Runtime knobs (`run.sh --help`): `SAB_STEPS` (default 60, the graded
value; the upstream deck runs 20 steps of 1800 s) scales the
run linearly, and `SAB_BUILD_JOBS` (default 4) only the build. Expected run
time on the declared resources, build excluded: about 11 s;
the per-check build (roughly 40 s on an x86_64 host) is reported by `run.sh`
as `SAB_BUILD_SECONDS` and does not count against the suite budget.

## The two initial conditions

`ic/nominal` is the upstream deck, assembled as `testreport` assembles it
(the experiment's `input/`, the input.htd/ overlay),
with these deck edits: `nTimeSteps` set to the graded window, `dumpFreq`,
`pChkptFreq` and `chkptFreq` set to zero and `dumpInitAndLast=.TRUE.` so that the only
state written is the initial and final dump, and
`writeBinaryPrec=64` so the dump is double precision and `useSingleCpuIO=.TRUE.` so the dump is one global file per field rather than one per tile; `useMNC=.FALSE.` in `data.pkg`; `dumpAtLast=.TRUE.` in `data.diagnostics`; `frequency(1)=108000.` in `data.diagnostics`; `frequency(2)=108000.` in `data.diagnostics`.

`ic/variant` holds only the deck files that differ, laid over `ic/nominal` by
`run.sh`; the difference is `shiCdrag=0.0015000000000000005` in `data.shelfice` instead of 0.0015:
two ulps of the graded precision (binary64) on a parameter that enters the
tendency from the first step, a distinct double, so the two runs differ at
round-off level from the first step. The
spread between them is the check's measured sensitivity under the pass policy
and must stay inside the bound.

`run.sh altbuild` runs `ic/nominal` on an alternative build of the same source, `genmake2 -ieee` (gfortran -O0
-ffloat-store, strict IEEE arithmetic) instead of the optimised optfile; grading never uses it, self-validation measures the
check's floor between two legitimate builds from it.

## The pass policy

Every cell of every prognostic field in the final state dump must satisfy
|candidate - reference| <= 1e-10 + 1e-08 |reference|.
The relative part is the working bound because the fields span many orders of
magnitude; the absolute part covers cells at or near zero. The graded observable is the end-of-run state dump together with the two time-averaged diagnostics files, which contain the quantities this configuration actually computes: SHIuStar, SHIgammT, SHIgammS, SHIfwFlx, SHIhtFlx, SHIForcT and SHIForcS. The bound is physical because the three-equation system is an algebraic closure with no tuning freedom once shiCdrag and the Prandtl and Schmidt numbers are fixed: the interface temperature and salinity are the root of a quadratic whose coefficients are the transfer coefficients, the latent heat and the heat capacities, so any dropped term or wrong coefficient moves the root by parts in 1e-3 and the melt rate by parts in 1e-2, five orders of magnitude above a 1e-8 relative bound. It is achievable because the whole path is closed-form arithmetic plus two deterministic linear solves: the tridiagonal implicit vertical solve, which is exact up to round-off, and cg2d, which stops on a global-sum residual test at 1e-13 and is the only place where a different summation order can change the iteration count and hence inject a perturbation of order the target residual. Starting from the deck's own pickup means the run begins in a developed, stably stratified cavity, so unlike the ISOMIP-mode check there is no degenerate density comparison and the floor should be set by cg2d alone. The window is 30 hours of a quasi-steady buoyancy-driven cavity flow, well inside the pointwise regime; the nominal-versus-variant spread recorded by selfcheck is the measurement of the amplification and the bound is finalised against it.
Faults: Replacing the Holland and Jenkins stability function by a constant transfer coefficient, or dropping the buoyancy correction in the gamma computation in pkg/shelfice/shelfice_thermodynamics.F, changes shiTransCoeffT by tens of percent and the melt rate with it. Taking the wrong root of the three-equation quadratic (the code takes -bqe-sqrt(discrim) and falls back to the other root only when the first is negative) or dropping the eps8 term that carries the ice heat capacity moves the interface salinity by parts in 1e-3 and the fresh-water flux by parts in 1e-2. Omitting the cFac term in shelficeForcingT and shelficeForcingS, which is what SHELFICEconserve turns on, breaks heat and salt conservation at the parts-in-1e-3 level. A cheaper implicit vertical solve, for instance a fixed number of Jacobi sweeps instead of the tridiagonal factorisation in model/src/solve_tridiagonal.F, moves theta by parts in 1e-6. Single precision anywhere in the flux computation or the tridiagonal solve appears as parts in 1e-7.

## Evidence

Hazards. (1) data.pkg sets useMNC=.TRUE., which must be turned off because the image has no NetCDF; data.mnc is then unread and is harmless to leave in place. (2) The deck reads pickup.0000008640.data/.meta, which must be copied into the run directory and kept; nIter0=8640 so the final iteration is 8640+steps and the graded files are named 0000008700 at 60 steps. (3) Only two of the three diagnostics lists in data.diagnostics are active: pkg/diagnostics/diagnostics_readparms.F silently ignores any list whose fileName is blank, and list 4 (the ADVx_TH/DFxE_TH group) has none, which the upstream output.htd.txt confirms by creating only surfDiag and dynDiag. The frequency edits therefore only touch lists 1 and 2; dumpAtLast is belt and braces so that the diagnostics still land at the final iteration if the step count is overridden at run time. (4) The deck sets nonlinFreeSurf=4 with hFacInf=0.02, so the top-cell thickness factor is rescaled every step; combined with pCellMix_select=20 this makes the vertical mixing coefficients a piecewise function of the top-cell thickness, a smooth ramp rather than a switch, so it is not a threshold hazard, but it is the reason a thin top cell is not a floor problem here. (5) ivdc_kappa=1 with implicitDiffusion means convection is handled by an enhanced-diffusivity switch rather than by convective adjustment; the pickup state is stratified so the test is not marginal, but it is still a comparison and worth watching in the measured spread. (6) shiCdrag is a package default (0.0015) that this deck does not set; because SHELFICEDragQuadratic is left unset and SHELFICEuseGammaFrict is true, shelfice_readparms.F copies shiCdrag into SHELFICEDragQuadratic, so the two-ulp variant perturbs both the friction velocity that drives the transfer coefficients and the quadratic top drag on momentum, from the first step. (7) readBinaryPrec=64 must stay; the ISOMIP binaries and the pickup are 64-bit.

Floor: self-validation measures it on every run from `run.sh altbuild`, the same source under genmake2 -ieee, graded against the nominal run with this check's validate.py, and records it in the rubric's evidence (floor, altbuild); that in-image number is the floor a reviewer reads. The native measurement of 2026-09-02 between the same two builds on the x86_64 host: the optimised gfortran build and the IEEE -O0 build differ on this deck by at most 1.0e-13 in absolute terms, 2.3e-04 of the bound (in U); the two builds pass each other under the rule. Faults, same build with one parameter changed: the cg2d target residual loosened to 1e-3 uses 4.9e+03 of the bound (FAIL), and the variant parameter off by five percent 2.3e+06 of the bound (FAIL). Measured run time of the nominal deck, build excluded: 11.0 s natively.
