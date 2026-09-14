# descriptors: authoring notes

This directory is hidden at Harbor runtime and is not part of the contract.
`comment/pipeline/` is written only by the CLI (module entry, test survey,
self-validation and runtime records). This file is the human-readable story.

## Module

The combined module covers DScribe's SOAP, MBTR/LMBTR/Valle–Oganov, ACSF,
and Coulomb/Sine/Ewald descriptor families and their supported derivatives.
Family-specific Python and C++ implementations under `dscribe/descriptors`
and `dscribe/ext` are owned; descriptor base classes, geometry, parallel,
binding, build, and Eigen code are shared support. Similarity-kernel
aggregation and downstream plotting/training examples are deliberately not
separate numerical responsibilities.

## Build

Both images compile the pinned extension once with `python3 setup.py build_ext
--inplace`. Every check points `SOURCE_DIR` at that shared build, so an
80-check solve does not recompile per check. Measured build, solve, and
per-check run seconds are recorded by the CLI in `comment/pipeline/` after
self-validation.

## Tolerances

The check-specific policies were consolidated from the former family leaves
and calibrated again with nominal/variant Docker self-validation in this
combined environment. The human finalized the resulting policies and
tolerances after reviewing the measured spreads and bound fractions. A second
self-validation then passed all 80 checks with reward 1.0; its measurements are
recorded in `comment/pipeline/self-validation.json`. Per-check warrants and
numerical details remain in each README and rubric.

## Blind spots

The checks do not grade `dscribe.kernels`, documentation rendering, plotting,
or downstream model training. Cross-compiler and accelerator-specific
floating-point variation is not yet measured; that uncertainty is presented
at tolerance finalisation rather than hidden.
