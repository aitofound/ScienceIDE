# 写手简报 — athena-gr

模块:General-relativistic hydrodynamics and MHD on fixed metrics

**可变异的源文件(13 个,模块只编译这些)**
  src/hydro/rsolvers/hydro/hlle_rel_no_transform.cpp
  src/hydro/rsolvers/hydro/llf_rel_no_transform.cpp
  src/hydro/rsolvers/mhd/hlle_mhd_rel_no_transform.cpp
  src/hydro/rsolvers/mhd/llf_mhd_rel_no_transform.cpp
  src/eos/adiabatic_hydro_gr.cpp
  src/eos/adiabatic_mhd_gr.cpp
  src/coordinates/minkowski.cpp
  src/coordinates/schwarzschild.cpp
  src/coordinates/kerr-schild.cpp
  src/coordinates/gr_user.cpp
  src/pgen/gr_shock_tube.cpp
  src/pgen/gr_bondi.cpp
  src/pgen/gr_torus.cpp

**死代码 / 不可达(1 条,永远不要在这里出题)**
  - The three compile-only tests are build checks, not fidelity checks; survey will mark them unsuitable

**坑(1 条)**
  ! Runtime tests all use Minkowski coordinates; curved-metric physics is only compile-covered upstream

## gr-hydro-shocks-hllc

- 容差 atol=1e-08 —— 症状小于容差 = marginal,漏斗必杀

## gr-hydro-shocks-hlle

- 容差 atol=1e-08 —— 症状小于容差 = marginal,漏斗必杀

## gr-hydro-shocks-hlle-notransform

- 容差 atol=1e-08 —— 症状小于容差 = marginal,漏斗必杀

## gr-hydro-shocks-llf

- 容差 atol=1e-08 —— 症状小于容差 = marginal,漏斗必杀

## gr-hydro-shocks-llf-notransform

- 容差 atol=1e-08 —— 症状小于容差 = marginal,漏斗必杀

## gr-mhd-shocks-hlld

- 容差 atol=1e-09 —— 症状小于容差 = marginal,漏斗必杀

## gr-mhd-shocks-hlle

- 容差 atol=1e-09 —— 症状小于容差 = marginal,漏斗必杀

## gr-mhd-shocks-llf

- 容差 atol=1e-09 —— 症状小于容差 = marginal,漏斗必杀
