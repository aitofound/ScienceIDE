# 写手简报 — mitgcm-atmos

模块:Atmospheric configurations: Held-Suarez and intermediate physics

**可变异的源文件(6 个,模块只编译这些)**
  pkg/aim_v23
  pkg/atm_phys
  pkg/atm_common
  pkg/fizhi
  pkg/gridalt
  pkg/land

**死代码 / 不可达(2 条,永远不要在这里出题)**
  - fizhi (the GEOS physics) is old, large and has no tutorial; propose it as a check pool only if the aim decks are too few
  - Coupled atmosphere-ocean (cpl_aim+ocn) needs two executables and a coupler, not packaged

**坑(2 条)**
  ! Held-Suarez runs are chaotic at long horizons; the short graded windows stay pointwise
  ! fizhi has its own non-standard grids (gridalt) and legacy code paths

## aim-cubed-sphere-land

- 官方测试源:`code/mitgcm/verification/aim.5l_cs/input`
- 活配置(决定哪些分支被编译/执行):verification/aim.5l_cs/input: the SPEEDY v23 intermediate-complexity atmosphere (pkg/aim_v23) on the 32x32x6 cubed sphere with 5 pressure levels, 6 tiles of 32x32 with exch2, real topography (topo.2f2_FM.bin) and the Franco Molteni surface boundary conditions (aim_useFMsurfBC with albedo, vegetation, SST, land surface temperature, sea-ice fraction, snow depth and soil moisture read from the deck's .bin fields), coupled to pkg/land for the ground temperature, soil moisture and snow prognostics (land_dzF = 0.1, 4.0 m, implicit ground temperature) with aim_energPrecip and aim_splitSIOsFx on and aim_dragStrato=2592000.; the dynamics is vector-invariant with useJamartWetPoints, a nonlinear rStar free surface (nonlinFreeSurf=4, select_rStar=2, exactConserv, hFacMin=0.2), third-order humidity advection (saltAdvScheme=3), cg2d on cg2dTargetResWunit=8.E-16, and pkg/shap_filt with nShapT=4, nShapUV=4, Shap_Trtau=5400., Shap_uvtau=1800.; restarted from the deck's pickup and pickup_land at iteration 69120 (one model year) and run the deck's own 10 steps of 450 s (75 minutes), the full upstream window, kept there because a spun-up moist atmosphere with convective triggers is chaotic over any longer window.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 10 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=6.70552e-08 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=6.70552e-08

## aim-cubed-sphere-thsice-from-rest

- 官方测试源:`code/mitgcm/verification/aim.5l_cs/input.thSI`
- 活配置(决定哪些分支被编译/执行):verification/aim.5l_cs/input with the input.thSI overlay: the SPEEDY v23 physics on the 32x32x6 cubed sphere with 5 pressure levels, 6 tiles of 32x32 with exch2, but with a THIRD surface package stacked under AIM - pkg/thsice (useThSIce=.TRUE. with data.ice: Tf0kel=273.15, rhosw=1030., iceMaskMin=0.01, hThinIce=0.1, hiMax=hsMax=10., stepFwd_oceMxL=.TRUE. so the slab ocean mixed layer is stepped forward, tauRelax_MxL=5184000., stressReduction=0.) beside pkg/land and pkg/aim_v23, and with the coupled-model surface boundary fields (topo.cpl_FM.bin, landFrc.cpl_FM.bin, albedo_cs32.bin, seaSurfT/lndSurfT/seaIce/snowDepth/soilMoist .cpl_FM.bin) instead of the 2f2/FM set of the primary deck; the dynamics is again vector-invariant with useJamartWetPoints, staggerTimeStep, a nonlinear rStar free surface (nonlinFreeSurf=4, select_rStar=2, exactConserv, hFacInf=0.2, hFacSup=2.0, hFacMin=0.2, uniformLin_PhiSurf=.FALSE.), integr_GeoPot=2 with selectFindRoSurf=1 and atm_Rq=0.6078E-3, third-order humidity advection, cg2d on cg2dTargetResWunit=7.8E-16, and pkg/shap_filt with nShapT=4, nShapUV=4, nShapTrPhys=1, Shap_TrLength=140000., Shap_Trtau=5400., Shap_uvtau=1800.; unlike every other AIM check this deck starts FROM REST at nIter0=0 (no pickup: U=V=0, theta=tRef, specific humidity identically zero, surface pressure from the topography alone) and runs the deck's own 10 steps of 450 s (75 minutes), which is the full upstream window.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 10 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=4.76837e-07 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=9.53674e-07

## aim-equatorial-channel

- 官方测试源:`code/mitgcm/verification/aim.5l_Equatorial_Channel/input`
- 活配置(决定哪些分支被编译/执行):verification/aim.5l_Equatorial_Channel/input: the SPEEDY v23 physics (pkg/aim_v23) on a spherical-polar equatorial CHANNEL of 128x23 points at 2.8125 degrees from 32.34S to 32.34N with 5 pressure levels, carried as 4 tiles of 32x23 on one process (2944 physics columns, the smallest AIM deck in the tree), closed by solid walls at the two channel edges by the experiment's own code/ini_depths.F, which sets Ro_surf=rF(Nr+1) wherever |yC| >= |ygOrigin|; the distinguishing feature is that BOTH standard AIM surface-boundary paths are switched off (aim_useFMsurfBC=.FALSE. and aim_useMMsurfFc=.FALSE. in data.aimphys) and the experiment's own code/aim_surf_bc.F supplies the surface state analytically - a Gaussian warm pool sst1 = 280 + 20*exp(-((x-xBump)/dxBump)^2 - ((y-yBump)/dyBump)^2) with land and ice surface temperatures set equal to it and the year fraction FROZEN at tYear = 0.25 - 10/365, so the insolation pattern does not move; there is no land package and no sea ice, the dynamics is vector-invariant-free (flux-form momentum, vectorInvariantMomentum unset) with staggerTimeStep, exactConserv, a linear implicit free surface, rotationPeriod=86400., gravity=9.81, rhoConst=1.0, third-order humidity advection (saltAdvScheme=3), tracForcingOutAB=1, cg2d on cg2dTargetResWunit=5.E-16, and pkg/shap_filt with Shap_funct=2, nShapT=4, nShapUV=4, Shap_Trtau=5400., Shap_uvtau=1800. and Shap_noSlip=1. for the channel walls; restarted from the deck's pickup at iteration 51840 (one model year at 600 s steps) and run the deck's own 10 steps of 600 s (100 minutes), the full upstream window.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 10 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=1.27329e-11 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=2.18279e-11

## aim-latlon-monthly-forcing

- 官方测试源:`code/mitgcm/verification/aim.5l_LatLon/input`
- 活配置(决定哪些分支被编译/执行):verification/aim.5l_LatLon/input: the SPEEDY v23 physics on a global spherical-polar grid of 128x64 points at 2.8125 degrees with 5 pressure levels, carried as 4 tiles of 128x16 on one process with OLx=OLy=3 - 8192 physics columns, the largest column count of any AIM deck in the tree and the reason this is the acceleration check; the surface boundary condition is the MONTHLY-MEAN path rather than the Molteni climatology (aim_useMMsurfFc=.TRUE., aim_surfPotTemp=.TRUE., aim_MMsufx='.ft.bin'), so aim_fields_load.F reads the twelve monthly stheta/smoist/salb fields and aim_surf_bc.F linearly interpolates them in time on every step, a code path no other check touches; the dynamics is FLUX-FORM momentum (vectorInvariantMomentum is not set) on a linear implicit free surface with exactConserv, real filtered topography (topo.filt_55.bin), third-order humidity advection, cg2d on cg2dTargetResWunit=9.E-16, pkg/shap_filt with nShapT=4, nShapUV=4, Shap_Trtau=5400., Shap_uvtau=1800. and Shap_noSlip=1., and pkg/zonal_filt's FFT polar filter poleward of 45 degrees; restarted from the deck's pickup at iteration 69120 (one model year) and run the deck's own 10 steps of 450 s (75 minutes), which is the full upstream window and the longest window a moist chaotic atmosphere with convective triggers can be compared over pointwise.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 10 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=8.18545e-11 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=2.18279e-10

## atm-gray-aquaplanet-window-band

- 官方测试源:`code/mitgcm/verification/atm_gray/input.ape`
- 活配置(决定哪些分支被编译/执行):verification/atm_gray/input with the input.ape overlay: the same 26-level, 32x32x6 cubed-sphere gray-radiation aquaplanet as atm-gray-radiation (pkg/atm_phys, OLx=OLy=4, vector-invariant momentum with useAbsVorticity, selectVortScheme=3, selectKEscheme=3, addFrictionHeating, nonlinear rStar free surface, all explicit viscosities and diffusivities zero so pkg/shap_filt is the only dissipation, cg2d on cg2dTargetResWunit=8.E-16, restarted from pickup.0000081000 and run for the deck's own 10 steps of 384 s), but the overlay replaces data.atm_gray and data.atm_phys and thereby switches THREE code paths inside pkg/atm_phys that the primary deck never reaches: wv_exponent=-1. selects the two-band longwave scheme of radiation_mod.F90 in which the spectral water-vapour window (default window=0.3732, set inside radiation_mod when wv_exponent=-1) is carried separately from the non-window band, solar_exponent=0. selects the CO2/water-vapour shortwave transmissivity branch instead of the p**solar_exponent profile scaled by atm_abs, and mixed_layer_bc together with an unset atmPhys_stepSST turns the interactive slab mixed layer OFF so the surface temperature is the prescribed aqua-planet-experiment profile read from SST_APE_1.bin and held fixed; the overlay also drops atmPhys_tauDampUV, so the stratospheric wind damping of the primary deck is absent, and leaves solar_constant, del_sol, atm_abs and albedo_value at the radiation_mod.F90 module defaults (1360., 1.4, 0.0, 0.06) instead of the deck values of the primary check.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 10 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=2.32831e-10 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=4.94765e-10

## atm-gray-radiation

- 官方测试源:`code/mitgcm/verification/atm_gray/input`
- 活配置(决定哪些分支被编译/执行):verification/atm_gray/input: the O'Gorman and Schneider gray-radiation aquaplanet (pkg/atm_phys, GFDL column physics wrapped for MITgcm) on the 32x32x6 cubed sphere with 26 non-uniform pressure levels and OLx=OLy=4, 6 tiles of 32x32 with exch2 - by far the deepest column count in the module (159744 cells); the physics is the two-stream gray radiation of radiation_mod.F90 (solar_constant=1365., atm_abs=0.22, albedo_value=0.38, wv_exponent=0.), Dargan-Betts-Miller convection (dargan_bettsmiller_mod.F90 with do_virtual and do_shallower), large-scale condensation (lscale_cond_mod.F90), Monin-Obukhov surface fluxes (surface_flux_mod.F90 with roughness 0.05 m), the vertical turbulence closure of vert_turb_driver_mod/diffusivity_mod with the tridiagonal implicit vertical diffusion of vert_diff_mod, and an INTERACTIVE 10 m slab mixed layer (mixed_layer_mod.F90, atmPhys_stepSST=.TRUE.) driven by the prescribed Q-flux Qflux_w90.bin over the SST_symEx3.bin initial state, plus a stratospheric wind damping (atmPhys_tauDampUV=86400. over the top six levels); the dynamics is vector-invariant with useAbsVorticity, selectVortScheme=3, selectKEscheme=3, addFrictionHeating, a nonlinear rStar free surface, all explicit viscosities and diffusivities set to zero so pkg/shap_filt (nShapT=4, nShapUV=4, Shap_TrLength=140000., Shap_Trtau=1800., Shap_uvtau=900.) is the only dissipation, and cg2d on cg2dTargetResWunit=8.E-16; restarted from the deck's pickup and pickup_atmPhys at iteration 81000 (one model year) and run the deck's own 10 steps of 384 s (64 minutes), the full upstream window, kept there because the moist aquaplanet is chaotic and the convection scheme carries triggers.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 10 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=2.61934e-10 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 4s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=4.07454e-10

## held-suarez-cs

- 官方测试源:`code/mitgcm/verification/hs94.cs-32x32x5/input`
- 活配置(决定哪些分支被编译/执行):verification/hs94.cs-32x32x5/input: the Held-Suarez (1994) dry benchmark on the 32x32x6 cubed sphere with 5 pressure levels, carried as 12 tiles of 16x32 with exch2 halo exchange across the six faces (useCubedSphereExchange), curvilinear metrics read from the six tile00N.mitgrid files that prepare_run links from aim.5l_cs/input, ideal-gas atmospheric buoyancy with integr_GeoPot defaults, vector-invariant momentum with staggerTimeStep and the quasi-second-order Adams-Bashforth (alph_AB=0.6, beta_AB=0.), an implicit linear free surface on surface pressure solved by cg2d to cg2dTargetResidual=1.E-12, the Held-Suarez Newtonian relaxation and Rayleigh drag supplied by the experiment's own apply_forcing.F, and pkg/shap_filt as the only dissipation (Shap_funct=2, nShapUV=4 with nShapUVPhys=4); started from rest at nIter0=0 with the analytic ini_theta.F profile and run the deck's own 20 steps of 600 s (3.3 h of model time), which is the full upstream window and short enough that the chaotic dry core has not yet separated trajectories.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 20 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=2.04891e-08 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=4.09782e-08

## held-suarez-latlon-polar-filter

- 官方测试源:`code/mitgcm/verification/hs94.128x64x5/input`
- 活配置(决定哪些分支被编译/执行):verification/hs94.128x64x5/input: the Held-Suarez dry benchmark on a global spherical-polar grid of 128x64 points at 2.8125 degrees with 5 pressure levels, carried as 2 tiles of 128x32 on one process, and it is the one deck in this module that runs the FLUX-FORM momentum code: vectorInvariantMomentum is not set, so mom_fluxform.F rather than mom_vecinv.F carries the momentum tendency, with selectCoriScheme=2 for the Coriolis discretisation; the polar singularity is handled by pkg/zonal_filt (zonal_filt_lat=45., sinpow=cospow=2), an FFT-based zonal filter that damps the modes a lat-lon grid cannot resolve poleward of 45 degrees, and pkg/shap_filt (Shap_funct=2, nShapT=4, nShapUV=4, Shap_Trtau=Shap_uvtau=5400.) supplies the horizontal dissipation; the Held-Suarez relaxation and drag come from the experiment's own external_forcing.F, the legacy interface that model/src/apply_forcing.F still dispatches to; started from rest at nIter0=0 with the T.init profile and run the deck's own 10 steps of 450 s (75 minutes), the full upstream window, which is far shorter than any chaotic separation time.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 10 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=2.54659e-11 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=1.20281e-10

## held-suarez-meridional-strip-s4-filter

- 官方测试源:`code/mitgcm/verification/hs94.1x64x5/input`
- 活配置(决定哪些分支被编译/执行):verification/hs94.1x64x5/input: the Held-Suarez (1994) dry benchmark on a spherical-polar grid ONE point wide in longitude and 64 points from pole to pole at 2.8125 degrees, with 5 pressure levels, carried as 2 tiles of 1x32 on one process; with a single zonal point and a periodic x direction every zonal derivative vanishes identically, so this is a two-dimensional (latitude-height) Held-Suarez problem and it is the cheapest atmospheric deck in the tree; all explicit dissipation is switched off by hand (viscAr=viscAh=viscA4=0, diffKrT=diffKhT=diffK4T=0, diffKrS=diffKhS=diffK4S=0) and pkg/shap_filt is the only damping, but uniquely in this module it selects Shap_funct=4, which routes shap_filt_apply_uv.F and shap_filt_apply_ts.F to shap_filt_uv_s4.F and shap_filt_tracer_s4.F instead of the s2 routines every other check uses, and which forces Shap_alwaysExchUV and Shap_alwaysExchTr to .TRUE. in shap_filt_readparms.F; the dynamics uses staggerTimeStep with abEps=0.1, an implicit linear free surface with exactConserv on cg2dTargetResidual=1.E-13 and cg2dMaxIters=600, gravity=9.81, rhoConst=1.0, and the Held-Suarez Newtonian relaxation and Rayleigh drag come from the experiment's own code/apply_forcing.F; pkg/mypackage is switched on but is the unmodified template (all myPa_applyTend* default to .FALSE.) and contributes nothing; started from rest at nIter0=0 with the analytic code/ini_theta.F profile and run the deck's own 10 steps of 1200 s (3.3 hours of model time), the full upstream window.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 10 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=1.78069e-06 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=3.21306e-06

## held-suarez-rstar-20l

- 官方测试源:`code/mitgcm/verification/tutorial_held_suarez_cs/input`
- 活配置(决定哪些分支被编译/执行):verification/tutorial_held_suarez_cs/input: the same Held-Suarez forcing as the 5-level deck but on 20 pressure levels of 50 hPa each, on the 32x32x6 cubed sphere as 6 tiles of 32x32 with exch2, and with the free surface treated nonlinearly: nonlinFreeSurf=4 with select_rStar=2, exactConserv=.TRUE., hFacInf=0.2/hFacSup=2.0 and uniformLin_PhiSurf=.FALSE., so the vertical coordinate is rescaled every step (calc_r_star.F, update_surf_dr.F, update_r_star.F) instead of being frozen; momViscosity is off and pkg/shap_filt with nShapUV=4 and nShapUVPhys=4 is again the only momentum dissipation, cg2d converges on cg2dTargetResWunit=8.E-16, the grid comes from the packed grid_cs32.face00N.bin files in the deck, and saltStepping is off; restarted from the deck's own spun-up pickup at iteration 276480 (startTime=124416000., four years in) and run the deck's own 16 steps of 450 s (2 h of model time), the upstream short-test window, kept at that length because a spun-up Held-Suarez state is fully chaotic and only a window of hours stays pointwise.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 16 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=6.54836e-11 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=8.73115e-11
