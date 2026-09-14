# 写手简报 — dscribe-descriptors

模块:Combined atomistic descriptors and derivatives

**可变异的源文件(21 个,模块只编译这些)**
  dscribe/descriptors/soap.py
  dscribe/ext/soap.cpp
  dscribe/ext/soap.h
  dscribe/ext/soapGTO.cpp
  dscribe/ext/soapGTO.h
  dscribe/ext/soapGeneral.cpp
  dscribe/ext/soapGeneral.h
  dscribe/descriptors/mbtr.py
  dscribe/descriptors/lmbtr.py
  dscribe/descriptors/valleoganov.py
  dscribe/ext/mbtr.cpp
  dscribe/ext/mbtr.h
  dscribe/descriptors/acsf.py
  dscribe/ext/acsf.cpp
  dscribe/ext/acsf.h
  dscribe/descriptors/descriptormatrix.py
  dscribe/descriptors/coulombmatrix.py
  dscribe/descriptors/sinematrix.py
  dscribe/descriptors/ewaldsummatrix.py
  dscribe/ext/coulombmatrix.cpp
  dscribe/ext/coulombmatrix.h

**死代码 / 不可达(2 条,永远不要在这里出题)**
  - dscribe.kernels similarity aggregation, whose sparse official coverage and downstream aggregation role do not justify a second environment
  - documentation, plotting, and machine-learning training examples, which are downstream demonstrations rather than owned numerical kernels

**坑(5 条)**
  ! Feature indices are physical only for a fixed descriptor configuration; sparse storage order is not.
  ! Periodic image enumeration and large reductions may change floating-point summation order across targets.
  ! Random matrix permutation must be graded statistically or with controlled seeds, never by raw draw order.
  ! Eigenspectra compare ordered eigenvalues, not eigenvector signs or phases.
  ! Analytical and numerical derivatives have different attainable numerical floors.

## acsf-analytic-features

- 官方测试源:`code/dscribe/tests/test_acsf.py`
- 活配置(决定哪些分支被编译/执行):Float64 ACSF observable, fixed deterministic structures and parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):G1 through G5 ACSF arrays together with the distances and cutoff values that define their analytical formulas.
- 容差 atol=1e-08;噪声地板=6.10623e-16 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## acsf-angular-cutoff

- 官方测试源:`code/dscribe/tests/test_acsf.py`
- 活配置(决定哪些分支被编译/执行):Float64 ACSF observable, fixed deterministic structures and parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):G1, G4 and G5 values at the neighbour-neighbour cutoff boundary and their analytical expectations.
- 容差 atol=1e-08;噪声地板=6.66134e-16 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## acsf-environment-basis

- 官方测试源:`code/dscribe/tests/test_acsf.py`
- 活配置(决定哪些分支被编译/执行):Float64 ACSF observable, fixed deterministic structures and parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Center-averaged ACSF vectors and normalized environment-overlap values across species environments and a supercell.
- 容差 atol=1e-08;噪声地板=8.88178e-16 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## acsf-numerical-derivatives

- 官方测试源:`code/dscribe/tests/test_acsf.py`
- 活配置(决定哪些分支被编译/执行):Float64 ACSF observable, fixed deterministic structures and parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Finite-difference ACSF derivative tensor and paired center features for an acetyl-fluoride geometry.
- 容差 atol=1e-06;噪声地板=2.04636e-12 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## acsf-parallel-centers

- 官方测试源:`code/dscribe/tests/test_acsf.py`
- 活配置(决定哪些分支被编译/执行):Float64 ACSF observable, fixed deterministic structures and parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):ACSF features and numerical derivatives from serial and two-worker execution over fixed center lists.
- 容差 atol=1e-08;噪声地板=1.81899e-12 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## acsf-periodic-coordination

- 官方测试源:`code/dscribe/tests/test_acsf.py`
- 活配置(决定哪些分支被编译/执行):Float64 ACSF observable, fixed deterministic structures and parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Radial and angular ACSF values for periodic simple-cubic hydrogen and rocksalt NaCl coordination shells.
- 容差 atol=1e-08;噪声地板=1.9984e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## acsf-periodic-images

- 官方测试源:`code/dscribe/tests/test_acsf.py`
- 活配置(决定哪些分支被编译/执行):Float64 ACSF observable, fixed deterministic structures and parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):ACSF vectors for equivalent explicit and wrapped periodic environments plus their residual.
- 容差 atol=1e-08;噪声地板=3.88578e-16 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## acsf-rigid-symmetries

