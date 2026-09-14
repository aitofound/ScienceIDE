#!/usr/bin/env python3
"""Apply an invariant agreement rubric using only the Python standard library."""
from __future__ import annotations
import argparse
import json
import math
import sys
from pathlib import Path

def column(path: Path, index: int) -> list[float]:
    values = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        text = raw.strip()
        if not text or text.startswith("#"):
            continue
        fields = text.split()
        if index >= len(fields):
            raise ValueError(f"column {index} absent from {path}")
        values.append(float(fields[index]))
    if not values:
        raise ValueError(f"no numeric rows in {path}")
    return values

def statistic(values: list[float], name: str) -> float:
    if name == "final": return values[-1]
    if name == "mean": return sum(values) / len(values)
    if name == "max": return max(values)
    if name == "min": return min(values)
    raise ValueError(f"unknown statistic {name!r}")

def main() -> int:
    ap = argparse.ArgumentParser()
    for flag in ("--reference", "--candidate", "--rubric", "--out"):
        ap.add_argument(flag, required=True)
    a = ap.parse_args()
    rubric = json.loads(Path(a.rubric).read_text(encoding="utf-8"))
    roots = {"reference": Path(a.reference), "candidate": Path(a.candidate)}
    failures, details = [], {}
    distance = bound_fraction = 0.0
    for spec in rubric["comparison"]["invariants"]:
        name, rel = spec["name"], spec["file"]
        series = {}
        for label, root in roots.items():
            path = root / rel
            if not path.is_file():
                failures.append(f"{name}: {label} is missing {rel}")
                continue
            try:
                series[label] = column(path, int(spec.get("column", 0)))
            except (OSError, ValueError) as exc:
                failures.append(f"{name}: {label}: cannot load {rel}: {exc}")
        if len(series) != 2:
            continue
        if not all(math.isfinite(x) for values in series.values() for x in values):
            failures.append(f"{name}: non-finite values")
            continue
        mode = spec.get("mode", "agreement")
        if mode != "agreement":
            failures.append(f"{name}: unsupported mode {mode!r}")
            continue
        stat = spec.get("statistic", "final")
        ref = statistic(series["reference"], stat)
        cand = statistic(series["candidate"], stat)
        atol, rtol = float(spec.get("atol", 0.0)), float(spec.get("rtol", 0.0))
        bound = atol + rtol * abs(ref)
        err = abs(cand - ref)
        relerr = err / abs(ref) if ref else err
        frac = err / bound if bound > 0 else (0.0 if err == 0 else float("inf"))
        distance, bound_fraction = max(distance, relerr), max(bound_fraction, frac)
        details[name] = {"reference": ref, "candidate": cand, "abs_error": err, "bound": bound, "bound_fraction": frac}
        if err > bound:
            failures.append(f"{name}: error {err:.6g} exceeds bound {bound:.6g}")
    result = {"passed": not failures, "policy": "invariants", "distance": distance, "bound_fraction": bound_fraction,
              "invariants": details, "reason": "all invariants within bound" if not failures else "; ".join(failures)}
    Path(a.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["reason"], file=sys.stderr)
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
