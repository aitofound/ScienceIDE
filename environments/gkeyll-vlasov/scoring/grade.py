"""Gkeyll Vlasov ladder: conformance .2 + passing output files .5 + time-base .3."""

import argparse
import filecmp
import json
import math
import os
import struct
import subprocess
import sys
import tempfile
import traceback

CHECKS = ["can-pb-annulus-sodshock-1x2v-p1"]  # specialised per task by the compiler
W_CONFORM, W_FILES, W_TIMEBASE = 0.2, 0.5, 0.3


def rubric_of(checks_dir, check):
    return json.load(open(os.path.join(checks_dir, check, "rubric.json"), encoding="utf-8"))


def gkyl_timebase(path, fmt):
    """Return the exact axis/header that defines a Gkeyll output's time base."""
    raw, off, times = open(path, "rb").read(), 0, []
    if fmt == "gkyl-field-v1":
        if raw[:5] != b"gkyl0":
            raise ValueError("bad Gkeyll magic")
        off = 5
        version, kind, meta_size = struct.unpack_from("<QQQ", raw, off)
        off += 24 + meta_size
        real_code, ndim = struct.unpack_from("<QQ", raw, off)
        off += 16
        cells = struct.unpack_from(f"<{ndim}Q", raw, off)
        off += 8 * ndim
        lower = struct.unpack_from(f"<{ndim}d", raw, off)
        off += 8 * ndim
        upper = struct.unpack_from(f"<{ndim}d", raw, off)
        off += 8 * ndim
        esznc, size = struct.unpack_from("<QQ", raw, off)
        if version != 1 or kind != 1:
            raise ValueError("unsupported Gkeyll field")
        return version, kind, real_code, ndim, cells, lower, upper, esznc, size
    if fmt != "gkyl-dynvec":
        raise ValueError(f"unsupported rubric format {fmt}")
    while off < len(raw):
        if raw[off:off + 5] != b"gkyl0":
            raise ValueError("bad Gkeyll magic")
        off += 5
        version, _kind, meta_size = struct.unpack_from("<QQQ", raw, off)
        off += 24 + meta_size
        if version != 1:
            raise ValueError("unsupported Gkeyll version")
        _real_code, esznc, size = struct.unpack_from("<QQQ", raw, off)
        off += 24
        times.extend(struct.unpack_from(f"<{size}d", raw, off))
        off += 8 * size + esznc * size
    if off != len(raw):
        raise ValueError("truncated Gkeyll dynamic vector")
    return times


def grade_check(check, ref_dir, cand_dir, checks_dir):
    detail = {"check": check}
    if not cand_dir or not os.path.isdir(cand_dir) or not os.listdir(cand_dir):
        detail.update(outcome="no_output", score=0.0, validator_passed=False)
        return detail
    check_dir = os.path.join(checks_dir, check)
    with tempfile.TemporaryDirectory(prefix="gkeyll-grade-") as scratch:
        out = os.path.join(scratch, "result.json")
        proc = subprocess.run(
            [sys.executable, "-B", "-s", "-E", "validate.py",
             "--reference", ref_dir, "--candidate", cand_dir,
             "--rubric", "rubric.json", "--out", out],
            cwd=check_dir, capture_output=True, text=True,
            env={"PATH": os.environ.get("PATH", ""), "LANG": "C.UTF-8"})
        if proc.returncode or not os.path.isfile(out):
            raise RuntimeError((proc.stderr or proc.stdout or "validator wrote no result")[-800:])
        result = json.load(open(out, encoding="utf-8"))
    rubric = rubric_of(checks_dir, check)
    files = result.get("files") or {}
    conforming = bool(files) and not any(
        token in result.get("reason", "") for token in
        ("missing on", "cannot load", "differs from reference", "non-finite"))
    files_total = len(rubric["comparison"]["files"])
    files_ok = sum(int(v.get("values_over_bound", 1) == 0) for v in files.values())
    try:
        timebase = conforming and all(
            gkyl_timebase(os.path.join(ref_dir, f["path"]),
                          f.get("format", "gkyl-dynvec")) ==
            gkyl_timebase(os.path.join(cand_dir, f["path"]),
                          f.get("format", "gkyl-dynvec"))
            for f in rubric["comparison"]["files"])
    except (OSError, ValueError, struct.error):
        timebase = False
    score = (W_CONFORM + W_FILES * files_ok / files_total +
             W_TIMEBASE * int(timebase)) if conforming else 0.1
    exact = all(os.path.isfile(os.path.join(ref_dir, f["path"])) and
                os.path.isfile(os.path.join(cand_dir, f["path"])) and
                filecmp.cmp(os.path.join(ref_dir, f["path"]), os.path.join(cand_dir, f["path"]), shallow=False)
                for f in rubric["comparison"]["files"])
    detail.update(outcome="passed" if result.get("passed") else ("diverged" if conforming else "nonconforming"),
                  score=round(score, 6), conformance_ok=conforming,
                  frames_ok=files_ok, frames_scored=files_total,
                  timebase_ok=timebase, exact_bytes=exact,
                  value=float(result.get("distance", 0.0)),
                  bound_fraction=float(result.get("bound_fraction", 0.0)),
                  validator_passed=bool(result.get("passed")),
                  validator_reason=result.get("reason", ""))
    return detail


def speedup(candidate, reference, all_passed):
    if not all_passed:
        return 0.0
    try:
        timing = json.load(open(os.path.join(candidate, "timing.json")))
        baked = json.load(open(os.path.join(reference, "walltimes.json")))
        ratios = [baked[c] / float(timing[c]) for c in CHECKS if c in timing and float(timing[c]) > 0]
        return round(min(ratios), 3) if ratios else 0.0
    except Exception:
        return 0.0


def grade_all(candidate, reference, checks_dir, checks=None):
    checks = list(checks or CHECKS)
    scores, rewards, details, all_passed = [], {}, [], True
    for check in checks:
        try:
            detail = grade_check(check, os.path.join(reference, check),
                                 os.path.join(candidate, check), checks_dir)
        except Exception:
            detail = {"check": check, "outcome": "grader_error", "score": 0.0,
                      "validator_passed": False, "error": traceback.format_exc()[-500:]}
        details.append(detail)
        scores.append(detail["score"])
        rewards["check_" + check.replace("-", "_")] = detail["score"]
        all_passed = all_passed and detail.get("validator_passed", False)
    floor_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "floor.json")
    floor = 0.0
    straw_status = "not-measured-here"
    if os.path.isfile(floor_path):
        floor_doc = json.load(open(floor_path, encoding="utf-8"))
        floor = float(floor_doc["floor"])
        straw_status = str(floor_doc.get("straw_status", "missing"))
        if not math.isfinite(floor) or not 0.0 <= floor < 1.0:
            raise RuntimeError(f"invalid measured straw floor: {floor}")
    reward = round(sum(scores) / len(scores), 6) if scores else 0.0
    rewards_out = {
        "reward": reward,
        "reward_repair": round(max(0.0, reward - floor) /
                               max(1.0e-6, 1.0 - floor), 6),
        "floor": floor,
        "straw_measurement_failed": int(straw_status.startswith("measurement_failed")),
        "straw_crashed": int(straw_status.startswith("crashed")),
        "grader_error": int(any(detail.get("outcome") == "grader_error"
                                for detail in details)),
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
    rewards, details = grade_all(args.candidate, args.reference, args.checks_dir)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(rewards, open(args.out, "w"), indent=1, sort_keys=True)
    json.dump({"rewards": rewards, "checks": details}, open(args.report, "w"), indent=1, sort_keys=True)
    print(json.dumps(rewards, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
