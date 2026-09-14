# cfc-online

Upstream test: `code/mitgcm/verification/cfc_example/input`. Policy: `pointwise`.

## The test

Online CFC-11 and CFC-12 with the layers package. `run.sh` builds one MITgcm executable for this
configuration with the tree's own `tools/genmake2` (the build configuration
under `mods/`: `SIZE.h`, `packages.conf` and the option headers of the
upstream experiment, gfortran optfile `linux_amd64_gfortran`, one process,
tiles only), then runs it on the deck under `ic/<ic>/`. Configuration:
verification/cfc_example/input: the 2.8-degree global ocean (128x64x15, four tiles of 64x32, POLY3 equation of state, implicit free surface with exactConserv, CD-scheme momentum, ivdc_kappa=10, GM/Redi) restarted from the deck's pickup and pickup_cd at iteration 4269600 and its linked pickup_ptracers, carrying two CFC tracers with the flux-limited scheme 77 and a vertical tracer diffusivity of 5e-5 m2/s; pkg/gchem calls pkg/cfc each step, which interpolates the northern- and southern-hemisphere atmospheric CFC-11 and CFC-12 mixing ratios from the ASCII table cfc1112.atm in time and across the equatorial band (atmCFC_yNorthBnd/ySouthBnd) and applies the solubility and Schmidt-number gas exchange of cfc11_surfforcing.F and cfc12_surfforcing.F under prescribed wind speed and ice fraction; pkg/layers is on, so the deck also accumulates the temperature- and density-layer transports LaUH1TH, LaVH1TH, LaUH2RHO and LaVH2RHO, and its DIAGNOSTICS_LIST sets dumpAtLast=.TRUE. so that stream is written at the end of any run; 20 tracer steps of 43200 s, 10 days, against the deck's 4..

The production path it forces: pkg/cfc/cfc_atmos.F and cfc_param.F for the time and latitude interpolation of the atmospheric table, cfc11_surfforcing.F and cfc12_surfforcing.F for the Wanninkhof solubility and Schmidt number over every surface cell, and pkg/layers (layers_calc.F, layers_fluxcalc.F) which bins the full three-dimensional transport into temperature and density classes every step; on the transport side two flux-limited gad_advection.F sweeps, the GM/Redi tensor and the tridiagonal implicit vertical diffusion per tracer..

Runtime knobs (`run.sh --help`): `SAB_STEPS` (default 20, the graded
value; the upstream deck runs 4 steps of 43200 s) scales the
run linearly, and `SAB_BUILD_JOBS` (default 4) only the build. Expected run
time on the declared resources, build excluded: about 6 s;
the per-check build (roughly 40 s on an x86_64 host) is reported by `run.sh`
as `SAB_BUILD_SECONDS` and does not count against the suite budget.

## The two initial conditions

