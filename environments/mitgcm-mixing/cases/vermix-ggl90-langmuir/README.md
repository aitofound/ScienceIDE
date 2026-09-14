# vermix-ggl90-langmuir

Upstream test: `code/mitgcm/verification/vermix/input.gglLC`. Policy: `pointwise`.

## The test

GGL90 with the Langmuir-circulation extension. `run.sh` builds one MITgcm executable for this
configuration with the tree's own `tools/genmake2` (the build configuration
under `mods/`: `SIZE.h`, `packages.conf` and the option headers of the
upstream experiment, gfortran optfile `linux_amd64_gfortran`, one process,
tiles only), then runs it on the deck under `ic/<ic>/`. Configuration:
verification/vermix with the input.gglLC overlay: the same 1x1x26 forced column, the same forcing files and the same frozen advection as the other vermix checks, with data.pkg selecting useGGL90 alone, but this deck differs from input.ggl90 in three ways that are the whole point of it: mxlMaxFlag=2 instead of 3, so the mixing length is limited by a downward and an upward sweep rather than by the distance to the surface and the bottom as well, useLANGMUIR=.TRUE., which compiles-in and switches on the Langmuir-circulation branch of pkg/ggl90/ggl90_mixinglength.F (ALLOW_GGL90_LANGMUIR is defined in the experiment's GGL90_OPTIONS.h), and a GGL90_PARM03 namelist that sets LC_Gamma=10, the factor by which the Langmuir circulation amplifies the mixing length wherever the downward sweep is the binding constraint; everything else, including GGL90TKEmin=1e-7, GGL90mixingLengthMin=3 m, GGL90writeState and the GGL90_MISSING_HFAC_BUG bug-compatibility flag, matches the primary GGL90 deck; the window is 360 steps of 1200 s, five days, so that the overlay's dynDiag, DiagMXL_3d and DiagMXL_2d streams close at the final iteration..

The production path it forces: pkg/ggl90/ggl90_calc.F, which builds and solves the implicit tridiagonal system for the turbulent kinetic energy every step, together with pkg/ggl90/ggl90_mixinglength.F, which in this deck runs the mxlMaxFlag=2 downward and upward sweeps and then the ALLOW_GGL90_LANGMUIR block that multiplies the mixing length by LC_Gamma, and the conversions in pkg/ggl90/ggl90_calc_visc.F and ggl90_calc_diff.F; the profiles are applied by model/src/impldiff.F and model/src/solve_tridiagonal.F..

Runtime knobs (`run.sh --help`): `SAB_STEPS` (default 360, the graded
value; the upstream deck runs 20 steps of 1200 s) scales the
run linearly, and `SAB_BUILD_JOBS` (default 4) only the build. Expected run
time on the declared resources, build excluded: about 3 s;
the per-check build (roughly 40 s on an x86_64 host) is reported by `run.sh`
as `SAB_BUILD_SECONDS` and does not count against the suite budget.

## The two initial conditions

`ic/nominal` is the upstream deck, assembled as `testreport` assembles it
(the experiment's `input/`, the input.gglLC/ overlay),
with these deck edits: `nTimeSteps` set to the graded window, `dumpFreq`,
`pChkptFreq` and `chkptFreq` set to zero and `dumpInitAndLast=.TRUE.` so that the only
state written is the initial and final dump, and
`writeBinaryPrec=64` so the dump is double precision and `useSingleCpuIO=.TRUE.` so the dump is one global file per field rather than one per tile; `GGL90dumpFreq=432000.` in `data.ggl90`; `useSingleCpuIO=.TRUE.` in `data`.

`ic/variant` holds only the deck files that differ, laid over `ic/nominal` by
`run.sh`; the difference is `LC_Gamma=10.000000000000004` in `data.ggl90` instead of 10:
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
magnitude; the absolute part covers cells at or near zero. The observable is every cell of the final prognostic dump plus the closure's own fields, the GGL90 turbulent kinetic energy, mixing length, diffusivity, the two viscosity components and the Prandtl number that the overlay's diagnostics streams write, and the instantaneous GGL90 snapshot that the GGL90dumpFreq edit adds at the final iteration. The relative bound is physical because the turbulent-kinetic-energy equation has a genuine equilibrium in a forced column, production, dissipation and vertical transport balancing, so the diffusivity that comes out is fixed by the coefficients and by the mixing-length rule, and every fault above moves it by parts in a hundred or more. It is achievable for the standard vermix reason: one disconnected column, no exchange, no global sum, a degenerate barotropic solve whose initial residual is exactly zero in the upstream log, and direct tridiagonal factorisations with no convergence tolerance, so two runs of the same build are bit-identical. Five days is a dissipative window even though the turbulent kinetic energy is prognostic and therefore remembers a perturbation: the dissipation term acts on the perturbation as strongly as on the mean, so the spread should saturate rather than grow. The hazard a reviewer must know about is specific to this deck and is not shared by input.ggl90. The Langmuir branch decides whether to multiply the mixing length by LC_Gamma with a bit-exact floating-point equality, IF (GGL90mixingLength .EQ. mxLength_Dn), that is, it asks whether the downward sweep was the binding side of a MIN. Most cells answer that question robustly, because the raw Gaspar length is the binding value in both sweeps and the two quantities are then literally the same number; but at the level where the downward and upward sweeps cross, the two are within round-off of each other, and a cell there can flip under a two-ulp perturbation and change its mixing length, and hence its diffusivity, by a factor of ten. That is a genuine O(1) discontinuity in one cell and no round-off bound can absorb it. It is a property of the deck rather than of the variant, since any perturbation feeds the same test through the state. A native window scan at 30, 60, 120, 240 and 360 steps should therefore be run before this check is fixed: smooth growth of the worst relative spread means 360 steps is safe, an isolated cell with an O(1) difference means the crossover flipped and the window must be shortened, or in the last resort GGL90Lmx and GGL90Kr excluded from grading. The variant perturbs LC_Gamma itself, which the deck writes explicitly in GGL90_PARM03 and which is in force in every cell on the amplified side of that test from the first step; the natural fallback, if the spread came out zero because no cell is amplified, is GGL90ck, the package default of 0.1 that multiplies mixing length times the square root of the turbulent kinetic energy in every wet cell and is the variant of the primary GGL90 check.
Faults: The Langmuir branch is a factor of ten on the mixing length in part of the column, so getting it wrong is loud. Dropping the LC_Gamma amplification altogether reduces GGL90Lmx by a factor of ten in every cell where the downward sweep binds and the diffusivity, which is proportional to the mixing length, by the same factor: an O(1) difference in GGL90Lmx and GGL90Kr and parts in 1e-2 in the temperature profile within a day. Applying the amplification to the wrong sweep, that is testing against the upward instead of the downward limit, moves the amplified region by several levels, again an O(1) difference in the graded GGL90Lmx. A one percent error in the dissipation constant GGL90ceps of ggl90_calc.F changes the equilibrium turbulent kinetic energy by about two percent and the diffusivity comparably, parts in 1e-2 of GGL90TKE and GGL90Kr. Solving the TKE equation explicitly instead of implicitly, or in single precision, leaves relative differences around 1e-7 in the temperature profile after 360 steps.

## Evidence

The overlay replaces data.pkg, data.ggl90 and data.diagnostics. Unlike every other vermix deck this one comments out useMNC, so no MNC edit is needed and input/data.mnc is simply unread; input/data.kpp is unread too and produces only the weak warning of model/src/packages_unused_msg.F. GGL90dumpFreq defaults to dumpFreq, which the generator zeroes, so the extra edit GGL90dumpFreq=432000. is what makes pkg/ggl90 write its instantaneous GGL90viscArU, GGL90viscArV, GGL90diffKr and GGL90TKE snapshot at the final iteration; 432000. is steps*dt. The overlay also defines a per-level statistics stream, stat_fName='dynStDiag' at stat_freq=-18000 (every fifteen steps) with diagSt_mnc=.FALSE., which pkg/diagnostics writes as plain text files named dynStDiag.<iteration>.txt; those are not .data files and are neither collected nor graded, but they do mean the run directory fills with twenty-four small text files, which is harmless. TKE.init is deliberately not dropped even though GGL90TKEFile is commented out, exactly as in the primary GGL90 check. GGL90_OPTIONS.h defines GGL90_MISSING_HFAC_BUG and ALLOW_GGL90_LANGMUIR and leaves ALLOW_GGL90_IDEMIX and ALLOW_GGL90_SMOOTH undefined; the build must reproduce that header unchanged. All input is real*8, readBinaryPrec=64, and ivdc_kappa is commented out. This deck sets neither globalFiles nor useSingleCpuIO, so MITgcm's mdsio writes one file per tile and names the final dump <field>.<iteration>.001.001.data (pkg/mdsio/mdsio_write_field.F, the 'Case of 1 file per tile' branch), which the generator's collector and validate.py, both of which match ^<field>.<10 digits>.data$, would not see at all; the extra edit useSingleCpuIO=.TRUE. makes mdsio gather the tiles and write one global file per field, exactly as every sea-ice check's deck does. It is a pure I/O switch and changes no arithmetic; globalFiles=.TRUE. would do the same job for the non-exch2 decks, but useSingleCpuIO is the variant the finished task already exercises.

Floor: self-validation measures it on every run from `run.sh altbuild`, the same source under genmake2 -ieee, graded against the nominal run with this check's validate.py, and records it in the rubric's evidence (floor, altbuild); that in-image number is the floor a reviewer reads. The native measurement of 2026-09-02 between the same two builds on the x86_64 host: the optimised gfortran build and the IEEE -O0 build differ on this deck by at most 0.0e+00 in absolute terms, 0.0e+00 of the bound (in no field); the two builds pass each other under the rule. Faults, same build with one parameter changed: the cg2d target residual loosened to 1e-3 uses 0.0e+00 of the bound (NO EFFECT: one water column, 1x1 horizontally, so the surface-pressure solve has nothing to iterate and its target cannot change the result), and the variant parameter off by five percent 3.0e+07 of the bound (FAIL). Measured run time of the nominal deck, build excluded: 0.5 s natively.
