"""NEST noble-element microphysics repair ladder over exact upstream SAB validators."""

import argparse
import json
import math
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import traceback

CHECKS = ["lar-mean-yields"]  # specialised per task by the compiler


def zero(check, reason, outcome="nonconforming"):
    return dict(check=check, passed=False, validator_passed=False,
                outcome=outcome, score=0.0, value=0.0, reason=reason)


def delivery_file(root, relative):
    """Only regular files inside the delivery may reach a validator."""
    root = Path(root)
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("output path escapes delivery")
    path = root
    for part in ("", *relative.parts):
        path = path / part
        if path.is_symlink():
            raise ValueError("symlink in output path: " + str(relative))
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError("output is not a regular file: " + str(relative))
    return path


def read_delivery_json(root, relative, warnings):
    path = delivery_file(root, relative)
    # Bound parsing of untrusted metadata, including deeply nested JSON.
    with path.open("rb") as handle:
        data = handle.read(1024 * 1024 + 1)
    if len(data) > 1024 * 1024:
        raise ValueError("status/manifest exceeds 1 MiB")

    def last_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                warnings.append(f"{relative}: duplicate JSON key {key!r}; kept last")
            result[key] = value
        return result

    return json.loads(data, object_pairs_hook=last_keys)


def status_entries(entries, warnings, source):
    if not isinstance(entries, list):
        raise ValueError("check statuses must be a list")
    statuses = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("check"), str) or not entry["check"]:
            raise ValueError("each check status must be an object with a check name")
        check = entry["check"]
        if check in statuses:
            warnings.append(f"{source}: duplicate check {check!r}; kept last")
        statuses[check] = entry
    return statuses


def load_delivery(candidate, checks):
    """Accept raw rowtool output, a check manifest, or a Harbor export.

    A check manifest is {"checks": [{"check": ..., "status": ..., "exit": ...}]}.
    A bare list of those records is also accepted. When present it is
    authoritative; otherwise read only <check>/_run_status.json. Extra files
    (including old experiment statuses) never become submitted checks.
    """
    root = Path(candidate)
    protocol = dict(layout="direct", warnings=[], errors=[])
    if root.is_symlink():
        protocol["errors"].append("candidate root is a symlink")
        return root, {}, protocol
    statuses = None
    # One Harbor export wrapper plus an optional manifest in its payload.
    for depth in range(2):
        if not os.path.lexists(root / "manifest.json"):
            break
        try:
            manifest = read_delivery_json(root, "manifest.json", protocol["warnings"])
            if isinstance(manifest, dict):
                entries = manifest.get("checks")
            elif isinstance(manifest, list):
                if manifest and isinstance(manifest[0], dict) and "source" in manifest[0]:
                    if depth:
                        raise ValueError("nested Harbor export")
                    exports = {}
                    for entry in manifest:
                        if (not isinstance(entry, dict) or
                                not all(isinstance(entry.get(k), str) for k in
                                        ("source", "destination", "type", "status"))):
                            raise ValueError("invalid Harbor export entry")
                        source = entry["source"]
                        if source in exports:
                            protocol["warnings"].append(f"duplicate export {source!r}; kept last")
                        exports[source] = entry
                    selected = exports.get("/logs/artifacts")
                    if not selected:
                        raise ValueError("Harbor manifest has no /logs/artifacts delivery")
                    if selected["type"] != "directory" or selected["destination"] != "artifacts/logs/artifacts":
                        raise ValueError("invalid /logs/artifacts export destination/type")
                    if selected["status"] != "ok":
                        raise ValueError("export status is not ok: " + selected["status"])
                    if (root / "logs").is_symlink() or (root / "logs/artifacts").is_symlink():
                        raise ValueError("symlink in Harbor export path")
                    protocol["layout"] = "harbor-export"
                    root = root / "logs/artifacts"
                    continue
                entries = manifest
            else:
                raise ValueError("manifest must be an object or a list")
            statuses = status_entries(entries, protocol["warnings"], "manifest.json")
            break
        except (OSError, ValueError, RecursionError) as exc:
            protocol["errors"].append("malformed manifest: " + str(exc))
            return root, {}, protocol
    if statuses is None:
        statuses = {}
        for check in checks:
            relative = Path(check) / "_run_status.json"
            if not os.path.lexists(root / relative):
                continue
            try:
                value = read_delivery_json(root, relative, protocol["warnings"])
                entries = value if isinstance(value, list) else [value]
                records = status_entries(entries, protocol["warnings"], str(relative))
                statuses[check] = records.get(check, {"error": "status check name mismatch"})
                for name in records.keys() - {check}:
                    protocol["warnings"].append(f"{relative}: ignored unknown check {name!r}")
            except (OSError, ValueError, RecursionError) as exc:
                statuses[check] = {"error": "malformed check status: " + str(exc)}
    for name in statuses.keys() - set(checks):
        protocol["warnings"].append(f"ignored unknown check {name!r}")
    return root, statuses, protocol


