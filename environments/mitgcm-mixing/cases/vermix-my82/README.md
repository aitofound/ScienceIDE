# vermix-my82

Upstream test: `code/mitgcm/verification/vermix/input.my82`. Policy: `pointwise`.

## The test

Mellor-Yamada level 2 closure in the same forced column. `run.sh` builds one MITgcm executable for this
configuration with the tree's own `tools/genmake2` (the build configuration
under `mods/`: `SIZE.h`, `packages.conf` and the option headers of the
upstream experiment, gfortran optfile `linux_amd64_gfortran`, one process,
tiles only), then runs it on the deck under `ic/<ic>/`. Configuration:
verification/vermix with the input.my82 overlay: the same 1x1x26 forced column on the same 5 km footprint, the same Qnet_72.forcing and taux_72.forcing surface fluxes, the same MDJWF equation of state and the same frozen advection (momAdvection and tempAdvection off) as the primary vermix deck, but data.pkg now selects useMY82 alone, so the vertical viscosity and diffusivity come from the Mellor and Yamada level-2 algebraic closure: the flux Richardson number is obtained from the gradient Richardson number capped at RiMax=0.195 through the quadratic of pkg/my82/my82_calc.F, the stability functions SH and SM follow, the turbulent kinetic energy is diagnosed as b1*(SH*GH+SM*GM), an energy-weighted centre of mass of that profile gives a boundary length scale MYhbl scaled by MYhblScale, and viscosity and diffusivity are MYhbl squared times the local turbulent velocity times SM or SH, floored by the background viscArNr and diffKrNrS and capped by MYviscMax=1 (the package default) and the deck's MYdiffMax=10; MYwriteState is on; the window is 360 steps of 1200 s, five days and exactly one externForcingPeriod, eighteen times the upstream twenty-step window, so that the overlay's own diagnostics streams close at the final iteration..

The production path it forces: pkg/my82/my82_calc.F, which evaluates the gradient Richardson number through pkg/my82/my82_ri_number.F, forms the stability functions and the length scale in three vertical sweeps and writes MYviscAr and MYdiffKr, then pkg/my82/my82_calc_visc.F and my82_calc_diff.F, which hand those profiles to the tridiagonal solves in model/src/impldiff.F and model/src/solve_tridiagonal.F; the MDJWF density evaluations in model/src/find_rho.F feed the Richardson number every step..

Runtime knobs (`run.sh --help`): `SAB_STEPS` (default 360, the graded
value; the upstream deck runs 20 steps of 1200 s) scales the
run linearly, and `SAB_BUILD_JOBS` (default 4) only the build. Expected run
time on the declared resources, build excluded: about 3 s;
the per-check build (roughly 40 s on an x86_64 host) is reported by `run.sh`
as `SAB_BUILD_SECONDS` and does not count against the suite budget.

## The two initial conditions

