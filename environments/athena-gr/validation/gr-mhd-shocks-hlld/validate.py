"""Pointwise final-frame validator for one Athena++ GR evolution row."""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "scoring")))
import gr_format  # noqa: E402

CHECK = "gr-mhd-shocks-hlld"
RUBRIC = json.load(open(os.path.join(HERE, "rubric.json")))
Invalid = gr_format.Invalid


def _parse_dir(path):
    return gr_format.parse_output(path, RUBRIC)


def validate(reference_dirs, candidate_dirs):
    if len(reference_dirs) != 1 or len(candidate_dirs) != 1:
        return {"passed": False, "reason": "validator needs one reference/candidate"}
    try:
        reference = _parse_dir(reference_dirs[0])
        candidate = _parse_dir(candidate_dirs[0])
        comparison = gr_format.compare(reference, candidate, RUBRIC)
    except Invalid as ex:
        return {"passed": False, "reason": str(ex), "distance": 0.0}
    passed = comparison["conforming"] and all(comparison["frame_matches"])
    return {"passed": bool(passed), "distance": comparison["worst_abs"],
            "reason": ("all final evolution frames are within tolerance"
                       if passed else comparison.get("error") or
                       "one or more final evolution frames diverged")}
