"""Pointwise end-to-end validator shared by the Athena chemistry rows."""

import json
import os

import chem_format


CHECK = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rubric.json"),
          encoding="utf-8") as handle:
    RUBRIC = json.load(handle)
Invalid = chem_format.Invalid


def _parse_dir(path):
    return chem_format.parse_output(path, RUBRIC)


def validate(reference_dirs, candidate_dirs):
    if len(reference_dirs) != 1 or len(candidate_dirs) != 1:
        return {"passed": False, "reason": "exactly one output directory required"}
    try:
        reference = _parse_dir(reference_dirs[0])
        candidate = _parse_dir(candidate_dirs[0])
    except Invalid as ex:
        return {"passed": False, "reason": str(ex)}
    result = chem_format.compare(reference, candidate, RUBRIC)
    passed = bool(result["conforming"] and result["frame_matches"] and
                  all(result["frame_matches"]))
    reason = ("all native evolution frames within pointwise bounds" if passed
              else result.get("error") or
              f"{sum(result['frame_matches'])}/{len(result['frame_matches'])} frames pass")
    return {"passed": passed, "reason": reason,
            "distance": result.get("worst_abs", 0.0)}
