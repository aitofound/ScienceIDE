# advect-xz-ppm-som

Upstream test: `code/mitgcm/verification/advect_xz/input`. Policy: `pointwise`.

## The test

Vertical-slice advection over a slope: the PPM-WENO and limited second-order-moment schemes on partial cells. `run.sh` builds one MITgcm executable for this
configuration with the tree's own `tools/genmake2` (the build configuration
under `mods/`: `SIZE.h`, `packages.conf` and the option headers of the
upstream experiment, gfortran optfile `linux_amd64_gfortran`, one process,
tiles only), then runs it on the deck under `ic/<ic>/`. Configuration:
verification/advect_xz/input: a 20x1x20 vertical slice, two tiles of 10x1, of 10 km cells and twenty 100 m levels over the sloping bottom of bathy_slope.bin, through which a steady non-divergent zonal velocity read from Uvel.bin (real*8) advects the initial tracer field Tini_G.bin, used for both temperature and salinity; momStepping=.FALSE. so the velocity never changes and the tracers never feed back (tAlpha=sBeta=0), and the point of the deck is the pair of high-order schemes it runs against each other over a partial-cell topography with hFacMin=0.1: tempAdvScheme=42, the piecewise-parabolic method with the WENO limiter, and saltAdvScheme=81, the second-order-moment scheme of Prather with its own limiter (GAD_ALLOW_TS_SOM_ADV is defined in code/GAD_OPTIONS.h, and DISABLE_MULTIDIM_ADVECTION is defined so the split multi-dimensional wrapper is out of the way); COSINEMETH_III is defined, the free surface is linear and implicit, and both readBinaryPrec and writeBinaryPrec are already 64. The deck runs endTime=240000 s at dt=1200 s, 200 steps; the window here is 400 steps, twice that..

The production path it forces: pkg/generic_advdiff: gad_ppm_adv_r.F and the WENO limiter for the vertical temperature flux, gad_som_advect.F with the Prather limiter routines for salinity (nine moment fields moved every step), and the partial-cell hFac weighting of gad_calc_rhs.F where the slope cuts the bottom cells..

Runtime knobs (`run.sh --help`): `SAB_STEPS` (default 400, the graded
value; the upstream deck runs 200 steps of 1200 s) scales the
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
magnitude; the absolute part covers cells at or near zero. The observable is every cell of U, V, W, T, S and Eta of the final dump under |c - r| <= 1e-10 + 1e-8|r|; U is frozen at the field read from Uvel.bin and W is the diagnosed vertical velocity that goes with it, so the graded content is dominated by T and S. The bound is physical because the flow is prescribed, steady and non-divergent, the tracers are passive (tAlpha=sBeta=0 and momStepping is off), and the whole integration is therefore a fixed linear operator applied 400 times; error accumulates linearly and nothing amplifies it. It is achievable because there is no elliptic solve at all (the upstream output.txt contains no cg2d_iters line), so no iteration count can flip, and because both limiters are built from min and max of continuous quantities and are Lipschitz continuous under a two-ulp perturbation. The one hazard worth naming is hFacMin=0.1, a clip on the partial-cell thickness, but it is applied once in ini_masks_etc.F from the fixed bathymetry and never re-evaluated during the run, so it cannot flip between the nominal and the variant unless the perturbation moves a cell thickness across the clip: dXspacing does not enter the vertical geometry at all, so it cannot. That is also part of why the variant is dXspacing: like the advect_xy decks this one has no viscosity, no diffusivity and no thermodynamic coefficient (tAlpha=sBeta=0, everything else at its zero default), so the horizontal grid metric is the only physical parameter that reaches the tendency, and it does so through recip_rA and dxC in the horizontal flux divergence and through the Courant number in the limiters, from the first step. It is achievable because the run is one process with the tiles swept in a fixed order (GLOBAL_SUM_ORDER_TILES), so every reduction and every solver sweep is deterministic and two correct builds of the same source differ only by round-off amplified through the steps of the integration; the nominal-versus-variant spread that selfcheck records is the measurement of that amplification under this exact rule, and the bound is finalised against it with the human.
Faults: Getting the WENO weights of the piecewise-parabolic reconstruction wrong, or applying the monotonic limiter where the WENO one is asked for, changes the vertical profile near the sharp gradients of Tini_G.bin by per cent within a couple of hundred steps. Dropping the partial-cell factor from the vertical flux at the sloping bottom breaks tracer conservation exactly where the slope cuts the cells, which is the fault this geometry exists to expose, at tens of per cent locally. Losing a moment in the second-order-moment scheme degrades salinity to a lower-order method and smears the front. Single precision gives about 1e-7 relative.

## Evidence

The variant key is spelled dXspacing (capital X) in PARM04 of the deck while ini_parms.F declares dxSpacing; the generator must match the deck's spelling. The deck uses endTime, so the generator must remove it and write nTimeSteps=400. All three binary inputs (bathy_slope.bin, Uvel.bin, Tini_G.bin) are real*8 and readBinaryPrec=64 is set explicitly; writeBinaryPrec is already 64. gendata.m and tr_checklist are not model input and are dropped; Udiv.bin belongs to the input.nlfs overlay and is harmlessly unused here. data.pkg is empty, so there is no useMNC and no diagnostics stream. No pickup. Like the advect_xy pair this deck is 400 grid points and cannot approach the 10-to-60-second target; the window was chosen for physics (twice the validated one) and the check earns its place as the module's only PPM-WENO test. The native survey did not run this experiment: it is absent from native-walltimes.txt, so the runtime here is NOT a scaled measurement but an estimate built from the grid size, the tile count, the solver iteration counts printed in verification/advect_xz/results/output.txt and the step count of the window, calibrated against the decks the survey did time. Treat it as an order-of-magnitude figure. The digits are reproduced upstream: verification/advect_xz/results/output.txt exists and the run ends normally.

Floor: the optimised gfortran build and the IEEE -O0 build of the same source, run natively on the x86_64 host on 2026-09-02, are bit-identical on this deck over all 2440 graded values (floor 0.0, in no field; re-verified on 2026-09-04 with validate.py from the retained runs); the two builds pass each other under the rule. Faults, same build with one parameter changed: the cg2d target residual loosened to 1e-3 uses 0.0e+00 of the bound (NO EFFECT (no cg2d in this configuration)), and the variant parameter off by five percent 1.5e+08 of the bound (FAIL). Measured run time of the nominal deck, build excluded: 0.9 s natively.
