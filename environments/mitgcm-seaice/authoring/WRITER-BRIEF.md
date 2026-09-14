# 写手简报 — mitgcm-seaice

模块:Sea ice: viscous-plastic dynamics and multi-category thermodynamics

**可变异的源文件(3 个,模块只编译这些)**
  pkg/seaice
  pkg/thsice
  pkg/salt_plume

**死代码 / 不可达(3 条,永远不要在这里出题)**
  - pkg/exf and pkg/cal (forcing and calendar) are shared infrastructure the checks depend on but the module does not own
  - Ocean dynamics under the ice (model/src, cg2d) belong to mitgcm-ocean-dynamics; lab_sea checks grade the ice fields
  - Adjoint decks (input_ad*, input_tap*) need TAF/Tapenade and are out of scope

**坑(3 条)**
  ! One build per deck: each check compiles its own mitgcmuv (one to three minutes) from the candidate tree
  ! lab_sea writes 32-bit output by default (writeBinaryPrec=32); checks set 64
  ! Keep nPx=nPy=1: MPI ranks change the cg2d global-sum order at round-off level

## cs32-icedyn

- 官方测试源:`code/mitgcm/verification/global_ocean.cs32x15/input.icedyn`
- 活配置(决定哪些分支被编译/执行):verification/global_ocean.cs32x15/input.icedyn: the same global cubed sphere (32x32x6 with 15 levels, 12 tiles of 32x16, exch2, vector-invariant momentum, rStar non-linear free surface, GM/Redi, CORE-style exf forcing from the core_*_cs32.bin files) but with the two ice packages split between the two jobs they can each do: pkg/seaice supplies only the viscous-plastic dynamics (its data.seaice sets nothing but LSR_ERROR=1e-12, so every other parameter, the ice strength included, is at its package default) while pkg/thsice supplies the thermodynamics (three-layer Winton ice with snow, thSIceAdvScheme=77, stressReduction=0, its own albedo constants and iceMaskMin=0.05 in data.ice); restarted from this deck's own pickups at iteration 36000 (ocean, sea-ice and thsice) and run 3 steps with a 1200 s momentum step and a one-day tracer and clock step, against the deck's 10. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 3 steps (UICE and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=2.44472e-09 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=3.84171e-09

## lab-sea-salt-plume

- 官方测试源:`code/mitgcm/verification/lab_sea/input.salt_plume`
- 活配置(决定哪些分支被编译/执行):verification/lab_sea/input.salt_plume: 20x16x23 Labrador Sea (2 degree spherical grid, 4 tiles of 10x8), full ocean dynamics with KPP and GM/Redi, exf forcing, pkg/seaice with the LSR solver at LSR_ERROR=1e-12, 7-category thermodynamics, two sea-ice tracers (ridge and salinity) and pkg/salt_plume distributing brine rejection over depth; started from the deck's pickup at iteration 1 and run 48 steps of 3600 s (two days) instead of the deck's 10. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 48 steps (UICE and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=1.25112e-10 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=3.15481e-11

## offline-jfnk

- 官方测试源:`code/mitgcm/verification/offline_exf_seaice/input.dyn_jfnk`
- 活配置(决定哪些分支被编译/执行):verification/offline_exf_seaice/input.dyn_jfnk: the same 80x42 channel with the JFNK solver (SEAICEuseJFNK, up to 200 Newton iterations at SEAICEnonLinTol=1e-9, 50 GMRES iterations each with 10 preconditioner sweeps, SEAICEetaZmethod=3), ocean temperature, salinity and momentum frozen, pkg/thsice thermodynamics; the deck's own 12 steps of 1800 s (six hours) are kept. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 12 steps (UICE and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-09;噪声地板=5.82077e-10 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 21s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=5.82077e-10

## offline-krylov-paralens

- 官方测试源:`code/mitgcm/verification/offline_exf_seaice/input.dyn_paralens`
- 活配置(决定哪些分支被编译/执行):verification/offline_exf_seaice/input.dyn_paralens: the same 80x42 channel with the Picard-Krylov solver (SEAICEuseKrylov, 2 outer iterations of 50 GMRES iterations with 10 preconditioner sweeps), the parabolic-lens yield curve with tensile strength (SEAICEusePL, SEAICE_tensilFac=0.05), no-slip lateral boundaries, ocean frozen, pkg/thsice thermodynamics; 48 steps of 1800 s (one day) instead of the deck's 12. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 48 steps (UICE and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=7.567e-10 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 6s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=9.31323e-10

## offline-lsr-flex

- 官方测试源:`code/mitgcm/verification/offline_exf_seaice/input.dyn_lsr`
- 活配置(决定哪些分支被编译/执行):verification/offline_exf_seaice/input.dyn_lsr: the same 80x42 channel (4 tiles of 40x21, one process) run as pure dynamics, with pkg/thsice switched off in the overlay's data.pkg and usePW79thermodynamics=.FALSE., so the only prognostic sea-ice variables are the velocities and the advected area, thickness and snow started from const100.bin/const+20.bin/const_00.bin; the solver is the LSR in its flexible form (SEAICEuseLSRflex=.TRUE., up to 20 non-linear iterations stopped on SEAICEnonLinTol=1e-10 rather than on a fixed count), advection scheme 41 for the ice fields, free-slip sides, ocean momentum, temperature and salinity frozen; 48 steps of 1800 s (one day) instead of the deck's 12. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 48 steps (UICE and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=1.29161e-13 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 7s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=1.35558e-13

## offline-seaice-thermo

- 官方测试源:`code/mitgcm/verification/offline_exf_seaice/input.thermo`
- 活配置(决定哪些分支被编译/执行):verification/offline_exf_seaice/input.thermo: the same 80x42 channel with SEAICEuseDYNAMICS=.FALSE., so the momentum solver never runs and the check is a pure test of the pkg/seaice thermodynamics: growth and melt of single-category zero-layer (Hibler) ice: SEAICE_ITD is undefined in the check's SEAICE_OPTIONS.h, so seaice_readparms.F sets SEAICE_multDim = 1, which is also what upstream's reference log for this deck records, the McPhee ocean-to-ice turbulent flux (SEAICE_mcPheePiston=8.7854425e-5), lead closing with HO=0.2, area loss formula 2, growth and melt by convergence, open-water melt, flooding, and the surface temperature solve; exf forcing from tair_4x.bin, qa70_4x.bin, dlw_250.bin, dsw_100.bin with a restoring SST from tocn.bin, the ice started from ice0_area.bin and ice0_heff.bin, advection scheme 77 with snow advection, ocean temperature stepped but not advected; the deck's own window of 120 steps of 3600 s (five days) is kept. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 120 steps (AREA and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=1.7053e-13 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=0

## offline-thsice-column

- 官方测试源:`code/mitgcm/verification/offline_exf_seaice/input.thsice`
- 活配置(决定哪些分支被编译/执行):verification/offline_exf_seaice/input.thsice: the same 80x42 channel with pkg/seaice switched off entirely (the overlay's data.pkg lists only exf, thsice and diagnostics), so the sea ice is the Winton three-layer thermodynamic model of pkg/thsice with no dynamics at all: two ice layers with enthalpies Qice1 and Qice2, a snow layer, a surface temperature solved implicitly, an albedo fixed at 0.6 (albIceMax = albIceMin = 0.6), penetrating shortwave, and the ocean mixed layer of the channel underneath; exf forcing from tair_4x.bin, qa70_4x.bin, dlw_250.bin and dsw_100.bin with SST restoring to tocn.bin, the ice fraction started from ice0_area.bin and the thickness from const+20.bin; the deck's own window of 120 steps of 3600 s (five days) is kept. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 120 steps (ice_fract and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=9.31323e-10 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=0

## seaice-itd-lipscomb07

- 官方测试源:`code/mitgcm/verification/seaice_itd/input.lipscomb07`
- 活配置(决定哪些分支被编译/执行):verification/seaice_itd/input.lipscomb07: the same 80x42 channel and 7-category thickness distribution as the primary ITD deck, but with the Lipscomb et al. (2007) ridging closure instead of Thorndike's: SEAICEpartFunc=1 selects the exponential participation function and SEAICEredistFunc=1 the exponential redistribution of ridged ice, with SEAICEsnowFracRidge=1 sending all the snow of the ridging categories into the ocean; usePW79thermodynamics=.FALSE., so growth and melt are off and the run is dynamics, ridging and advection only; LSR at LSR_ERROR=1e-12 with up to 1500 linear iterations, advection scheme 77 per category, ocean frozen; 48 steps of 1800 s (one day) instead of the deck's 12. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 48 steps (UICE and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=3.96128e-13 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 16s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=1.34204e-12

## seaice-itd-remap

- 官方测试源:`code/mitgcm/verification/seaice_itd/input`
- 活配置(决定哪些分支被编译/执行):verification/seaice_itd/input: the 80x42 channel with the multi-category ice thickness distribution (SEAICE_ITD, 7 categories, linear remapping between categories, Thorndike ridging with SEAICE_cf=2 setting the ice strength, useHibler79IceStrength off), LSR solver at LSR_ERROR=1e-12, multidimensional advection scheme 77 of every category, ocean frozen; 48 steps of 1800 s (one day) instead of the deck's 12. Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 48 steps (UICE and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=2.72928e-11 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 16s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=3.93641e-11

## seaice-obcs-evp

- 官方测试源:`code/mitgcm/verification/seaice_obcs/input.regDenom`
- 活配置(决定哪些分支被编译/执行):verification/seaice_obcs/input.regDenom: 10x8x23 cut of the Labrador Sea setup (2 degree spherical grid, 2 tiles of 5x8) with pkg/obcs prescribing ocean and sea-ice fields on all four boundaries every hour, full ocean dynamics with KPP, GM/Redi and salt plumes, exf forcing from the lab_sea files, and the adaptive elastic-viscous-plastic solver (SEAICEaEVPcoeff=0.5, SEAICEnEVPstarSteps=500, SEAICE_evpAreaReg=1e-5) with 7-category thermodynamics; started from the deck's pickup at iteration 1 and run 8 steps of 3600 s instead of the deck's 5 (the boundary files hold 12 hourly records, which caps the window at 9 hours). Graded: every <field>.<final iteration>.data written by the end-of-run state dump (the prognostic fields of write_state.F and of the packages in use), read with the shape and precision of the .meta sidecar; the initial-state dump and the log are not graded.
- 判分观测量(缺陷必须动到它):every graded field of the final state dump after 8 steps (UICE and the other prognostic and package fields written at the final iteration), all cells
- 容差 atol=1e-10;噪声地板=1.50416e-09 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=2.874e-10
