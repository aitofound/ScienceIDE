# 写手简报 — mitgcm-ocean

模块:Ocean dynamical core: hydrostatic and non-hydrostatic Boussinesq solver

**可变异的源文件(7 个,模块只编译这些)**
  model/src
  pkg/mom_common
  pkg/mom_fluxform
  pkg/mom_vecinv
  pkg/cd_code
  pkg/shap_filt
  pkg/zonal_filt

**死代码 / 不可达(3 条,永远不要在这里出题)**
  - Vertical mixing and eddy parameterisations (kpp, gmredi, ggl90) are mitgcm-mixing-parameterizations
  - Atmospheric configurations of the same core (hs94, aim, fizhi) are mitgcm-atmosphere
  - pkg/generic_advdiff is listed as shared infrastructure because every module's tracers use it

**坑(2 条)**
  ! cg2d residual is a global sum; single process with fixed tile order is deterministic, MPI ranks are not
  ! tutorial_barotropic_gyre and tutorial_baroclinic_gyre write 32-bit output by default

## adjustment-cs-barotropic

- 官方测试源:`code/mitgcm/verification/adjustment.cs-32x32x1/input`
- 活配置(决定哪些分支被编译/执行):verification/adjustment.cs-32x32x1/input, the OCEANIC base deck of the experiment (the atmosphere task owns only its input.nlfs overlay): a single layer 1366 m thick on the 32x32 cubed sphere, deliberately decomposed into 48 tiles of 16x8 (nSx=2, nSy=24 in code/SIZE.h) so that each cube face carries eight tiles and four of them (tiles 11 to 14) fall entirely inside the large quasi-rectangular continent of bathy_f2.bin and become blank tiles, which is the point of the deck: it is the module's only exercise of the blank-tile bookkeeping of pkg/exch2 together with useCubedSphereExchange=.TRUE. in eedata; the ocean starts at rest with a large-scale free-surface anomaly at the equator read from ssh_eq.bin as pSurfInitFile, and relaxes by radiating external inertia-gravity (Poincare) waves; the dynamics is deliberately linear, momAdvection=.FALSE. with tempStepping and saltStepping both off and every viscosity exactly zero (viscAr=viscAh=viscA4=0), on a linear free surface (nonlinFreeSurf and hFacInf/hFacSup are commented out) with implicSurfPress=implicDiv2DFlow=0.5 and exactConserv, gravity=9.8184 and rhoConst=rhonil=1000; the curvilinear metrics come from the six tile00N.mitgrid files that prepare_run links from aim.5l_cs/input, and cg2d runs to cg2dTargetResidual=1.E-13 in five or six iterations. The window is 96 steps of 900 s, one day, four times the deck's own 24 steps (six hours), long enough for the wave front to cross several faces and every edge of the cube.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 96 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=7.90479e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=2.75335e-14

## advect-xy-som-prather

- 官方测试源:`code/mitgcm/verification/advect_xy/input`
- 活配置(决定哪些分支被编译/执行):verification/advect_xy/input: a 20x20 doubly periodic Cartesian square of 10 km cells with a single 10 km-thick level, split into two tiles of 20x10, in which a uniform diagonal velocity field is imposed analytically by the experiment's own code/ini_vel.F (uVel=vVel=1 m/s in every cell, masked and never updated because momStepping=.FALSE.) and two different tracer distributions are carried by two different schemes so that the same flow tests both: temperature is a smooth Gaussian of 20 km width centred at (40 km, 40 km), set analytically in code/ini_theta.F, advected with tempAdvScheme=80, the unlimited second-order-moment scheme of Prather that carries nine moments per cell (GAD_ALLOW_TS_SOM_ADV is defined in code/GAD_OPTIONS.h); salinity is a top hat, sRef+1 inside a circle of 60 km radius from code/ini_salt.F, advected with saltAdvScheme=33, the flux-limited third-order direct-space-time scheme, which is the combination the deck exists to compare; f0=beta=0 and tAlpha=0 so there is no rotation and no feedback of the tracers on the flow, and DISABLE_MULTIDIM_ADVECTION is defined in code/GAD_OPTIONS.h so the directionally-split multi-dimensional wrapper is out of the way. The deck runs endTime=200000 s at dt=2500 s, which is 80 steps and exactly one traversal of the 200 km periodic domain at 1 m/s; the window here is 240 steps, three full traversals, so the exact solution is again the initial condition and the graded field is directly comparable with it.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 240 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=6.39488e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=2.08167e-16

