"""Pointwise final-state reward ladder for MITgcm biogeochemistry."""

import argparse
import json
import os
import subprocess
import sys
import tempfile

# BEGIN SPECIALISED CHECKS
CHECKS = [
    "global-dic", "so-box-dic", "so-box-obcs-saphe",
    "so-box-calcite-keir", "so-box-calcite-naviaux", "global-bling",
    "cfc-online", "cfc-offline", "ptracer-advection-gyre",
]
# END SPECIALISED CHECKS

W_CONFORM, W_FILES, W_TIME = 0.2, 0.5, 0.3


def _status(directory):
    try:
        return json.load(open(os.path.join(directory, "_run_status.json"),
                              encoding="utf-8"))
    except (OSError, ValueError):
        return {"status": "missing_output"}


def _final_iteration(directory):
    import re
    found = []
    for name in os.listdir(directory) if os.path.isdir(directory) else []:
        match = re.match(r"^[A-Za-z_0-9]+[.](\d{10})[.]data$", name)
        if match:
            found.append(match.group(1))
    return max(found) if found else None


def grade_check(check, candidate_dir, reference_dir, checks_dir):
    status = _status(candidate_dir)
    if status.get("status") != "ok":
        verdict = {"passed": False, "outcome": status.get("status", "no_output"),
                   "error": status.get("tail", "row produced no usable output"),
                   "files_ok": 0, "files_scored": 0,
                   "final_iteration_match": False, "value": None}
        return score(verdict), verdict
    validator = os.path.join(checks_dir, check, "validate.py")
    rubric = os.path.join(checks_dir, check, "rubric.json")
    os.makedirs(candidate_dir, exist_ok=True)
    with tempfile.TemporaryDirectory() as scratch:
        result_path = os.path.join(scratch, "result.json")
        result = subprocess.run(
            [sys.executable, "-B", "-s", "-E", validator,
             "--reference", reference_dir, "--candidate", candidate_dir,
             "--rubric", rubric, "--out", result_path],
            capture_output=True, text=True,
            env={"PATH": os.environ.get("PATH", ""), "LANG": "C.UTF-8"})
        if result.returncode != 0 or not os.path.isfile(result_path):
            verdict = {"passed": False, "outcome": "grader_exception",
                       "error": (result.stdout + result.stderr)[-1000:],
                       "files_ok": 0, "files_scored": 0,
                       "final_iteration_match": False, "value": None}
            return 0.0, verdict
        measured = json.load(open(result_path, encoding="utf-8"))
    ref_it = _final_iteration(reference_dir)
    cand_it = _final_iteration(candidate_dir)
    details = measured.get("files", {})
    files_scored = len(details)
    files_ok = sum(int(item.get("values_over_bound", 1) == 0)
                   for item in details.values())
    time_ok = bool(ref_it and ref_it == cand_it)
    reason = measured.get("reason", "")
    structural = any(token in reason for token in (
        "missing on candidate", "cannot load", "shape", "non-finite",
        "has no <field>", "lacks required"))
    outcome = ("passed" if measured.get("passed") else
               "nonconforming" if structural else
               "time_base" if not time_ok else "diverged")
    verdict = {
        "passed": bool(measured.get("passed")),
        "outcome": outcome,
        "files_ok": files_ok,
        "files_scored": files_scored,
        "final_iteration_match": time_ok,
        "value": measured.get("distance"),
        "worst_file": max(details, key=lambda key: details[key].get("max_abs_error", 0.0),
                          default=None),
        "error": reason,
        "details": details,
    }
    return score(verdict), verdict


def score(verdict):
    outcome = verdict.get("outcome")
    if outcome in ("no_output", "missing_output", "crash", "timeout",
                   "build_failed", "grader_exception"):
        return 0.0
    if outcome == "nonconforming":
        return 0.1
    total = int(verdict.get("files_scored", 0))
    # A row is one end-to-end final state, not a bag of independently useful
    # unit diagnostics.  Do not award most of the reward merely because an
    # unrelated prognostic field stayed unchanged: the final-state component
    # is earned only when every pointwise-graded file passes.
    final_state_ok = total > 0 and int(verdict.get("files_ok", 0)) == total
    value = W_CONFORM + W_FILES * int(final_state_ok)
    if verdict.get("final_iteration_match"):
        value += W_TIME
    if verdict.get("passed"):
        value = 1.0
    return round(min(value, 1.0), 6)


def grade_all(candidate_dir, reference_dir, checks_dir, checks=None):
    selected = list(checks or CHECKS)
    rows, values = {}, []
    for check in selected:
        value, verdict = grade_check(
            check, os.path.join(candidate_dir, check),
            os.path.join(reference_dir, check), checks_dir)
        rows[check] = verdict
        values.append(value)
    passed = bool(values) and all(rows[check].get("passed") for check in selected)
    rewards_out = {
        "reward": round(sum(values) / len(values), 6) if values else 0.0,
        "equivalence_pass": int(passed),
        "speedup": 0.0,
    }
    rewards_out.update({"check_" + check.replace("-", "_"): value
                        for check, value in zip(selected, values)})
    return rewards_out, {"checks": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--checks-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    rewards_out, report = grade_all(args.candidate, args.reference,
                                    args.checks_dir, CHECKS)
    floor = 0.0
    try:
        floor = float(json.load(open(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "floor.json"),
            encoding="utf-8")).get("floor", 0.0))
    except (OSError, ValueError, KeyError, TypeError):
        pass
    rewards_out["floor"] = floor
    rewards_out["reward_repair"] = round(
        max(0.0, rewards_out["reward"] - floor) / max(1.0e-6, 1.0 - floor), 6)
    with open(args.report, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(rewards_out, handle, indent=1, sort_keys=True)
    print(json.dumps(rewards_out, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
