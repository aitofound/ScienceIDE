# isomip-icefront

Upstream test: `code/mitgcm/verification/isomip/input.icefront`. Policy: `pointwise`.

## The test

Vertical calving face with pkg/icefront on top of the shelfice cavity. `run.sh` builds one MITgcm executable for this
configuration with the tree's own `tools/genmake2` (the build configuration
under `mods/`: `SIZE.h`, `packages.conf` and the option headers of the
upstream experiment, gfortran optfile `linux_amd64_gfortran`, one process,
tiles only), then runs it on the deck under `ic/<ic>/`. Configuration:
verification/isomip/input.icefront laid over input: the same 50x100x30 ISOMIP cavity from rest, but with pkg/icefront switched on next to pkg/shelfice and the shelfice thermodynamics moved off the ISOMIP branch (useISOMIPTD=.FALSE., SHELFICEconserve=.TRUE., SHELFICEboundaryLayer=.TRUE., no gamma friction, so the transfer coefficients are the constant SHELFICEheatTransCoeff and its salt companion and the melt comes from the three-equation quadratic); the ice front is described by frontdepth.xuyun and frontcircum.xuyun, which give a depth and a wetted circumference to every column so that a vertical melting face is distributed over the water column, and applyIcefrontTendT and applyIcefrontTendS put the resulting heat and fresh-water tendencies into theta and salt at every level the face touches; graded window 60 steps of 1800 s, three times the deck's 20. Both diagnostics streams (shelficeDiag with SHIfwFlx and SHIhtFlx, icefrontDiag with ICFfwFlx and ICFhtFlx) are retimed to the run length so that the two packages' melt rates are graded side by side..

The production path it forces: pkg/icefront/icefront_thermodynamics.F, which walks every column that carries a front, builds the linear ice temperature profile between ICEFRONTthetaSurface and the base, solves the same style of melt balance (eps1, eps2, eps5 and the latent-heat denominator) at every level, and scales the result by the wetted area from the depth and circumference files, followed by icefront_tendency_apply.F, which adds the tendency to gT and gS; then pkg/shelfice/shelfice_thermodynamics.F on the horizontal ice base, model/src/cg2d.F at about 210 iterations per step, model/src/thermodynamics.F and model/src/convective_adjustment.F..

Runtime knobs (`run.sh --help`): `SAB_STEPS` (default 60, the graded
value; the upstream deck runs 20 steps of 1800 s) scales the
run linearly, and `SAB_BUILD_JOBS` (default 4) only the build. Expected run
time on the declared resources, build excluded: about 9 s;
the per-check build (roughly 40 s on an x86_64 host) is reported by `run.sh`
as `SAB_BUILD_SECONDS` and does not count against the suite budget.

## The two initial conditions

