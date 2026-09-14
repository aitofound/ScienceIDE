# vermix-kpp

Upstream test: `code/mitgcm/verification/vermix/input`. Policy: `pointwise`.

## The test

KPP boundary-layer mixing in a forced single column. `run.sh` builds one MITgcm executable for this
configuration with the tree's own `tools/genmake2` (the build configuration
under `mods/`: `SIZE.h`, `packages.conf` and the option headers of the
upstream experiment, gfortran optfile `linux_amd64_gfortran`, one process,
tiles only), then runs it on the deck under `ic/<ic>/`. Configuration:
verification/vermix/input: a 1x1x26 single water column on a 5 km Cartesian footprint (one tile, DISCONNECTED_TILES, 26 levels from 10 m to 40 m thick), with horizontal and vertical advection of both momentum and temperature switched off (momAdvection=.FALSE., tempAdvection=.FALSE.) so that the column evolves only under the surface heat flux Qnet_72.forcing, the zonal wind stress taux_72.forcing, Coriolis at f0=1.4e-4, the MDJWF equation of state and the vertical mixing that pkg/kpp diagnoses, with implicitDiffusion and implicitViscosity both on and background viscAz=1e-4, diffKzT=diffKzS=1e-5; KPP runs with minKPPhbl=10 m, Ricr=0.45, KPP_GHAT and KPP_ESTIMATE_UREF compiled in and all the KPP_SMOOTH_* options off; the window is 360 steps of 1200 s, exactly five days and exactly one externForcingPeriod, eighteen times the upstream twenty-step window, chosen so that the deck's own diagnostics interval of 432000 s closes precisely at the final iteration and its time-averaged KPP fields are written and graded..

The production path it forces: pkg/kpp/kpp_calc.F driving the KPPMIX, BLDEPTH, RI_IWMIX, BLMIX, ENHANCE and SWFRAC routines in pkg/kpp/kpp_routines.F, then pkg/kpp/kpp_calc_visc.F, pkg/kpp/kpp_calc_diff_t.F and kpp_calc_diff_s.F and the non-local transport in pkg/kpp/kpp_transport_t.F, with the resulting profiles applied by the tridiagonal solves in model/src/impldiff.F and model/src/solve_tridiagonal.F; the MDJWF density evaluations in model/src/find_rho.F feed the bulk Richardson number every step..

Runtime knobs (`run.sh --help`): `SAB_STEPS` (default 360, the graded
value; the upstream deck runs 20 steps of 1200 s) scales the
run linearly, and `SAB_BUILD_JOBS` (default 4) only the build. Expected run
time on the declared resources, build excluded: about 3 s;
the per-check build (roughly 40 s on an x86_64 host) is reported by `run.sh`
as `SAB_BUILD_SECONDS` and does not count against the suite budget.

## The two initial conditions

