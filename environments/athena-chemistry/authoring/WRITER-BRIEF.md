# 写手简报 — athena-chemistry

模块:Chemistry networks with CVODE and six-ray radiation

**可变异的源文件(7 个,模块只编译这些)**
  src/chemistry/
  src/chem_rad/
  src/pgen/chem_G14Sod.cpp
  src/pgen/chem_H2.cpp
  src/pgen/chem_uniform.cpp
  src/pgen/chem_uniform_sixray.cpp
  src/pgen/read_vtk.cpp

**死代码 / 不可达(1 条,永远不要在这里出题)**
  - Cosmic-ray transport; see not_packaged

**坑(2 条)**
  ! Six of eight tests need SUNDIALS/CVODE (public package, version-sensitive API)
  ! read_vtk depends on tst/regression/data VTK fixtures

## g14sod-shock-1024

- 判分观测量(缺陷必须动到它):native history plus final shock/contact/rarefaction primitive and eight-species frame

## gow17-const-4

- 判分观测量(缺陷必须动到它):native history plus final twelve-species, temperature, and radiation-field equilibrium frame

## h2-cvode-gaussian-256

- 判分观测量(缺陷必须动到它):native history plus all eight final primitive/species MeshBlock frames after CVODE chemistry and Gaussian advection

## h2-cvode-gaussian-32

- 判分观测量(缺陷必须动到它):native history plus the final primitive/species frame after CVODE chemistry and Gaussian advection

## h2-euler-uniform-4

- 判分观测量(缺陷必须动到它):native history plus the final primitive/species frame after explicit H/H2 evolution

## kida-gow17-4

- 判分观测量(缺陷必须动到它):native history plus final eighteen-species KIDA-assembled equilibrium frame

## sixray-x1split-16x16x32

- 判分观测量(缺陷必须动到它):native history plus both final MeshBlock species/radiation frames after four six-ray sweeps and x1 column handoffs

## sixray-x3split-16x16x32

- 判分观测量(缺陷必须动到它):native history plus both final MeshBlock species/radiation frames after four six-ray sweeps and x3 column handoffs
