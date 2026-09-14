# advect-xy-som-prather

Upstream test: `code/mitgcm/verification/advect_xy/input`. Policy: `pointwise`.

## The test

Two-dimensional advection of a Gaussian and a top hat: Prather second-order moments against a flux limiter. `run.sh` builds one MITgcm executable for this
configuration with the tree's own `tools/genmake2` (the build configuration
under `mods/`: `SIZE.h`, `packages.conf` and the option headers of the
upstream experiment, gfortran optfile `linux_amd64_gfortran`, one process,
tiles only), then runs it on the deck under `ic/<ic>/`. Configuration:
verification/advect_xy/input: a 20x20 doubly periodic Cartesian square of 10 km cells with a single 10 km-thick level, split into two tiles of 20x10, in which a uniform diagonal velocity field is imposed analytically by the experiment's own code/ini_vel.F (uVel=vVel=1 m/s in every cell, masked and never updated because momStepping=.FALSE.) and two different tracer distributions are carried by two different schemes so that the same flow tests both: temperature is a smooth Gaussian of 20 km width centred at (40 km, 40 km), set analytically in code/ini_theta.F, advected with tempAdvScheme=80, the unlimited second-order-moment scheme of Prather that carries nine moments per cell (GAD_ALLOW_TS_SOM_ADV is defined in code/GAD_OPTIONS.h); salinity is a top hat, sRef+1 inside a circle of 60 km radius from code/ini_salt.F, advected with saltAdvScheme=33, the flux-limited third-order direct-space-time scheme, which is the combination the deck exists to compare; f0=beta=0 and tAlpha=0 so there is no rotation and no feedback of the tracers on the flow, and DISABLE_MULTIDIM_ADVECTION is defined in code/GAD_OPTIONS.h so the directionally-split multi-dimensional wrapper is out of the way. The deck runs endTime=200000 s at dt=2500 s, which is 80 steps and exactly one traversal of the 200 km periodic domain at 1 m/s; the window here is 240 steps, three full traversals, so the exact solution is again the initial condition and the graded field is directly comparable with it..

The production path it forces: pkg/generic_advdiff: gad_som_advect.F and the second-order-moment advection and limiter routines (gad_som_adv_x/y, gad_som_lim_x/y) for temperature, which move nine moment fields per tracer per step, and gad_dst3fl_adv_x/y for the flux-limited salinity, plus the halo exchanges of the two tiles..

Runtime knobs (`run.sh --help`): `SAB_STEPS` (default 240, the graded
value; the upstream deck runs 80 steps of 2500 s) scales the
run linearly, and `SAB_BUILD_JOBS` (default 4) only the build. Expected run
time on the declared resources, build excluded: about 2 s;
the per-check build (roughly 40 s on an x86_64 host) is reported by `run.sh`
as `SAB_BUILD_SECONDS` and does not count against the suite budget.

## The two initial conditions

