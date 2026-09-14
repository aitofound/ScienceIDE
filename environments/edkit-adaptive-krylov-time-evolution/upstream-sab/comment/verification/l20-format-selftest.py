#!/usr/bin/env python3
"""Small synthetic regression tests for the L20 binary-format validator.

Run with a Python 3.11+ interpreter that has NumPy installed:
    python3 -B comment/verification/l20-format-selftest.py

The current validator is copied into a temporary check directory with synthetic
L=2 inputs. No scientific input, rubric, source file, or recorded result is
changed. This exercises Python format/pointwise-policy handling only: it does
not run Julia, exercise the Julia writer, validate L20 physics, measure noise,
or establish that a GPU implementation meets the candidate tolerance.
"""
from __future__ import annotations

import json
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path


CHECK = "xxz-quench-full-basis-l20"
STATES = [
    1 + 0j, 0.5 - 0.25j, 0j, -0.75 + 0.125j,
    0.2 + 0.3j, -0.4 + 0.5j, 0.6 - 0.7j, 0j,
]
THREAD_VARS = ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")


def binary_states(states: list[complex], endian: str = "<") -> bytes:
    parts = [part for z in states for part in (z.real, z.imag)]
    return struct.pack(endian + "d" * len(parts), *parts)


def write_run(root: Path, states: list[complex] | None = None, mode: str = "nominal") -> None:
    root.mkdir()
    (root / "run.ok").write_text(f"ic={mode}\n", encoding="utf-8")
    (root / "result.toml").write_text(
        f'schema_version = 1\ncheck = "{CHECK}"\ncase = "synthetic"\n'
        'dimension = 4\ntimes = [0.5, 1.0]\nstates_file = "states.bin"\n',
        encoding="utf-8",
    )
    (root / "states.bin").write_bytes(binary_states(STATES if states is None else states))


