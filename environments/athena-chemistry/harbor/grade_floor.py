#!/usr/bin/env python3
"""Measure the unfixed straw, treating any unusable straw as floor zero."""

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


def grade_floor():
    if args.straw_status != "ok":
        return zero(args.straw_status)
    try:
        with tempfile.TemporaryDirectory() as temporary:
            reward = os.path.join(temporary, "reward.json")
            report = os.path.join(temporary, "report.json")
            result = subprocess.run(
                [sys.executable, args.grade, "--candidate", args.candidate,
                 "--reference", args.reference,
                 "--checks-dir", args.checks_dir, "--out", reward,
                 "--report", report], capture_output=True, text=True,
                timeout=args.timeout)
            if result.returncode or not os.path.isfile(reward):
                return zero("crashed: grade")
            try:
                with open(reward, encoding="utf-8") as handle:
                    graded = json.load(handle)
                value = float(graded["reward"])
                per_check = {key: item for key, item in graded.items()
                             if key.startswith("check_")}
                if not math.isfinite(value) or not 0.0 <= value <= 1.0 \
                        or not per_check:
                    return zero("crashed: grade")
            except (KeyError, TypeError, ValueError, json.JSONDecodeError,
                    OSError):
                return zero("crashed: grade")
    except (OSError, subprocess.SubprocessError):
        return zero("crashed: grade")
    return {"floor": value, "straw_status": "ok",
            "per_check": per_check}


floor = grade_floor()
with open(args.out, "w", encoding="utf-8") as handle:
    json.dump(floor, handle, indent=1, sort_keys=True)
    handle.write("\n")
print("straw floor:", json.dumps(floor, sort_keys=True))
