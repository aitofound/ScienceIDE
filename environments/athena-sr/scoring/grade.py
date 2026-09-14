"""SR ladder: conformance .2 + end-to-end final frames .5 + exact bytes .3."""

import argparse
import importlib.util
import json
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sr_format  # noqa: E402

CHECKS = ["sr-hydro-hllc-mb1"]  # specialised per task by the compiler
W_CONFORM, W_FRAMES, W_EXACT = 0.2, 0.5, 0.3


def load_validator(checks_dir, check):
    path = os.path.join(checks_dir, check, "validate.py")
    spec = importlib.util.spec_from_file_location(
        "validate_" + check.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def grade_check(vmod, ref_dir, cand_dir):
    detail = {"check": vmod.CHECK}
    if not cand_dir or not os.path.isdir(cand_dir) or not os.listdir(cand_dir):
        detail.update(outcome="no_output", score=0.0, validator_passed=False)
        return detail
    try:
        reference = vmod._parse_dir(ref_dir)
    except Exception as ex:
        raise RuntimeError(f"reference invalid for {vmod.CHECK}: {ex}") from ex
    try:
        candidate = vmod._parse_dir(cand_dir)
    except vmod.Invalid as ex:
        detail.update(outcome="nonconforming", score=0.1,
                      validator_passed=False, error=str(ex)[:300])
        return detail
    comparison = sr_format.compare(reference, candidate, vmod.RUBRIC)
    if not comparison["conforming"]:
        detail.update(outcome="nonconforming", score=0.1,
                      validator_passed=False, error=comparison["error"])
        return detail
    frame_matches = comparison["frame_matches"]
    frames_ok = sum(bool(value) for value in frame_matches)
    frames_frac = frames_ok / len(frame_matches) if frame_matches else 0.0
    exact = bool(comparison["exact"])
    verdict = vmod.validate([ref_dir], [cand_dir])
    score = W_CONFORM + W_FRAMES * frames_frac + W_EXACT * exact
    detail.update(
        outcome="passed" if verdict["passed"] else "diverged",
        score=round(score, 6), conformance_ok=True,
        frames_ok=frames_ok, frames_scored=len(frame_matches),
        exact_bytes=exact, worst_abs=comparison["worst_abs"],
        value=comparison["worst_abs"],
        validator_passed=bool(verdict["passed"]),
        validator_reason=verdict.get("reason", "")[:300])
    return detail


def speedup(candidate, reference, all_passed):
    if not all_passed:
        return 0.0
    try:
        timing = json.load(open(os.path.join(candidate, "timing.json")))
        baked = json.load(open(os.path.join(reference, "walltimes.json")))
        ratios = [baked[check] / float(timing[check]) for check in CHECKS
                  if check in timing and float(timing[check]) > 0 and check in baked]
        return round(min(ratios), 3) if ratios else 0.0
    except Exception:
        return 0.0


def grade_all(candidate, reference, checks_dir, checks=None):
    checks = list(checks or CHECKS)
    scores, rewards, details, all_passed = [], {}, [], True
    for check in checks:
        try:
            vmod = load_validator(checks_dir, check)
            detail = grade_check(vmod, os.path.join(reference, check),
                                 os.path.join(candidate, check))
        except Exception:
            detail = {"check": check, "outcome": "grader_error", "score": 0.0,
                      "validator_passed": False,
                      "error": traceback.format_exc()[-500:]}
        details.append(detail)
        scores.append(detail["score"])
        rewards["check_" + check.replace("-", "_")] = detail["score"]
        all_passed = all_passed and detail.get("validator_passed", False)
    reward = round(sum(scores) / len(scores), 6) if scores else 0.0
    rewards_out = {
        "reward": reward,
        "equivalence_pass": 1 if all_passed else 0,
        "speedup": speedup(candidate, reference, all_passed),
    }
    rewards_out.update(rewards)
    return rewards_out, details


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--checks-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    rewards_out, details = grade_all(
        args.candidate, args.reference, args.checks_dir)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as handle:
        json.dump(rewards_out, handle, indent=1, sort_keys=True)
    with open(args.report, "w") as handle:
        json.dump({"rewards": rewards_out, "checks": details}, handle,
                  indent=1, sort_keys=True)
    print(json.dumps(rewards_out, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
