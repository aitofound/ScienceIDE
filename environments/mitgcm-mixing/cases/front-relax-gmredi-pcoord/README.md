# front-relax-gmredi-pcoord

Upstream test: `code/mitgcm/verification/front_relax/input.in_p`. Policy: `pointwise`.

## The test

GM advective form relaxing the same front in pressure coordinates. `run.sh` builds one MITgcm executable for this
configuration with the tree's own `tools/genmake2` (the build configuration
under `mods/`: `SIZE.h`, `packages.conf` and the option headers of the
upstream experiment, gfortran optfile `linux_amd64_gfortran`, one process,
tiles only), then runs it on the deck under `ic/<ic>/`. Configuration:
verification/front_relax with the input.in_p overlay: the primary front-relaxation set-up transcribed into pressure coordinates, a 1x32x25 zonally symmetric y-z channel (two tiles of 1x16, 10 km meridional spacing from the same dy.bin, 15 active levels plus 10 dead ones so that one executable serves all five upstream set-ups) with buoyancyRelation='OCEANICP', the vertical grid given as delRc in Pascals and the initial temperature file flipped in the vertical (Tini_flip.bin), gravity and rhoNil set to the round numbers 10 and 1000 so that the P and Z runs can be compared directly, a linear equation of state with temperature as the only buoyancy-carrying tracer and salinity as a passive dye, no surface forcing at all, f-plane at f0=1e-4, viscAr=2e4 and diffKrT=diffKrS=3e3 in pressure units and zero horizontal diffusivity, so that the only lateral tracer transport is what pkg/gmredi supplies; unlike the primary deck this one runs GM in its advective (bolus transport) form, GM_AdvForm=.TRUE., with the same GM_background_K=1000 setting both the GM and the Redi coefficient and the same GM_maxSlope=1e-2, and the deck's stratification is again strong enough everywhere that no tapering is needed; the window is 360 steps of 1800 s, seven and a half days, the same window as the primary check so that the two remain directly comparable, and eighteen times the upstream twenty-step window..

The production path it forces: pkg/gmredi/gmredi_calc_tensor.F forming the isopycnal slopes and the mixing tensor at every cell face with the P-coordinate branches of the slope treatment in pkg/gmredi/gmredi_slope_limit.F and gmredi_slope_psi.F, the bolus streamfunction of pkg/gmredi/gmredi_calc_psi_bolus.F and the eddy-induced velocities it produces, applied through pkg/gmredi/gmredi_xtransport.F, gmredi_ytransport.F and gmredi_rtransport.F inside model/src/calc_gt.F and calc_gs.F; the vertical component of the Redi tensor is folded into model/src/impldiff.F..

Runtime knobs (`run.sh --help`): `SAB_STEPS` (default 360, the graded
value; the upstream deck runs 20 steps of 1800 s) scales the
run linearly, and `SAB_BUILD_JOBS` (default 4) only the build. Expected run
time on the declared resources, build excluded: about 3 s;
the per-check build (roughly 40 s on an x86_64 host) is reported by `run.sh`
as `SAB_BUILD_SECONDS` and does not count against the suite budget.

## The two initial conditions

