# 写手简报 — nest-noble-element-microphysics

模块:Noble-element yield and detector-response microphysics

**可变异的源文件(2 个,模块只编译这些)**
  src
  include

**死代码 / 不可达(4 条,永远不要在这里出题)**
  - G4integration is an optional Geant4 adapter and is excluded from the first core-microphysics task.
  - GarfieldppIntegration is an optional gas-table integration utility and is excluded from the first core-microphysics task.
  - ROOT-only analysis tools are optional downstream consumers rather than the core calculation.
  - Examples and utilities remain vendored as official drivers and test sources but are not implementation paths owned by the module.

**坑(5 条)**
  ! The repository has standard examples but no tests directory or registered CTest suite; suitable checks must be derived and justified from those official examples.
  ! Event and fluctuation calculations are stochastic; correct implementations may consume random numbers or order events differently, so event-slot pointwise grading would be invalid.
  ! Default LAr benchmark grids emit 1.4 million CSV rows (114--177 MB), so later checks need scientifically justified windows while keeping runtime/output controls visible.
  ! CMake fetches pinned gcem source at configure time, and gcem needs a compatibility policy with CMake 4.
  ! Optional Geant4, ROOT, and Garfield++ integrations add substantial external build dependencies and were not exercised in the native investigation.

## barenest-single-event

- 官方测试源:`code/nest/examples/bareNEST.cpp`
- 活配置(决定哪些分支被编译/执行):The upstream minimal single-event API path repeated for 128 consecutive fixed seeds and reduced to ensemble summaries
- 判分观测量(缺陷必须动到它):ensemble means of photons, electrons, corrected S1, and corrected S2 from the minimal NESTcalc API
- 参考耗时 80s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## execnest-detector-response

- 官方测试源:`code/nest/src/execNEST.cpp`
- 活配置(决定哪些分支被编译/执行):2,000 monoenergetic 10 keV ER events at 200 V/cm and fixed position (0,0,0) mm, summarized over accepted event rows
- 判分观测量(缺陷必须动到它):ensemble means of photons, electrons, corrected S1, and corrected S2 detector response
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## lar-fluctuations

- 官方测试源:`code/nest/examples/LArNEST/LArNESTFluctuationBenchmarks.cpp`
- 活配置(决定哪些分支被编译/执行):All upstream NR, ER, and alpha field families on a 512-point energy grid, with 100 random samples per point
- 判分观测量(缺陷必须动到它):global means of LAr total, charge, and light yields and their sampled standard deviations
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## lar-mean-yields

- 官方测试源:`code/nest/examples/LArNEST/LArNESTMeanYieldsBenchmarks.cpp`
- 活配置(决定哪些分支被编译/执行):Every upstream NR, ER, and alpha electric-field family on a 512-point 0.1--1000 keV energy grid
- 判分观测量(缺陷必须动到它):seven LAr yield and quanta columns aligned by interaction and stable physical-grid rank
- 容差 atol=1e-06;噪声地板=0.7 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=0

## lar-neutron-capture

- 官方测试源:`code/nest/examples/LArNEST/LArNESTNeutronCapture.cpp`
- 活配置(决定哪些分支被编译/执行):All 38 official capture energies crossed with all 11 upstream electric fields at liquid-argon density
- 判分观测量(缺陷必须动到它):seven capture-cascade yield and quanta columns aligned by stable physical-grid rank
- 容差 atol=1e-06;噪声地板=4 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=0

## legacy-larnest-yields

- 官方测试源:`code/nest/examples/LArNEST/LegacyLArNESTBenchmarks.cpp`
- 活配置(决定哪些分支被编译/执行):Electron PDG 11 legacy calculation over all eight official fields and a 512-point 0.1--1000 keV grid, averaging 64 stochastic calculations per point
- 判分观测量(缺陷必须动到它):ensemble means of seven legacy LAr yield and quanta columns over the physical grid
- 参考耗时 6s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
