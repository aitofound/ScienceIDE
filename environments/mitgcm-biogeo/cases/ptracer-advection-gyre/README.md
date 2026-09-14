# ptracer-advection-gyre

Upstream test: `code/mitgcm/verification/tutorial_advection_in_gyre/input`. Policy: `pointwise`.

## The test

Second-order-moment tracer advection in a barotropic gyre. `run.sh` builds one MITgcm executable for this
configuration with the tree's own `tools/genmake2` (the build configuration
under `mods/`: `SIZE.h`, `packages.conf` and the option headers of the
upstream experiment, gfortran optfile `linux_amd64_gfortran`, one process,
tiles only), then runs it on the deck under `ic/<ic>/`. Configuration:
verification/tutorial_advection_in_gyre/input: a single-layer 60x60 Cartesian box at 20 km resolution (four tiles of 30x30, 5000 m deep, beta plane, linear equation of state with sBeta=0 and a uniform 20 C temperature so the flow is purely wind-driven and barotropic, no-slip sides and bottom, implicit free surface, readBinaryPrec=64 and useSingleCPUio) restarted from the deck's pickup at iteration 259200, that is after a ten-year spin-up, and carrying a single dye tracer initialised from dye.bin as a delta in one cell near the western boundary; the tracer is advected with pkg/ptracers scheme 80, the unlimited Prather second-order-moment scheme, which is the only place in the module where PTRACERS_ALLOW_DYN_STATE and the moment state of gad_som_advect.F are exercised, and has exactly zero horizontal, biharmonic and vertical diffusivity so the check is a pure advection test; run 120 steps of 1200 s (40 hours) against the deck's 4. No gchem, dic, bling or cfc: this is pkg/ptracers on its own..

The production path it forces: model/src/gad_som_advect.F and the gad_som_adv_x/y/r kernels, which carry and update the ten second-order moments of the tracer distribution in each cell every step, together with the barotropic momentum step and the cg2d free-surface solve of the gyre..

Runtime knobs (`run.sh --help`): `SAB_STEPS` (default 120, the graded
value; the upstream deck runs 4 steps of 1200 s) scales the
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
`writeBinaryPrec=64` so the dump is double precision and `useSingleCpuIO=.TRUE.` so the dump is one global file per field rather than one per tile; `useMNC=.FALSE.` in `data.pkg`.

`ic/variant` holds only the deck files that differ, laid over `ic/nominal` by
`run.sh`; the difference is `viscAh=400.0000000000001` in `data` instead of 400:
two ulps of the graded precision (binary64) on a parameter that enters the
tendency from the first step, a distinct double, so the two runs differ at
round-off level from the first step. The
spread between them is the check's measured sensitivity under the pass policy
and must stay inside the bound.

## The pass policy

Every cell of every prognostic field in the final state dump must satisfy
|candidate - reference| <= 1e-10 + 1e-08 |reference|.
The relative part is the working bound because the fields span many orders of
magnitude; the absolute part covers cells at or near zero. The observable is every cell of the final state dump, which here is the barotropic ocean state and the single PTRACER01 field, compared as |c - r| <= atol + rtol|r|. The bound is physical because the second-order-moment scheme is exactly conservative and, unlimited, entirely smooth: there is no branch anywhere in gad_som_advect.F for round-off to flip, so two correct runs differ only by the round-off of the advecting flow. That flow is where the honest caveat lies. This deck has no biogeochemical or tracer parameter that can be perturbed at all: all three ptracer diffusivities are set to exactly zero, and because the deck has no heat forcing, no relaxation and an empty hydrogThetaFile, temperature is identically tRef = 20 C for the whole run, which makes diffKhT a mathematical no-op. The one-ulp change is therefore made to viscAh, the lateral viscosity of the gyre the tracer rides on, which enters the momentum tendency at the first step and reaches PTRACER01 through the advecting velocity. That means, unlike the other five checks, the dynamics does differ between nominal and variant, so the cg2d solve at cg2dTargetResidual=1e-10 is part of the floor and the gyre's own round-off growth is too: the Munk boundary layer width here, (viscAh/beta)^(1/3), is about 34 km, under two grid cells, so the western boundary current is only marginally resolved and mildly eddying. Forty hours is chosen to stay well inside one eddy turnover, and it is the reason this check has by far the shortest physical window relative to its deck; if the measured spread comes back above the round-off floor of the other checks, the step count should come down rather than the bound going up.
Faults: Dropping or mis-normalising any of the ten moments in gad_som_advect.F, or updating them in the wrong operator-splitting order, changes the dye distribution by parts in 1e-2 within tens of steps and destroys the scheme's near-zero numerical diffusion, which is the entire point of the deck. Applying a limiter where none is asked for (scheme 81 rather than 80) clips the delta and changes the peak by percent. Losing the no-slip side condition or the bottom drag term that viscAz supplies changes the gyre velocities by parts in 1e-3 and, through them, the dye. Single precision in the moment state shows up at parts in 1e-6 after a few tens of steps.

## Evidence

data.pkg sets useMNC=.TRUE. and must be edited to .FALSE., because the image has no NetCDF and genmake2 drops pkg/mnc from packages.conf, which would otherwise make packages_check abort; data.mnc then becomes dead and is dropped. This deck is the one in the set that sets readBinaryPrec=64, and its topog.box5000, dye.bin, windx.m01cos2y and pickup.0000259200.data are all double precision, so readBinaryPrec must stay at 64 here even though every other check in the module needs 32. dumpFreq and chkptFreq are already 0 in the deck; only pChkptFreq needs zeroing. build/genmake_local exists in this experiment and is not part of the -mods directory. data.diagnostics writes a TRAC01 snapshot every 2592000 s (2160 steps) and two statistics streams every 259200 s (216 steps), so with 120 steps nothing from the diagnostics package lands on the final iteration and the graded set is the state dump plus PTRACER01 only. This experiment was surveyed under ocean dynamics rather than biogeochemistry; it is taken here on the parent task's instruction because it is the only pure pkg/ptracers deck in verification/.

Floor: the optimised gfortran build and the IEEE -O0 build of the same source, run natively on the x86_64 host on 2026-09-02, differ on this deck by at most 0.0e+00 in absolute terms, 0.0e+00 of the bound (in no field); the two builds pass each other under the rule. Faults, same build with one parameter changed: the cg2d target residual loosened to 1e-3 uses 8.8e+01 of the bound (FAIL), and the variant parameter off by five percent 2.8e+06 of the bound (FAIL). Measured run time of the nominal deck, build excluded: 0.7 s natively.
