#!/usr/bin/env python3
"""Small packaging self-tests, not EDKit scientific calibration or selfcheck.

Run from any directory with Python 3.11+ and NumPy:
    python3 -B comment/verification/revision-contract-selftest.py

The script imports the 23 small-check validators and exercises their oracle
wiring on a two-component synthetic state. It also exercises run.sh's actual
verify_pins predicate with in-memory Project/Manifest documents. No Julia,
Docker, dependency installation, physical workload, output file, or pipeline
record is produced. These probes do not establish CUDA dependency compatibility,
container reproducibility, calibrated numerical bounds, or a task reward.

The approved adaptive-counter policy is regression-tested in all 23 validator/
oracle pairs: internal work counts and matvec_budget do not gate acceptance,
while total_times_served, cache-array shape statuses and other API outcomes
retain their existing requirements. Synthetic fixture values below are not
physical task inputs or replacement scientific bounds.
"""
from __future__ import annotations

import ast
import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tomllib


# Also remain cache-free if the caller forgets -B. Limit NumPy before import.
sys.dont_write_bytecode = True
for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[variable] = "1"

LEAF = Path(__file__).resolve().parents[2]
CHECKS = LEAF / "tests" / "checks"


def load_toml(path: Path) -> dict:
    with path.open("rb") as stream:
        return tomllib.load(stream)


def contract_caches() -> set[Path]:
    return {
        path
        for directory in ("tests", "solution", "environment", "target")
        for path in (LEAF / directory).rglob("__pycache__")
    }