- 官方测试源:`code/dscribe/tests/test_acsf.py`
- 活配置(决定哪些分支被编译/执行):Float64 ACSF observable, fixed deterministic structures and parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Original and rigidly transformed center-resolved ACSF vectors plus their residual.
- 容差 atol=1e-08;噪声地板=8.88178e-16 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## acsf-standard-example

- 官方测试源:`code/dscribe/tests/test_acsf.py`
- 活配置(决定哪些分支被编译/执行):Float64 ACSF observable, fixed deterministic structures and parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):The official water example's center-resolved ACSF vector with radial and angular parameter families.
- 容差 atol=1e-08;噪声地板=3.33067e-16 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## analytical-derivatives

- 官方测试源:`code/dscribe/tests/test_soap.py`
- 活配置(决定哪些分支被编译/执行):Analytical derivatives; float64 output, SAB_REPEATS=1, fixed deterministic geometry, and the parameters documented in runner.py.
- 判分观测量(缺陷必须动到它):Analytical GTO derivative tensors and paired features for attached/detached centers and two compression modes.
- 容差 atol=1e-06;噪声地板=3.77476e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## center-modes

- 官方测试源:`code/dscribe/tests/test_soap.py`
- 活配置(决定哪些分支被编译/执行):Index and Cartesian centers; float64 output, SAB_REPEATS=1, fixed deterministic geometry, and the parameters documented in runner.py.
- 判分观测量(缺陷必须动到它):SOAP arrays for atom-index centers, equivalent Cartesian centers, and an external center.
- 容差 atol=1e-08;噪声地板=1.60982e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## coefficient-integration

- 官方测试源:`code/dscribe/tests/test_soap.py`
- 活配置(决定哪些分支被编译/执行):High-angular-order integration; float64 output, SAB_REPEATS=1, fixed deterministic geometry, and the parameters documented in runner.py.
- 判分观测量(缺陷必须动到它):High-l GTO and polynomial SOAP spectra on the deterministic upstream coefficient-integration geometry.
- 容差 atol=1e-10;噪声地板=8.45678e-18 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 0.3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## coulomb-eigenspectrum

- 官方测试源:`code/dscribe/tests/test_coulombmatrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Coulomb eigenspectrum, independent symmetric eigenvalues, and residual.
- 容差 atol=1e-08;噪声地板=5.68434e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## coulomb-finite-distance

- 官方测试源:`code/dscribe/tests/test_coulombmatrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Coulomb matrices with periodic flags disabled and enabled on identical finite coordinates.
- 容差 atol=1e-08;噪声地板=7.10543e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## coulomb-numerical-derivatives

- 官方测试源:`code/dscribe/tests/test_coulombmatrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Numerical matrix and eigenspectrum derivative tensors with features.
- 容差 atol=1e-06;噪声地板=5.68434e-10 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## coulomb-parallel-create

- 官方测试源:`code/dscribe/tests/test_coulombmatrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Serial and two-worker Coulomb matrices for two molecules, plus residual.
- 容差 atol=1e-08;噪声地板=7.10543e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## coulomb-random-permutation

- 官方测试源:`code/dscribe/tests/test_coulombmatrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Seeded random-rank probability matrix and physical row norms.
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## coulomb-reference-formula

- 官方测试源:`code/dscribe/tests/test_coulombmatrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):DScribe Coulomb matrix, independent charge-over-distance formula, and residual.
- 容差 atol=1e-08;噪声地板=7.10543e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## coulomb-sorted-matrix

- 官方测试源:`code/dscribe/tests/test_coulombmatrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Sorted Coulomb matrix, independent stable row-norm sort, and residual.
- 容差 atol=1e-08;噪声地板=7.10543e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## coulomb-standard-example

- 官方测试源:`code/dscribe/examples/coulombmatrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):None, sorted-L2, and eigenspectrum Coulomb outputs for the official water example.
- 容差 atol=1e-08;噪声地板=3.55271e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## coulomb-symmetries

