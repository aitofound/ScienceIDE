#!/usr/bin/env python3
"""Grade a straw, mapping crash/hang/build/missing-output symptoms to zero."""

import argparse
import glob
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

statuses = []
for path in sorted(glob.glob(os.path.join(
        args.candidate, "*", "_run_status.json"))):
    try:
        statuses.append(json.load(open(path, encoding="utf-8")))
    except (OSError, ValueError):
        statuses.append({"check": os.path.basename(os.path.dirname(path)),
                         "status": "malformed_status"})

with tempfile.TemporaryDirectory() as scratch:
    reward_path = os.path.join(scratch, "reward.json")
    report_path = os.path.join(scratch, "report.json")
    result = subprocess.run(
        [sys.executable, args.grade, "--candidate", args.candidate,
         "--reference", args.reference, "--checks-dir", args.checks_dir,
         "--out", reward_path, "--report", report_path],
        capture_output=True, text=True)
    if result.returncode or not os.path.isfile(reward_path):
        graded = {"reward": 0.0}
        grader_error = (result.stdout + result.stderr)[-1000:]
    else:
        graded = json.load(open(reward_path, encoding="utf-8"))
        grader_error = None

bad = [status for status in statuses if status.get("status") != "ok"]
raw_floor = float(graded.get("reward", 0.0))
payload = {
    "floor": 0.0 if bad else raw_floor,
    "raw_grader_floor": raw_floor,
    "floor_reason": ("straw_crash_hang_or_missing_output"
                     if bad else "graded_straw_outputs"),
    "straw_status": statuses,
    "per_check": {key: value for key, value in graded.items()
                  if key.startswith("check_")},
}
if grader_error:
    payload["grader_error"] = grader_error
with open(args.out, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, indent=1, sort_keys=True)
    handle.write("\n")
print(json.dumps(payload, sort_keys=True))
