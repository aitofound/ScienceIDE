# Environments

> Code: [github.com/aitofound/ScienceIDE](https://github.com/aitofound/ScienceIDE) · Dataset: [huggingface.co/datasets/AItonomy/ScienceIDE](https://huggingface.co/datasets/AItonomy/ScienceIDE) · Project page: [aitonomy.org/projects/scienceide](https://aitonomy.org/projects/scienceide)

Fifteen environments are published with their full runtime (Dockerfile templates, physics cases, checks, scoring) under `environments/`. The remaining 49 are held out as a test set for now; their names are listed so results can be reported against them.

## Published (15)

| Environment | Upstream license |
|---|---|
| `athena-chemistry` | BSD-3-Clause |
| `athena-gr` | BSD-3-Clause |
| `athena-sgfft` | BSD-3-Clause |
| `athena-sr` | BSD-3-Clause |
| `mitgcm-atmos` | MIT |
| `mitgcm-biogeo` | MIT |
| `mitgcm-iceshelf` | MIT |
| `mitgcm-mixing` | MIT |
| `mitgcm-ocean` | MIT |
| `mitgcm-seaice` | MIT |
| `gkeyll-vlasov` | MIT |
| `dscribe-descriptors` | Apache-2.0 |
| `nest-noble-element-microphysics` | Apache-2.0 |
| `edkit-adaptive-krylov-time-evolution` | MIT |
| `stim-stab` | Apache-2.0 |

## Held out (49)

- `athena-fft`
- `athena-nhydro`
- `athena-nmhd`
- `athena-radiation`
- `athena-sts`
- `athena-turb`
- `basilisk-spacecraft-reaction-wheel-dynamics`
- `eftcamb-linear-perturbations`
- `epoch-maxwell-solvers-stencils`
- `g4cmp-phonon-transport`
- `gkeyll-fluid`
- `gkeyll-gyrokinetic`
- `gkeyll-pkpm`
- `laps`
- `laps-3d-compressible`
- `meep-adjoint-sensitivity`
- `meep-fdtd`
- `mink-constrained-differential-ik`
- `open-eprem-focused-particle-transport`
- `phantom`
- `phantom-dust-growth`
- `phantom-gr`
- `phantom-gravsinks`
- `phantom-hdturb`
- `phantom-mhd-nonideal`
- `phantom-pilot`
- `phantom-radiation-thermochemistry`
- `phantom-winds`
- `pluto-cooling-chemistry`
- `pluto-hd-diffusion`
- `pluto-mhd-les`
- `pluto-particles-dust`
- `pluto-rhd-radiation`
- `pluto-rmhd-resrmhd`
- `pyamg-aggregation-amg`
- `pyamg-classical`
- `pyamg-krylov`
- `pyamg-relaxation`
- `pymatgen-interface`
- `pymatgen-phase-diagram`
- `pymatgen-pourbaix`
- `pyxsim-thermal-spectral-synthesis`
- `qutip-generator`
- `s4-fmm-fourier-factorization`
- `s4-rcwa`
- `scirpy-sequence-distance-metrics`
- `simupy-flight-nesc-6dof-flight-dynamics`
- `strax-xenon-stream-processing`
- `tsid-talos-fixed-contact-inverse-dynamics`