`ic/nominal` is the upstream deck, assembled as `testreport` assembles it
(the experiment's `input/`, the input.in_p/ overlay),
with these deck edits: `nTimeSteps` set to the graded window, `dumpFreq`,
`pChkptFreq` and `chkptFreq` set to zero and `dumpInitAndLast=.TRUE.` so that the only
state written is the initial and final dump, and
`writeBinaryPrec=64` so the dump is double precision and `useSingleCpuIO=.TRUE.` so the dump is one global file per field rather than one per tile.

`ic/variant` holds only the deck files that differ, laid over `ic/nominal` by
`run.sh`; the difference is `GM_background_K=1000.0000000000002` in `data.gmredi` instead of 1000:
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
magnitude; the absolute part covers cells at or near zero. The rule compares every cell of U, V, W, T, S, Eta and the pressure fields relatively with an absolute floor for the near-zero cells, and it is physical because the configuration has an unambiguous answer: with no forcing, no eddies and no tapering, the front relaxes at a rate set only by GM_background_K and the isopycnal slope, so the state after seven and a half days is a deterministic functional of the tensor and the streamfunction. It is achievable because the amplification mechanisms are weak and identifiable, exactly as for the primary check. The one iterative step is the barotropic solve, and the deck sets cg2dTargetResidual=1e-13 on a 32-point domain, tight enough that the solution error is far below the bound and the iteration count is very unlikely to differ between two nearly identical states. There is no threshold switch anywhere in the step: ivdc_kappa is commented out and cAdjFreq is unset, so neither model/src/calc_ivdc.F nor model/src/convective_adjustment.F ever runs, and GM_maxSlope=1e-2 is never reached because the background stratification was chosen to avoid tapering, so the limiter in gmredi_slope_limit.F stays on its linear branch. Most importantly the flow is two-dimensional in y and z with no x structure, so baroclinic instability cannot develop at all and nothing in the configuration can grow a round-off perturbation exponentially; the front slumps and viscosity and diffusion damp everything else. That is what makes a window eighteen times the upstream one safe here. The variant perturbs GM_background_K, which the deck writes explicitly and which sets both the GM and, by default, the Redi coefficient, so it enters the tendency of both tracers in every wet cell from the first step; it is the same parameter as the primary check's variant, which is deliberate, because keeping the two windows and the two perturbations identical is what makes the Z-versus-P pair informative. Ten of the twenty-five levels are dead cells and are graded as exact zeros against the absolute floor.
The binding field is W: the two-ulp variant uses 0.048 of the bound there (21x headroom) and the two builds are bit-identical; the human accepted this headroom on 2026-09-05.
Faults: This deck isolates the advective form of GM: the front slumps only because the bolus streamfunction advects it, so a fault in that streamfunction cannot be hidden. Dropping the vertical derivative that turns the streamfunction into an eddy-induced vertical velocity in gmredi_calc_psi_bolus.F stops the front flattening entirely, tenths of a kelvin after seven days, parts in 1e-2 of the temperature field. A ten percent error in GM_background_K changes the slumping rate by ten percent and the temperature by parts in 1e-3 within the same window. Getting the sign of the bolus velocity wrong steepens the front instead of flattening it, an O(1) difference. Because salinity is a passive dye carried by the same eddy-induced transport plus the isopycnal part of the tensor, a fault in the Redi part alone shows in S at parts in 1e-2 while leaving T much less disturbed, which is a useful discriminator. Getting the P-coordinate sign conventions wrong, the single most likely error when a routine is generalised over both coordinate systems, is an O(1) failure that this check catches and the Z-coordinate check does not. A single-precision tensor leaves relative errors near 1e-7 in both tracers.

## Evidence

The overlay supplies its own data, data.pkg, data.gmredi, data.diagnostics, eedata and its own bathy_inP.bin, Tini_flip.bin, Sini_Ydir.bin and Sini_Patch.bin; only delYfile='dy.bin' still comes from input/, which is why dy.bin must not be dropped. The Z-coordinate binaries of input/ (bathy_inZ.bin, Tini_+10l.bin) and the unused Sini_Patch.bin alternative initial salinity are dropped, as are the matlab generator, the MPI-only data.mpi and the multi-threaded eedata.mth. Unlike its siblings this deck already sets useSingleCpuIO=.TRUE., so mdsio writes global files and no I/O extra edit is needed. useDiagnostics is on, but every stream in the overlay's data.diagnostics has a frequency of -864000 s, that is 480 steps, so none of them fires inside this 360-step window; two of those streams have no fileName at all, which is exactly why the window must not be extended to 480 steps without first checking what pkg/diagnostics does with a blank output-stream name. The per-level statistics stream at stat_freq=21600 writes plain text files, which are not collected. There is no MNC, no pickup, no prepare_run and no cg3d, so only the core state dump from model/src/write_state.F is graded: U, V, W, T, S, Eta, PH and PHL on a 1x32x25 grid. All binaries are real*8 and the deck sets readBinaryPrec=64 and writeBinaryPrec=64. debugLevel=2 makes the log verbose but changes no answer.

Floor: self-validation measures it on every run from `run.sh altbuild`, the same source under genmake2 -ieee, graded against the nominal run with this check's validate.py, and records it in the rubric's evidence (floor, altbuild); that in-image number is the floor a reviewer reads. The native measurement of 2026-09-02 between the same two builds on the x86_64 host: the optimised gfortran build and the IEEE -O0 build differ on this deck by at most 0.0e+00 in absolute terms, 0.0e+00 of the bound (in no field); the two builds pass each other under the rule. Faults, same build with one parameter changed: the cg2d target residual loosened to 1e-3 uses 9.2e+06 of the bound (FAIL), and the variant parameter off by five percent 8.0e+06 of the bound (FAIL). Measured run time of the nominal deck, build excluded: 1.3 s natively.
