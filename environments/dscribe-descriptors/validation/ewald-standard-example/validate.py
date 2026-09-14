#!/usr/bin/env python3
"""Check ewald-standard-example: the PASS POLICY half of the check (pointwise).

Compares every graded value of the candidate with the reference:
    |candidate - reference| <= atol + rtol * |reference|      for every value
with atol/rtol and the file list read from rubric.json. Standard library and
numpy only; reads only this check directory. Adapt the loaders to the
module's output formats; keep the numbers in rubric.json. Grade physical
production quantities only: an array is compared by position only where the
position is physical (a grid cell); an unordered collection (particles, sinks,
modes) is put in the order of an identity the output carries first, and that
permutation covers every array and block of the collection. Never grade
storage order, layouts, step counts, timings or random draws. Writes a result
with "passed", "reason", "distance" (the largest absolute error seen, which
selfcheck records as the measured spread) and "bound_fraction" (the largest
fraction of the bound |err| / (atol + rtol|ref|) used by any graded value; its
reciprocal is the headroom the presentation prints).

    python3 validate.py --reference DIR --candidate DIR --rubric rubric.json --out result.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


def load(path: Path, spec: dict) -> np.ndarray:
    fmt = spec.get("format", "f64")
    if fmt in ("f64", "f32"):
        dtype = np.float64 if fmt == "f64" else np.float32
        return np.fromfile(path, dtype=dtype, offset=int(spec.get("skip_header_bytes", 0))).astype(np.float64)
    if fmt == "npy":
        return np.load(path).astype(np.float64).ravel()
    if fmt == "text":
        return np.loadtxt(path, comments=spec.get("comments", "#"), skiprows=int(spec.get("skip_rows", 0)),
                          usecols=spec.get("columns")).astype(np.float64).ravel()
    raise ValueError(f"unknown format {fmt!r} for {path}")


def main() -> int:
    ap = argparse.ArgumentParser()
    for flag in ("--reference", "--candidate", "--rubric", "--out"):
        ap.add_argument(flag, required=True)
    a = ap.parse_args()
    rubric = json.loads(Path(a.rubric).read_text(encoding="utf-8"))
    comparison = rubric["comparison"]
    atol, rtol = float(comparison["atol"]), float(comparison.get("rtol", 0.0))
    reference, candidate = Path(a.reference), Path(a.candidate)
    worst, worst_frac, failures, details = 0.0, 0.0, [], {}
    for spec in comparison["files"]:
        rel = spec["path"]
        ref_path, cand_path = reference / rel, candidate / rel
        if not ref_path.is_file() or not cand_path.is_file():
            failures.append(f"{rel}: missing on {'reference' if not ref_path.is_file() else 'candidate'}")
            continue
        try:
            r, c = load(ref_path, spec), load(cand_path, spec)
        except (OSError, ValueError) as exc:
            failures.append(f"{rel}: cannot load: {exc}")
            continue
        if r.shape != c.shape:
            failures.append(f"{rel}: shape {c.shape} differs from reference {r.shape}")
            continue
        if not np.all(np.isfinite(c)):
            failures.append(f"{rel}: candidate contains non-finite values")
            continue
        err = np.abs(c - r)
        bound = atol + rtol * np.abs(r)
        over = int(np.count_nonzero(err > bound))
        max_err = float(err.max()) if err.size else 0.0
        frac = float((err / bound).max()) if err.size else 0.0
        details[rel] = {"values": int(r.size), "max_abs_error": max_err, "values_over_bound": over, "bound_fraction": frac}
        if over:
            failures.append(f"{rel}: {over} of {r.size} values exceed atol={atol:g} rtol={rtol:g} (max |err| {max_err:.3e})")
        worst = max(worst, max_err)
        worst_frac = max(worst_frac, frac)
    passed = not failures
    result = {"passed": passed, "policy": "pointwise", "atol": atol, "rtol": rtol, "distance": worst, "bound_fraction": worst_frac,
              "files": details, "reason": "all graded values within bound" if passed else "; ".join(failures)}
    Path(a.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["reason"], file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