`ic/nominal` is the upstream deck, assembled as `testreport` assembles it
(the experiment's `input/`),
with these deck edits: `nTimeSteps` set to the graded window, `dumpFreq`,
`pChkptFreq` and `chkptFreq` set to zero and `dumpInitAndLast=.TRUE.` so that the only
state written is the initial and final dump, and
`writeBinaryPrec=64` so the dump is double precision and `useSingleCpuIO=.TRUE.` so the dump is one global file per field rather than one per tile; `useMNC=.FALSE.` in `data.pkg`; `kpp_dumpFreq=432000.` in `data.kpp`.

`ic/variant` holds only the deck files that differ, laid over `ic/nominal` by
`run.sh`; the difference is `Ricr=0.4500000000000001` in `data.kpp` instead of 0.45:
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
|candidate - reference| <= 1e-10 + 1e-08 |reference|; inside `dynDiag` the records `DFrI_TH` are not graded (DFrI_TH is the implicit vertical heat flux averaged over the window; it takes its value from KPP's discrete boundary-layer level and one cell of it differed by 1e-6 in the calibration while every prognostic field stayed at round-off).
The relative part is the working bound because the fields span many orders of
magnitude; the absolute part covers cells at or near zero. The observable is every cell of the final prognostic dump plus the KPP fields the deck asks for, compared as a relative difference with an absolute floor, and for this check the round-off floor is unusually clean because there is essentially nothing in the step that amplifies it. The domain is one column with DISCONNECTED_TILES, so there is no horizontal exchange and no global reduction whose summation order could vary; the barotropic solve is degenerate on a single point and the upstream log records cg2d_init_res exactly zero, so the elliptic solver contributes no iteration-count sensitivity at all; the only remaining sources of round-off are the MDJWF polynomial in find_rho.F, the KPP profile functions, and the direct tridiagonal factorisation in impldiff.F and solve_tridiagonal.F, all of which are fixed-length arithmetic with no convergence test and therefore reproduce bit-for-bit between two runs of the same build. Physically the column is dissipative: KPP mixes a stably stratified, wind- and buoyancy-forced profile, so a perturbation is damped rather than grown, and five days is short compared with the 360-day forcing cycle the deck was designed around, well inside the regime where a pointwise comparison is meaningful rather than a statistical one. The one thing a reviewer must know is that the boundary-layer depth is found by linearly interpolating the bulk Richardson number to Ricr in BLDEPTH, so hbl is a continuous function of the state and of Ricr, and the level-index bookkeeping around it does not introduce a jump; the one-ulp change to Ricr therefore produces a genuinely infinitesimal, everywhere-differentiable perturbation, which is exactly the sensitivity the calibration is meant to measure.
The binding record is KPPghatK in DiagMXL_3d: the two-ulp variant uses 0.070 of the bound there (14x headroom), the state fields under 0.011, and the two builds are bit-identical; the human accepted this headroom on 2026-09-05.
Faults: Dropping the non-local counter-gradient term (the ghat contribution assembled in pkg/kpp/kpp_calc_diff_t.F and applied in pkg/kpp/kpp_transport_t.F) changes the temperature profile inside the boundary layer by hundredths of a kelvin within a single day, parts in 1e-3 of the field, five orders of magnitude above the bound. A one-percent error in the critical bulk Richardson number or in the shear term of BLDEPTH in pkg/kpp/kpp_routines.F moves the diagnosed boundary-layer depth by a fraction of a level and the diffusivity immediately below it by tens of percent, which reaches the graded KPPhbl and KPPdiffT fields directly. Replacing the tridiagonal implicit solve in model/src/impldiff.F with an explicit or a single-precision variant leaves relative errors of 1e-7 or worse in T, U and V after 360 steps, an order of magnitude above the relative bound, and truncating the interior wave-mixing table of RI_IWMIX to single precision shows up in KPPviscA at the 1e-7 level.

## Evidence

data.pkg sets useMNC=.TRUE. and must be turned off (no NetCDF in the image); data.mnc is then unread and is kept only so the deck stays recognisable. The kpp_dumpFreq edit is what makes pkg/kpp write its instantaneous KPPviscAz, KPPdiffKzT, KPPdiffKzS, KPPghat and KPPhbl snapshot at the final iteration: without it the generator's dumpFreq=0 suppresses it, because pkg/kpp/kpp_output.F gates on DIFFERENT_MULTIPLE(kpp_dumpFreq,...) and that function returns false for a zero frequency. The value 432000. is steps*dt; if an operator overrides SAB_STEPS the KPP snapshot simply disappears from both the reference and the candidate, which is harmless but worth knowing. The deck's own data.diagnostics writes dynDiag (UVEL, VVEL, WVEL, THETA, PHIHYD, DFrI_TH), DiagMXL_3d (KPPviscA, KPPdiffT, KPPghatK) and DiagMXL_2d (MXLDEPTH, KPPhbl) at 432000 s into the run directory, so with steps=360 they land at the final iteration and are graded too; all of them are continuous functions of the state, including MXLDEPTH, which model/src/calc_oce_mxlayer.F obtains by interpolation. All input binaries are real*8 and the deck sets readBinaryPrec=64. Salinity is uniform at 35 with no salt forcing, so the graded S field is constant and contributes nothing; that is expected, not a bug. ivdc_kappa is commented out in this deck, so the hard convective switch in model/src/calc_ivdc.F never runs here.

Floor: self-validation measures it on every run from `run.sh altbuild`, the same source under genmake2 -ieee, graded against the nominal run with this check's validate.py, and records it in the rubric's evidence (floor, altbuild); that in-image number is the floor a reviewer reads. The native measurement of 2026-09-02 between the same two builds on the x86_64 host: the optimised gfortran build and the IEEE -O0 build differ on this deck by at most 0.0e+00 in absolute terms, 0.0e+00 of the bound (in no field); the two builds pass each other under the rule. Faults, same build with one parameter changed: the cg2d target residual loosened to 1e-3 uses 0.0e+00 of the bound (NO EFFECT: one water column, 1x1 horizontally, so the surface-pressure solve has nothing to iterate and its target cannot change the result), and the variant parameter off by five percent 1.6e+06 of the bound (FAIL). Measured run time of the nominal deck, build excluded: 0.6 s natively.
