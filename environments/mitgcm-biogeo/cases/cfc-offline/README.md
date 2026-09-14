# cfc-offline

Upstream test: `code/mitgcm/verification/tutorial_cfc_offline/input`. Policy: `pointwise`.

## The test

Offline CFC transport on pre-computed flow. `run.sh` builds one MITgcm executable for this
configuration with the tree's own `tools/genmake2` (the build configuration
under `mods/`: `SIZE.h`, `packages.conf` and the option headers of the
upstream experiment, gfortran optfile `linux_amd64_gfortran`, one process,
tiles only), then runs it on the deck under `ic/<ic>/`. Configuration:
verification/tutorial_cfc_offline/input: the same 2.8-degree global grid (128x64x15, four tiles of 64x32) with the dynamical core switched off entirely by useOffLine, so that momentum, the free surface and the equation of state are never integrated and pkg/offline instead reads monthly-mean velocity, vertical velocity, GM streamfunction components, potential temperature, salinity and a convective-mixing index from the deck's input_off/ files and interpolates them linearly in time; the two CFC tracers are then advected with the flux-limited scheme 77, mixed by the read-in GM tensor and by an implicit vertical diffusivity of 5e-5 m2/s, and forced at the surface by pkg/cfc exactly as in the online check; restarted from pickup_ptracers at iteration 4269600 and run 24 tracer steps of 43200 s (12 days) against the deck's 4. Because WRITE_STATE is skipped when useOffLine is set (model/src/do_the_model_io.F), the only files at the final iteration are PTRACER01 and PTRACER02, which makes this the one check in the module that grades the tracer transport and nothing else..

The production path it forces: pkg/offline/offline_fields_load.F and offline_get_diffus.F, which read and exchange nine three-dimensional fields and rebuild the GM diffusivity each time the record pair changes, and then the two flux-limited gad_advection.F sweeps, the GM/Redi tensor application and the tridiagonal implicit vertical diffusion per tracer, plus pkg/cfc's atmospheric interpolation and gas exchange over the surface..

Runtime knobs (`run.sh --help`): `SAB_STEPS` (default 24, the graded
value; the upstream deck runs 4 steps of 43200 s) scales the
run linearly, and `SAB_BUILD_JOBS` (default 4) only the build. Expected run
time on the declared resources, build excluded: about 3 s;
the per-check build (roughly 40 s on an x86_64 host) is reported by `run.sh`
as `SAB_BUILD_SECONDS` and does not count against the suite budget.

## The two initial conditions

