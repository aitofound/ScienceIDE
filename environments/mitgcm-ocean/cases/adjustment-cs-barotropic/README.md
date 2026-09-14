# adjustment-cs-barotropic

Upstream test: `code/mitgcm/verification/adjustment.cs-32x32x1/input`. Policy: `pointwise`.

## The test

Barotropic adjustment on the cubed sphere: Poincare waves over 48 tiles with blank tiles. `run.sh` builds one MITgcm executable for this
configuration with the tree's own `tools/genmake2` (the build configuration
under `mods/`: `SIZE.h`, `packages.conf` and the option headers of the
upstream experiment, gfortran optfile `linux_amd64_gfortran`, one process,
tiles only), then runs it on the deck under `ic/<ic>/`. Configuration:
verification/adjustment.cs-32x32x1/input, the OCEANIC base deck of the experiment (the atmosphere task owns only its input.nlfs overlay): a single layer 1366 m thick on the 32x32 cubed sphere, deliberately decomposed into 48 tiles of 16x8 (nSx=2, nSy=24 in code/SIZE.h) so that each cube face carries eight tiles and four of them (tiles 11 to 14) fall entirely inside the large quasi-rectangular continent of bathy_f2.bin and become blank tiles, which is the point of the deck: it is the module's only exercise of the blank-tile bookkeeping of pkg/exch2 together with useCubedSphereExchange=.TRUE. in eedata; the ocean starts at rest with a large-scale free-surface anomaly at the equator read from ssh_eq.bin as pSurfInitFile, and relaxes by radiating external inertia-gravity (Poincare) waves; the dynamics is deliberately linear, momAdvection=.FALSE. with tempStepping and saltStepping both off and every viscosity exactly zero (viscAr=viscAh=viscA4=0), on a linear free surface (nonlinFreeSurf and hFacInf/hFacSup are commented out) with implicSurfPress=implicDiv2DFlow=0.5 and exactConserv, gravity=9.8184 and rhoConst=rhonil=1000; the curvilinear metrics come from the six tile00N.mitgrid files that prepare_run links from aim.5l_cs/input, and cg2d runs to cg2dTargetResidual=1.E-13 in five or six iterations. The window is 96 steps of 900 s, one day, four times the deck's own 24 steps (six hours), long enough for the wave front to cross several faces and every edge of the cube..

The production path it forces: model/src/cg2d.F, but only for five or six iterations, so the real cost is elsewhere: the 48-tile halo exchange, pkg/exch2's cubed-sphere face and corner exchanges (exch2_uv_agrid, the scalar exchanges and the blank-tile short-circuits in exch2_topology), model/src/integr_continuity.F and solve_for_pressure.F/calc_grad_phi_surf.F which assemble and apply the two-dimensional free-surface operator, and the Coriolis and pressure-gradient terms of pkg/mom_fluxform on a curvilinear grid..

Runtime knobs (`run.sh --help`): `SAB_STEPS` (default 96, the graded
value; the upstream deck runs 24 steps of 900 s) scales the
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
`writeBinaryPrec=64` so the dump is double precision and `useSingleCpuIO=.TRUE.` so the dump is one global file per field rather than one per tile; `useDiagnostics=.FALSE.` in `data.pkg`.

`ic/variant` holds only the deck files that differ, laid over `ic/nominal` by
`run.sh`; the difference is `gravity=9.818400000000004` in `data` instead of 9.8184:
two ulps of the graded precision (binary64) on a parameter that enters the
tendency from the first step, a distinct double, so the two runs differ at
round-off level from the first step. The
spread between them is the check's measured sensitivity under the pass policy
and must stay inside the bound.

## The pass policy

