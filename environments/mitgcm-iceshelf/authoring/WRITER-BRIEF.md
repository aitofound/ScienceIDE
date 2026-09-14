# 写手简报 — mitgcm-iceshelf

模块:Ice shelf cavities and ice-stream dynamics

**可变异的源文件(4 个,模块只编译这些)**
  pkg/shelfice
  pkg/streamice
  pkg/icefront
  pkg/steep_icecavity

**死代码 / 不可达(1 条,永远不要在这里出题)**
  - shelfice_2d_remesh exercises dynamic remeshing with obcs; if too fragile it is left as an untested entry point

**坑(2 条)**
  ! streamice has a nonlinear solver with iteration-count sensitivity; the floor must be measured
  ! Only three decks: THIN unless isomip variants are used as separate checks

## isomip-icefront

- 官方测试源:`code/mitgcm/verification/isomip/input.icefront`
- 活配置(决定哪些分支被编译/执行):verification/isomip/input.icefront laid over input: the same 50x100x30 ISOMIP cavity from rest, but with pkg/icefront switched on next to pkg/shelfice and the shelfice thermodynamics moved off the ISOMIP branch (useISOMIPTD=.FALSE., SHELFICEconserve=.TRUE., SHELFICEboundaryLayer=.TRUE., no gamma friction, so the transfer coefficients are the constant SHELFICEheatTransCoeff and its salt companion and the melt comes from the three-equation quadratic); the ice front is described by frontdepth.xuyun and frontcircum.xuyun, which give a depth and a wetted circumference to every column so that a vertical melting face is distributed over the water column, and applyIcefrontTendT and applyIcefrontTendS put the resulting heat and fresh-water tendencies into theta and salt at every level the face touches; graded window 60 steps of 1800 s, three times the deck's 20. Both diagnostics streams (shelficeDiag with SHIfwFlx and SHIhtFlx, icefrontDiag with ICFfwFlx and ICFhtFlx) are retimed to the run length so that the two packages' melt rates are graded side by side.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 60 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=7.99361e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 9s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=5.77316e-14

## isomip-shelfice-gammafrict

- 官方测试源:`code/mitgcm/verification/isomip/input.htd`
- 活配置(决定哪些分支被编译/执行):verification/isomip/input.htd laid over input: the same 50x100x30 ISOMIP cavity but restarted from the deck's pickup at iteration 8640 (six months of spin-up, so the cavity circulation is developed and the water column is no longer degenerate) and switched to the Holland and Jenkins three-equation formulation, SHELFICEuseGammaFrict=.TRUE. with SHI_ALLOW_GAMMAFRICT compiled in, SHELFICEselectDragQuadr=1, SHELFICEadvDiffHeatFlux=.TRUE., SHELFICEconserve=.TRUE. and a prescribed ice mass from iceShelf_Mass.bin instead of a load-anomaly file, together with the non-linear free surface (nonlinFreeSurf=4, hFacInf=0.02, hFacSup=2.0), implicit vertical viscosity and diffusion with ivdc_kappa=1, thin-top-cell mixing (pCellMix_select=20 with pCellMix_viscAr=4e-4 and pCellMix_diffKr=2e-4), Jamart wet points and viscAh=1000; graded window 60 steps of 1800 s from iteration 8640 to 8700, three times the deck's 20 steps. The two active diagnostics streams (surfDiag with the friction velocity, the two transfer coefficients, the melt and heat fluxes, the shelfice forcing terms and the top stresses; dynDiag with the velocities, hydrostatic pressure, theta and salt) are retimed to the run length so they land at the final iteration.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 60 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=6.57252e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 11s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=6.57252e-14

## isomip-shelfice-isomiptd