## advect-xz-ppm-som

- 官方测试源:`code/mitgcm/verification/advect_xz/input`
- 活配置(决定哪些分支被编译/执行):verification/advect_xz/input: a 20x1x20 vertical slice, two tiles of 10x1, of 10 km cells and twenty 100 m levels over the sloping bottom of bathy_slope.bin, through which a steady non-divergent zonal velocity read from Uvel.bin (real*8) advects the initial tracer field Tini_G.bin, used for both temperature and salinity; momStepping=.FALSE. so the velocity never changes and the tracers never feed back (tAlpha=sBeta=0), and the point of the deck is the pair of high-order schemes it runs against each other over a partial-cell topography with hFacMin=0.1: tempAdvScheme=42, the piecewise-parabolic method with the WENO limiter, and saltAdvScheme=81, the second-order-moment scheme of Prather with its own limiter (GAD_ALLOW_TS_SOM_ADV is defined in code/GAD_OPTIONS.h, and DISABLE_MULTIDIM_ADVECTION is defined so the split multi-dimensional wrapper is out of the way); COSINEMETH_III is defined, the free surface is linear and implicit, and both readBinaryPrec and writeBinaryPrec are already 64. The deck runs endTime=240000 s at dt=1200 s, 200 steps; the window here is 400 steps, twice that.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 400 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=4.09395e-16 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=0

## advect-xz-pqm

- 官方测试源:`code/mitgcm/verification/advect_xz/input.pqm`
- 活配置(决定哪些分支被编译/执行):verification/advect_xz/input.pqm: the same 20x1x20 vertical slice, the same non-divergent Uvel.bin and Tini_G.bin initial field over bathy_slope.bin with hFacMin=0.1 and momStepping=.FALSE., differing from the primary deck only in the pair of advection schemes it selects: tempAdvScheme=51 and saltAdvScheme=52, the piecewise QUARTIC method with the monotonic limiter and with the WENO limiter respectively (ENUM_PQM_MONO_LIMIT and ENUM_PQM_WENO_LIMIT of pkg/generic_advdiff/GAD.h). This is the module's only exercise of the PQM family, the highest-order reconstruction MITgcm offers for tracers, and running the two limiters side by side in the same flow is exactly the comparison the overlay exists for. The deck runs endTime=240000 s at dt=1200 s, 200 steps; the window here is 400 steps, twice that.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 400 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=2.96638e-16 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=6.93889e-17

## baroclinic-gyre

- 官方测试源:`code/mitgcm/verification/tutorial_baroclinic_gyre/input`
- 活配置(决定哪些分支被编译/执行):verification/tutorial_baroclinic_gyre/input: a 62x62 spherical-polar basin between 14N and 76N with 15 unequal levels down to 1800 m, decomposed as four 31x31 tiles in one process, wind-driven by a cosine zonal stress and relaxed at the surface to the observed-like SST field SST_relax.bin on a 30-day timescale, linear equation of state with tAlpha=2.E-4 and sBeta=0 so that density depends on temperature alone, saltStepping off, flux-form momentum with viscAh=5000 and viscAr=1.E-2 and no-slip sidewalls, horizontal tracer diffusion diffKhT=1000, implicit vertical diffusion with implicitDiffusion=.TRUE. and the convective-adjustment diffusivity ivdc_kappa=1, implicit free surface with exactConserv=.TRUE. and cg2d at cg2dTargetResidual=1.E-7; MNC and the diagnostics package are switched off at run time (see notes). The deck runs to endTime=12000 s, which is 10 steps of 1200 s; the window here is 40 steps, about 13.3 hours of the spin-up from rest and from a horizontally uniform tRef stratification, chosen long enough that the vertical modes and the implicit vertical solve have been exercised several times and short enough that the water column stays firmly stratified.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 40 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=7.10543e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=3.76088e-15

