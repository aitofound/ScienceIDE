# Reviewer verification helpers

These files are hidden reviewer/authoring helpers under `comment/`. They are
not installed in the solver image and are not runtime dependencies of any
graded check. They do not replace Docker self-validation or finalize a
scientific tolerance.

## Minimal restart implementation controls

[Restart control results](restart-controls-v1.md) and the
[scalar evidence](restart-controls-v1.json) record the separate approved
nominal-only follow-up: baseline, a correct projected-exponential evaluation,
and one stale-anchor implementation fault, each executing the existing
`long-grid` and `nonunit-restart` cases. Both positive versions passed the
unchanged policy; the negative version completed finite trajectories and was
rejected by state/L2 errors, not by a crash or by norm/energy drift. Fixed
upstream source and all graded files remained unchanged. The source-copy
patches, runner and raw outputs remain in the external authoring workspace.
This is neither an exhaustive mutation campaign nor a final selfcheck.

## Checking machinery and input generation

`test_oracle.py` loads the shipped `oracle.py` and `validate.py` from the
`operator-dense-reference` check using `importlib`; it does not use a second
private copy of either policy. The 25 small offline tests cover fault rejection
and positive controls: wrong evolution sign despite conserved norm and energy,
global phase, accidental normalization, nonfinite or incomplete output,
independent Hamiltonian construction, API outcomes, rubric-owned bounds and
trusted time-window overrides. These are tests of the checking machinery,
not 25 additional graded task checks. Their synthetic test bounds are local
unit-test settings, not the final task tolerances.

From the task directory, use Python 3.11 or newer with NumPy installed:

```sh
VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 SAB_TIME_SCALE=1.0 \
  python3 -B comment/verification/test_oracle.py -v
```

`generate_fixtures.jl` regenerates the declarative input fixtures and their
provenance manifest. It preserves the documented RNG sequence, initial-state
construction and two-ULP perturbations. It uses EDKit to construct selected
bases and initial states, but never calls `timeevolve` or another evolution
solver and never produces reference evolution answers.

Configure your own Julia 1.10 environment containing EDKit v0.5.0 at commit
`538fce882ab73e3af447f4bc6a1704d290c88aba` and compatible locked dependencies.
The original fixtures were generated with Julia 1.10.12; use that patch version
when checking byte-for-byte regeneration. The upstream root Manifest was
generated with Julia 1.12.5, so activate a compatible external environment
instead of assuming that Manifest is suitable for Julia 1.10. No machine-local
environment path is embedded in this helper.

The generator requires an explicit scratch directory outside this task. Its
parent must already exist; the destination may be absent or an empty real
directory. It rejects a populated destination, a symbolic-link destination,
and any path inside the task. For example, from the task directory:

```sh
EDKIT_FIXTURE_SCRATCH=$(mktemp -d)
julia --project=/absolute/path/to/your/edkit-environment \
  comment/verification/generate_fixtures.jl "$EDKIT_FIXTURE_SCRATCH"
```

Inspect and compare the scratch files before proposing any change to the
shipped inputs. Regeneration does not modify `tests/`, the rubrics or pipeline
records, and does not constitute a solver/verifier run.