- 官方测试源:`code/dscribe/tests/test_coulombmatrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Rigid-motion matrices and atom-permutation eigenspectra with residuals.
- 容差 atol=1e-08;噪声地板=1.42109e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## crossover-compression

- 官方测试源:`code/dscribe/tests/test_soap.py`
- 活配置(决定哪些分支被编译/执行):Crossover compression; float64 output, SAB_REPEATS=1, fixed deterministic geometry, and the parameters documented in runner.py.
- 判分观测量(缺陷必须动到它):GTO and polynomial SOAP arrays with full species crossover and crossover-disabled layouts.
- 容差 atol=1e-08;噪声地板=2.17049e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## ewald-automatic-cutoffs

- 官方测试源:`code/dscribe/tests/test_ewaldsummatrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Automatically converged Ewald matrices across accuracy and cost-weight settings.
- 容差 atol=1e-08;噪声地板=1.42109e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## ewald-eigenspectrum

- 官方测试源:`code/dscribe/tests/test_ewaldsummatrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Ewald eigenspectrum, independent symmetric eigenvalues, and residual.
- 容差 atol=1e-08;噪声地板=2.13163e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## ewald-electrostatic-reference

- 官方测试源:`code/dscribe/tests/test_ewaldsummatrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Converged Ewald matrix, reconstructed total energy, and all two-particle energies.
- 容差 atol=1e-05;噪声地板=1.06581e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## ewald-numerical-derivatives

- 官方测试源:`code/dscribe/tests/test_ewaldsummatrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Numerical matrix and eigenspectrum Ewald derivative tensors with features.
- 容差 atol=1e-06;噪声地板=8.73115e-11 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 8s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## ewald-parallel-create

- 官方测试源:`code/dscribe/tests/test_ewaldsummatrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Serial and two-worker Ewald matrices for two periodic systems, plus residual.
- 容差 atol=1e-08;噪声地板=1.42109e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 4s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## ewald-random-permutation

- 官方测试源:`code/dscribe/tests/test_ewaldsummatrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Seeded random-rank probability matrix and physical Ewald row norms.
- 参考耗时 12s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## ewald-screening-independence

- 官方测试源:`code/dscribe/tests/test_ewaldsummatrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Explicit-cutoff Ewald matrices at three screening widths and pairwise residuals.
- 容差 atol=1e-05;噪声地板=1.42109e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## ewald-sorted-matrix

- 官方测试源:`code/dscribe/tests/test_ewaldsummatrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Sorted Ewald matrix, independent stable row-norm sort, and residual.
- 容差 atol=1e-08;噪声地板=1.06581e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## ewald-standard-example

- 官方测试源:`code/dscribe/examples/ewaldsummatrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):None, sorted-L2, and eigenspectrum Ewald outputs for an official-style periodic example.
- 容差 atol=1e-08;噪声地板=1.06581e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## ewald-symmetries

- 官方测试源:`code/dscribe/tests/test_ewaldsummatrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Rigid cell-motion matrices and atom-permutation Ewald eigenspectra with residuals.
- 容差 atol=1e-08;噪声地板=1.77636e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## ewald-unit-cells

- 官方测试源:`code/dscribe/tests/test_ewaldsummatrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Ewald matrices in orthorhombic, cubic, and triclinic unit cells.
- 容差 atol=1e-08;噪声地板=1.06581e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## inner-average

- 官方测试源:`code/dscribe/tests/test_soap.py`
- 活配置(决定哪些分支被编译/执行):Inner averaging; float64 output, SAB_REPEATS=1, fixed deterministic geometry, and the parameters documented in runner.py.
- 判分观测量(缺陷必须动到它):Inner-averaged GTO and polynomial SOAP arrays over three centers.
- 容差 atol=1e-10;噪声地板=3.10862e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## lmbtr-geometry-peaks

- 官方测试源:`code/dscribe/tests/test_lmbtr.py`
- 活配置(决定哪些分支被编译/执行):Float64 MBTR-family observable, fixed deterministic atomic structures and descriptor parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Local K2-distance and K3-angle distributions at two centers.
- 容差 atol=1e-08;噪声地板=4.35207e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## lmbtr-k-body-bases

- 官方测试源:`code/dscribe/tests/test_lmbtr.py`
- 活配置(决定哪些分支被编译/执行):Float64 MBTR-family observable, fixed deterministic atomic structures and descriptor parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Center-resolved LMBTR K2 inverse-distance and K3 angle feature vectors.
- 容差 atol=1e-08;噪声地板=7.99361e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## lmbtr-normalization

