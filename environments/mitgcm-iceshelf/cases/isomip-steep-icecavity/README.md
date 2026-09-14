# isomip-steep-icecavity

Upstream test: `code/mitgcm/verification/isomip/input.stic`. Policy: `pointwise`.

## The test

Steep ice cavity: fluxes distributed over a sloping ice base. `run.sh` builds one MITgcm executable for this
configuration with the tree's own `tools/genmake2` (the build configuration
under `mods/`: `SIZE.h`, `packages.conf` and the option headers of the
upstream experiment, gfortran optfile `linux_amd64_gfortran`, one process,
tiles only), then runs it on the deck under `ic/<ic>/`. Configuration:
verification/isomip/input.stic laid over input: the 50x100x30 ISOMIP cavity from rest with pkg/steep_icecavity switched on alongside pkg/shelfice (useSTIC=.TRUE., STICdepthFile=icetopo.exp1), which replaces shelfice_thermodynamics by stic_thermodynamics and lets the melt of a steeply sloping ice base be computed against the water actually adjacent to the face rather than against the single top cell, using three-dimensional transfer coefficients (ALLOW_SHITRANSCOEFF_3D is on by default in pkg/steep_icecavity/STIC_OPTIONS.h) and solving the flux balance in stic_solve4fluxes.F; the shelfice side runs the three-equation formulation with constant transfer coefficients (no gamma friction), SHELFICEconserve=.TRUE., SHELFICEadvDiffHeatFlux=.TRUE. and SHELFICEkappa deliberately set to zero, and the deck inherits input/data, so 1800 s steps, the C-D scheme and convective adjustment every step; graded window 60 steps of 1800 s, three times the deck's 20. The three active diagnostics streams are retimed to the run length: dynDiag for the ocean state, sticDiag3D for the three-dimensional transfer coefficients and the steep-cavity fluxes and forcing terms, sticDiag2D for the vertical-face contributions..

The production path it forces: pkg/steep_icecavity/stic_thermodynamics.F, which sweeps the sloping ice face level by level, gathers the neighbouring water properties along the slope and fills the three-dimensional shiTransCoeffT3d and shiTransCoeffS3d arrays, and pkg/steep_icecavity/stic_solve4fluxes.F, which is called for every face segment and forms the local heat and fresh-water balance from gammaT, gammaS, the latent heat, the ice heat capacity and SHELFICEkappa; then model/src/cg2d.F at about 210 iterations per step, model/src/thermodynamics.F and model/src/convective_adjustment.F. This is the most expensive of the four ISOMIP checks because the flux solve is done per level along the face rather than once per column..

Runtime knobs (`run.sh --help`): `SAB_STEPS` (default 60, the graded
value; the upstream deck runs 20 steps of 1800 s) scales the
run linearly, and `SAB_BUILD_JOBS` (default 4) only the build. Expected run
time on the declared resources, build excluded: about 13 s;
the per-check build (roughly 40 s on an x86_64 host) is reported by `run.sh`
as `SAB_BUILD_SECONDS` and does not count against the suite budget.

## The two initial conditions