def status_reason(status, raw=False):
    if status is None:
        return "missing check status"
    if "error" in status:
        return "invalid check status: " + repr(status["error"])
    state = status.get("status")
    if state not in ("ok", "failed"):
        return "unknown check status: " + repr(state)
    code = status.get("exit")
    ordinary_crash = (raw and state == "failed" and status.get("build") == "ok"
                      and type(code) is int and code not in (0, 124))
    if not ordinary_crash and (state != "ok" or type(code) is not int or code != 0):
        return "check did not complete successfully: status=" + repr(state) + ", exit=" + repr(code)
    return None


def output_specs(checks_dir, check):
    with open(os.path.join(checks_dir, check, "rubric.json"), encoding="utf-8") as handle:
        comparison = json.load(handle)["comparison"]
    return comparison.get("files") or [dict(path=name) for name in sorted(
        {spec["file"] for spec in comparison["invariants"]})]


def check_table(root, spec):
    path = delivery_file(root, spec["path"])
    rows = [line.split() for line in path.read_text(encoding="utf-8").splitlines()[spec.get("skip_rows", 0):]
            if line.strip() and not line.lstrip().startswith("#")]
    if not rows or not all(math.isfinite(float(x)) for row in rows for x in row):
        raise ValueError("empty or non-finite table: " + spec["path"])


def grade_check(checks_dir, check, ref_dir, cand_dir):
    if not os.path.isdir(ref_dir) or not os.path.isfile(os.path.join(ref_dir, "run.ok")):
        raise RuntimeError(f"reference output missing for {check}")
    if not cand_dir or not os.path.isdir(cand_dir) or not os.path.isfile(
            os.path.join(cand_dir, "run.ok")):
        return zero(check, "missing check output or run.ok", "no_output")
    try:
        delivery_file(cand_dir, "run.ok")
        # Reject unreadable/non-finite tables before the unchanged validator.
        for spec in output_specs(checks_dir, check):
            check_table(cand_dir, spec)
    except (OSError, ValueError, RecursionError) as exc:
        return zero(check, "invalid check output: " + str(exc))
    detail = {"check": check, "passed": False, "validator_passed": False}
    check_dir = os.path.join(checks_dir, check)
    with tempfile.TemporaryDirectory(prefix="nest-grade-") as scratch:
        out = os.path.join(scratch, "result.json")
        proc = subprocess.run(
            [sys.executable, "-B", "-s", "-E", "validate.py",
             "--reference", ref_dir, "--candidate", cand_dir,
             "--rubric", "rubric.json", "--out", out],
            cwd=check_dir, capture_output=True, text=True,
            env={"PATH": os.environ.get("PATH", ""), "LANG": "C.UTF-8"})
        if proc.returncode or not os.path.isfile(out):
            raise RuntimeError(f"validator failed for {check}: " +
                               (proc.stderr or proc.stdout)[-500:])
        result = json.load(open(out, encoding="utf-8"))
    passed = result.get("passed") is True
    score = 1.0 if passed else 0.5
    value = result.get("bound_fraction", result.get("distance", 0.0 if passed else 1.0))
    detail.update(result)
    detail.update(passed=passed, validator_passed=passed,
                  outcome="passed" if passed else "diverged",
                  score=score, value=float(value or 0.0))
    return detail