`ic/nominal` is the upstream deck, assembled as `testreport` assembles it
(the experiment's `input/`, the input.icefront/ overlay),
with these deck edits: `nTimeSteps` set to the graded window, `dumpFreq`,
`pChkptFreq` and `chkptFreq` set to zero and `dumpInitAndLast=.TRUE.` so that the only
state written is the initial and final dump, and
`writeBinaryPrec=64` so the dump is double precision and `useSingleCpuIO=.TRUE.` so the dump is one global file per field rather than one per tile; `dumpAtLast=.TRUE.` in `data.diagnostics`; `frequency(1)=108000.` in `data.diagnostics`; `frequency(2)=108000.` in `data.diagnostics`.

`ic/variant` holds only the deck files that differ, laid over `ic/nominal` by
`run.sh`; the difference is `ICEFRONTlatentHeat=334000.0000000001` in `data.icefront` instead of 334000:
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
magnitude; the absolute part covers cells at or near zero. The graded set is the state dump plus the two package melt-rate files, and the bound is physical because both melt closures are algebraic: the icefront flux is a wetted-area-weighted balance between the ocean heat delivered at the local transfer coefficient and the latent heat plus the conductive load of warming ice from ICEFRONTthetaSurface to the freezing point, so a wrong area weighting, a wrong ice profile or a missing term moves the flux by percents, and the flux is applied straight into the theta and salt tendencies where the first graded time level already sees it. It is achievable because the icefront and shelfice routines contain no iteration and no tolerance at all, only arithmetic over a fixed list of columns and levels; the only iterative object in the whole check is cg2d, whose residual test at 1e-13 sets the floor and is reached after about 210 deterministic conjugate-gradient steps with global sums taken over tiles in a fixed order in a single process. The window is 30 hours from rest in a laminar cavity, so the comparison stays pointwise. The one caveat a reviewer must know is that, like the base ISOMIP deck, this configuration starts from a uniform T and S column and calls convective adjustment every step, so the neutral-density comparisons inject a one-ulp perturbation from the first step and the floor will be measurably looser than in the pickup-started checks; the recorded spread, not an assumption, is what the bound is set against.
Faults: Scaling the icefront tendency by the cell face area instead of the wetted circumference times the layer thickness, or forgetting the recip_drF factor when the flux is converted into a tendency in pkg/icefront/icefront_tendency_apply.F, moves theta and salt near the face by parts in 1e-2. Using the base temperature instead of the linear ice profile between ICEFRONTthetaSurface and zero, or dropping the ICEFRONTheatCapacity_Cp term in the latent-heat denominator of icefront_thermodynamics.F, changes ICFfwFlx by several percent. Applying the tendency only in the top cell rather than through the whole front depth is an order-one error at depth and would be caught by the first graded T field. On the shelfice side, taking the wrong root of the three-equation quadratic or dropping the SHELFICEconserve correction moves SHIfwFlx by parts in 1e-2. A relaxed cg2d target or a single-precision state shows up at parts in 1e-9 and 1e-7 respectively.

## Evidence

Hazards. (1) This overlay carries no data file of its own, so it inherits verification/isomip/input/data with nTimeSteps=20, useCDScheme=.TRUE., tauCD=400000 and cAdjFreq=-1; the neutral initial column and the every-step convective adjustment are the same floor hazard as in isomip-shelfice-isomiptd. (2) The overlay supplies its own icetopo.exp1 and phi0surf.exp1.jmd95z, which must win over the copies in input/. (3) frontdepth.xuyun and frontcircum.xuyun are 64-bit 50x100 fields; readBinaryPrec=64 must stay. (4) data.pkg has no useMNC, so no NetCDF edit is needed. (5) Both diagnostics lists have an explicit fileName, so both are active; pkg/diagnostics ignores lists with a blank fileName, which the upstream output.icefront.txt confirms. Their upstream frequency of 18000 s already divides a 60-step run of 108000 s, so the frequency edits are only a guard against a step count that does not. (6) ICEFRONTkappa is in the ICEFRONT_PARM01 namelist but is never referenced by icefront_thermodynamics.F, so it is not usable as a variant; ICEFRONTlatentHeat, the package default of 334000 J/kg, enters eps2 and the melt denominator on the first step and is the right knob. (7) ALLOW_EXF is not compiled here, so the subglacial-runoff block commented out at the bottom of data.icefront is inert. (8) Under the two-ulp ICEFRONTlatentHeat variant every graded prognostic field (Eta, PH, PHL, S, T, U, V, W) and shelficeDiag are bit-identical between the two runs; only icefrontDiag differs, by 7.99e-14 against a reference maximum of 10.3, because the melt tendency is scaled by ICEFRONTlength, the front length over the cell area (icefront_thermodynamics.F), which puts the perturbation below the ulp of T. The recorded spread therefore characterises the icefront diagnostic alone; the state-side evidence for this check is the two-build floor, 5.8e-14 in U. A shelfice-side variant would reach the state directly, as it does in the four sibling ISOMIP checks; whether to switch is the steward's call.

Floor: self-validation measures it on every run from `run.sh altbuild`, the same source under genmake2 -ieee, graded against the nominal run with this check's validate.py, and records it in the rubric's evidence (floor, altbuild); that in-image number is the floor a reviewer reads. The native measurement of 2026-09-02 between the same two builds on the x86_64 host: the optimised gfortran build and the IEEE -O0 build differ on this deck by at most 5.8e-14 in absolute terms, 1.2e-04 of the bound (in U); the two builds pass each other under the rule. Faults, same build with one parameter changed: the cg2d target residual loosened to 1e-3 uses 9.4e+03 of the bound (FAIL), and the variant parameter off by five percent 4.0e+06 of the bound (FAIL). Measured run time of the nominal deck, build excluded: 8.7 s natively.