`ic/nominal` is the upstream deck, assembled as `testreport` assembles it
(the experiment's `input/`, the input.stic/ overlay),
with these deck edits: `nTimeSteps` set to the graded window, `dumpFreq`,
`pChkptFreq` and `chkptFreq` set to zero and `dumpInitAndLast=.TRUE.` so that the only
state written is the initial and final dump, and
`writeBinaryPrec=64` so the dump is double precision and `useSingleCpuIO=.TRUE.` so the dump is one global file per field rather than one per tile; `dumpAtLast=.TRUE.` in `data.diagnostics`; `frequency(2)=108000.` in `data.diagnostics`; `frequency(3)=108000.` in `data.diagnostics`; `frequency(4)=108000.` in `data.diagnostics`.

`ic/variant` holds only the deck files that differ, laid over `ic/nominal` by
`run.sh`; the difference is `SHELFICElatentHeat=334000.0000000001` in `data.shelfice` instead of 334000:
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
magnitude; the absolute part covers cells at or near zero. The observable is the state dump plus the three-dimensional steep-cavity diagnostics, which expose the package's own arrays (SHIgam3T, SHIgam3S, STCfwFlx, STChtFlx, STCForcT, STCForcS) rather than only their imprint on the ocean, so a fault in the face sweep is visible before it has been diluted by advection. The bound is physical because the steep-cavity closure is the same algebraic three-equation balance as the flat-base one, evaluated at a different place: the freezing point at the face depth, the transfer coefficients along the slope, and the latent-heat denominator have no free constants, and any geometric mis-assignment or dropped term moves the flux by percents, which is six orders of magnitude above a 1e-8 relative bound. It is achievable because stic_solve4fluxes.F is closed-form arithmetic with no iteration and no tolerance, and the only iterative object in the check is cg2d with its 1e-13 residual test, so two correct runs differ only by round-off amplified through the free-surface solve over 60 steps. The window is 30 hours from rest, comfortably pointwise. The reviewer must know two things: this deck inherits the base data file, so the neutral initial column and the every-step convective adjustment inject a one-ulp perturbation from the first step exactly as in the two other from-rest ISOMIP checks and the floor will be correspondingly looser; and SHELFICEkappa is set to zero in this deck, which is why the variant is placed on SHELFICElatentHeat, a parameter that stic_solve4fluxes.F uses in four separate places and that enters the melt from the first step.
Faults: Collapsing the three-dimensional transfer coefficients back to the two-dimensional top-cell values, that is using shiTransCoeffT instead of shiTransCoeffT3d in the flux loop of stic_thermodynamics.F, removes the entire point of the package and moves STCfwFlx by tens of percent wherever the ice base is steep. Mis-assigning which neighbouring water column belongs to a face segment, or using the cell centre rather than the face depth when the local freezing point is evaluated, changes the flux by parts in 1e-2. In stic_solve4fluxes.F, dropping the eps2 latent-heat term or the SHELFICEheatCapacity_Cp correction in the melt denominator is a parts-in-1e-2 error in fwFlux; using the wrong sign convention on the upward heat flux is order one. Distributing the resulting tendency over the wrong levels shows up directly in the graded T and S at depth. A relaxed cg2d target moves Eta by parts in 1e-9, and single precision anywhere in the face sweep by parts in 1e-7.

## Evidence

Hazards. (1) input.stic contains neither a data nor an eedata file, so both come from verification/isomip/input; the base data file's nTimeSteps=20, useCDScheme, cAdjFreq=-1 and neutral Tref/Sref all apply, and the neutral-column convective-adjustment comparison is the same floor hazard as in the other from-rest ISOMIP checks. (2) STICdepthFile points at icetopo.exp1, which lives in input/, so the overlay is not self-contained. (3) The first diagnostics list in data.stic has no fileName and is therefore silently dropped by pkg/diagnostics/diagnostics_readparms.F: only dynDiag, sticDiag3D and sticDiag2D are created, which the upstream output.stic.txt confirms. This means the generic SHIfwFlx/SHIhtFlx/SHIgammT/SHIgammS group is not graded in this check; the steep-cavity equivalents in sticDiag3D are, which is the point. If more coverage is wanted later, adding fileName(1)='surfDiag' would activate that list. (4) STIC_PARM01 holds only file names, so there is no STIC-specific numeric parameter available as a variant. (5) SHELFICEkappa=0 in this deck, so it cannot be used as the perturbed parameter (one ulp of zero is a denormal). (6) data.pkg has no useMNC, so no NetCDF edit is needed. (7) readBinaryPrec=64 must stay.

Floor: self-validation measures it on every run from `run.sh altbuild`, the same source under genmake2 -ieee, graded against the nominal run with this check's validate.py, and records it in the rubric's evidence (floor, altbuild); that in-image number is the floor a reviewer reads. The native measurement of 2026-09-02 between the same two builds on the x86_64 host: the optimised gfortran build and the IEEE -O0 build differ on this deck by at most 2.2e-13 in absolute terms, 2.4e-04 of the bound (in U); the two builds pass each other under the rule. Faults, same build with one parameter changed: the cg2d target residual loosened to 1e-3 uses 1.2e+04 of the bound (FAIL), and the variant parameter off by five percent 3.4e+06 of the bound (FAIL). Measured run time of the nominal deck, build excluded: 12.7 s natively.
