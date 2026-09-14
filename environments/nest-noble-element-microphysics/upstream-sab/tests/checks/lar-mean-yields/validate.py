#!/usr/bin/env python3
"""Apply a pointwise text-table rubric using only the Python standard library."""
from __future__ import annotations
import argparse
import json
import math
import sys
from pathlib import Path

def table(path: Path, skip: int) -> list[list[float]]:
    rows = []
    for raw in path.read_text(encoding="utf-8").splitlines()[skip:]:
        text = raw.strip()
        if text and not text.startswith("#"):
            rows.append([float(value) for value in text.split()])
    if not rows:
        raise ValueError(f"no numeric rows in {path}")
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError(f"ragged numeric table in {path}")
    return rows

def main() -> int:
    ap = argparse.ArgumentParser()
    for flag in ("--reference", "--candidate", "--rubric", "--out"):
        ap.add_argument(flag, required=True)
    a = ap.parse_args()
    rubric = json.loads(Path(a.rubric).read_text(encoding="utf-8"))
    comparison = rubric["comparison"]
    atol, rtol = float(comparison["atol"]), float(comparison.get("rtol", 0.0))
    key_columns = int(comparison.get("key_columns", 0))
    roots = {"reference": Path(a.reference), "candidate": Path(a.candidate)}
    failures, details = [], {}
    worst = worst_frac = 0.0
    for spec in comparison["files"]:
        rel = spec["path"]
        paths = {name: root / rel for name, root in roots.items()}
        missing = [name for name, path in paths.items() if not path.is_file()]
        if missing:
            failures.append(f"{rel}: missing on {', '.join(missing)}")
            continue
        try:
            ref = table(paths["reference"], int(spec.get("skip_rows", 0)))
            cand = table(paths["candidate"], int(spec.get("skip_rows", 0)))
        except (OSError, ValueError) as exc:
            failures.append(f"{rel}: cannot load: {exc}")
            continue
        if len(ref) != len(cand) or len(ref[0]) != len(cand[0]):
            failures.append(f"{rel}: candidate shape differs from reference")
            continue
        over = 0
        file_worst = file_frac = 0.0
        for row_index, (rrow, crow) in enumerate(zip(ref, cand)):
            if rrow[:key_columns] != crow[:key_columns]:
                failures.append(f"{rel}: physical keys differ at sorted row {row_index}")
                over += 1
            for rv, cv in zip(rrow[key_columns:], crow[key_columns:]):
                if not math.isfinite(cv):
                    failures.append(f"{rel}: candidate contains non-finite values")
                    over += 1
                    continue
                err = abs(cv - rv)
                bound = atol + rtol * abs(rv)
                frac = err / bound if bound > 0 else (0.0 if err == 0 else float("inf"))
                file_worst, file_frac = max(file_worst, err), max(file_frac, frac)
                if err > bound:
                    over += 1
        values = len(ref) * (len(ref[0]) - key_columns)
        details[rel] = {"values": values, "max_abs_error": file_worst, "values_over_bound": over, "bound_fraction": file_frac}
        if over:
            failures.append(f"{rel}: {over} of {values} values exceed atol={atol:g} rtol={rtol:g}")
        worst, worst_frac = max(worst, file_worst), max(worst_frac, file_frac)
    result = {"passed": not failures, "policy": "pointwise", "atol": atol, "rtol": rtol,
              "distance": worst, "bound_fraction": worst_frac, "files": details,
              "reason": "all graded values within bound" if not failures else "; ".join(failures)}
    Path(a.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["reason"], file=sys.stderr)
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
