# 写手简报 — athena-sr

模块:Special-relativistic hydrodynamics and MHD

**可变异的源文件(10 个,模块只编译这些)**
  src/hydro/rsolvers/hydro/hllc_rel.cpp
  src/hydro/rsolvers/hydro/hlle_rel.cpp
  src/hydro/rsolvers/hydro/llf_rel.cpp
  src/hydro/rsolvers/mhd/hlld_rel.cpp
  src/hydro/rsolvers/mhd/hlle_mhd_rel.cpp
  src/hydro/rsolvers/mhd/llf_mhd_rel.cpp
  src/eos/adiabatic_hydro_sr.cpp
  src/eos/adiabatic_mhd_sr.cpp
  src/pgen/gr_shock_tube.cpp
  src/pgen/gr_linear_wave.cpp

**死代码 / 不可达(1 条,永远不要在这里出题)**
  - GR (curved metric, frame transforms) -> athena-general-relativity

**坑(1 条)**
  ! Conserved-to-primitive inversion is iterative; tolerance floor must be measured, not assumed

## sr-hydro-hllc-mb1

- 容差 atol=1e-08 —— 症状小于容差 = marginal,漏斗必杀

## sr-hydro-hllc-wave0-r64

- 容差 atol=1e-09 —— 症状小于容差 = marginal,漏斗必杀

## sr-hydro-hlle-mb2

- 容差 atol=1e-08 —— 症状小于容差 = marginal,漏斗必杀

## sr-hydro-llf-mb4

- 容差 atol=1e-08 —— 症状小于容差 = marginal,漏斗必杀

## sr-mhd-hlld-mub2

- 容差 atol=1e-08 —— 症状小于容差 = marginal,漏斗必杀

## sr-mhd-hlld-wave2-r16-3d

- 容差 atol=1e-11 —— 症状小于容差 = marginal,漏斗必杀

## sr-mhd-hlle-mub4

- 容差 atol=1e-09 —— 症状小于容差 = marginal,漏斗必杀

## sr-mhd-llf-mub1

- 容差 atol=1e-09 —— 症状小于容差 = marginal,漏斗必杀