def grade_all(candidate, reference, checks_dir, checks=None, raw=True, protocol=None):
    checks = list(checks or CHECKS)
    try:
        candidate, statuses, delivery = load_delivery(candidate, checks)
    except (OSError, ValueError, RecursionError) as exc:
        statuses = {}
        delivery = dict(layout="direct", warnings=[], errors=["unreadable delivery: " + str(exc)])
    if protocol is not None:
        protocol.update(delivery)
    scores, rewards, details, all_passed = [], {}, [], True
    for check in checks:
        # Reference assets belong to the verifier, even for an empty delivery.
        for path in (Path(reference) / check / "run.ok",
                     Path(checks_dir) / check / "validate.py", Path(checks_dir) / check / "rubric.json"):
            if not path.is_file():
                raise RuntimeError("verifier reference/validator missing: " + str(path))
        for spec in output_specs(checks_dir, check):
            check_table(Path(reference) / check, spec)
        reason = "; ".join(delivery["errors"]) or status_reason(statuses.get(check), raw)
        if reason:
            detail = zero(check, reason)
        else:
            detail = grade_check(checks_dir, check, os.path.join(reference, check),
                                 os.path.join(candidate, check))
        details.append(detail)
        scores.append(detail["score"])
        rewards["check_" + check.replace("-", "_")] = detail["score"]
        all_passed = all_passed and detail.get("validator_passed", False)
    reward = round(sum(scores) / len(scores), 6) if scores else 0.0
    rewards_out = {"reward": reward, "equivalence_pass": int(all_passed), "grader_error": 0,
                   "nonconforming": int(any(d["outcome"] == "nonconforming" or
                                             (d["outcome"] == "no_output" and not raw) for d in details))}
    rewards_out.update(rewards)
    return rewards_out, details


def evaluate(args):
    protocol = {}
    rewards_out, details = grade_all(args.candidate, args.reference, args.checks_dir,
                                     raw=args.raw_floor_measurement, protocol=protocol)
    if not args.raw_floor_measurement:
        path = args.floor_file or os.path.join(os.path.dirname(os.path.abspath(__file__)), "floor.json")
        with open(path, encoding="utf-8") as handle:
            floor = json.load(handle)["floor"]
        if type(floor) not in (int, float) or not math.isfinite(floor) or not 0.0 <= floor < 1.0:
            raise ValueError(f"invalid measured floor {floor}")
        rewards_out["floor"] = floor
        rewards_out["reward_repair"] = round(max(0.0, rewards_out["reward"] - floor) / (1.0 - floor), 6)
        rewards_out["speedup"] = 0.0
    return rewards_out, details, protocol


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--checks-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--floor-file", help="verifier-owned floor file (defaults to adjacent floor.json)")
    parser.add_argument("--raw-floor-measurement", action="store_true")
    args = parser.parse_args()
    code = 0
    try:
        rewards_out, details, protocol = evaluate(args)
    except Exception as exc:
        # Delivery parse/validation failures are handled above. Reaching here
        # means trusted assets, the validator process, or the verifier failed.
        traceback.print_exc()
        code = 1
        rewards_out = dict(reward=0.0, reward_repair=0.0, equivalence_pass=0, grader_error=1)
        rewards_out.update({"check_" + check.replace("-", "_"): 0.0 for check in CHECKS})
        details = [zero(check, str(exc), "grader_error") for check in CHECKS]
        protocol = dict(errors=["verifier fault: " + str(exc)], warnings=[])
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
    json.dump(rewards_out, open(args.out, "w", encoding="utf-8"), indent=1, sort_keys=True)
    json.dump({"rewards": rewards_out, "checks": details, "protocol": protocol},
              open(args.report, "w", encoding="utf-8"), indent=1, sort_keys=True)
    print(json.dumps(rewards_out, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