- 官方测试源:`code/dscribe/tests/test_lmbtr.py`
- 活配置(决定哪些分支被编译/执行):Float64 MBTR-family observable, fixed deterministic atomic structures and descriptor parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Periodic center-resolved LMBTR vectors and their L2 norms.
- 容差 atol=1e-08;噪声地板=5.55112e-16 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## lmbtr-numerical-derivatives

- 官方测试源:`code/dscribe/tests/test_lmbtr.py`
- 活配置(决定哪些分支被编译/执行):Float64 MBTR-family observable, fixed deterministic atomic structures and descriptor parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Attached and detached-center numerical LMBTR derivatives with paired features.
- 容差 atol=1e-06;噪声地板=3.81988e-11 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## lmbtr-parallel-centers

- 官方测试源:`code/dscribe/tests/test_lmbtr.py`
- 活配置(决定哪些分支被编译/执行):Float64 MBTR-family observable, fixed deterministic atomic structures and descriptor parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Serial and parallel LMBTR center features for multiple systems, plus residuals.
- 容差 atol=1e-08;噪声地板=7.99361e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## lmbtr-rigid-symmetries

- 官方测试源:`code/dscribe/tests/test_lmbtr.py`
- 活配置(决定哪些分支被编译/执行):Float64 MBTR-family observable, fixed deterministic atomic structures and descriptor parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Center-resolved LMBTR features under rigid motion, plus their residual.
- 容差 atol=1e-08;噪声地板=1.15463e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## lmbtr-standard-example

- 官方测试源:`code/dscribe/examples/lmbtr.py`
- 活配置(决定哪些分支被编译/执行):Float64 MBTR-family observable, fixed deterministic atomic structures and descriptor parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):End-to-end atom-index and Cartesian-center LMBTR vectors adapted from the official example.
- 容差 atol=1e-08;噪声地板=7.99361e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## mbtr-analytical-derivatives

- 官方测试源:`code/dscribe/tests/test_mbtr.py`
- 活配置(决定哪些分支被编译/执行):Float64 MBTR-family observable, fixed deterministic atomic structures and descriptor parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Analytical K2-distance and K3-cosine derivative tensors with paired features.
- 容差 atol=1e-06;噪声地板=1.25944e-12 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## mbtr-gaussian-distribution

- 官方测试源:`code/dscribe/tests/test_mbtr.py`
- 活配置(决定哪些分支被编译/执行):Float64 MBTR-family observable, fixed deterministic atomic structures and descriptor parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Normalized and unnormalized Gaussian-broadened H2 distance distributions.
- 容差 atol=1e-08;噪声地板=2.22045e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## mbtr-geometry-peaks

- 官方测试源:`code/dscribe/tests/test_mbtr.py`
- 活配置(决定哪些分支被编译/执行):Float64 MBTR-family observable, fixed deterministic atomic structures and descriptor parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):K1, K2-distance, and K3-angle distributions on fixed grids.
- 容差 atol=1e-08;噪声地板=4.26326e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## mbtr-k-body-bases

- 官方测试源:`code/dscribe/tests/test_mbtr.py`
- 活配置(决定哪些分支被编译/执行):Float64 MBTR-family observable, fixed deterministic atomic structures and descriptor parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):K1 atomic-number, K2 inverse-distance, and K3 angle feature vectors.
- 容差 atol=1e-08;噪声地板=7.99361e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## mbtr-normalization

- 官方测试源:`code/dscribe/tests/test_mbtr.py`
- 活配置(决定哪些分支被编译/执行):Float64 MBTR-family observable, fixed deterministic atomic structures and descriptor parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Periodic copper MBTR vectors under none, L2, per-atom, and Valle–Oganov normalization.
- 容差 atol=1e-08;噪声地板=2.98428e-13 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## mbtr-numerical-derivatives

- 官方测试源:`code/dscribe/tests/test_mbtr.py`
- 活配置(决定哪些分支被编译/执行):Float64 MBTR-family observable, fixed deterministic atomic structures and descriptor parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Numerical derivatives under none, L2, and per-atom normalization with paired features.
- 容差 atol=1e-06;噪声地板=3.81988e-11 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## mbtr-parallel-create