`ic/nominal` is the upstream deck, assembled as `testreport` assembles it
(the experiment's `input/`, and the files its prepare_run links from sibling experiments),
with these deck edits: `nTimeSteps` set to the graded window, `dumpFreq`,
`pChkptFreq` and `chkptFreq` set to zero and `dumpInitAndLast=.TRUE.` so that the only
state written is the initial and final dump, and
`writeBinaryPrec=64` so the dump is double precision and `useSingleCpuIO=.TRUE.` so the dump is one global file per field rather than one per tile; `UvelFile='uVeltave'` in `data.off`; `VvelFile='vVeltave'` in `data.off`; `WvelFile='wVeltave'` in `data.off`; `GMwxFile='GM_Kwx-T'` in `data.off`; `GMwyFile='GM_Kwy-T'` in `data.off`; `GMwzFile='GM_Kwz-T'` in `data.off`; `ConvFile='Convtave'` in `data.off`; `SaltFile='Stave'` in `data.off`; `ThetFile='Ttave'` in `data.off`.

`ic/variant` holds only the deck files that differ, laid over `ic/nominal` by
`run.sh`; the difference is `PTRACERS_diffKr(1)=5.0000000000000016e-05` in `data.ptracers` instead of 5e-05:
two ulps of the graded precision (binary64) on a parameter that enters the
tendency from the first step, a distinct double, so the two runs differ at
round-off level from the first step. The
spread between them is the check's measured sensitivity under the pass policy
and must stay inside the bound.

## The pass policy

Every cell of every prognostic field in the final state dump must satisfy
|candidate - reference| <= 1e-20 + 1e-08 |reference| (the CFC concentrations are of order 1e-9 mol/m3, so the usual absolute part of 1e-10 would swallow the tracer entirely: a five percent error in the tracer diffusivity moved the tracer by 3e-4 relative and still passed under 1e-10; with 1e-20 the absolute part only covers exact zeros).
The relative part is the working bound because the fields span many orders of
magnitude; the absolute part covers cells at or near zero. This is the cleanest pointwise check in the module because there is no dynamical core at all: the advecting flow is read from disk and is byte-identical in the two runs, so the only difference is the one-ulp change to the vertical diffusivity of CFC-11, and the observable is a linear, damped advection-diffusion problem with a surface source. Perturbations cannot grow; they are stirred and diffused, so the window can be twelve days and stay comfortably inside the pointwise regime. The round-off floor is set by the linear time interpolation between the two flow records, the fixed sweep order of the multi-dimensional advection, the continuous min/max branches of the scheme-77 limiter, and the direct tridiagonal factorisation of the implicit vertical diffusion, none of which has a convergence tolerance. The strongest statement a reviewer can take from this check is a negative one: since only PTRACER01 and PTRACER02 are graded, any fault in the offline field loading, the GM reconstruction or the tracer transport has nowhere to hide behind an unchanged ocean state.
Faults: Interpolating the wrong record pair, or getting the weights of GET_PERIODIC_INTERVAL backwards, changes the advecting velocity by percent and both tracers by parts in 1e-3 within a step. Forgetting the EXCH_UV_XYZ_RS halo exchange on the loaded velocities leaves stale halo values and corrupts the tile edges by order one. Dropping the GM skew-flux terms rebuilt in offline_get_diffus.F, or applying the read-in Convtave index as a diffusivity of the wrong magnitude, moves the subsurface CFC by parts in 1e-2. Cheapening the tridiagonal solve or carrying the loaded fields in single precision (they are stored as float32 on disk and read into _RS arrays) shows up at parts in 1e-6.

## Evidence

Two hazards, both hard. First, the step count is capped by the data: only two flow records exist in input_off/, at iterations 4248060 and 4248720, which are records 1 and 12 of a twelve-record annual cycle (offlineIter0=4248000, Ifprd = offlineForcingPeriod/deltaToffline = 60, so the file suffix is intime*60 + 4248000). At nIter0=4269600 GET_PERIODIC_INTERVAL returns intime0=12, intime1=1 with equal weights, and intime1 advances to record 2, whose file does not exist, exactly 30 steps later. nTimeSteps must therefore stay at or below 29; 24 is chosen to leave margin, and the step count must never be raised past 29 by a knob. Second, data.off addresses the flow fields as '../input/input_off/uVeltave', which only resolves under testreport's <exp>/run layout; the extra_edits above rewrite the nine paths to bare prefixes and the links entry copies all 36 files of input_off/ flat into the run directory, so the two must be kept consistent. The input_off files are float32 with .meta sidecars and are read at offlineLoadPrec = readBinaryPrec = 32 (the deck does not set readBinaryPrec), which must not be changed. data.pkg enables useOffLine, and code/packages.conf explicitly removes mom_common, mom_fluxform and mom_vecinv, so the momentum code is not even compiled; that is intentional and must survive into mods/.

Floor: the optimised gfortran build and the IEEE -O0 build of the same source, run natively on the x86_64 host on 2026-09-02, differ on this deck by at most 2.1e-25 in absolute terms, 1.2e-07 of the bound (in PTRACER01); the two builds pass each other under the rule. Faults, same build with one parameter changed: the cg2d target residual loosened to 1e-3 uses 0.0e+00 of the bound (NO EFFECT (no cg2d in this configuration)), and the variant parameter off by five percent 1.3e+05 of the bound (FAIL). Measured run time of the nominal deck, build excluded: 2.7 s natively.
