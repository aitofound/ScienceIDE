# vermix-opps

Upstream test: `code/mitgcm/verification/vermix/input.opps`. Policy: `pointwise`.

## The test

OPPS penetrative plume convection in the same column. `run.sh` builds one MITgcm executable for this
configuration with the tree's own `tools/genmake2` (the build configuration
under `mods/`: `SIZE.h`, `packages.conf` and the option headers of the
upstream experiment, gfortran optfile `linux_amd64_gfortran`, one process,
tiles only), then runs it on the deck under `ic/<ic>/`. Configuration:
verification/vermix with the input.opps overlay: the same 1x1x26 column under the same surface cooling and wind stress, but data.pkg selects useOPPS alone, so instead of a diffusivity the mixing is done by an explicit plume model: wherever the density difference across an interface falls below STABILITY_THRESHOLD=-1e-4 the scheme launches a plume of radius PlumeRadius=100 m descending at VERTICAL_VELOCITY=0.03 m/s, entrains ambient water at ENTRAINMENT_RATE=-0.05 per unit depth up to MAX_FRACTIONAL_AREA=0.8, and redistributes temperature and salinity along the plume path; all parameters are at their package defaults because the deck's data.opps is empty; the window is 360 steps of 1200 s, five days, the same as the other vermix checks so that the whole family shares one forcing period..

The production path it forces: pkg/opps/opps_interface.F, which gathers each column and writes the mixed tracers back, and pkg/opps/opps_calc.F, whose nested plume loop over starting level and descent level (bounded by MAX_ABE_ITERATIONS) is the whole cost of the scheme; the surrounding step still runs model/src/impldiff.F for the background viscAz and diffKzT..

Runtime knobs (`run.sh --help`): `SAB_STEPS` (default 360, the graded
value; the upstream deck runs 20 steps of 1200 s) scales the
run linearly, and `SAB_BUILD_JOBS` (default 4) only the build. Expected run
time on the declared resources, build excluded: about 3 s;
the per-check build (roughly 40 s on an x86_64 host) is reported by `run.sh`
as `SAB_BUILD_SECONDS` and does not count against the suite budget.

## The two initial conditions

`ic/nominal` is the upstream deck, assembled as `testreport` assembles it
(the experiment's `input/`, the input.opps/ overlay),
with these deck edits: `nTimeSteps` set to the graded window, `dumpFreq`,
`pChkptFreq` and `chkptFreq` set to zero and `dumpInitAndLast=.TRUE.` so that the only
state written is the initial and final dump, and
`writeBinaryPrec=64` so the dump is double precision and `useSingleCpuIO=.TRUE.` so the dump is one global file per field rather than one per tile; `useMNC=.FALSE.` in `data.pkg`.

`ic/variant` holds only the deck files that differ, laid over `ic/nominal` by
`run.sh`; the difference is `ENTRAINMENT_RATE=-0.04999999999999999` in `data.opps` instead of -0.05:
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
|candidate - reference| <= 1e-10 + 1e-08 |reference|; inside `dynDiag` the records `OPPScadj` are not graded (OPPScadj is an integer count of convection events).
The relative part is the working bound because the fields span many orders of
magnitude; the absolute part covers cells at or near zero. The graded observable is every cell of the final prognostic dump plus the deck's mixed-layer-depth diagnostic, and the relative bound is physical because after a convection event the column is, by construction, the neutrally mixed profile the plume model prescribes; that profile is fixed by the entrainment and area rules, so any error in them displaces it by parts in a hundred. It is achievable for the usual vermix reason: one disconnected column, no global sums, a degenerate barotropic solve, and direct tridiagonal arithmetic with no convergence tolerance, so two runs of the same build are bit-identical and the measured spread is exactly the amplification of the one-ulp parameter change. The caution a reviewer must carry away is that OPPS is the least smooth scheme in the suite: whether a plume starts at all is a strict inequality on the density difference against STABILITY_THRESHOLD, and a state perturbed by one ulp can in principle fall on the other side of it, which would give one cell an O(1) difference rather than a round-off one. Two consequences follow, and both are built into this check. First, the integer plume counter OPPSconvectCount that the deck asks the diagnostics package to output as OPPScadj cannot be graded at all, so the whole dynDiag file is excluded; a single flipped event changes that average by 1/360, eight orders of magnitude above the bound, and it carries no information a graded temperature profile does not. Second, if the calibration measures an isolated cell with an O(1) difference rather than a round-off spread, that is the threshold flipping and not a broken check, and the response is to shorten the window rather than to loosen the bound. The opposite failure is also possible and is the reason the variant is flagged in the notes: if no plume forms anywhere in five days, perturbing an OPPS-only parameter produces an identically zero spread.
Faults: OPPS is the only scheme in this suite that moves tracers directly rather than through a diffusivity, so a fault is loud: dropping the entrainment update of the plume mass flux in pkg/opps/opps_calc.F (the newflux accumulation) makes the plume penetrate to the wrong depth and changes the post-convection temperature profile by tenths of a kelvin, parts in 1e-2. A wrong plume radius recomputation from the new mass flux (the radius = sqrt(newflux/(Wd*Dd)) line) changes the fractional area and hence how much ambient water is mixed, again at the percent level. Mis-signing the stability test would either mix a stable column or leave an unstable one unmixed, an O(1) failure that the graded temperature profile shows immediately. Single-precision plume arithmetic leaves around 1e-7 relative in the final temperature.

## Evidence

Overlay replaces data.pkg (useOPPS only); the unread input/data.kpp only produces a weak warning. useMNC must be turned off. pkg/opps has no writeState hook at all (OPPSwriteState and OPPSdumpFreq are commented out of the namelist in pkg/opps/opps_readparms.F), so there is no package snapshot to enable and only the core state dump plus the deck's DiagMXL_2d file are graded. not_graded lists dynDiag because that stream carries OPPScadj, an integer count of plume events from pkg/opps/opps_interface.F; the other six records in it (UVEL, VVEL, WVEL, THETA, PHIHYD, DFrI_TH) are duplicated by the state dump or are of secondary interest, so nothing important is lost. The variant perturbs ENTRAINMENT_RATE, an OPPS-only parameter at its package default of -0.05 (note the sign: the generator must take nextafter of a negative number); this is the right parameter physically, but it only acts when a plume exists. The upstream reference log shows the column cooling at the surface (theta_max falls step by step), so plumes are expected, but if selfcheck reports a spread of exactly zero the fallback is to move the variant to diffKzT=1e-5 in PARM01 of data, which the deck sets explicitly and which acts in every cell from the first step. ivdc_kappa is off in this deck, so OPPS is the only convective path.

Floor: self-validation measures it on every run from `run.sh altbuild`, the same source under genmake2 -ieee, graded against the nominal run with this check's validate.py, and records it in the rubric's evidence (floor, altbuild); that in-image number is the floor a reviewer reads. The native measurement of 2026-09-02 between the same two builds on the x86_64 host: the optimised gfortran build and the IEEE -O0 build differ on this deck by at most 0.0e+00 in absolute terms, 0.0e+00 of the bound (in no field); the two builds pass each other under the rule. Faults, same build with one parameter changed: the cg2d target residual loosened to 1e-3 uses 0.0e+00 of the bound (NO EFFECT: one water column, 1x1 horizontally, so the surface-pressure solve has nothing to iterate and its target cannot change the result), and the variant parameter off by five percent 8.9e+05 of the bound (FAIL). Measured run time of the nominal deck, build excluded: 0.5 s natively.