## cheapaml-box-coare3

- 官方测试源:`code/mitgcm/verification/cheapAML_box/input`
- 活配置(决定哪些分支被编译/执行):verification/cheapAML_box/input: a 100x100 box on a spherical polar grid of 0.25 degree cells starting at 30N, decomposed into eight tiles of 50x25, with a SINGLE ocean level 1000 m thick over topog.box, so the ocean is a slab whose only job is to provide a sea-surface temperature; on top of it runs pkg/cheapaml, a two-dimensional atmospheric mixed layer of depth cheapaml_h=1000 m that carries its own air temperature and humidity, advects and diffuses them, and computes the air-sea fluxes itself with FluxFormula='COARE3', useRelativeWind=.TRUE. (so the stress is computed from the wind relative to the ocean current), useFreshWaterFlux=.TRUE. and useFluxLimit=.TRUE. (which selects the flux-limited third-order direct-space-time scheme, GAD_DST3FL_ADV_X/Y, for the atmospheric advection instead of centred second order), with cheapaml_ntim=5 atmospheric sub-steps per ocean step and a cheapaml_mask_width=4 relaxation frame at the lateral boundaries; the ocean itself is simple, viscAh=500, diffKhT=diffKhS=200, tempAdvScheme=33, staggerTimeStep, a linear equation of state and celsius2K=273.16, with PARM02 left entirely empty so cg2d runs on its defaults. The deck runs endTime=28800 s at deltaT=1200 s, 24 steps (eight hours); the window here is 48 steps, sixteen hours, twice the deck's own.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 48 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=2.57919e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=2.54866e-14

## deep-convection-smag3d