Every cell of every prognostic field in the final state dump must satisfy
|candidate - reference| <= 1e-10 + 1e-08 |reference|.
The relative part is the working bound because the fields span many orders of
magnitude; the absolute part covers cells at or near zero. The observable is every cell of U, V, Eta and the surface pressure of the final dump under |c - r| <= 1e-10 + 1e-8|r|; with tempStepping and saltStepping off, T and S are frozen at tRef=15 and sRef=0 and grading them only confirms that nothing corrupted them. The bound is physical because the problem is exactly linear: momentum advection is off, the free surface is linear, the equation of state is linear and never enters (no tracer stepping), so the map from the initial free-surface anomaly to the state after 96 steps is a fixed linear operator, and a round-off perturbation propagates through it with an amplification bounded by its condition number rather than growing exponentially as it would in a chaotic flow. There is nothing discontinuous anywhere in the deck: no convective adjustment (cAdjFreq=0), no freezing clip, no limiter (no advection at all), no moving cell heights. What a reviewer must know is why the variant is gravity rather than a viscosity: every viscosity in this deck is exactly zero, and perturbing a zero by two ulps gives a denormal that underflows out of every product and leaves the two runs bit-identical, so the only physical coefficient that reaches the tendency is gravity, which the deck sets explicitly to 9.8184. Perturbing it moves the whole barotropic system consistently: ini_parms.F line 482 sets gBaro=gravity when gBaro is unset (this deck leaves it unset), so ini_linear_phisurf.F fills Bo_surf and recip_Bo with the perturbed value and both the free-surface restoring term and the cg2d matrix change by two ulps from the first step, which is exactly the external gravity-wave speed sqrt(gH) the deck is built to measure. The other candidate, rhoConst, would have been weaker here because with a linear free surface and no tracer stepping it cancels out of most of the barotropic balance. The one-day window is four times the deck's own and is safe because the system is linear and undamped rather than unstable; it is nevertheless deliberately not stretched further, because with zero viscosity nothing damps accumulated round-off and a very long integration would test arithmetic accumulation rather than the discretisation. It is achievable because the run is one process with the tiles swept in a fixed order (GLOBAL_SUM_ORDER_TILES), so every reduction and every solver sweep is deterministic and two correct builds of the same source differ only by round-off amplified through the steps of the integration; the nominal-versus-variant spread that selfcheck records is the measurement of that amplification under this exact rule, and the bound is finalised against it with the human.
Faults: A wrong blank-tile decision (running a tile that should be skipped, or skipping one that should run) shows up immediately as a wrong Eta over the continent or as a missing halo update at its boundary, at order one. A dropped or unrotated vector exchange across a cube edge leaves a seam in U and V at the face boundaries within a few steps, at tens of per cent. Getting the implicit free-surface weighting wrong (implicSurfPress or implicDiv2DFlow away from 0.5) changes the phase speed of the Poincare waves and moves Eta by per cent over one day. Loosening cg2d from 1.E-13 moves Eta by about the residual it stops at. Single precision gives about 1e-7 relative on Eta after 96 steps. All are far above 1e-8 relative.

## Evidence

prepare_run must be honoured: the six tile00N.mitgrid curvilinear grid files live in aim.5l_cs/input and are symlinked in, exactly as the atmosphere task's p-coord-nonlinear-free-surface-cs check does for the input.nlfs overlay of the same experiment; without them the run dies in ini_curvilinear_grid. data.exch2.mpi is dropped: it is the multi-process blank-tile topology that goes with code/SIZE.h_mpi and code/CPP_EEOPTIONS.h_mpi, it is never read (the model looks for data.exch2, which the deck does not ship, so pkg/exch2 builds its own six-face topology from SIZE.h), and leaving a file with that name only invites confusion. useDiagnostics must be forced off: data.diagnostics defines a dynDiag and a dyn_Aux snapshot stream at frequency -21600 s with timePhase -1800 s and a dynStDiag statistics stream at -7200 s with phase 0; at dt=900 the statistics stream lands on t=86400, i.e. on the final iteration of a 96-step window (it writes only .txt, so it would not pollute the graded glob, but the snapshot streams would if the window were changed), and switching the package off removes both the risk and the DIAGNOSTICS_FILL cost. readBinaryPrec=64 is set and both binary inputs are real*8. writeBinaryPrec is commented out in the deck, so the generator's edit to 64 is a real change; it does not affect the computation, only the dump. No pickup: nIter0=0. The deck uses nTimeSteps, not endTime. The native survey did not run this experiment: it is absent from native-walltimes.txt, so the runtime here is NOT a scaled measurement but an estimate built from the grid size, the tile count, the solver iteration counts printed in verification/adjustment.cs-32x32x1/results/output.txt and the step count of the window, calibrated against the decks the survey did time. Treat it as an order-of-magnitude figure. The digits are reproduced upstream: verification/adjustment.cs-32x32x1/results/output.txt exists for this deck (alongside output.nlfs.txt for the atmospheric overlay), the run ends normally, and the deck is not on the addendum's list of decks whose digits fail.

Floor: the optimised gfortran build and the IEEE -O0 build of the same source, run natively on the x86_64 host on 2026-09-02, differ on this deck by at most 2.8e-14 in absolute terms, 8.5e-05 of the bound (in PH); the two builds pass each other under the rule. Faults, same build with one parameter changed: the cg2d target residual loosened to 1e-3 uses 4.2e+06 of the bound (FAIL), and the variant parameter off by five percent 9.6e+09 of the bound (FAIL). Measured run time of the nominal deck, build excluded: 0.5 s natively.