- 官方测试源:`code/dscribe/tests/test_mbtr.py`
- 活配置(决定哪些分支被编译/执行):Float64 MBTR-family observable, fixed deterministic atomic structures and descriptor parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Serial/parallel MBTR features and derivative tensors for two water-like systems.
- 容差 atol=1e-08;噪声地板=6.27498e-13 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## mbtr-periodic-images

- 官方测试源:`code/dscribe/tests/test_mbtr.py`
- 活配置(决定哪些分支被编译/执行):The three K1/K2/K3 parameter cases and cubic, triclinic, and FCC unit-cell comparisons from upstream test_periodic_images_1, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):L2-normalized periodic K1 atomic-number, K2 inverse-distance, and K3 cosine MBTR arrays for the official cubic/triclinic cells, their 2x1x1 supercells, and three equivalent FCC cells.
- 容差 atol=1e-08;噪声地板=4.05231e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## mbtr-periodic-translation

- 官方测试源:`code/dscribe/tests/test_mbtr.py`
- 活配置(决定哪些分支被编译/执行):Float64 MBTR-family observable, fixed deterministic atomic structures and descriptor parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Periodic K2 and K3 features before and after a lattice-vector translation, plus residuals.
- 容差 atol=1e-08;噪声地板=7.77156e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## mbtr-rigid-symmetries

- 官方测试源:`code/dscribe/tests/test_mbtr.py`
- 活配置(决定哪些分支被编译/执行):Float64 MBTR-family observable, fixed deterministic atomic structures and descriptor parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):MBTR features before and after a rigid rotation and translation, plus their residual.
- 容差 atol=1e-08;噪声地板=1.15463e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## mbtr-standard-example

- 官方测试源:`code/dscribe/examples/mbtr.py`
- 活配置(决定哪些分支被编译/执行):Float64 MBTR-family observable, fixed deterministic atomic structures and descriptor parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):End-to-end finite and periodic MBTR vectors adapted from the official example.
- 容差 atol=1e-08;噪声地板=7.99361e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## mbtr-supercell-similarity

- 官方测试源:`code/dscribe/tests/test_mbtr.py`
- 活配置(决定哪些分支被编译/执行):The three K1/K2/K3 parameter cases and four hydrogen FCC cells from upstream test_periodic_supercell_similarity, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):L2-normalized periodic K1 atomic-number, K2 inverse-distance, and K3 cosine MBTR arrays for the official primitive, 2x2x2, orthorhombic, and conventional cubic FCC cells.
- 容差 atol=1e-08;噪声地板=3.88578e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 4s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## mbtr-valle-oganov-derivatives

- 官方测试源:`code/dscribe/tests/test_mbtr.py`
- 活配置(决定哪些分支被编译/执行):Float64 MBTR-family observable, fixed deterministic atomic structures and descriptor parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Numerical and analytical derivatives of periodic Valle–Oganov-normalized MBTR.
- 容差 atol=1e-06;噪声地板=1.23691e-10 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 4s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## mu1nu1-compression

- 官方测试源:`code/dscribe/tests/test_soap.py`
- 活配置(决定哪些分支被编译/执行):mu1nu1 compression; float64 output, SAB_REPEATS=1, fixed deterministic geometry, and the parameters documented in runner.py.
- 判分观测量(缺陷必须动到它):mu1nu1-compressed GTO and polynomial SOAP arrays at two centers.
- 容差 atol=1e-10;噪声地板=1.94289e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## numerical-derivatives

- 官方测试源:`code/dscribe/tests/test_soap.py`
- 活配置(决定哪些分支被编译/执行):Numerical derivatives; float64 output, SAB_REPEATS=1, fixed deterministic geometries: the four-atom H2O-C molecule with two centers for the per-center configurations (r_cut 3.5, n_max 3, l_max 3), and a periodic cell of 64 rotated copies of it (256 atoms, cubic cell 12.4 A) with every atom as a center for the averaged configurations (r_cut 6.0, n_max 6, l_max 6); parameters documented in runner.py.
- 判分观测量(缺陷必须动到它):Finite-difference derivative tensors and paired SOAP features: per-center tensors on the molecule for the off/off and off/mu1nu1 configurations, and inner- and outer-averaged global-descriptor derivatives with respect to all 256 atom positions of the periodic cell for the inner/off and outer/crossover configurations.
- 容差 atol=1e-06;噪声地板=4.9738e-10 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 140s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## outer-average

