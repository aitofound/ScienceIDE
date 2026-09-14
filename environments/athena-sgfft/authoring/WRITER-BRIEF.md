# 写手简报 — athena-sgfft

模块:Self-gravity (FFT and multigrid Poisson solvers), FFT infrastructure and driven turbulence

**可变异的源文件(6 个,模块只编译这些)**
  src/gravity/
  src/fft/
  src/multigrid/
  src/pgen/jeans.cpp
  src/pgen/fft.cpp
  src/pgen/turb.cpp

**死代码 / 不可达(1 条,永远不要在这里出题)**
  - Cosmic-ray diffusion also uses multigrid but is separate physics; see not_packaged

**坑(2 条)**
  ! FFTW3 required; fft and turb tests are written for MPI (-mpi, mpirun)
  ! turb_3d uses a seeded random driving; determinism across ranks must be verified in the survey

## fft-periodic-stable-mpi2


## fft-periodic-unstable-r16-mpi2


## fft-periodic-unstable-r32-mpi2


## mg-fmg-multipole-stable


## mg-fmg-periodic-stable-mpi2


## mg-fmg-periodic-stable-serial


## mg-fmg-periodic-unstable-r16


## mg-fmg-periodic-unstable-r32


## mg-mgi-fixed-periodic-stable