def replace_metadata(root: Path, old: str, new: str) -> None:
    path = root / "result.toml"
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise AssertionError(f"fixture metadata target not found: {old}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def main() -> int:
    leaf = Path(__file__).resolve().parents[2]
    source = leaf / "tests" / "checks" / CHECK / "validate.py"
    reports = []
    with tempfile.TemporaryDirectory(prefix="edkit-l20-format-") as scratch:
        root = Path(scratch)
        check = root / "check"
        check.mkdir()
        validator = check / "validate.py"
        shutil.copyfile(source, validator)
        fixture = (
            f'schema_version = 1\ncheck = "{CHECK}"\n'
            '[[cases]]\nid = "synthetic"\ntimes = [0.5, 1.0]\n'
            '[cases.hamiltonian]\nL = 2\n'
        )
        for mode in ("nominal", "variant"):
            folder = check / "ic" / mode
            folder.mkdir(parents=True)
            (folder / "input.toml").write_text(fixture, encoding="utf-8")
        rubric = root / "rubric.json"
        rubric.write_text(json.dumps({"policy": "pointwise", "comparison": {"atol": 1e-9, "rtol": 0.0}}), encoding="utf-8")
        reference = root / "reference"
        write_run(reference)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", SAB_TIME_SCALE="1.0")

        def run_case(name, expected_pass, mutate=None, *, mode="nominal", reason_contains=None, expected_distance=None):
            candidate = root / name
            write_run(candidate, mode=mode)
            if mutate:
                mutate(candidate)
            output = root / f"{name}.json"
            process = subprocess.run(
                [sys.executable, "-B", str(validator), "--reference", str(reference),
                 "--candidate", str(candidate), "--rubric", str(rubric), "--out", str(output)],
                env=env, capture_output=True, text=True, timeout=30,
            )
            if process.returncode != 0:
                raise AssertionError(f"{name}: validator crashed: {process.stderr}")
            report = json.loads(output.read_text(encoding="utf-8"))
            if report["passed"] is not expected_pass:
                raise AssertionError(f"{name}: unexpected decision {report}")
            if reason_contains and reason_contains not in report["reason"]:
                raise AssertionError(f"{name}: wrong rejection reason {report}")
            if expected_distance is not None and not math.isclose(report["distance"], expected_distance, rel_tol=1e-14, abs_tol=0):
                raise AssertionError(f"{name}: wrong distance {report}")
            reports.append({"test": name, "expected_pass": expected_pass, "observed_pass": report["passed"], "reason": report["reason"]})

        def changed_amplitude(delta):
            def mutate(candidate):
                values = list(STATES)
                values[2] = delta
                (candidate / "states.bin").write_bytes(binary_states(values))
            return mutate

        run_case("identical", True, expected_distance=0.0)
        run_case("variant-marker", True, mode="variant")
        run_case("altbuild-marker", True, mode="altbuild")
        run_case("below-atol", True, changed_amplitude(0.5e-9 + 0j), expected_distance=0.5e-9)
        run_case("exactly-atol", True, changed_amplitude(1e-9 + 0j), expected_distance=1e-9)
        run_case("above-atol", False, changed_amplitude(2e-9 + 0j), reason_contains="exceed the pair bound", expected_distance=2e-9)
        run_case("complex-magnitude-over-atol", False, changed_amplitude(0.8e-9 + 0.8e-9j), reason_contains="exceed the pair bound")
        for tail_size in (1, 7, 8):
            run_case(f"trailing-{tail_size}-bytes", False,
                     lambda candidate, n=tail_size: (candidate / "states.bin").write_bytes(binary_states(STATES) + b"\0" * n),
                     reason_contains="bytes, expected 128")
        run_case("truncated", False, lambda candidate: (candidate / "states.bin").write_bytes(binary_states(STATES)[:-8]), reason_contains="bytes, expected 128")
        run_case("float32-payload", False,
                 lambda candidate: (candidate / "states.bin").write_bytes(struct.pack("<16f", *[p for z in STATES for p in (z.real, z.imag)])),
                 reason_contains="bytes, expected 128")
        run_case("big-endian-payload", False, lambda candidate: (candidate / "states.bin").write_bytes(binary_states(STATES, ">")))
        run_case("nan-amplitude", False, changed_amplitude(complex(float("nan"), 0)), reason_contains="non-finite amplitude")
        run_case("inf-amplitude", False, changed_amplitude(complex(float("inf"), 0)), reason_contains="non-finite amplitude")
        run_case("wrong-times", False, lambda candidate: replace_metadata(candidate, "[0.5, 1.0]", "[0.5, 1.5]"), reason_contains="output times differ")
        run_case("wrong-dimension", False, lambda candidate: replace_metadata(candidate, "dimension = 4", "dimension = 8"), reason_contains="result dimension")
        run_case("noninteger-dimension", False, lambda candidate: replace_metadata(candidate, "dimension = 4", "dimension = 4.0"), reason_contains="result dimension")
        run_case("boolean-schema-version", False, lambda candidate: replace_metadata(candidate, "schema_version = 1", "schema_version = true"), reason_contains="schema_version must be 1")
        run_case("relative-escape", False, lambda candidate: replace_metadata(candidate, 'states_file = "states.bin"', 'states_file = "../reference/states.bin"'), reason_contains="fixed filename states.bin")
        run_case("absolute-escape", False, lambda candidate: replace_metadata(candidate, 'states_file = "states.bin"', f"states_file = {json.dumps(str(reference / 'states.bin'))}"), reason_contains="fixed filename states.bin")

        def external_symlink(candidate):
            (candidate / "states.bin").unlink()
            (candidate / "states.bin").symlink_to(reference / "states.bin")

        run_case("symlink-escape", False, external_symlink, reason_contains="not a symlink")
        run_case("missing-payload", False, lambda candidate: (candidate / "states.bin").unlink(), reason_contains="regular file")

        thread_probe = (
            "import importlib.util,os,sys; "
            "s=importlib.util.spec_from_file_location('l20_format_validator',sys.argv[1]); "
            "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
            "assert all(os.environ[k]=='1' for k in " + repr(THREAD_VARS) + ")"
        )
        thread_env = dict(env, **{name: "8" for name in THREAD_VARS})
        subprocess.run([sys.executable, "-B", "-c", thread_probe, str(validator)], env=thread_env, check=True, timeout=30)
        if list(root.rglob("__pycache__")):
            raise AssertionError("synthetic test unexpectedly created a bytecode cache")

    print(json.dumps({"passed": True, "validator_cases": len(reports), "single_thread_environment": "passed",
                      "scope": "synthetic Python format and pointwise-policy regression only; no Julia writer or L20 physics execution",
                      "cases": reports}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
