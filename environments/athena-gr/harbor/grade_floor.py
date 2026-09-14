#!/usr/bin/env python3
"""Measure a defective straw floor; crashes and hangs are floor-zero symptoms."""

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
parser.add_argument("--straw-status", required=True)
args = parser.parse_args()

floor = {"floor": 0.0, "per_check": {}, "straw_status": args.straw_status}
if args.straw_status == "ok":
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "reward.json")
        report = os.path.join(tmp, "report.json")
        result = subprocess.run(
            [sys.executable, args.grade, "--candidate", args.candidate,
             "--reference", args.reference, "--checks-dir", args.checks_dir,
             "--out", out, "--report", report], capture_output=True, text=True)
        if result.returncode == 0 and os.path.isfile(out):
            try:
                graded = json.load(open(out))
                floor = {
                    "floor": float(graded["reward"]),
                    "per_check": {key: value for key, value in graded.items()
                                  if key.startswith("check_")},
                    "straw_status": "ok",
                }
            except (OSError, ValueError, KeyError, TypeError):
                floor["straw_status"] = "crashed: grade"
        else:
            floor["straw_status"] = "crashed: grade"

with open(args.out, "w") as handle:
    json.dump(floor, handle, indent=1, sort_keys=True)
    handle.write("\n")
print("straw floor:", json.dumps(floor, sort_keys=True))
