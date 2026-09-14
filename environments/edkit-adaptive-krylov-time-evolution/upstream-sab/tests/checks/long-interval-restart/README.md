# long-interval-restart

Adaptive basis-build, extension, restart and matvec work counts (including
matvec_budget) are diagnostic-only under pipeline 5.11.3. Frozen fixture
requirements document upstream coverage, not candidate pass conditions.
The numerical bounds and public API requirements are unchanged.

Status: acceptance policy and auxiliary gates finalized by the curator after
calibration, with their existing values retained. Packaging review remains pending.

## Upstream origin and scope

EDKit v0.5.0, commit `538fce882ab73e3af447f4bc6a1704d290c88aba`,
`test/timeevolve_tests.jl`: Adaptive Krylov Time Evolution / Restart happens on a long interval.
The solver and original tests are upstream work. This contribution packages
the environment, freezes reproducible inputs and adds independent checks.

Original Julia 1.10 shared Random.seed!(11) draw order preserved across all direct selectors; the wide-spectrum selector resets to 42 as upstream. Inputs frozen in TOML; no runtime random generation. Added controls use copies of existing states and consume no draws.

## Run and output contract

`run.sh nominal` and `run.sh variant` copy read-only `SOURCE_DIR` into an
isolated scratch package and run it with Julia 1.12.5 under the candidate
tree's own `Project.toml` and `Manifest.toml`. The check's copies of the
upstream lock files are the floor: `verify_pins` requires every upstream
direct dependency to remain and every pinned package to resolve at its
pinned version; packages a port adds (a GPU stack, say) must resolve offline
from a depot the tree carries at `.sab-depot/` or from the image depot.
They run offline, with one Julia and one BLAS thread, and write `result.toml`.
The input file specifies all cases, complex initial states, Hamiltonians,
requested times, solver settings, required API outcomes and upstream coverage metadata.
Every output column and complex phase is retained; no phase alignment or
post-normalization is applied except the explicitly tested normalize option.

`run.sh --help` documents `SAB_TIME_SCALE=1.0`. Smaller positive values shorten
the physical horizon for diagnostics only; the verifier uses the trusted
environment setting, never a candidate-supplied time scale. A short window
may not exercise upstream restarts/extensions; those counts are diagnostic-only.
Default grading uses the original complete windows. The discrete API case cannot
meaningfully be shortened. `run.sh altbuild` runs the nominal inputs on the
same source compiled at `julia -O0`; the distance between that build and the
nominal one is the check's measured floor.

## Independent validation and finalized bounds

The bit-action oracle uses physical spin S=sigma/2, periodic bonds, big-endian
tensor coordinates and an independently constructed momentum-zero orbit basis
where applicable. Matrix-input cases use the frozen explicit matrix. The
independent calculation uses full Hermitian diagonalization or analytic
diagonal phases. No generated exact states are included in this package.

The pass policy has two parts, both in `validate.py`: the pointwise pair
comparison of candidate against reference, and a same-input gate that checks
each run's complex state, its L2 error, norm and normalized energy expectation
against an independent dense diagonalisation of that run's own inputs. The density integration additionally checks
trace and the original pure-state/density relation. Declared magnetization is
checked independently. Public API outcomes, total_times_served and cache-array
shape requirements remain mandatory. Adaptive work counts and matvec_budget
are diagnostic-only and do not constrain candidate implementations.

| Case | Pointwise / L2 absolute caps | Norm/trace cap | Normalized energy cap |
| --- | --- | --- | --- |
| long-grid | 1e-06 / 1e-06 | 1e-06 | 2.16e-05 |
| nonunit-restart | 2.5e-06 / 2.5e-06 | 1e-08 | 2.16e-05 |

All relative terms are zero in this policy. Cross-case L2 comparisons use
`1e-10`; declared magnetization uses `1e-9`. These bounds and auxiliary gates
were retained unchanged at human finalization. Source assertions are the
starting constraints, not evidence of measured roundoff. Bounds are case-specific;
one case's cap does not relax any other case.

`distance` and `bound_fraction` report only the complex-state pair
comparison. The same-input gate's metrics are reported under `oracle` in the
verifier's JSON and are never mixed into those two numbers. Norm and energy never substitute for state error.
Build/load duration is printed as `SAB_BUILD_SECONDS`; run time still includes
first-use Julia JIT, so it is not a pure kernel benchmark. Detailed local measurements, when available, are reviewer
notes; only genuine container selfcheck can produce the pipeline record.

## Explicit additions to the official selector

- `nonunit-restart`: Nonunit initial state (complex factor (3+4i)/2, norm 2.5) across forced restarts exposes hidden normalization and anchor-scale loss.

## Physical reference

Anders W. Sandvik, *Computational Studies of Quantum Spin Systems*,
AIP Conf. Proc. 1297, 135 (2010), doi:10.1063/1.3518900, Sections 4.1-4.2:
spin-model matrix construction and finite-precision Lanczos reliability.
The lecture is a model/reliability reference, not a new ground-state task or
an error-bound prescription for this real-time solver.