- 官方测试源:`code/mitgcm/verification/tutorial_deep_convection/input.smag3d`
- 活配置(决定哪些分支被编译/执行):verification/tutorial_deep_convection/input.smag3d: the same half-million-cell open-ocean convection box as the acceleration check (100x100 points at 20 m spacing by 50 levels of 20 m, four 50x50 tiles in one process, f0=1.E-4, restarted from the 120-minute state T.120mn.bin, U.120mn.bin, V.120mn.bin and Eta.120mn.bin so the plumes are fully developed at step zero, cooled by Qnet_p32.bin, linear equation of state on temperature alone with saltStepping off, implicit free surface with cg2d at 1.E-9, nonHydrostatic=.TRUE. with cg3d at cg3dTargetResidual=1.E-9 and cg3dMaxIters=100) but with the constant viscosity replaced by the isotropic three-dimensional Smagorinsky closure of pkg/mom_common: useSmag3D=.TRUE. with smag3D_coeff=8.838834764831845E-4 (upstream's value chosen to reproduce the results of an earlier build that was missing a scaling factor), the residual constant viscosity dropped to viscAh=viscAz=1.E-5, the explicit tracer diffusivities switched off altogether so that temperature is mixed only by advection and by the numerical scheme, seventh-order one-step advection with a monotonicity-preserving limiter for temperature (tempAdvScheme=77), staggered time stepping, exactConserv, and both the surface forcing and the momentum dissipation taken out of the Adams-Bashforth extrapolation (forcing_In_AB=.FALSE., momDissip_In_AB=.FALSE.), which changes the time-stepping structure of the dissipation term as well as its form. The window is the deck's own 3 steps of 20 s, one minute of model time, held there because the plume field is chaotic.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 3 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=3.34281e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 4s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=0

## dome-overflow

- 官方测试源:`code/mitgcm/verification/dome/input`
- 活配置(决定哪些分支被编译/执行):verification/dome/input: the DOME dense-overflow benchmark on a 200x45 Cartesian grid (10 km zonally, a stretched delYvar meridionally) with 25 levels of 144 m over a sloping bottom (topog.slope), decomposed as 24 tiles of 25x15 in one process; this is the only check that runs pkg/mom_vecinv, selected by vectorInvariantMomentum=.TRUE., together with staggerTimeStep=.TRUE., seventh-order one-step advection with a monotonicity-preserving limiter for both temperature and salinity (tempAdvScheme=77, saltAdvScheme=77), no explicit lateral viscosity or diffusivity at all (viscAh=0, viscA4=0, diffKhT=0, diffKrT=0) so that the entire lateral dissipation is the Leith biharmonic closure viscC4Leith=1.458198138065 with useAreaViscLength=.TRUE., quadratic bottom drag bottomDragQuadratic=2.E-3, no-slip sides and bottom, hFacMin=0.2 partial cells, a linear equation of state on temperature alone (sBeta=0) and an implicit free surface solved by cg2d at the tight cg2dTargetResidual=1.E-11; pkg/obcs is on with an Orlanski radiation condition on the western boundary, a prescribed northern inflow and useOBCSbalance=.TRUE., all generated in the experiment's own code/obcs_calc.F with no external boundary data files; the window is 60 steps of 300 s, five hours of the dense plume descending the slope, against the 12000 steps of the full experiment the deck comments out.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 60 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=7.10543e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 7s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=1.06581e-14

## exp2-cd-code

- 官方测试源:`code/mitgcm/verification/exp2/input`
- 活配置(决定哪些分支被编译/执行):verification/exp2/input: a 90x40 four-degree global ocean with 20 levels down to 5200 m, decomposed as four 45x20 tiles in one process, initialised from a Levitus-like temperature and salinity field (theta.bin, salt.bin, all inputs 32-bit) with realistic bathymetry (topog.bin), forced by the Trenberth wind stress components and relaxed at the surface to climatological SST and SSS on 30-day timescales, linear equation of state, flux-form momentum with viscAh=5.E5, viscAz=1.E-3, free-slip sides and no-slip bottom, the non-hydrostatic metric terms switched on with useNHMTerms=.TRUE., implicit free surface with cg2d at the tight cg2dTargetResidual=1.E-13, convective adjustment every tracer step (cAdjFreq=-1), and the distinguishing feature, useCDscheme=.TRUE., which runs pkg/cd_code alongside the C-grid momentum with a coupling timescale tauCD=321428 s and the experiment's own CD_CODE_OPTIONS.h defining CD_CODE_NO_AB_MOMENTUM and CD_CODE_NO_AB_CORIOLIS; time stepping is asynchronous, deltaTmom=2400 s against deltaTtracer=deltaTClock=108000 s, so each clock step is 45 momentum sub-steps' worth of accelerated tracer time. The deck runs to endTime=2808000 s, which at deltaTClock=108000 is 26 steps; the window here is 40 steps, about 50 days of the accelerated spin-up, a negligible fraction of the 3110400000 s production run the deck comments out.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 40 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=2.27374e-13 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=3.41061e-13

## exp4-floats

- 官方测试源:`code/mitgcm/verification/exp4/input.with_flt`
- 活配置(决定哪些分支被编译/执行):verification/exp4/input.with_flt: the deck that used to be verification/flt_example and was moved into exp4 by upstream PR #830; the same 80x42x8 seamount channel on an f-plane with the same linear equation of state (tAlpha=2.E-4, sBeta=0) and the same lateral dissipation viscAh=1.E3, diffKhT=diffKhS=1.E3 (written here with the deprecated viscAz/diffKzT/diffKzS spellings for the vertical coefficients), but with NO open boundaries at all: the channel is closed and driven instead by a zonal wind stress read from windx.sin_y, and the only package switched on is pkg/FLT, which advects a set of Lagrangian floats whose initial positions are read from flt_ini_pos.bin, writes their trajectories every flt_int_traj=3600 s and their profiles every flt_int_prof=10800 s, with flt_noise=0 so the advection is deterministic. This is the module's only exercise of pkg/flt and hence of the bilinear interpolation of the model velocity onto off-grid particle positions. cg2d here is solved only to cg2dTargetResidual=1.E-9, which is looser than any other exp4 deck. The deck runs nTimeSteps=18 at deltaT=600 s, three hours; the window here is 72 steps, twelve hours, four times the deck's own and an integer number of the 3600 s trajectory-writing intervals.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 72 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=9.57567e-16 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=0

## exp4-obcs-rstar-vecinv

- 官方测试源:`code/mitgcm/verification/exp4/input.nlfs`
- 活配置(决定哪些分支被编译/执行):verification/exp4/input.nlfs: the same seamount channel, a 400x210x4.5 km channel on an f-plane (f0=1.E-4, beta=0) resolved as 80x42x8 cells of 5 km by 5 km by 562.5 m, decomposed into four tiles of 40x21, with a tall seamount in the middle read from topog.bump; the equation of state is linear with tAlpha=2.E-4 and sBeta=0, so salt is a passive tracer, and the dissipation is viscAr=1.E-3, viscAh=1.E3 with a deliberately small biharmonic viscA4=1.E8 put there (as the deck's own comment says) only to exercise the biharmonic path, plus diffKhT=diffKhS=1.E3 and diffKrT=diffKrS=1.E-5; hFacMin=0.2 partial cells, exactConserv, an implicit free surface, momDissip_In_AB=.FALSE. so the dissipation is outside the Adams-Bashforth extrapolation, and all binary input real*8 with readBinaryPrec=64, but hydrostatic (nonHydrostatic is commented out) and with a different momentum discretisation and a different free surface: vectorInvariantMomentum=.TRUE. with selectVortScheme=3 and selectKEscheme=2, so pkg/mom_vecinv runs with a specific vorticity and kinetic-energy pairing, staggerTimeStep=.TRUE., doAB_onGtGs=.FALSE., and the non-linear free surface in rStar form (select_rStar=2, nonlinFreeSurf=4, hFacInf=0.2, hFacSup=2.0) so the cell heights move every step; the open boundaries are specified with the newer simplified OB_singleJnorth/Jsouth/Ieast/Iwest syntax rather than the per-column arrays, and, uniquely among the exp4 decks, the SEA LEVEL itself is prescribed at the eastern and western edges from OB_WestH.bin and OB_EastH.bin, which with a small time-varying imbalance between the western inflow and the eastern outflow is what generates the sea-level fluctuations this overlay exists to test; pkg/ptracers and pkg/rbcs are still on. The deck runs nTimeSteps=10 at deltaT=600 s from baseTime=10800 s; the window here is 40 steps.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 40 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=3.43077e-11 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=0

## exp4-obcs-stevens

- 官方测试源:`code/mitgcm/verification/exp4/input.stevens`
- 活配置(决定哪些分支被编译/执行):verification/exp4/input.stevens: the same seamount channel, a 400x210x4.5 km channel on an f-plane (f0=1.E-4, beta=0) resolved as 80x42x8 cells of 5 km by 5 km by 562.5 m, decomposed into four tiles of 40x21, with a tall seamount in the middle read from topog.bump; the equation of state is linear with tAlpha=2.E-4 and sBeta=0, so salt is a passive tracer, and the dissipation is viscAr=1.E-3, viscAh=1.E3 with a deliberately small biharmonic viscA4=1.E8 put there (as the deck's own comment says) only to exercise the biharmonic path, plus diffKhT=diffKhS=1.E3 and diffKrT=diffKrS=1.E-5; hFacMin=0.2 partial cells, exactConserv, an implicit free surface, momDissip_In_AB=.FALSE. so the dissipation is outside the Adams-Bashforth extrapolation, and all binary input real*8 with readBinaryPrec=64, hydrostatic and in flux form, but with two things no other exp4 deck has: the STEVENS open-boundary formulation is selected at the eastern and western edges (useStevensEast and useStevensWest in OBCS_PARM01, with TrelaxStevens and SrelaxStevens both 86400 s in OBCS_PARM04), which replaces the simple prescription of the normal velocity by a formulation that computes the boundary tracer values from the sign of the normal flow and relaxes them on a timescale, and the bottom is made frictional with no_slip_bottom=.TRUE. and bottomDragLinear=1.E-2 m/s; pkg/ptracers and pkg/rbcs are switched OFF in this overlay's data.pkg, so only useOBCS is active and the graded set is the plain ocean state. The deck runs nTimeSteps=10 at deltaT=600 s from baseTime=10800 s; the window here is 40 steps.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 40 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=2.30491e-11 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=0