def import_validator(check: Path):
    spec = importlib.util.spec_from_file_location(
        "revision_selftest_" + check.name.replace("-", "_"),
        check / "validate.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {check.name}/validate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def synthetic_documents() -> tuple[dict, dict, dict]:
    # H = diag(0, 1), psi(0) = (1, 0): psi(t) = (1, 0) exactly.
    # Test-only bounds below belong to this synthetic fixture. No task rubric
    # or input is modified or substituted into a formal grading run.
    case = {
        "id": "synthetic-stationary-state",
        "mode": "single",
        "times": [0.0, 0.5],
        "state_real": [1.0, 0.0],
        "state_imag": [0.0, 0.0],
        "hamiltonian": {"kind": "diagonal", "values": [0.0, 1.0]},
        "expected_statuses": {},
    }
    inputs = {"schema_version": 1, "check": "packaging-synthetic", "cases": [case]}
    result = {
        "schema_version": 1,
        "check": inputs["check"],
        "cases": [{
            "id": case["id"],
            "times": case["times"].copy(),
            "states_real": [[1.0, 0.0], [1.0, 0.0]],
            "states_imag": [[0.0, 0.0], [0.0, 0.0]],
            "statuses": {},
        }],
    }
    scientific = {
        key: value
        for metric in ("state", "l2", "norm", "energy")
        for key, value in ((f"{metric}_atol", 1e-9), (f"{metric}_rtol", 0.0))
    }
    rubric = {
        "policy": "pointwise",
        "comparison": {"atol": 1e-9, "rtol": 0.0, "scientific": scientific},
    }
    return inputs, result, rubric


def validator_probes() -> dict:
    checks = sorted(path for path in CHECKS.iterdir() if (path / "oracle.py").is_file())
    if len(checks) != 23:
        raise RuntimeError(f"expected 23 small-check oracle/validator pairs, found {len(checks)}")
    rows = {}
    for check in checks:
        try:
            validator = import_validator(check)
            inputs, correct, rubric = synthetic_documents()
            wrong = copy.deepcopy(correct)
            wrong["cases"][0]["states_real"][1][0] = 0.9
            pair = validator.pair_evaluate(correct, correct, inputs, inputs, rubric)
            oracle = validator.oracle_evaluate(check, inputs, correct, rubric)
            negative = validator.oracle_evaluate(check, inputs, wrong, rubric)
            row = {
                "imported": True,
                "correct_pair_passed": pair["passed"] is True,
                "correct_oracle_passed": oracle["passed"] is True,
                "corrupted_state_oracle_rejected": negative["passed"] is False,
                "negative_reason": negative.get("reason", ""),
            }
            row["passed"] = all(row[key] for key in (
                "imported", "correct_pair_passed", "correct_oracle_passed",
                "corrupted_state_oracle_rejected",
            ))
        except Exception as exc:
            row = {"passed": False, "reason": f"{type(exc).__name__}: {exc}"}
        rows[check.name] = row
    return {"passed": all(row["passed"] for row in rows.values()), "count": len(rows), "checks": rows}


def pin_probes() -> dict:
    check = CHECKS / "long-interval-restart"
    source = (check / "run.sh").read_text(encoding="utf-8")
    # Execute the actual embedded predicate, replacing only its disk loader
    # with an in-memory document lookup. No shell or Julia is invoked.
    function = source.split("verify_pins() {", 1)[1]
    predicate = function.split("<<'PY'\n", 1)[1].split("\nPY\n", 1)[0]
    syntax = ast.parse(predicate, filename="run.sh:verify_pins")
    loaders = [node for node in syntax.body if isinstance(node, ast.FunctionDef) and node.name == "load"]
    if len(loaders) != 1:
        raise RuntimeError("verify_pins no longer has the expected single load helper")
    syntax.body = [node for node in syntax.body if node is not loaders[0]]
    code = compile(ast.fix_missing_locations(syntax), "run.sh:verify_pins", "exec")
    upstream_project = load_toml(check / "Project.toml")
    upstream_manifest = load_toml(check / "Manifest.toml")
    hash_package = next(
        name for name, entries in upstream_manifest["deps"].items()
        if any("git-tree-sha1" in entry for entry in entries)
    )
    direct_package = next(iter(upstream_project["deps"]))

    def trial(name: str, expected_exit: int) -> dict:
        project, manifest = copy.deepcopy(upstream_project), copy.deepcopy(upstream_manifest)
        if name == "additional_synthetic_direct_package":
            uuid = "ffffffff-ffff-ffff-ffff-ffffffffffff"
            project["deps"]["SyntheticGPU"] = uuid
            manifest["deps"]["SyntheticGPU"] = [{
                "uuid": uuid, "version": "1.0.0", "git-tree-sha1": "f" * 40,
            }]
        elif name == "upstream_hash_drift":
            for entry in manifest["deps"][hash_package]:
                if "git-tree-sha1" in entry:
                    entry["git-tree-sha1"] = "0" * 40
        elif name == "removed_upstream_direct_dependency":
            project["deps"].pop(direct_package)
        elif name != "unchanged_upstream_pins":
            raise ValueError(f"unknown pin probe {name}")
        documents = {
            "/pinned/Project.toml": upstream_project,
            "/pinned/Manifest.toml": upstream_manifest,
            "/candidate/Project.toml": project,
            "/candidate/Manifest.toml": manifest,
        }
        namespace = {"load": lambda path: copy.deepcopy(documents[str(path)])}
        stdout, stderr = io.StringIO(), io.StringIO()
        previous_argv = sys.argv
        exit_code = 0
        try:
            sys.argv = ["verify_pins", "/pinned", "/candidate"]
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exec(code, namespace)
        except SystemExit as exc:
            exit_code = exc.code
        finally:
            sys.argv = previous_argv
        return {
            "passed": exit_code == expected_exit,
            "exit_code": exit_code,
            "expected_exit_code": expected_exit,
            "reason": stderr.getvalue().strip() or "pin inclusion predicate accepted",
        }

    rows = {
        name: trial(name, status)
        for name, status in (
            ("unchanged_upstream_pins", 0),
            ("additional_synthetic_direct_package", 0),
            ("upstream_hash_drift", 2),
            ("removed_upstream_direct_dependency", 2),
        )
    }
    return {
        "passed": all(row["passed"] for row in rows.values()),
        "scope": "pin inclusion predicate only; no Pkg resolution or GPU package loading",
        "cases": rows,
    }


def counter_policy_probe() -> dict:
    checks = sorted(path for path in CHECKS.iterdir() if (path / "oracle.py").is_file())
    if len(checks) != 23:
        raise RuntimeError(f"expected 23 counter-policy validator/oracle pairs, found {len(checks)}")
    counters = ("basis_builds", "basis_extensions", "restarts", "matvecs", "max_dim_used")
    trials = (
        ("unchanged_requirements", True),
        ("missing_internal_counts", True),
        ("changed_internal_counts", True),
        ("missing_matvec_budget", True),
        ("failed_matvec_budget", True),
        ("missing_counts_and_matvec_budget", True),
        ("wrong_total_times_served", False),
        ("missing_total_times_served", False),
        ("wrong_reduced_phase_length", False),
        ("missing_reduced_phase_length", False),
        ("wrong_reduced_coeffs_length", False),
        ("missing_reduced_coeffs_length", False),
        ("wrong_api_outcome", False),
        ("missing_api_outcome", False),
        ("unexpected_api_status", False),
    )
    rows = {}
    for check in checks:
        validator = import_validator(check)
        inputs, correct, rubric = synthetic_documents()
        inputs["cases"][0]["diagnostic_requirements"] = {
            key: {"eq": 1} for key in counters
        }
        inputs["cases"][0]["diagnostic_requirements"]["total_times_served"] = {"eq": 2}
        inputs["cases"][0]["expected_statuses"] = {
            "matvec_budget": "pass",
            "reduced_phase_length": "pass",
            "reduced_coeffs_length": "pass",
            "negative_single": "ArgumentError",
        }
        correct["cases"][0]["diagnostics"] = {key: 1 for key in counters}
        correct["cases"][0]["diagnostics"]["total_times_served"] = 2
        correct["cases"][0]["statuses"] = copy.deepcopy(inputs["cases"][0]["expected_statuses"])
        probes = {}
        for name, expected_pass in trials:
            candidate = copy.deepcopy(correct)
            actual = candidate["cases"][0]
            if name in ("missing_internal_counts", "missing_counts_and_matvec_budget"):
                for key in counters:
                    actual["diagnostics"].pop(key)
            if name == "changed_internal_counts":
                actual["diagnostics"].update({key: 999 for key in counters})
            if name in ("missing_matvec_budget", "missing_counts_and_matvec_budget"):
                actual["statuses"].pop("matvec_budget")
            elif name == "failed_matvec_budget":
                actual["statuses"]["matvec_budget"] = "fail"
            elif name == "wrong_total_times_served":
                actual["diagnostics"]["total_times_served"] = 99
            elif name == "missing_total_times_served":
                actual["diagnostics"].pop("total_times_served")
            elif name.startswith("wrong_reduced_"):
                actual["statuses"][name.removeprefix("wrong_")] = "fail"
            elif name.startswith("missing_reduced_"):
                actual["statuses"].pop(name.removeprefix("missing_"))
            elif name == "wrong_api_outcome":
                actual["statuses"]["negative_single"] = "no_exception"
            elif name == "missing_api_outcome":
                actual["statuses"].pop("negative_single")
            elif name == "unexpected_api_status":
                actual["statuses"]["undeclared_api_status"] = "pass"
            try:
                pair = validator.pair_evaluate(correct, candidate, inputs, inputs, rubric)
                pair_passed, pair_reason = pair["passed"] is True, pair.get("reason", "")
            except ValueError as exc:
                pair_passed, pair_reason = False, str(exc)
            oracle = validator.oracle_evaluate(check, inputs, candidate, rubric)
            oracle_passed = oracle["passed"] is True
            probes[name] = {
                "passed": pair_passed == expected_pass and oracle_passed == expected_pass,
                "expected_acceptance": expected_pass,
                "pair_accepted": pair_passed,
                "oracle_accepted": oracle_passed,
                "pair_reason": pair_reason,
                "oracle_reason": oracle.get("reason", ""),
            }
        rows[check.name] = {
            "passed": all(probe["passed"] for probe in probes.values()),
            "cases": probes,
        }
    return {
        "passed": all(row["passed"] for row in rows.values()),
        "status": "approved_policy_regression",
        "counts_toward_selftest_pass": True,
        "fixture": "exact stationary two-component state with synthetic bookkeeping and API requirements",
        "count": len(rows),
        "probes_per_check": len(trials),
        "checks": rows,
        "note": "Policy regression only; task inputs, numerical bounds and scientific verification records remain untouched.",
    }


def main() -> int:
    before = contract_caches()
    report = {
        "schema_version": 1,
        "kind": "packaging_synthetic_selftest",
        "not_scientific_calibration": True,
        "python_version": sys.version.split()[0],
    }
    try:
        report["validator_wiring"] = validator_probes()
        report["pin_inclusion"] = pin_probes()
        report["adaptive_counter_policy"] = counter_policy_probe()
        report["passed"] = all(report[key]["passed"] for key in (
            "validator_wiring", "pin_inclusion", "adaptive_counter_policy",
        ))
    except Exception as exc:
        report.update(passed=False, reason=f"{type(exc).__name__}: {exc}")
    added = contract_caches() - before
    report["new_contract_cache_directories"] = sorted(str(path.relative_to(LEAF)) for path in added)
    if added:
        report["passed"] = False
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
