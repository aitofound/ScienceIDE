# ScienceIDE-Hard (85 tasks)

> Code: [github.com/aitofound/ScienceIDE](https://github.com/aitofound/ScienceIDE) · Dataset: [huggingface.co/datasets/AItonomy/ScienceIDE](https://huggingface.co/datasets/AItonomy/ScienceIDE) · Project page: [aitonomy.org/projects/scienceide](https://aitonomy.org/projects/scienceide)

The core benchmark is 85 tasks. Thirty of them, all inside the published environments, are released here with their instruction, injected defect, reference fix, provenance and measurement records. The other 55 are held out as a test set; their names are listed below.

## Published (30)

- `athena-chemistry/athena-chemistry-repair-chem-sol-cvode-002-loosen-relative-tolerance`
- `athena-chemistry/athena-chemistry-repair-coef-thermo-l20k25`
- `athena-chemistry/athena-chemistry-repair-sign-bvals-sixray-l86c16`
- `athena-chemistry/athena-chemistry-repair-sign-thermo-l222c16`
- `athena-gr/athena-gr-repair-gr-sol-inv-003-aitken-publish-from-newest`
- `athena-sgfft/athena-sgfft-repair-sg-sol-cycle-003-fmg-skips-coarsest-level`
- `athena-sr/athena-sr-repair-sr-sol-hllc-041-use-direct-contact-root`
- `athena-sr/athena-sr-repair-sr-sol-inv-003-aitken-publish-from-newest`
- `mitgcm-atmos/mitgcm-atmos-repair-sem-data-aim-convection-qbl`
- `mitgcm-atmos/mitgcm-atmos-repair-sem-data-aim-longwave-cloud-offset`
- `mitgcm-atmos/mitgcm-atmos-repair-sem-data-aim-shortwave-dry-air`
- `mitgcm-atmos/mitgcm-atmos-repair-sem-data-aim-surface-land-heat`
- `mitgcm-atmos/mitgcm-atmos-repair-sem-data-gray-window-co2-window-base`
- `mitgcm-atmos/mitgcm-atmos-repair-sem-data-gray-window-wv-log-curvature`
- `mitgcm-biogeo/mitgcm-biogeo-repair-sem-data-bling-ligand-stability-max`
- `mitgcm-biogeo/mitgcm-biogeo-repair-sem-data-cfc11-schmidt-cubic`
- `mitgcm-biogeo/mitgcm-biogeo-repair-sem-data-saphe-waters-k1-temp-s`
- `mitgcm-biogeo/mitgcm-biogeo-repair-sem-data-saphe-waters-k2-temp-s`
- `mitgcm-iceshelf/mitgcm-iceshelf-repair-sem-data-gammafrict-molecular-scale`
- `mitgcm-iceshelf/mitgcm-iceshelf-restore-excise-shelfice-shelfice-readparms-shelfice-readparms`
- `mitgcm-mixing/mitgcm-mixing-repair-sem-data-kpp-dd-molecular-visc`
- `mitgcm-mixing/mitgcm-mixing-repair-sem-data-kpp-interior-conv-visc`
- `mitgcm-mixing/mitgcm-mixing-restore-excise-ggl90-ggl90-init-varia-ggl90-init-varia`
- `mitgcm-mixing/mitgcm-mixing-restore-excise-ggl90-ggl90-readparms-ggl90-readparms`
- `mitgcm-ocean/mitgcm-ocean-restore-excise-cubed-sphere-exch2-get-uv-bounds-exch2-get-uv-bounds`
- `mitgcm-ocean/mitgcm-ocean-restore-excise-cubed-sphere-w2-set-tile2tiles-w2-set-tile2tiles`
- `mitgcm-seaice/mitgcm-seaice-repair-sem-data-aevp-stability-factor`
- `mitgcm-seaice/mitgcm-seaice-repair-sem-data-seaice-vapor-poly-c5`
- `mitgcm-seaice/mitgcm-seaice-restore-excise-seaice-thermodynamics-seaice-readparms-seaice-readparms`
- `mitgcm-seaice/mitgcm-seaice-restore-excise-thsice-thermodynamics-thsice-readparms-thsice-readparms`

## Held out (55)

- `athena-chemistry-repair-swaparg-thermo-l413c27`
- `laps-repair-multi2-2d-coef-mhd-l404k0-sign-mhdrhs-l80c64`
- `laps-repair-multi2-3d-coef-mhd-l433k0-sign-mhdrhs-l227c73`
- `laps-repair-multi3-2d-coef-mhd-l404k0-rkorder-rktmod-l39-sign-mhdrhs-l75c63`
- `laps-restore-2d-mhd-vardt`
- `laps-restore-2d-mhdinit-background-fields-initialize`
- `laps-restore-3d-mhd-vardt`
- `laps-restore-3d-mhdinit-perturbation-initialize`
- `laps-restore-xmulti2-2d-perturbation-initialize-calc-flux`
- `laps-restore-xmulti2-2d-vardt-background-fields-initialize`
- `laps-restore-xmulti2-3d-perturbation-initialize-calc-flux`
- `laps-restore-xmulti2-3d-vardt-background-fields-initialize`
- `mitgcm-atmos-repair-sem-data-aim-shortwave-water-visible`
- `mitgcm-atmos-repair-sem-data-gray-window-wv-nonwindow-scale`
- `mitgcm-atmos-repair-sem-data-gray-window-wv-window-linear`
- `mitgcm-atmos-repair-sem-data-gray-window-wv-window-quadratic`
- `mitgcm-biogeo-restore-excise-cfc-gas-exchange-cfc-param-cfc-param`
- `mitgcm-iceshelf-repair-sem-data-gammafrict-molecular-offset`
- `mitgcm-mixing-restore-excise-kpp-kpp-readparms-kpp-readparms`
- `mitgcm-mixing-restore-excise-my82-my82-init-varia-my82-init-varia`
- `mitgcm-ocean-repair-sem-data-coare3-air-kinematic-viscosity`
- `mitgcm-seaice-repair-sem-data-seaice-vapor-poly-c2`
- `mitgcm-seaice-repair-sem-data-seaice-vapor-poly-c3`
- `phantom-repair-step-011-twas-absolute-commit`
- `pluto-cool-repair-coef-radiat-l43k9`
- `pluto-cool-repair-sol-cool-tol`
- `pluto-cool-repair-sol-r2-h2-rotational-temperature`
- `pluto-cool-repair-sol-r2-h2-vibrational-temperature`
- `pluto-cool-repair-sol-substep-handoff`
- `pluto-cool-restore-cx-power-law-cooling-powerlawcooling`
- `pluto-cool-restore-cx-sneq-radiat-radiat`
- `pluto-cool-restore-cx-tabulated-radiat-radiat`
- `pluto-cool-restore-cxf-init-init-profile`
- `pluto-cr-restore-cx-cr-bell-instability-init-init`
- `pluto-hd-repair-famlit-init-l57k12`
- `pluto-hd-repair-famlit-init-l64k8`
- `pluto-hd-repair-famlit-init-l66k8`
- `pluto-hd-repair-famlit-init-l67k8`
- `pluto-hd-repair-sol-dt-growth-ramp`
- `pluto-hd-repair-sol-sedov-deposit-radius`
- `pluto-hd-restore-cx-hd-viscosity-taylor-couette-init-init`
- `pluto-hd-restore-cx-mhd-thermal-conduction-blast-init-init`
- `pluto-hd-restore-cx-mhd-thermal-conduction-tcfront-init-tprofile`
- `pluto-hd-restore-cxf-init-init-init`
- `pluto-rad-repair-opac-init-l160`
- `pluto-rad-repair-opac-init-l166`
- `pluto-rad-repair-sign-hllc-mb-l191c26`
- `pluto-rad-repair-sign-rad-tools-l161c16`
- `pluto-rad-restore-cx-radiation-relativistic-rhd-shadow-init-init`
- `pluto-rad-restore-cx-radiation-relativistic-rhd-shadow-init-userdefopacities`
- `pluto-repair-cfl-main-l572`
- `pluto-restore-cx-field-loop-init-init`
- `pluto-restore-cx-fluxes-flux`
- `pluto-restore-cx-glm-glm-solve`
- `pluto-rmhd-restore-cx-glm-glm-glm-solve`