- 官方测试源:`code/dscribe/tests/test_soap.py`
- 活配置(决定哪些分支被编译/执行):Outer averaging; float64 output, SAB_REPEATS=1, fixed deterministic geometry, and the parameters documented in runner.py.
- 判分观测量(缺陷必须动到它):Outer-averaged SOAP arrays, explicit means of center-wise arrays, and their residuals for both bases.
- 容差 atol=1e-08;噪声地板=1.09635e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## parallel-centers

- 官方测试源:`code/dscribe/tests/test_soap.py`
- 活配置(决定哪些分支被编译/执行):Parallel structures and center modes; float64 output, SAB_REPEATS=1, fixed deterministic geometry, and the parameters documented in runner.py.
- 判分观测量(缺陷必须动到它):Repeated dense SOAP feature arrays from one- and two-worker execution using index and Cartesian centers.
- 容差 atol=1e-08;噪声地板=1.44329e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1.5s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## periodic-images

- 官方测试源:`code/dscribe/tests/test_soap.py`
- 活配置(决定哪些分支被编译/执行):Periodic image enumeration; float64 output, SAB_REPEATS=1, fixed deterministic geometry, and the parameters documented in runner.py.
- 判分观测量(缺陷必须动到它):Periodic NaCl SOAP arrays before and after a full-cell translation, plus their residuals.
- 容差 atol=1e-08;噪声地板=3.9968e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## periodic-padding

- 官方测试源:`code/dscribe/tests/test_soap.py`
- 活配置(决定哪些分支被编译/执行):Periodic cell padding; float64 output, SAB_REPEATS=1, fixed deterministic geometry, and the parameters documented in runner.py.
- 判分观测量(缺陷必须动到它):SOAP arrays for orthogonal and equivalent monoclinic cells at three sizes and cutoffs, plus residuals.
- 容差 atol=1e-08;噪声地板=2.77556e-16 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## radial-bases

- 官方测试源:`code/dscribe/tests/test_soap.py`
- 活配置(决定哪些分支被编译/执行):GTO and polynomial radial bases; float64 output, SAB_REPEATS=1, fixed deterministic geometry, and the parameters documented in runner.py.
- 判分观测量(缺陷必须动到它):SOAP arrays for the GTO and polynomial radial-basis implementations.
- 容差 atol=1e-08;噪声地板=2.17049e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## rbf-orthonormality

- 官方测试源:`code/dscribe/tests/test_soap.py`
- 活配置(决定哪些分支被编译/执行):Radial-basis orthonormality; float64 output, SAB_REPEATS=1, fixed deterministic geometry, and the parameters documented in runner.py.
- 判分观测量(缺陷必须动到它):GTO alpha/beta arrays and numerically integrated radial overlap matrices through l=20.
- 容差 atol=1e-08;噪声地板=5.91172e-12 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## rigid-symmetries

- 官方测试源:`code/dscribe/tests/test_soap.py`
- 活配置(决定哪些分支被编译/执行):Rigid-motion symmetries; float64 output, SAB_REPEATS=1, fixed deterministic geometry, and the parameters documented in runner.py.
- 判分观测量(缺陷必须动到它):GTO and polynomial feature arrays before and after a fixed rotation and translation, plus their residuals.
- 容差 atol=1e-08;噪声地板=2.17049e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## sine-eigenspectrum

- 官方测试源:`code/dscribe/tests/test_sinematrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Sine eigenspectrum, independent symmetric eigenvalues, and residual.
- 容差 atol=1e-08;噪声地板=7.10543e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## sine-numerical-derivatives

- 官方测试源:`code/dscribe/tests/test_sinematrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Numerical matrix and eigenspectrum derivative tensors with features.
- 容差 atol=1e-06;噪声地板=6.40284e-10 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## sine-parallel-create

- 官方测试源:`code/dscribe/tests/test_sinematrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Serial and two-worker Sine matrices for two periodic systems, plus residual.
- 容差 atol=1e-08;噪声地板=1.06581e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## sine-periodic-formula

- 官方测试源:`code/dscribe/tests/test_sinematrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):DScribe Sine matrix, independent periodic sine formula, and residual.
- 容差 atol=1e-08;噪声地板=1.06581e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## sine-random-permutation

- 官方测试源:`code/dscribe/tests/test_sinematrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Seeded random-rank probability matrix and physical row norms.
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## sine-sorted-matrix

- 官方测试源:`code/dscribe/tests/test_sinematrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Sorted Sine matrix, independent stable row-norm sort, and residual.
- 容差 atol=1e-08;噪声地板=1.06581e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## sine-standard-example