`ic/nominal` is the upstream deck, assembled as `testreport` assembles it
(the experiment's `input/`, the input.my82/ overlay),
with these deck edits: `nTimeSteps` set to the graded window, `dumpFreq`,
`pChkptFreq` and `chkptFreq` set to zero and `dumpInitAndLast=.TRUE.` so that the only
state written is the initial and final dump, and
`writeBinaryPrec=64` so the dump is double precision and `useSingleCpuIO=.TRUE.` so the dump is one global file per field rather than one per tile; `useMNC=.FALSE.` in `data.pkg`; `MYdumpFreq=432000.` in `data.my82`; `useSingleCpuIO=.TRUE.` in `data`.

`ic/variant` holds only the deck files that differ, laid over `ic/nominal` by
`run.sh`; the difference is `MYhblScale=0.10000000000000003` in `data.my82` instead of 0.1:
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
magnitude; the absolute part covers cells at or near zero. The rule is a relative bound with an absolute floor on every cell of the final prognostic dump and on the two MY82 profile fields the MYdumpFreq edit makes pkg/my82/my82_output.F write at the final iteration, and it is physical because the closure is a deterministic pointwise function of the local shear and stratification: there is no averaging, no iteration and no memory inside the step, so the profile it returns is fully determined by the formula and every fault above displaces it by parts in a hundred or worse. It is achievable for the reason that makes the whole vermix family clean: one disconnected column with DISCONNECTED_TILES, no horizontal exchange and no global reduction whose summation order could vary, a degenerate barotropic solve whose initial residual the upstream log for this deck records as exactly zero at every step, and only direct tridiagonal factorisations downstream, so the round-off floor is set by fixed-length arithmetic and not by any convergence tolerance, and two runs of the same build agree bit for bit. Five days of a stably stratified, wind- and buoyancy-forced column is a dissipative window: the closure damps perturbations rather than growing them, and the comparison stays pointwise rather than statistical. Two cautions belong in the record. The first is that MY82 contains a cap (MIN against RiMax=0.195 on the Richardson number, MIN against MYviscMax and MYdiffMax) and a floor (MAX against viscArNr and diffKrNrS), and a clamped cell is insensitive to any parameter; the variant deliberately perturbs MYhblScale, which multiplies the length scale before every clamp and therefore acts wherever the closure is not clamped, but if the measured spread came out identically zero it would mean every cell was clamped and the fallback is to move the perturbation to diffKzT=1e-5 in PARM01 of data, which the deck sets explicitly and which acts in every cell from the first step. The second is that RiMax is set in pkg/my82/my82_readparms.F but is not a member of the MY_PARM01 namelist, so it cannot be used as a variant however attractive it looks.
The dynDiag record DFrI_TH, the implicit vertical diffusive flux of temperature, is excluded from grading as it is in vermix-kpp: measured on 2026-09-05 from the retained runs, the two-ulp variant moves it by 0.108 of the bound while every state field stays under 0.02, a heavy tail in one diagnostic record that the state does not share; with it excluded the binding fields are MYdiffKr and MYviscAr, the closure's own coefficients, at 0.084 and 0.083 of the bound (12x headroom, accepted by the human on 2026-09-05); the two builds are bit-identical on this deck.
Faults: MY82 is a closed algebraic closure whose output profiles are graded directly, so a fault is immediately visible. A wrong coefficient in the flux-Richardson quadratic of my82_calc.F (the beta1 to beta4 constants) changes SH and SM by tens of percent wherever the Richardson number is order one and moves MYVISCAR and MYDIFFKR by the same amount, parts in 1e-1. Replacing the energy-weighted centre of mass that defines MYhbl by a simpler depth estimate changes the viscosity quadratically, since it enters as MYhbl squared, so a ten percent error in the length scale is a twenty percent error in the viscosity and reaches the temperature profile at parts in 1e-3 within a day. Omitting the MAX against the background viscArNr and diffKrNrS leaves the deep, quiescent part of the column with no mixing at all, an O(1) difference below the mixed layer. Computing the Richardson number from a one-sided instead of a centred difference in my82_ri_number.F shifts the whole profile by a level and gives O(1) errors at the base of the mixed layer. A single-precision evaluation of the closure leaves around 1e-7 relative in the viscosity, an order of magnitude above the relative bound.

## Evidence

The overlay replaces data.pkg (useMY82 only, useKPP off) and data.diagnostics; input/data.kpp is then present but unread and MITgcm prints only the weak warning of model/src/packages_unused_msg.F, which is how testreport runs this deck upstream too. data.pkg still sets useMNC=.TRUE. and must be turned off. MYdumpFreq is not written in data.my82 and defaults to dumpFreq, which the generator zeroes, so the extra edit MYdumpFreq=432000. is what makes pkg/my82/my82_output.F write the MYviscAr and MYdiffKr snapshot at the final iteration; 432000. is steps*dt and an operator who overrides SAB_STEPS simply loses that snapshot from both runs. MYhblScale is likewise not written in the deck, so the generator must insert it into MY_PARM01 with the base value 0.1 taken from pkg/my82/my82_readparms.F. The overlay's data.diagnostics writes dynDiag (UVEL, VVEL, WVEL, THETA, PHIHYD, DFrI_TH), DiagMXL_3d (MYVISCAR, MYDIFFKR) and DiagMXL_2d (MXLDEPTH, MYHBL) at 432000 s, which with 360 steps is exactly the final iteration, so all of them are graded; every one of them is a continuous function of the state. All input binaries are real*8 and the deck keeps readBinaryPrec=64. ivdc_kappa is commented out in this deck. This deck sets neither globalFiles nor useSingleCpuIO, so MITgcm's mdsio writes one file per tile and names the final dump <field>.<iteration>.001.001.data (pkg/mdsio/mdsio_write_field.F, the 'Case of 1 file per tile' branch), which the generator's collector and validate.py, both of which match ^<field>.<10 digits>.data$, would not see at all; the extra edit useSingleCpuIO=.TRUE. makes mdsio gather the tiles and write one global file per field, exactly as every sea-ice check's deck does. It is a pure I/O switch and changes no arithmetic; globalFiles=.TRUE. would do the same job for the non-exch2 decks, but useSingleCpuIO is the variant the finished task already exercises.

Floor: self-validation measures it on every run from `run.sh altbuild`, the same source under genmake2 -ieee, graded against the nominal run with this check's validate.py, and records it in the rubric's evidence (floor, altbuild); that in-image number is the floor a reviewer reads. The native measurement of 2026-09-02 between the same two builds on the x86_64 host: the optimised gfortran build and the IEEE -O0 build differ on this deck by at most 0.0e+00 in absolute terms, 0.0e+00 of the bound (in no field); the two builds pass each other under the rule. Faults, same build with one parameter changed: the cg2d target residual loosened to 1e-3 uses 0.0e+00 of the bound (NO EFFECT: one water column, 1x1 horizontally, so the surface-pressure solve has nothing to iterate and its target cannot change the result), and the variant parameter off by five percent 8.8e+07 of the bound (FAIL). Measured run time of the nominal deck, build excluded: 0.5 s natively.
