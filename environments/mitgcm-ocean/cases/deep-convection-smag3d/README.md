# deep-convection-smag3d

Upstream test: `code/mitgcm/verification/tutorial_deep_convection/input.smag3d`. Policy: `pointwise`.

## The test

Non-hydrostatic deep convection closed by the three-dimensional Smagorinsky viscosity. `run.sh` builds one MITgcm executable for this
configuration with the tree's own `tools/genmake2` (the build configuration
under `mods/`: `SIZE.h`, `packages.conf` and the option headers of the
upstream experiment, gfortran optfile `linux_amd64_gfortran`, one process,
tiles only), then runs it on the deck under `ic/<ic>/`. Configuration:
verification/tutorial_deep_convection/input.smag3d: the same half-million-cell open-ocean convection box as the acceleration check (100x100 points at 20 m spacing by 50 levels of 20 m, four 50x50 tiles in one process, f0=1.E-4, restarted from the 120-minute state T.120mn.bin, U.120mn.bin, V.120mn.bin and Eta.120mn.bin so the plumes are fully developed at step zero, cooled by Qnet_p32.bin, linear equation of state on temperature alone with saltStepping off, implicit free surface with cg2d at 1.E-9, nonHydrostatic=.TRUE. with cg3d at cg3dTargetResidual=1.E-9 and cg3dMaxIters=100) but with the constant viscosity replaced by the isotropic three-dimensional Smagorinsky closure of pkg/mom_common: useSmag3D=.TRUE. with smag3D_coeff=8.838834764831845E-4 (upstream's value chosen to reproduce the results of an earlier build that was missing a scaling factor), the residual constant viscosity dropped to viscAh=viscAz=1.E-5, the explicit tracer diffusivities switched off altogether so that temperature is mixed only by advection and by the numerical scheme, seventh-order one-step advection with a monotonicity-preserving limiter for temperature (tempAdvScheme=77), staggered time stepping, exactConserv, and both the surface forcing and the momentum dissipation taken out of the Adams-Bashforth extrapolation (forcing_In_AB=.FALSE., momDissip_In_AB=.FALSE.), which changes the time-stepping structure of the dissipation term as well as its form. The window is the deck's own 3 steps of 20 s, one minute of model time, held there because the plume field is chaotic..

The production path it forces: model/src/cg3d.F through pre_cg3d.F and post_cg3d.F, the half-million-unknown non-hydrostatic pressure solve to 1.E-9, is again the dominant cost; on top of it this deck adds pkg/mom_common's mom_calc_smag_3d.F, which evaluates the full three-dimensional strain-rate tensor (all nine gradient components, on their several staggered positions) and forms the Smagorinsky viscosity on every cell of every level every step, and pkg/generic_advdiff's seventh-order limited scheme for temperature. Together with the acceleration check this is the most expensive per-step configuration in the module..

Runtime knobs (`run.sh --help`): `SAB_STEPS` (default 3, the graded
value; the upstream deck runs 3 steps of 20 s) scales the
run linearly, and `SAB_BUILD_JOBS` (default 4) only the build. Expected run
time on the declared resources, build excluded: about 4 s;
the per-check build (roughly 40 s on an x86_64 host) is reported by `run.sh`
as `SAB_BUILD_SECONDS` and does not count against the suite budget.

## The two initial conditions

`ic/nominal` is the upstream deck, assembled as `testreport` assembles it
(the experiment's `input/`, the input.smag3d/ overlay),
with these deck edits: `nTimeSteps` set to the graded window, `dumpFreq`,
`pChkptFreq` and `chkptFreq` set to zero and `dumpInitAndLast=.TRUE.` so that the only
state written is the initial and final dump, and
`writeBinaryPrec=64` so the dump is double precision and `useSingleCpuIO=.TRUE.` so the dump is one global file per field rather than one per tile; `useDiagnostics=.FALSE.` in `data.pkg`.

`ic/variant` holds only the deck files that differ, laid over `ic/nominal` by
`run.sh`; the difference is `smag3D_coeff=0.0008838834764831847` in `data` instead of 0.000883883:
two ulps of the graded precision (binary64) on a parameter that enters the
tendency from the first step, a distinct double, so the two runs differ at
round-off level from the first step. The
spread between them is the check's measured sensitivity under the pass policy
and must stay inside the bound.

## The pass policy

Every cell of every prognostic field in the final state dump must satisfy
|candidate - reference| <= 1e-10 + 1e-08 |reference|.
The relative part is the working bound because the fields span many orders of
magnitude; the absolute part covers cells at or near zero. The observable is every cell of U, V, W, T, S, Eta, PH and PNH in the final dump under |c - r| <= 1e-10 + 1e-8|r|. Vertical plume velocities are of order 1e-2 m/s, temperature is near 20 C with anomalies of order 1e-2 K, and the non-hydrostatic pressure is of order 1e-4 m2/s2, so the relative part of the bound is the working test and the absolute part covers cells that are exactly zero. The bound is physical for the same reason as for the constant-viscosity sibling: at 20 m resolution the plumes are as wide as they are tall, the hydrostatic balance is genuinely broken, and the non-hydrostatic pressure is a leading-order term rather than a correction, so an error in the operator or in the closure appears at once in W and PNH. What this check adds over the sibling is that the dissipation itself is now state-dependent: the Smagorinsky viscosity is recomputed from the resolved strain every step, so the check grades a feedback loop (strain sets viscosity, viscosity damps strain) rather than a fixed coefficient, and that loop is exactly where an accelerated implementation is likely to cut corners, for instance by evaluating the strain on a coarser stencil or by freezing the viscosity across steps. It is achievable because the window is deliberately one minute of model time: over three steps of 20 s a round-off perturbation cannot grow, since the plumes turn over on a timescale of tens of minutes; because both elliptic solves stop on their residual (cg3d has 100 iterations to reach 1.E-9, cg2d has 1000), so a flip in the last iteration costs about 1e-9, close to but not above the bound; and because the Smagorinsky viscosity is built out of squares and a square root of a strictly positive quantity in an actively straining flow, which is smooth, with no limiter and no threshold. The one thing a reviewer must know is that the window is short on purpose and must not be extended: this is the same chaotic deck as the acceleration check, three steps is what upstream ships, and the correct response to a large spread is to loosen the bound or drop the check, never to lengthen the run.
Faults: mom_calc_smag_3d.F is the term under test: dropping any of the strain-rate components, averaging them to the wrong staggered point, or getting the |S| = sqrt(2 S_ij S_ij) contraction wrong changes the viscosity field by tens of per cent everywhere the plumes are active, and because there is essentially no constant viscosity left (1.E-5 against a Smagorinsky viscosity of order 1e-2 in the plumes) there is nothing to hide the error behind: U, V and W move at the per-cent level within three steps. Getting smag3D_coeff wrong by the historical scaling factor that upstream's comment refers to changes the viscosity by a fixed ratio and the velocities by per-cent amounts. Reinstating the dissipation inside the Adams-Bashforth extrapolation (momDissip_In_AB=.TRUE.) changes the effective time discretisation of the viscous term and moves the velocities by about the Adams-Bashforth truncation error, well above 1e-8. Stopping cg3d at 1.E-5 instead of 1.E-9 gives about 1e-5 relative on PNH and W. Replacing the seventh-order limited advection by a lower-order scheme changes the temperature front by tens of per cent. Single precision gives about 1e-7 relative on PNH and W.

## Evidence

Chaotic deck: the window is fixed at the deck's own 3 steps, exactly as for the acceleration check on the same experiment, and must not be lengthened. useSmag3D requires ALLOW_SMAG_3D, which the experiment's code/MOM_COMMON_OPTIONS.h defines (it also defines COSINEMETH_III and leaves ALLOW_LEITH_QG, ALLOW_3D_VISCAH and ALLOW_3D_VISCA4 undefined); CPP_OPTIONS.h leaves ALLOW_SMAG_3D_DIFFUSIVITY undefined, and correspondingly smag3D_diffCoeff is left commented out in the deck, so the Smagorinsky closure acts on momentum only. smag3D_coeff is read in PARM01 of data by model/src/ini_parms.F (the namelist line that also carries viscC2leith, viscC4leith and useSmag3D), so the variant edit lands in the deck's own line. The overlay ships no data.diagnostics of its own, so the two streams and the DIAG_STATIS stream of input/data.diagnostics are in force; useDiagnostics must be forced off, both because the package is enabled in the overlay's data.pkg and because the DIAGNOSTICS_FILL calls inside the momentum routines would add cost. useMNC is commented out in the overlay's data.pkg. The initial-state files and Qnet_p32.bin are read at the default readBinaryPrec=64; they are ordinary input files rather than a pickup, so nIter0 stays 0 and the final iteration is 3. pChkptFreq=43200, chkptFreq=7200 and dumpFreq=3600 will be zeroed by the generator. The overlay ships its own eedata and eedata.mth; eedata.mth is filtered out by the generator and eedata sets nTx=nTy=1, which is what the single-process contract wants. SIZE.h is the largest in the module (100x100x50 across four tiles), so this check has the same memory footprint as the acceleration check.

Floor: the optimised gfortran build and the IEEE -O0 build of the same source, run natively on the x86_64 host on 2026-09-02, are bit-identical on this deck over all 3520000 graded values (floor 0.0, in no field; re-verified on 2026-09-04 with validate.py from the retained runs); the two builds pass each other under the rule. Faults, same build with one parameter changed: the cg2d target residual loosened to 1e-3 uses 2.4e+05 of the bound (FAIL), and the variant parameter off by five percent 5.8e+03 of the bound (FAIL). Measured run time of the nominal deck, build excluded: 3.3 s natively.
