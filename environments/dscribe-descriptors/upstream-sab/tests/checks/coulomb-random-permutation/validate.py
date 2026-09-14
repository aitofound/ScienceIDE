#!/usr/bin/env python3
"""Validate seeded random-permutation distribution invariants."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


def main():
    parser = argparse.ArgumentParser()
    for flag in ("--reference", "--candidate", "--rubric", "--out"):
        parser.add_argument(flag, required=True)
    args = parser.parse_args()
    rubric = json.loads(Path(args.rubric).read_text(encoding="utf-8"))
    failures, details, distance, worst_fraction = [], {}, 0.0, 0.0
    try:
        reference = np.load(Path(args.reference) / "output.npy").astype(float).ravel()
        candidate = np.load(Path(args.candidate) / "output.npy").astype(float).ravel()
    except (OSError, ValueError) as exc:
        failures.append(f"cannot load output.npy: {exc}")
        reference = candidate = np.empty(0)
    if reference.shape != candidate.shape:
        failures.append(f"shape {candidate.shape} differs from reference {reference.shape}")
    elif not np.all(np.isfinite(candidate)):
        failures.append("candidate contains non-finite values")
    else:
        for invariant in rubric["comparison"]["invariants"]:
            name, index = invariant["name"], int(invariant["index"])
            ref, cand = float(reference[index]), float(candidate[index])
            error = abs(cand - ref)
            bound = float(invariant.get("atol", 0)) + float(invariant.get("rtol", 0)) * abs(ref)
            fraction = error / bound if bound else (0.0 if error == 0 else float("inf"))
            details[name] = {"reference": ref, "candidate": cand, "abs_error": error, "bound": bound, "bound_fraction": fraction}
            distance = max(distance, error)
            worst_fraction = max(worst_fraction, fraction)
            if error > bound:
                failures.append(f"{name}: error {error:.3e} exceeds {bound:.3e}")
    result = {"passed": not failures, "policy": "invariants", "distance": distance, "bound_fraction": worst_fraction, "invariants": details, "reason": "all invariants within bound" if not failures else "; ".join(failures)}
    Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["reason"], file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