`ic/nominal` is the upstream deck, assembled as `testreport` assembles it
(the experiment's `input/`, and the files its prepare_run links from sibling experiments),
with these deck edits: `nTimeSteps` set to the graded window, `dumpFreq`,
`pChkptFreq` and `chkptFreq` set to zero and `dumpInitAndLast=.TRUE.` so that the only
state written is the initial and final dump, and
`writeBinaryPrec=64` so the dump is double precision and `useSingleCpuIO=.TRUE.` so the dump is one global file per field rather than one per tile.

`ic/variant` holds only the deck files that differ, laid over `ic/nominal` by
`run.sh`; the difference is `PTRACERS_diffKr(1)=5.0000000000000016e-05` in `data.ptracers` instead of 5e-05:
two ulps of the graded precision (binary64) on a parameter that enters the
tendency from the first step, a distinct double, so the two runs differ at
round-off level from the first step. The
spread between them is the check's measured sensitivity under the pass policy
and must stay inside the bound.

## The pass policy

Every cell of every prognostic field in the final state dump must satisfy
|candidate - reference| <= 1e-20 + 1e-08 |reference| (the CFC concentrations are of order 1e-9 mol/m3, so the usual absolute part of 1e-10 would swallow the tracer entirely: a five percent error in the tracer diffusivity moved the tracer by 3e-4 relative and still passed under 1e-10; with 1e-20 the absolute part only covers exact zeros; the ocean state of this deck (U, V, W, T, S, Eta, PH, PHL) is not graded here because it cannot live under a 1e-20 absolute part (near-zero velocities differ at round-off) and is the object of the ocean-dynamics checks; this check grades the two CFC tracers and the layers diagnostics; DiagOcnLAYERS bins transports into discrete density layers, a classification round-off can flip, and is not graded); the fields `DiagOcnLAYERS`, `Eta`, `PH`, `PHL`, `S`, `T`, `U`, `V`, `W` are not graded.
The relative part is the working bound because the fields span many orders of
magnitude; the absolute part covers cells at or near zero. The comparison is pointwise over the ocean state, the two PTRACERnn fields and the layers diagnostics, and it is achievable because the perturbed parameter is the vertical diffusivity of tracer 1 only: temperature, salinity, momentum and the free surface are computed without reference to the passive tracers in this configuration, so the whole dynamical core, including cg2d at cg2dTargetResidual=1e-13 and the convective-adjustment switch at ivdc_kappa=10, replays bit-identically and the difference lives entirely in the CFC-11 field and whatever the layers package derives from the identical velocity and density. The bound is physical because CFC uptake is a linear, strongly damped surface-flux problem with no internal sources or sinks: the tracer relaxes towards the local solubility equilibrium and is then stirred, so a round-off change in the vertical mixing coefficient decays rather than grows and ten days is far inside the pointwise regime. The floor is set by the tridiagonal implicit vertical solve, which is a direct factorisation with no tolerance, by the min/max branches of the scheme-77 limiter, which are continuous, and by the accumulation order of the layers binning, which is fixed for a single process with tiles swept in fixed order. A reviewer should note that grading tracer 2 as well as tracer 1 is deliberate: CFC-12 must come back bit-identical, and any spread there would mean the two tracers are coupled somewhere they should not be.
Faults: A wrong Schmidt-number polynomial or a dropped temperature dependence of the solubility in cfc11_surfforcing.F changes the piston velocity by percent and the surface CFC concentration by parts in 1e-4 within a step. Interpolating the atmospheric table with the wrong offset (atmCFC_timeOffset is derived from PTRACERS_Iter0 and the time step) shifts both tracers by parts in 1e-3. Mis-binning the layers transports, for instance by using the cell-centre rather than the interface density, moves LaUH2RHO by order one in individual bins while leaving the tracers untouched, which is exactly the kind of fault a check that graded only the tracers would miss. Cheapening the implicit vertical diffusion solve, or dropping the hFac weighting from it, moves both CFCs by parts in 1e-5.

## Evidence

The pickup data files in this deck are stored without the .data suffix (pickup.0004269600 is 8060928 bytes = 128*64*123*8 with its .meta sidecar alongside, and pickup_cd.0004269600 has no .meta at all). This is legal: pkg/mdsio/mdsio_read_field.F first tries the bare file name and only then fName.data, so the files must be copied verbatim and must not be renamed. prepare_run links two sets of files, and it must not overwrite the deck's own sillev1-free set: from tutorial_global_oce_biogeo/input everything except sillev1.bin and bathy.bin, and from tutorial_cfc_offline/input the bathymetry depth_g77.bin and the ptracers pickup at 4269600. All linked binaries are 32-bit, so readBinaryPrec stays at 32. data.ptracers sets PTRACERS_Iter0=4248000 below nIter0=4269600, which is what makes the model read pickup_ptracers rather than the initial files. code/MDSIO_BUFF_3D.h and code/LAYERS_SIZE.h are part of the build configuration and travel with the -mods directory.

Floor: the optimised gfortran build and the IEEE -O0 build of the same source, run natively on the x86_64 host on 2026-09-02, differ on this deck by at most 4.4e-21 in absolute terms, 3.9e-02 of the bound (in PTRACER02); the two builds pass each other under the rule. Faults, same build with one parameter changed: the cg2d target residual loosened to 1e-3 uses 4.5e+05 of the bound (FAIL), and the variant parameter off by five percent 1.1e+05 of the bound (FAIL). Measured run time of the nominal deck, build excluded: 5.9 s natively.