`ic/nominal` is the upstream deck, assembled as `testreport` assembles it
(the experiment's `input/`),
with these deck edits: `nTimeSteps` set to the graded window, `dumpFreq`,
`pChkptFreq` and `chkptFreq` set to zero and `dumpInitAndLast=.TRUE.` so that the only
state written is the initial and final dump, and
`writeBinaryPrec=64` so the dump is double precision and `useSingleCpuIO=.TRUE.` so the dump is one global file per field rather than one per tile.

`ic/variant` holds only the deck files that differ, laid over `ic/nominal` by
`run.sh`; the difference is `dXspacing=10000.000000000004` in `data` instead of 10000:
two ulps of the graded precision (binary64) on a parameter that enters the
tendency from the first step, a distinct double, so the two runs differ at
round-off level from the first step. The
spread between them is the check's measured sensitivity under the pass policy
and must stay inside the bound.

## The pass policy

Every cell of every prognostic field in the final state dump must satisfy
|candidate - reference| <= 1e-10 + 1e-08 |reference|.
The relative part is the working bound because the fields span many orders of
magnitude; the absolute part covers cells at or near zero. The observable is every cell of U, V, W, T, S and Eta of the final dump under |c - r| <= 1e-10 + 1e-8|r|; U and V are frozen at the analytic value 1 m/s and W is identically zero on a single level, so those three check the initialisation and the probe, while T and S carry the advection result. The bound is physical because advection of a passive tracer by a uniform, non-divergent, steady velocity field is the least chaotic problem in the module: there is no feedback, the operator applied at every step is the same, and an error in it accumulates linearly over the 240 steps rather than being amplified. It is achievable because there is no elliptic solve at all (momStepping=.FALSE. means solve_for_pressure is never reached, and indeed the upstream output.txt contains no cg2d_iters line at all), so the module's usual reproducibility hazard, an iteration-count flip, cannot occur, and because the only non-smooth elements are the two limiters, both built from min and max of continuous quantities and therefore Lipschitz continuous, so a two-ulp input perturbation produces a two-ulp output change and not a jump. What a reviewer must know is why the variant is the grid spacing rather than a diffusivity: this deck has no viscosity and no diffusivity at all (they are left at their zero defaults and momentum is not stepped), and tAlpha is explicitly zero, so no dissipative or thermodynamic coefficient exists to perturb; the same argument that made rSphere the variant of the advect-cubed-sphere check makes dXspacing the variant here. It enters ini_cartesian_grid.F as the x cell width, hence recip_rA and dxC, hence the flux divergence and the Courant number in the limiter, from the first step. One threshold had to be checked before choosing it: ini_salt.F sets the top hat with the hard test rD <= 60 km on the cell-centre coordinates, so a perturbed grid could in principle move a cell across that circle and change its initial salinity by a whole unit. It cannot happen here: with cell centres at 10000*(i-0.5) the quantity (i-4.5)^2 + (j-4.5)^2 is always an integer plus one half and can therefore never equal the 36 that rD=60 km requires, and the nearest attainable radii are about 400 m away from the circle, twenty orders of magnitude further than a two-ulp perturbation of a 10 km spacing. It is achievable because the run is one process with the tiles swept in a fixed order (GLOBAL_SUM_ORDER_TILES), so every reduction and every solver sweep is deterministic and two correct builds of the same source differ only by round-off amplified through the steps of the integration; the nominal-versus-variant spread that selfcheck records is the measurement of that amplification under this exact rule, and the bound is finalised against it with the human.
Faults: Losing or mis-updating one of the second-order moments degrades the Prather scheme to a lower-order method and smears the Gaussian by tens of per cent over three traversals; because the exact answer is the initial condition, the fault is visible simply as a broadened, shifted peak. Replacing the limiter of gad_dst3fl.F by an unlimited third-order flux, or getting its Courant-number-dependent coefficients wrong, produces the over- and undershoots at the edges of the top hat that the limiter exists to suppress, at per-cent to tens-of-per-cent level. A wrong metric factor in the flux divergence breaks conservation and shows up as a drift in the global tracer mean. Single precision gives about 1e-7 relative on theta after 240 steps.

## Evidence

CASE OF THE VARIANT KEY, please check when generating: the deck spells the parameter dXspacing (capital X) in PARM04 while model/src/ini_parms.F declares it dxSpacing; Fortran namelists are case-insensitive so both work at run time, but a generator that edits the file textually must match the spelling that is actually in the deck, which is dXspacing. The same applies to the three advect_xz checks. This deck cannot come near the 10-to-60-second run-time target: it is 400 grid points on one level, and 240 steps of it is a fraction of a second of arithmetic, so the run time is dominated by process start-up and I/O. The window was chosen for physics (an integer number of traversals of the periodic domain) rather than for cost, and the check earns its place by covering the Prather second-order-moment scheme, which nothing else in the module exercises on a Cartesian grid. The deck uses endTime, not nTimeSteps, so the generator must remove endTime and write nTimeSteps=240. readBinaryPrec is left at its default and no binary file is read at all: every field is set analytically in the experiment's own code/ini_*.F, which also means there is nothing to link and nothing to gunzip. tr_checklist is a testreport control file, not model input, and is dropped. No pickup. No packages: data.pkg is empty, so there is no useMNC and no diagnostics stream to worry about. The native survey did not run this experiment: it is absent from native-walltimes.txt, so the runtime here is NOT a scaled measurement but an estimate built from the grid size, the tile count, the solver iteration counts printed in verification/advect_xy/results/output.txt and the step count of the window, calibrated against the decks the survey did time. Treat it as an order-of-magnitude figure. The digits are reproduced upstream: verification/advect_xy/results/output.txt exists and the run ends normally.

Floor: the optimised gfortran build and the IEEE -O0 build of the same source, run natively on the x86_64 host on 2026-09-02, differ on this deck by at most 2.1e-16 in absolute terms, 2.6e-07 of the bound (in T); the two builds pass each other under the rule. Faults, same build with one parameter changed: the cg2d target residual loosened to 1e-3 uses 0.0e+00 of the bound (NO EFFECT (no cg2d in this configuration)), and the variant parameter off by five percent 4.3e+08 of the bound (FAIL). Measured run time of the nominal deck, build excluded: 0.2 s natively.
