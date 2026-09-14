# atm-gray-radiation

Upstream test: `code/mitgcm/verification/atm_gray/input`. Policy: `pointwise`.

## The test

Gray-radiation aquaplanet with atm_phys column physics, 26 levels. `run.sh` builds one MITgcm executable for this
configuration with the tree's own `tools/genmake2` (the build configuration
under `mods/`: `SIZE.h`, `packages.conf` and the option headers of the
upstream experiment, gfortran optfile `linux_amd64_gfortran`, one process,
tiles only), then runs it on the deck under `ic/<ic>/`. Configuration:
verification/atm_gray/input: the O'Gorman and Schneider gray-radiation aquaplanet (pkg/atm_phys, GFDL column physics wrapped for MITgcm) on the 32x32x6 cubed sphere with 26 non-uniform pressure levels and OLx=OLy=4, 6 tiles of 32x32 with exch2 - by far the deepest column count in the module (159744 cells); the physics is the two-stream gray radiation of radiation_mod.F90 (solar_constant=1365., atm_abs=0.22, albedo_value=0.38, wv_exponent=0.), Dargan-Betts-Miller convection (dargan_bettsmiller_mod.F90 with do_virtual and do_shallower), large-scale condensation (lscale_cond_mod.F90), Monin-Obukhov surface fluxes (surface_flux_mod.F90 with roughness 0.05 m), the vertical turbulence closure of vert_turb_driver_mod/diffusivity_mod with the tridiagonal implicit vertical diffusion of vert_diff_mod, and an INTERACTIVE 10 m slab mixed layer (mixed_layer_mod.F90, atmPhys_stepSST=.TRUE.) driven by the prescribed Q-flux Qflux_w90.bin over the SST_symEx3.bin initial state, plus a stratospheric wind damping (atmPhys_tauDampUV=86400. over the top six levels); the dynamics is vector-invariant with useAbsVorticity, selectVortScheme=3, selectKEscheme=3, addFrictionHeating, a nonlinear rStar free surface, all explicit viscosities and diffusivities set to zero so pkg/shap_filt (nShapT=4, nShapUV=4, Shap_TrLength=140000., Shap_Trtau=1800., Shap_uvtau=900.) is the only dissipation, and cg2d on cg2dTargetResWunit=8.E-16; restarted from the deck's pickup and pickup_atmPhys at iteration 81000 (one model year) and run the deck's own 10 steps of 384 s (64 minutes), the full upstream window, kept there because the moist aquaplanet is chaotic and the convection scheme carries triggers..

The production path it forces: pkg/atm_phys's atm_phys_driver.F over 6144 columns of 26 levels every step: radiation_mod.F90's radiation_down and radiation_up, which build the shortwave and longwave transmissivity profiles and integrate the two-stream equations up and down all 27 interfaces per column; dargan_bettsmiller_mod.F90, which computes CAPE and the reference profile per column; lscale_cond_mod.F90; vert_turb_driver_mod/diffusivity_mod and the tridiagonal solves of vert_diff_mod (gcm_vert_diff_down/up); and, on the dynamics side, mom_vecinv.F, calc_phi_hyd.F and shap_filt_uv_s2.F/shap_filt_tracer_s2.F over 26 levels with OLx=4 halos..

