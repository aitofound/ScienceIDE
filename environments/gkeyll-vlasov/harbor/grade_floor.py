#!/usr/bin/env python3
"""Measure an unfixed straw; crashes, hangs, and grader failures mean floor 0."""

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile


parser = argparse.ArgumentParser()
parser.add_argument("--grade", required=True)
parser.add_argument("--candidate", required=True)
parser.add_argument("--reference", required=True)
parser.add_argument("--checks-dir", required=True)
parser.add_argument("--out", required=True)
parser.add_argument("--straw-status", default="ok")
parser.add_argument("--timeout", type=int, default=120)
args = parser.parse_args()


def zero(status):
    return {"floor": 0.0, "straw_status": status, "per_check": {}}


def measure():
    if args.straw_status != "ok":
        return zero(args.straw_status)
    try:
        with tempfile.TemporaryDirectory() as temporary:
            out = os.path.join(temporary, "reward.json")
            report = os.path.join(temporary, "report.json")
            result = subprocess.run(
                [sys.executable, args.grade, "--candidate", args.candidate,
                 "--reference", args.reference, "--checks-dir", args.checks_dir,
                 "--out", out, "--report", report],
                capture_output=True, text=True, timeout=args.timeout)
            if result.returncode or not os.path.isfile(out):
                return zero("crashed: grade")
            with open(out, encoding="utf-8") as handle:
                graded = json.load(handle)
            floor = float(graded["reward"])
            per_check = {key: value for key, value in graded.items()
                         if key.startswith("check_")}
            if not math.isfinite(floor) or not 0.0 <= floor <= 1.0 or not per_check:
                return zero("crashed: grade")
            return {"floor": floor, "straw_status": "ok",
                    "per_check": per_check}
    except (OSError, ValueError, KeyError, json.JSONDecodeError,
            subprocess.SubprocessError):
        return zero("crashed: grade")


floor = measure()
with open(args.out, "w", encoding="utf-8") as handle:
    json.dump(floor, handle, indent=1, sort_keys=True)
    handle.write("\n")
print("straw floor:", json.dumps(floor, sort_keys=True))
