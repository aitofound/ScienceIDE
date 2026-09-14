"""Shared per-row validator binding for the self-gravity evolution suite."""

import json
import os
import sys


def bind(here):
    for candidate in (os.path.abspath(os.path.join(here, "..", "..", "scoring")),
                      "/app", "/tests"):
        if candidate not in sys.path:
            sys.path.insert(0, candidate)
    import sg_format

    check = os.path.basename(here)
    rubric = json.load(open(os.path.join(here, "rubric.json")))

    def parse_dir(path):
        return sg_format.parse_output(path, rubric)

    def validate(reference_dirs, candidate_dirs):
        try:
            reference = parse_dir(reference_dirs[0])
            candidate = parse_dir(candidate_dirs[0])
        except (IndexError, sg_format.Invalid) as exc:
            return {"check": check, "passed": False, "reason": str(exc)}
        comparison = sg_format.compare(reference, candidate, rubric)
        passed = comparison["conforming"] and all(comparison["frame_matches"])
        return {
            "check": check,
            "passed": bool(passed),
            "reason": ("ok" if passed else
                       f"conforming={comparison['conforming']} "
                       f"frames={sum(comparison['frame_matches'])}/"
                       f"{len(comparison['frame_matches'])} "
                       f"worst_abs={comparison['worst_abs']:.6e}"),
        }

    return check, rubric, sg_format.Invalid, parse_dir, validate