Runtime knobs (`run.sh --help`): `SAB_STEPS` (default 10, the graded
value; the upstream deck runs 10 steps of 384 s) scales the
run linearly, and `SAB_BUILD_JOBS` (default 4) only the build. Expected run
time on the declared resources, build excluded: about 4 s;
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
`run.sh`; the difference is `solar_constant=1365.0000000000005` in `data.atm_gray` instead of 1365:
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
magnitude; the absolute part covers cells at or near zero. The graded observable is the full state dump over 26 levels, and the round-off floor here is set by the vertical integrals rather than by an iterative solve: radiation_down and radiation_up accumulate transmissivity products and flux sums down and up 27 interfaces per column, which is a fixed-length recurrence with no termination test, so two correct runs differ in it only by the last bits of about 27 sequential operations, of order 1e-15 relative; the tridiagonal vertical diffusion in vert_diff_mod is likewise a direct solve of fixed length, not an iteration; and cg2d stops on cg2dTargetResWunit=8.E-16, machine precision per unit weight, so the pressure solve contributes about 1e-15 even if the iteration count differs by one. The switches that a round-off perturbation could flip are in the convection: dargan_bettsmiller_mod.F90 decides per column whether a parcel is buoyant and where the level of zero buoyancy sits, and lscale_cond_mod.F90 gates on saturation. Over ten steps the perturbation stays near 1e-13 relative, so the chance that any of the 6144 columns sits within 1e-13 of its trigger, or that the discrete level of zero buoyancy shifts by one, is small but not zero; that is the argument for keeping this window at the deck's own 10 steps and for letting the calibration selfcheck set the final bound. The variant perturbs solar_constant, which the deck sets explicitly to 1365. in the RADIATION_NML group of data.atm_gray (the module default in radiation_mod.F90 is 1360.) and which radiation_down uses at line 341 as solar = 0.25*solar_constant*(1 + del_sol*p2 + del_sw*ss) with select_incSW=0, i.e. a time-invariant insolation profile: with no diurnal cycle in this configuration the perturbation reaches EVERY column on the very first step, which makes this the cleanest variant of the six and the one whose measured spread is most representative of the deck's true sensitivity.
The binding field on the two-build floor is PH: the optimised and the IEEE build differ by 4.1e-10 there, 0.025 of the bound (39x headroom), and the two-ulp variant uses 4.3e-3 (233x), also in PH; the human accepted this headroom on 2026-09-05 rather than widen the rule.
Faults: Truncating the two-stream integration (skipping the window band, or using a coarser vertical quadrature in radiation_down/radiation_up) changes the radiative heating by tenths of a K/day, parts in 1e-5 of T per step and parts in 1e-4 over the window. Replacing the exponential transmissivity by a linearised form changes the longwave cooling rate by per cent. Getting the Betts-Miller reference profile or the relaxation time wrong in dargan_bettsmiller_mod.F90 changes T and q in convecting columns by parts in 1e-3 in one step. Solving the vertical diffusion explicitly, or dropping the implicit coupling between the surface flux and the lowest level in gcm_vert_diff_down/up, changes the lowest-level T by parts in 1e-4 per step and destabilises within tens of steps. Stepping the slab SST with the wrong depth or dropping the Q-flux in mixed_layer_mod.F90 changes the surface temperature by parts in 1e-5 per step. Any of these, and any single-precision column physics (parts in 1e-7), is decades above a round-off bound.

## Evidence

BUILD HAZARD, THE MOST IMPORTANT NOTE IN THIS FILE: atm_gray does NOT build with a bare 'genmake2 -mods code -optfile linux_amd64_gfortran'. The experiment ships verification/atm_gray/build/genmake_local, which sets FFLAGS='-fdefault-real-8 -fdefault-double-8' and ALWAYS_USE_F90=1, and genmake2 reads genmake_local from the CURRENT BUILD DIRECTORY. pkg/atm_phys is Fortran-90 GFDL code written with bare 'real' declarations that must be promoted to 8 bytes; without genmake_local the package compiles at single precision (or fails to compile at all) and every number in the dump is wrong. The generator must therefore copy verification/atm_gray/build/genmake_local into the build directory that run.sh creates, alongside -mods, and the check is not valid until a build log confirms the '-fdefault-real-8' setting was echoed. This is why the upstream README insists on passing an explicit optfile. Second: prepare_run links the six dxC1_dXYa.face00N.bin curvilinear grid files from ../../fizhi-cs-32x32x40/input - the fizhi experiment is excluded as a CHECK but its input directory must still be present in the source tree for this check to build its grid. Third: the pickups here are named with a .data extension (pickup.0000081000.data/.meta and pickup_atmPhys.0000081000.data/.meta), unlike the cubed-sphere decks whose pickups have no extension; a collection glob of the form '*.<iter>.data' will match the INPUT pickup as well as the output fields, which is harmless only because the final iteration is 81010 and the input pickup is at 81000 - do not assume that invariant if the window ever starts at the pickup iteration. Fourth: data.diagnostics streams fire at 432000 s and the run starts at t=31104000 s, an exact multiple, so the next write is 432000 s away and no diagnostics file lands inside the 3840 s window; stream 3's fileName is commented out so its -172800 s snapshot is inert. useSingleCpuIO=.TRUE. is set and is harmless on one process. useMNC is commented out and packages.conf does not list mnc. The slab-ocean SST is prognostic but lives only in pickup_atmPhys, so it is not directly graded; its error reaches the graded fields only through the surface fluxes. Window is the deck's own 10 steps.

Floor: self-validation measures it on every run from `run.sh altbuild`, the same source under genmake2 -ieee, graded against the nominal run with this check's validate.py, and records it in the rubric's evidence (floor, altbuild); that in-image number is the floor a reviewer reads. The native measurement of 2026-09-02 between the same two builds on the x86_64 host: the optimised gfortran build and the IEEE -O0 build differ on this deck by at most 4.1e-10 in absolute terms, 2.5e-02 of the bound (in PH); the two builds pass each other under the rule. Faults, same build with one parameter changed: the cg2d W-unit target (the deck's active key; cg2dTargetResidual is inert here) loosened 1e10 to 8.0E-06 uses 2.9e+06 of the bound (FAIL, 429317 of 964608 values over, cg2d 4 iterations instead of 14), and loosened only 1e3 to 8.0E-13 uses 0.26 of the bound (NOT REJECTED), and the variant parameter off by five percent 3.1e+09 of the bound (FAIL). Measured run time of the nominal deck, build excluded: 3.9 s natively.