- 官方测试源:`code/mitgcm/verification/isomip/input`
- 活配置(决定哪些分支被编译/执行):verification/isomip/input: the ISOMIP ice-shelf cavity on a 50x100x30 spherical-polar grid (0.3 deg x 0.1 deg, 30 levels of 30 m, eight 25x25 tiles, one process) started from rest and a uniform Tref=-1.9 C / Sref=34.4 water column under the exp1 ice draft, hydrostatic with the implicit free surface, JMD95Z equation of state, the C-D scheme for momentum (useCDScheme with tauCD=400000 s), convective adjustment every step (cAdjFreq=-1), Laplacian viscosity and diffusivity (viscAh=600, diffKhT=diffKhS=100, viscAz=1e-3, diffKz=5e-5), quadratic bottom drag, and pkg/shelfice in its ISOMIP mode (useISOMIPTD=.TRUE., SHELFICEboundaryLayer=.TRUE., SHELFICEuseGammaFrict=.FALSE., a prescribed load anomaly phi0surf.exp1.jmd95z and topography icetopo.exp1); the graded window is 60 steps of 1800 s (30 hours, three times the deck's 20 steps), long enough for the melt-driven boundary plume to organise along the ice base and short enough that the comparison stays pointwise. SHELFICE_dumpFreq is set to the time step so that the package's own shelfIceFreshWaterFlux and shelfIceHeatFlux fields land at the final iteration next to the state dump, because this deck runs without pkg/diagnostics.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 60 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=3.97904e-13 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 8s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=9.37916e-13

## isomip-shelfice-obcs

- 官方测试源:`code/mitgcm/verification/isomip/input.obcs`
- 活配置(决定哪些分支被编译/执行):verification/isomip/input.obcs laid over input: the same 50x100x30 spherical-polar ISOMIP cavity (0.3 deg x 0.1 deg, 30 levels of 30 m, eight 25x25 tiles, one process, bathy.box from input/) but with its own data file and a completely different numerical configuration from the other four isomip checks, namely a stratified initial column (Tref=-1.9 C everywhere, Sref rising from 34.4 to 35.27 over the lower twenty levels so that N^2=1e-5 s^-2), implicitDiffusion and implicitViscosity with no convective adjustment at all, the GGL90 turbulent-kinetic-energy closure (mxlMaxFlag=2, GGL90TKEsurfMin=1e-5 so that the ice-shelf bottom stress is felt in the TKE budget), the non-linear free surface in rStar form (nonlinFreeSurf=4, select_rStar=2, hFacInf=0.02, hFacSup=2.0, exactConserv) driven by a real fresh-water flux (useRealFreshWaterFlux), a prescribed open northern boundary (OB_Jnorth=50*-1 with useOBCSprescribe and no OB files, so T and S on the boundary fall back to tRef and sRef and the normal velocity to zero) whose volume and surface-flux imbalance is removed every step by useOBCSbalance with OBCSbalanceSurf and OBCS_balanceFacN=1, and pkg/shelfice in its full three-equation mode with velocity-dependent transfer coefficients (SHELFICEuseGammaFrict, SHELFICEconserve, SHELFICEboundaryLayer, SHELFICEadvDiffHeatFlux, SHELFICEselectDragQuadr=1) driving an ice shelf whose mass is stepped forward every time step from the prescribed tendency file iceShelf_MassTend.obcs (SHELFICEMassStepping with SHELFICEMassDynTendFile) over the truncated draft icetopo.obcs and the truncated load iceShelf_Mass.obcs; the graded window is 12 steps of 1800 s (21600 s, six hours, the deck's own 12 steps), which matches the window of the other four isomip checks and is long enough for the initial free-surface adjustment to the imperfectly balanced ice load to propagate to the open boundary and back while staying far inside the laminar, pointwise-reproducible regime (the deck's own monitor shows advcfl_uvel_max below 6e-4).. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 12 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=3.32778e-12 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=4.06963e-12

## isomip-steep-icecavity

- 官方测试源:`code/mitgcm/verification/isomip/input.stic`
- 活配置(决定哪些分支被编译/执行):verification/isomip/input.stic laid over input: the 50x100x30 ISOMIP cavity from rest with pkg/steep_icecavity switched on alongside pkg/shelfice (useSTIC=.TRUE., STICdepthFile=icetopo.exp1), which replaces shelfice_thermodynamics by stic_thermodynamics and lets the melt of a steeply sloping ice base be computed against the water actually adjacent to the face rather than against the single top cell, using three-dimensional transfer coefficients (ALLOW_SHITRANSCOEFF_3D is on by default in pkg/steep_icecavity/STIC_OPTIONS.h) and solving the flux balance in stic_solve4fluxes.F; the shelfice side runs the three-equation formulation with constant transfer coefficients (no gamma friction), SHELFICEconserve=.TRUE., SHELFICEadvDiffHeatFlux=.TRUE. and SHELFICEkappa deliberately set to zero, and the deck inherits input/data, so 1800 s steps, the C-D scheme and convective adjustment every step; graded window 60 steps of 1800 s, three times the deck's 20. The three active diagnostics streams are retimed to the run length: dynDiag for the ocean state, sticDiag3D for the three-dimensional transfer coefficients and the steep-cavity fluxes and forcing terms, sticDiag2D for the vertical-face contributions.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 60 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=9.23706e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 13s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=2.0961e-13

## shelfice-remesh

- 官方测试源:`code/mitgcm/verification/shelfice_2d_remesh/input`
- 活配置(决定哪些分支被编译/执行):verification/shelfice_2d_remesh/input: a 1x200x90 meridional slice of a southern-ocean shelf (spherical-polar, 0.0078125 deg in latitude, 90 uniform 10 m levels, four 1x50 tiles, one process) with a flat 900 m bottom, an open northern boundary prescribing v, theta and salt with a linear sponge, and a trapezoidal ice shelf whose mass evolves under SHELFICEMassStepping driven both by its own melt and by a deliberately unrealistic prescribed tendency shelfice_dMdt.r02.bin of +/-0.0286 kg/m2/s, so that the top grid cell crosses the merge threshold of 0.10 and the split threshold of 1.12 several times in a short run; ALLOW_SHELFICE_REMESHING is compiled in from the experiment's own SHELFICE_OPTIONS.h, remeshing is attempted every SHELFICEremeshFrequency=600 s (every two steps), the melt uses the three-equation formulation with gamma friction (SHELFICEuseGammaFrict=.TRUE., SHELFICEselectDragQuadr=2, shiCdrag=SHELFICEDragQuadratic=0.0015) and no boundary layer, the free surface is non-linear with real fresh-water flux, vertical viscosity and diffusivity are implicit and enhanced under thin top cells (pCellMix_select=20), convection is by ivdc_kappa=1, and momentum uses the vector-invariant form with 77-scheme advection of theta and salt; the run restarts from the deck's pickup and pickup_shelfice at iteration 2898 and the graded window is 80 steps of 300 s (6.7 hours, four times the deck's 20 steps), which should produce of the order of sixteen remeshing events instead of four.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 80 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=6.13352e-10 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 9s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=4.63953e-10

## streamice-halfpipe

- 官方测试源:`code/mitgcm/verification/halfpipe_streamice/input`
- 活配置(决定哪些分支被编译/执行):verification/halfpipe_streamice/input: an 80 km by 40 km Cartesian half-pipe ice stream on a 40x20 single-level grid (two 20x20 tiles, one process) with the ocean stepping switched off entirely (momStepping, tempStepping and saltStepping all false, Nr=1) so that the run is pure pkg/streamice; the shelf profile is built analytically from STREAMICEthickInit='PARAM' with shelf_max_draft=1300 m, shelf_min_draft=300 m, shelf_edge_pos=70 km and shelf_slope_scale=62 km, a uniform Glen coefficient B_glen_isothermal=700 and a uniform basal friction C_basal_fric_const=5 with n_glen=3 and n_basal_friction=1, a prescribed influx of 1.5e6 on the western face, a calving-front boundary condition on the eastern face, no-flow walls north and south, and STREAMICE_move_front=.TRUE. so the partially filled front cells evolve; the compile-time configuration in code/STREAMICE_OPTIONS.h selects the constructed matrix (STREAMICE_CONSTRUCT_MATRIX), the hybrid stress balance (STREAMICE_HYBRID_STRESS), the smoothed floatation taper (STREAMICE_SMOOTH_FLOATATION) and USE_ALT_RLOW, with PETSC undefined; every time step is 6307200 s (73 days) and the graded window is 20 steps, four years of ice-stream evolution and twice the deck's 10 steps.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 20 steps (land_ice and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=2.51266e-08 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 9s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=0
