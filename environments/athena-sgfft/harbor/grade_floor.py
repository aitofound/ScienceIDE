#!/usr/bin/env python3
"""Measure straw reward; any straw grader failure is a recoverable floor zero."""

import argparse
import json
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
args = parser.parse_args()

with tempfile.TemporaryDirectory() as tmp:
    reward = os.path.join(tmp, "reward.json")
    report = os.path.join(tmp, "report.json")
    result = subprocess.run(
        [sys.executable, args.grade, "--candidate", args.candidate,
         "--reference", args.reference, "--checks-dir", args.checks_dir,
         "--out", reward, "--report", report], capture_output=True, text=True)
    if result.returncode == 0 and os.path.isfile(reward):
        graded = json.load(open(reward))
        floor = {"floor": graded.get("reward", 0.0),
                 "per_check": {key: value for key, value in graded.items()
                               if key.startswith("check_")},
                 "straw_status": "graded"}
    else:
        floor = {"floor": 0.0, "per_check": {},
                 "straw_status": "crash_or_hang_floor_zero",
                 "diagnostic": (result.stdout + result.stderr)[-500:]}

json.dump(floor, open(args.out, "w"), indent=1, sort_keys=True)
print("straw floor:", json.dumps(floor, sort_keys=True))
