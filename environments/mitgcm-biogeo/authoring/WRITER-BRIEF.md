# 写手简报 — mitgcm-biogeo

模块:Passive tracers and ocean biogeochemistry

**可变异的源文件(7 个,模块只编译这些)**
  pkg/ptracers
  pkg/gchem
  pkg/dic
  pkg/bling
  pkg/cfc
  pkg/offline
  pkg/longstep

**死代码 / 不可达(1 条,永远不要在这里出题)**
  - gmredi and cd_code enabled in these decks belong to other modules

**坑(2 条)**
  ! Carbon chemistry uses iterative pH solves whose convergence depth sets the round-off floor
  ! offline decks read pre-computed flow fields from the repository (small binaries)

## cfc-offline

- 官方测试源:`code/mitgcm/verification/tutorial_cfc_offline/input`
- 活配置(决定哪些分支被编译/执行):verification/tutorial_cfc_offline/input: the same 2.8-degree global grid (128x64x15, four tiles of 64x32) with the dynamical core switched off entirely by useOffLine, so that momentum, the free surface and the equation of state are never integrated and pkg/offline instead reads monthly-mean velocity, vertical velocity, GM streamfunction components, potential temperature, salinity and a convective-mixing index from the deck's input_off/ files and interpolates them linearly in time; the two CFC tracers are then advected with the flux-limited scheme 77, mixed by the read-in GM tensor and by an implicit vertical diffusivity of 5e-5 m2/s, and forced at the surface by pkg/cfc exactly as in the online check; restarted from pickup_ptracers at iteration 4269600 and run 24 tracer steps of 43200 s (12 days) against the deck's 4. Because WRITE_STATE is skipped when useOffLine is set (model/src/do_the_model_io.F), the only files at the final iteration are PTRACER01 and PTRACER02, which makes this the one check in the module that grades the tracer transport and nothing else.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 24 steps (PTRACER01 and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-20;噪声地板=1.03398e-25 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=2.06795e-25

## cfc-online

- 官方测试源:`code/mitgcm/verification/cfc_example/input`
- 活配置(决定哪些分支被编译/执行):verification/cfc_example/input: the 2.8-degree global ocean (128x64x15, four tiles of 64x32, POLY3 equation of state, implicit free surface with exactConserv, CD-scheme momentum, ivdc_kappa=10, GM/Redi) restarted from the deck's pickup and pickup_cd at iteration 4269600 and its linked pickup_ptracers, carrying two CFC tracers with the flux-limited scheme 77 and a vertical tracer diffusivity of 5e-5 m2/s; pkg/gchem calls pkg/cfc each step, which interpolates the northern- and southern-hemisphere atmospheric CFC-11 and CFC-12 mixing ratios from the ASCII table cfc1112.atm in time and across the equatorial band (atmCFC_yNorthBnd/ySouthBnd) and applies the solubility and Schmidt-number gas exchange of cfc11_surfforcing.F and cfc12_surfforcing.F under prescribed wind speed and ice fraction; pkg/layers is on, so the deck also accumulates the temperature- and density-layer transports LaUH1TH, LaVH1TH, LaUH2RHO and LaVH2RHO, and its DIAGNOSTICS_LIST sets dumpAtLast=.TRUE. so that stream is written at the end of any run; 20 tracer steps of 43200 s, 10 days, against the deck's 4.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 20 steps (PTRACER01 and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-20;噪声地板=1.03398e-25 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 6s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=4.37496e-21

## global-bling

- 官方测试源:`code/mitgcm/verification/global_oce_biogeo_bling/input`
- 活配置(决定哪些分支被编译/执行):verification/global_oce_biogeo_bling/input: the same 2.8-degree global ocean as the DIC check (128x64x15, four tiles of 64x32, CD-scheme, Bryan-Lewis diffusivity, ivdc_kappa=100, GM/Redi) but started cold from eight three-dimensional initial files and carrying eight BLING tracers (DIC, alkalinity, O2, NO3, PO4, dissolved iron, DON, DOP) advected with the unlimited third-order direct-space-time scheme 30 and a horizontal tracer diffusivity of 1 m2/s; pkg/gchem calls pkg/bling once per step, which is the BLINGv2 path (USE_BLING_V1 undefined, so bling_bio_nitrogen.F rather than bling_bio.F, with BLING_NO_NEG, MIN_NUT_LIM and ML_MEAN_PHYTO on and the adjoint-safe branch selected), and BLING evaluates its carbonate system over the whole three-dimensional volume, not only the surface; run 30 tracer steps of 43200 s (15 days, the deck runs 4), a multiple of both diagnostics frequencies so the eight-tracer blingTracDiag average and the soundSpeedDiag stream complete on the final iteration.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 30 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=8.88178e-16 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 12s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=1.18007e-10

## global-dic

- 官方测试源:`code/mitgcm/verification/tutorial_global_oce_biogeo/input`
- 活配置(决定哪些分支被编译/执行):verification/tutorial_global_oce_biogeo/input: the 2.8-degree global ocean (128x64x15, four tiles of 64x32, spherical polar, JMD95Z equation of state, implicit free surface, CD-scheme momentum, Bryan-Lewis vertical diffusivity, ivdc_kappa=100 convective adjustment and GM/Redi) carrying five DIC-package passive tracers (DIC, alkalinity, PO4, DOP, O2) advected with the flux-limited scheme 77 and mixed by GM/Redi, with pkg/gchem calling pkg/dic once per step (nsubtime=1) for biological production, remineralisation, the calcium-carbonate rain flux and the air-sea CO2 and O2 fluxes driven by prescribed wind speed, sea-ice fraction and silica fields; restarted from the deck's pickup, pickup_cd and pickup_dic at iteration 5184000 and run 16 tracer steps of 43200 s (8 days, the deck runs 4), which is long enough for the surfDiag two-day averaging stream (frequency 172800 s) to land on the final iteration so the DIC surface fluxes, pCO2 and mean pH are graded alongside the state.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 16 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=2.22045e-16 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 4s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=7.93079e-10

## ptracer-advection-gyre

- 官方测试源:`code/mitgcm/verification/tutorial_advection_in_gyre/input`
- 活配置(决定哪些分支被编译/执行):verification/tutorial_advection_in_gyre/input: a single-layer 60x60 Cartesian box at 20 km resolution (four tiles of 30x30, 5000 m deep, beta plane, linear equation of state with sBeta=0 and a uniform 20 C temperature so the flow is purely wind-driven and barotropic, no-slip sides and bottom, implicit free surface, readBinaryPrec=64 and useSingleCPUio) restarted from the deck's pickup at iteration 259200, that is after a ten-year spin-up, and carrying a single dye tracer initialised from dye.bin as a delta in one cell near the western boundary; the tracer is advected with pkg/ptracers scheme 80, the unlimited Prather second-order-moment scheme, which is the only place in the module where PTRACERS_ALLOW_DYN_STATE and the moment state of gad_som_advect.F are exercised, and has exactly zero horizontal, biharmonic and vertical diffusivity so the check is a pure advection test; run 120 steps of 1200 s (40 hours) against the deck's 4. No gchem, dic, bling or cfc: this is pkg/ptracers on its own.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 120 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=1.02141e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=0

## so-box-calcite-keir

- 官方测试源:`code/mitgcm/verification/so_box_biogeo/input.caSat0`
- 活配置(决定哪些分支被编译/执行):verification/so_box_biogeo/input: a 42x20x15 Southern Ocean box cut out of the global 2.8-degree grid (six tiles of 14x10, nSx=3 nSy=2, JMD95Z equation of state, implicit free surface with exactConserv, viscAh=3e5, Bryan-Lewis vertical diffusivity, ivdc_kappa=10 convective adjustment, GM/Redi in advective form with GM_background_K=1e3 and the gkw91 taper, and asynchronous time stepping with deltaTMom=900 s under a deltaTClock and deltaTtracer of 43200 s) started cold from the deck's T, S, eta and velocity initial files and five DIC tracer initial files, with pkg/obcs prescribing western, eastern and northern boundary values for temperature, salinity, both velocity components and all five tracers from the monthly Ob* files plus the connect masks, and first-order upwind advection at the boundaries (OBCS_u1_adv_T/S/Tr) with the input.caSat0 overlay, which replaces data.dic (and the statistics-stream field list of data.diagnostics) so that pkg/dic switches on the calcite-saturation path: useCalciteSaturation=.TRUE. with calcOmegaCalciteFreq left at its default, which is deltaTClock, so CALCITE_SATURATION is called every single step and rebuilds the carbonate ion concentration and the calcite saturation state omegaC over all fifteen levels of every wet column, using DIC_COEFFS_SURF followed by the pressure correction of DIC_COEFFS_DEEP and then the Follows solver CALC_PCO2_APPROX (selectPHsolver is left at 0), and selectCalciteDissolution=2, the Keir (1980) dissolution law, so that the sinking calcium-carbonate rain is dissolved by CAR_FLUX_OMEGA_TOP only in cells where omegaC < 1 instead of by the depth power law of CAR_FLUX; the overlay also adds DIC_deepSilicaFile='silicate_3D_12m_box.bin', the twelve-month three-dimensional silica field that the deep carbonate chemistry needs and that no other check in the module reads; run 60 tracer steps of 43200 s (30 days, the deck runs 10) so that both the 10-step dynDiag and the 60-step surfDiag averaging streams complete exactly at the final iteration.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 60 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=4.44089e-16 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=2.44264e-09

## so-box-calcite-naviaux

- 官方测试源:`code/mitgcm/verification/so_box_biogeo/input.caSat3`
- 活配置(决定哪些分支被编译/执行):verification/so_box_biogeo/input: a 42x20x15 Southern Ocean box cut out of the global 2.8-degree grid (six tiles of 14x10, nSx=3 nSy=2, JMD95Z equation of state, implicit free surface with exactConserv, viscAh=3e5, Bryan-Lewis vertical diffusivity, ivdc_kappa=10 convective adjustment, GM/Redi in advective form with GM_background_K=1e3 and the gkw91 taper, and asynchronous time stepping with deltaTMom=900 s under a deltaTClock and deltaTtracer of 43200 s) started cold from the deck's T, S, eta and velocity initial files and five DIC tracer initial files, with pkg/obcs prescribing western, eastern and northern boundary values for temperature, salinity, both velocity components and all five tracers from the monthly Ob* files plus the connect masks, and first-order upwind advection at the boundaries (OBCS_u1_adv_T/S/Tr) with the input.caSat3 overlay, which replaces data.dic (and the statistics-stream field list of data.diagnostics) with the most fully switched-on DIC configuration in the whole module: useCalciteSaturation=.TRUE. with calcOmegaCalciteFreq at its default of deltaTClock, so CALCITE_SATURATION runs over all fifteen levels every step; selectPHsolver=3, the Munhoven (2013) SolveSAPHE FAST solver, which is a different root-finding routine from the GENERAL solver of the input.saphe check and is exercised nowhere else, and which here is called through CALC_PCO2_SOLVESAPHE for every wet cell of the three-dimensional volume rather than only at the surface; the alternative constants selectBTconst=1, selectFTconst=1, selectHFconst=1 and selectK1K2const=6; and selectCalciteDissolution=3, the Naviaux et al. (2019) two-regime dissolution law with its own rate constants and exponents; the overlay also adds DIC_deepSilicaFile='silicate_3D_12m_box.bin'; run 60 tracer steps of 43200 s (30 days, the deck runs 10) so that both the 10-step dynDiag and the 60-step surfDiag averaging streams complete exactly at the final iteration.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 60 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=1.77636e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=2.44264e-09

## so-box-dic

- 官方测试源:`code/mitgcm/verification/so_box_biogeo/input`
- 活配置(决定哪些分支被编译/执行):verification/so_box_biogeo/input: a 42x20x15 Southern Ocean box cut out of the global 2.8-degree grid (six tiles of 14x10, nSx=3 nSy=2, JMD95Z equation of state, implicit free surface with exactConserv, viscAh=3e5, Bryan-Lewis vertical diffusivity, ivdc_kappa=10 convective adjustment, GM/Redi in advective form with GM_background_K=1e3 and the gkw91 taper, and asynchronous time stepping with deltaTMom=900 s under a deltaTClock and deltaTtracer of 43200 s) started cold from the deck's T, S, eta and velocity initial files and five DIC tracer initial files, with pkg/obcs prescribing western, eastern and northern boundary values for temperature, salinity, both velocity components and all five tracers from the monthly Ob* files plus the connect masks, and first-order upwind advection at the boundaries (OBCS_u1_adv_T/S/Tr); pkg/gchem calls pkg/dic once per step (nsubtime=1) for light- and phosphate-limited production, Martin remineralisation, the calcium-carbonate rain flux and the air-sea CO2 and O2 fluxes driven by the prescribed wind speed, sea-ice fraction and surface silica of the box. This is the base deck of the experiment, and its carbonate chemistry is the combination that no other check in the module has: the experiment's code/DIC_OPTIONS.h defines CARBONCHEM_SOLVESAPHE and CARBONCHEM_TOTALPHSCALE, so the dissociation coefficients come from DIC_COEFFS_SURF on the total pH scale, while data.dic leaves selectPHsolver at its default 0, so the pH itself is obtained from the Follows et al. (2006) fixed-point approximation in CALC_PCO2_APPROX and selectBTconst, selectFTconst, selectHFconst and selectK1K2const all take their default value 1 rather than the alternative constants the input.saphe overlay selects; run 60 tracer steps of 43200 s (30 days, the deck runs 10) so that both the 10-step dynDiag and the 60-step surfDiag averaging streams complete exactly at the final iteration.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 60 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=4.44089e-16 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=2.44264e-09

## so-box-obcs-saphe

- 官方测试源:`code/mitgcm/verification/so_box_biogeo/input.saphe`
- 活配置(决定哪些分支被编译/执行):verification/so_box_biogeo/input with the input.saphe overlay: a 42x20x15 Southern Ocean box cut out of the global 2.8-degree grid (six tiles of 14x10, exactly conserving free surface, ivdc_kappa=10, GM/Redi) started cold from the deck's T, S, eta, velocity and five tracer initial files, with pkg/obcs prescribing western, eastern and northern boundary values for temperature, salinity, both velocity components and all five DIC tracers from monthly files plus connect masks, and first-order upwind advection at the boundaries (OBCS_u1_adv_Tr); the overlay replaces data.dic so that pkg/dic runs with the Munhoven (2013) SolveSAPHE GENERAL total-alkalinity solver (selectPHsolver=1) and the alternative borate, fluoride, HF and K1/K2 constants (selectBTconst=1, selectFTconst=1, selectHFconst=1, selectK1K2const=6) that the experiment's DIC_OPTIONS.h enables with CARBONCHEM_SOLVESAPHE and CARBONCHEM_TOTALPHSCALE; run 60 tracer steps of 43200 s (30 days, the deck runs 10) so that both the 10-step dynDiag and the 60-step surfDiag averaging streams complete exactly at the final iteration.. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 60 steps (T and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=4.44089e-16 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=2.44264e-09