- 官方测试源:`code/dscribe/examples/sinematrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):None, sorted-L2, and eigenspectrum Sine outputs for an official-style periodic example.
- 容差 atol=1e-08;噪声地板=4.26326e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## sine-symmetries

- 官方测试源:`code/dscribe/tests/test_sinematrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Rigid cell-motion matrices and atom-permutation eigenspectra with residuals.
- 容差 atol=1e-08;噪声地板=4.26326e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## sine-unit-cells

- 官方测试源:`code/dscribe/tests/test_sinematrix.py`
- 活配置(决定哪些分支被编译/执行):Float64 matrix-descriptor observable on fixed deterministic three-atom structures, parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Sine matrices in orthorhombic, cubic, and triclinic unit cells.
- 容差 atol=1e-08;噪声地板=1.13687e-13 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## standard-example

- 官方测试源:`code/dscribe/examples/soap.py`
- 活配置(决定哪些分支被编译/执行):Official end-to-end example; float64 output, SAB_REPEATS=1, fixed deterministic geometry, and the parameters documented in runner.py.
- 判分观测量(缺陷必须动到它):Averaged SOAP vectors for water, methanol, and peroxide and their pairwise distance matrix.
- 容差 atol=1e-08;噪声地板=3.55271e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## valle-oganov-analytical-derivatives

- 官方测试源:`code/dscribe/tests/test_valle_oganov.py`
- 活配置(决定哪些分支被编译/执行):Float64 MBTR-family observable, fixed deterministic atomic structures and descriptor parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Analytical Valle–Oganov derivative tensor and paired features.
- 容差 atol=1e-06;噪声地板=3.42837e-13 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## valle-oganov-numerical-derivatives

- 官方测试源:`code/dscribe/tests/test_valle_oganov.py`
- 活配置(决定哪些分支被编译/执行):Float64 MBTR-family observable, fixed deterministic atomic structures and descriptor parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Numerical Valle–Oganov derivative tensor and paired features.
- 容差 atol=1e-06;噪声地板=4.36557e-11 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## valle-oganov-parallel-create

- 官方测试源:`code/dscribe/tests/test_valle_oganov.py`
- 活配置(决定哪些分支被编译/执行):Float64 MBTR-family observable, fixed deterministic atomic structures and descriptor parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Serial and parallel Valle–Oganov descriptors for two periodic NaCl systems.
- 容差 atol=1e-08;噪声地板=1.68754e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## valle-oganov-standard-example

- 官方测试源:`code/dscribe/examples/valle_oganov.py`
- 活配置(决定哪些分支被编译/执行):Float64 MBTR-family observable, fixed deterministic atomic structures and descriptor parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):End-to-end distance and angle Valle–Oganov vectors adapted from the official example.
- 容差 atol=1e-08;噪声地板=1.68754e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## valle-oganov-symmetries

- 官方测试源:`code/dscribe/tests/test_valle_oganov.py`
- 活配置(决定哪些分支被编译/执行):Float64 MBTR-family observable, fixed deterministic atomic structures and descriptor parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Valle–Oganov features before and after rigid motion, plus their residual.
- 容差 atol=1e-08;噪声地板=1.68754e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## valle-oganov-vs-mbtr

- 官方测试源:`code/dscribe/tests/test_valle_oganov.py`
- 活配置(决定哪些分支被编译/执行):Float64 MBTR-family observable, fixed deterministic atomic structures and descriptor parameters documented in runner.py, SAB_REPEATS=1.
- 判分观测量(缺陷必须动到它):Distance and angle Valle–Oganov outputs beside equivalent normalized MBTR outputs and residuals.
- 容差 atol=1e-08;噪声地板=3.9968e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点

## weighting-functions

- 官方测试源:`code/dscribe/tests/test_soap.py`
- 活配置(决定哪些分支被编译/执行):Neighbour weighting functions; float64 output, SAB_REPEATS=1, fixed deterministic geometry, and the parameters documented in runner.py.
- 判分观测量(缺陷必须动到它):SOAP arrays for polynomial, power-law, and exponential weights with both radial bases.
- 容差 atol=1e-10;噪声地板=3.78586e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 0.3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
