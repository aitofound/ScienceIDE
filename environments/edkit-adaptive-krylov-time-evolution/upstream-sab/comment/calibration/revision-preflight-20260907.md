# Revision minimal preflight — 2026-09-07

The two selected checks completed nominal (`-O2`) and alternative-build
(`-O0`, same nominal input) runs successfully. All four output validations
passed. This is a bounded packaging preflight, **not a 24-check calibration,
perturbation test, or official selfcheck/reward record**.

## Environment and scope

- Local Apple Silicon, native Linux/ARM64 Docker, Julia 1.12.5.
- Each test container: 2 CPUs, 4 GiB memory, no extra swap, network disabled;
  Julia compute/interactive threads 1/0 and BLAS 1, verified in each run.
- Host Python/NumPy validators used one BLAS/OMP thread. They ran outside the
  container's 4 GiB memory limit.
- Two independent image tags were built from unchanged Dockerfiles, using
  the existing build cache. Build-time networking was permitted.
- Each run loaded EDKit from its own scratch source copy; the runtime source
  path and unchanged upstream Project/Manifest hashes were verified.
- Source, task, and prior validation files were byte-identical before/after
  execution. This explanatory note and its README link were added afterward;
  no runtime file or numerical bound was changed after the preflight.

## Measurements

| Check | Build mode | Complete container run (s) | Source preparation within run (s) | Maximum sampled memory (MiB) | Validation |
| --- | --- | ---: | ---: | ---: | --- |
| doc-matrix-free-operator | nominal / -O2 | 17.022 | 7.429 | 1247.232 | pass |
| doc-matrix-free-operator | altbuild / -O0 | 13.123 | 7.159 | 854.500 | pass |
| xxz-quench-full-basis-l20 | nominal / -O2 | 48.724 | 7.674 | 1270.784 | pass |
| xxz-quench-full-basis-l20 | altbuild / -O0 | 131.842 | 6.820 | 1248.256 | pass |

Container times include startup, source preparation and first-use JIT; they
are not pure solver timings. Memory values are maxima of Docker stats samples,
not exact peak measurements. All four container exit codes were zero, with
`OOMKilled=false`.

One complete preflight took **267.622 seconds** out of a 1200-second ceiling.
This includes Docker startup (ready around 41.76 s), both cached image builds
(5.297 s + 1.078 s), the four complete container runs (210.711 s total), four
host validations (7.771 s total), and snapshot/inspection/report overhead.
No individual run reached its 180/180/300/600-second cap.

## Numerical evidence and its meaning

For `doc-matrix-free-operator`, both builds passed the independently constructed
dense-ED reference gates. Across its 21 requested times (dimension 1024),
maximum complex-component error was `2.967584103602404e-15` and maximum full-state
L2 error was `9.133545068743845e-15`, each against the unchanged `1e-9` cap.
Norm error was `6.661338147750939e-16`; normalized-energy error was
`6.661338744203279e-15`. The -O2/-O0 complex-state distance was exactly zero.

For `xxz-quench-full-basis-l20`, both runs produced the required binary output;
the nominal/altbuild comparison checked all 4,194,304 complex values and found
zero differing amplitudes against the unchanged `1e-9` pair cap. This exercised
the actual Julia little-endian writer and Python reader. L20 has **no independent
dense oracle**: nominal self-comparison verifies output validity, and the build
comparison verifies consistency with the same pinned implementation, not its
independent scientific accuracy.

The measured build difference being zero does not establish a universal zero
error floor, cross-platform agreement, or equivalence of other implementations.
No variant input, GPU dependency installation, x86_64 execution, or GPU execution
was performed in this preflight. The full 24-check calibration and final
selfcheck remain outstanding; historical 23-check records are unchanged.

## Packaging regression checks

The diagnostic-only work-count policy was exercised with synthetic inputs in
all 23 small-check validator/oracle pairs (15 counter/API probes per pair),
alongside correct/wrong-state oracle controls and four dependency-pin probes.
Missing/changed adaptive counts and matvec_budget did not reject otherwise
valid results; wrong/missing API and output-count requirements still did.
The separate L20 format regression passed 23 synthetic cases. These tests
exercise packaging logic and do not substitute for physical calibration.

Task lint reported 24 checks and zero warnings; registry generation/check,
repository validation, vendored-pipeline integrity, Harbor schema validation
and whitespace checks passed. Numerical comparison policies, fixtures,
dependency locks, Dockerfiles, and upstream code were unchanged relative to
the curator's revision.

## Local detailed evidence

The standalone controller and its immutable task/source snapshot, execution
record, four raw produce outputs, validator JSON, image identities and Docker
resource samples are retained outside the repository at:

`/Users/gaoqucheng/Documents/Codex_my/202609_GPU_work/preflight-revision.lIOqSn72/`

The controller stages an unchanged test.sh with exactly one unchanged check;
the original produce driver writes each run.ok. It does not fabricate a pipeline
record. Original images and records were not overwritten or deleted.
