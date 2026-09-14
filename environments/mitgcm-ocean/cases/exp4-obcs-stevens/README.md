# exp4-obcs-stevens

Upstream test: `code/mitgcm/verification/exp4/input.stevens`. Policy: `pointwise`.

## The test

Stevens open-boundary formulation with linear bottom drag and no-slip bottom. `run.sh` builds one MITgcm executable for this
configuration with the tree's own `tools/genmake2` (the build configuration
under `mods/`: `SIZE.h`, `packages.conf` and the option headers of the
upstream experiment, gfortran optfile `linux_amd64_gfortran`, one process,
tiles only), then runs it on the deck under `ic/<ic>/`. Configuration:
verification/exp4/input.stevens: the same seamount channel, a 400x210x4.5 km channel on an f-plane (f0=1.E-4, beta=0) resolved as 80x42x8 cells of 5 km by 5 km by 562.5 m, decomposed into four tiles of 40x21, with a tall seamount in the middle read from topog.bump; the equation of state is linear with tAlpha=2.E-4 and sBeta=0, so salt is a passive tracer, and the dissipation is viscAr=1.E-3, viscAh=1.E3 with a deliberately small biharmonic viscA4=1.E8 put there (as the deck's own comment says) only to exercise the biharmonic path, plus diffKhT=diffKhS=1.E3 and diffKrT=diffKrS=1.E-5; hFacMin=0.2 partial cells, exactConserv, an implicit free surface, momDissip_In_AB=.FALSE. so the dissipation is outside the Adams-Bashforth extrapolation, and all binary input real*8 with readBinaryPrec=64, hydrostatic and in flux form, but with two things no other exp4 deck has: the STEVENS open-boundary formulation is selected at the eastern and western edges (useStevensEast and useStevensWest in OBCS_PARM01, with TrelaxStevens and SrelaxStevens both 86400 s in OBCS_PARM04), which replaces the simple prescription of the normal velocity by a formulation that computes the boundary tracer values from the sign of the normal flow and relaxes them on a timescale, and the bottom is made frictional with no_slip_bottom=.TRUE. and bottomDragLinear=1.E-2 m/s; pkg/ptracers and pkg/rbcs are switched OFF in this overlay's data.pkg, so only useOBCS is active and the graded set is the plain ocean state. The deck runs nTimeSteps=10 at deltaT=600 s from baseTime=10800 s; the window here is 40 steps..

The production path it forces: pkg/obcs's Stevens routines (obcs_calc_stevens.F and the eastern and western apply paths), which are called every step and are what this overlay exists to exercise; pkg/mom_common's bottom-drag routines (mom_u_bottomdrag.F and its v counterpart) with the linear coefficient; model/src/cg2d.F at 1.E-13; and pkg/mom_fluxform with the Laplacian and biharmonic viscosity..

Runtime knobs (`run.sh --help`): `SAB_STEPS` (default 40, the graded
value; the upstream deck runs 10 steps of 600 s) scales the
run linearly, and `SAB_BUILD_JOBS` (default 4) only the build. Expected run
time on the declared resources, build excluded: about 3 s;
the per-check build (roughly 40 s on an x86_64 host) is reported by `run.sh`
as `SAB_BUILD_SECONDS` and does not count against the suite budget.

## The two initial conditions

`ic/nominal` is the upstream deck, assembled as `testreport` assembles it
(the experiment's `input/`, the input.stevens/ overlay),
with these deck edits: `nTimeSteps` set to the graded window, `dumpFreq`,
`pChkptFreq` and `chkptFreq` set to zero and `dumpInitAndLast=.TRUE.` so that the only
state written is the initial and final dump, and
`writeBinaryPrec=64` so the dump is double precision and `useSingleCpuIO=.TRUE.` so the dump is one global file per field rather than one per tile.

`ic/variant` holds only the deck files that differ, laid over `ic/nominal` by
`run.sh`; the difference is `bottomDragLinear=0.010000000000000004` in `data` instead of 0.01:
two ulps of the graded precision (binary64) on a parameter that enters the
tendency from the first step, a distinct double, so the two runs differ at
round-off level from the first step. The
spread between them is the check's measured sensitivity under the pass policy
and must stay inside the bound.

## The pass policy

Every cell of every prognostic field in the final state dump must satisfy
|candidate - reference| <= 1e-10 + 1e-08 |reference|.
The relative part is the working bound because the fields span many orders of
magnitude; the absolute part covers cells at or near zero. The observable is every cell of U, V, W, T, S, Eta and the hydrostatic pressure of the final dump under |c - r| <= 1e-10 + 1e-8|r|; no passive tracer is written because the overlay switches pkg/ptracers off. The bound is physical for the same reason as the other exp4 checks: six hours and forty minutes of a viscous, laminar, boundary-forced channel flow at 5 km resolution, with a single well-converged two-dimensional elliptic solve at 1.E-13 and no three-dimensional one. The hazard a reviewer must weigh is specific to this overlay and is the reason it is worth naming: the Stevens formulation contains a genuine SIGN TEST on the normal velocity at the boundary, deciding whether a boundary cell is an inflow or an outflow, and a cell whose normal velocity sits within round-off of zero could in principle be classified differently in the nominal and the variant run, which would be a finite difference rather than a round-off one. Over a forty-step window with a prescribed inflow of order 1e-2 m/s at the western edge and a matching outflow at the eastern one, the normal velocities at the Stevens boundaries are far from zero and no such crossing is expected, but this is the check whose measured spread should be read most carefully, and the correct response to a jump would be to shorten the window or drop the check, never to loosen the bound. The variant is bottomDragLinear=1.E-2, which is unique to this deck among the exp4 family and is therefore the choice that exercises what the overlay adds: it enters mom_u_bottomdrag.F and its v counterpart in the bottom cell of every wet column from the first step, and because the seamount brings the bottom close to the surface in the middle of the channel the perturbation reaches the interior quickly rather than staying in a thin bottom layer. It is achievable because the run is one process with the tiles swept in a fixed order (GLOBAL_SUM_ORDER_TILES), so every reduction and every solver sweep is deterministic and two correct builds of the same source differ only by round-off amplified through the steps of the integration; the nominal-versus-variant spread that selfcheck records is the measurement of that amplification under this exact rule, and the bound is finalised against it with the human.
Faults: Getting the Stevens inflow/outflow test wrong, that is deciding from the wrong sign of the normal velocity whether a boundary tracer is relaxed towards the prescribed value or advected out, changes the temperature and salinity in the boundary columns at order one within a few steps and then propagates inwards. Getting the Stevens relaxation timescale wrong by a factor changes the boundary values by per cent over forty steps. Dropping the linear bottom drag, or applying it as a quadratic drag, changes the near-bottom velocity by tens of per cent over the seamount, which is where the flow is fastest and the drag matters most. Single precision gives about 1e-7 relative.

## Evidence

The overlay switches pkg/ptracers and pkg/rbcs OFF (both are commented out in its data.pkg), so the rbcs and ptracers input that arrives from input/ is dead weight: rbcs_Tr1_fld.bin and rbcs_mask.bin are 215 kB each and are dropped along with data.rbcs and data.ptracers, and the two OB files the overlay comments out (OBzonalW.bin, which only a non-hydrostatic run reads, and OBzonalU.bin) are dropped too. OBzonalS.bin IS still read (OBWsFile) and must stay. The overlay ships its own data.obcs, so the primary deck's is replaced rather than merged. There is no data.diagnostics and no useMNC in the experiment, so no extra edit is needed. baseTime=10800 s with nIter0=0. No pickup, nothing to link, nothing to gunzip. The native survey did not run this experiment: it is absent from native-walltimes.txt, so the runtime here is NOT a scaled measurement but an estimate built from the grid size, the tile count, the solver iteration counts printed in verification/exp4/results/output.stevens.txt and the step count of the window, calibrated against the decks the survey did time. Treat it as an order-of-magnitude figure. The digits are reproduced upstream: verification/exp4/results/output.stevens.txt exists and the run ends normally.

Floor: the optimised gfortran build and the IEEE -O0 build of the same source, run natively on the x86_64 host on 2026-09-02, are bit-identical on this deck over all 168000 graded values (floor 0.0, in no field; re-verified on 2026-09-04 with validate.py from the retained runs); the two builds pass each other under the rule. Faults, same build with one parameter changed: the cg2d target residual loosened to 1e-3 uses 2.6e+07 of the bound (FAIL), and the variant parameter off by five percent 3.3e+07 of the bound (FAIL). Measured run time of the nominal deck, build excluded: 0.5 s natively.
