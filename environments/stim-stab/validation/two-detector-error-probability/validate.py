#!/usr/bin/env python3
"""Check two-detector-error-probability: the PASS POLICY half of the check (invariants).

Two correct runs of a stochastic configuration differ pointwise, so the policy
compares invariants. Each entry of rubric.json comparison.invariants is:
  mode "agreement": a statistic of a column (final|mean|max|min) must agree:
                    |cand - ref| <= atol + rtol * |ref|
  mode "drift":     the column must be conserved within each run on its own:
                    max |x(t) - x(0)| / |x(0)| <= max_relative_drift
Standard library and numpy only; reads only this check directory. Writes a
result with "passed", "reason", "bound_fraction" (the largest fraction of its
bound used by any invariant; its reciprocal is the headroom the presentation
prints) and "distance" (the largest relative deviation seen across agreement
invariants), which selfcheck records as the spread.

    python3 validate.py --reference DIR --candidate DIR --rubric rubric.json --out result.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


def load_column(path: Path, spec: dict) -> np.ndarray:
    fmt = spec.get("format", "text")
    if fmt == "text":
        data = np.loadtxt(path, comments=spec.get("comments", "#"), skiprows=int(spec.get("skip_rows", 0)), ndmin=2)
        return data[:, int(spec.get("column", 0))].astype(np.float64)
    if fmt == "npy":
        return np.load(path).astype(np.float64).ravel()
    if fmt in ("f64", "f32"):
        dtype = np.float64 if fmt == "f64" else np.float32
        return np.fromfile(path, dtype=dtype, offset=int(spec.get("skip_header_bytes", 0))).astype(np.float64)
    raise ValueError(f"unknown format {fmt!r} for {path}")


STATS = {"final": lambda v: float(v[-1]), "mean": lambda v: float(v.mean()),
         "max": lambda v: float(v.max()), "min": lambda v: float(v.min())}


def main() -> int:
    ap = argparse.ArgumentParser()
    for flag in ("--reference", "--candidate", "--rubric", "--out"):
        ap.add_argument(flag, required=True)
    a = ap.parse_args()
    rubric = json.loads(Path(a.rubric).read_text(encoding="utf-8"))
    reference, candidate = Path(a.reference), Path(a.candidate)
    failures, details, distance, bound_fraction = [], {}, 0.0, 0.0
    for inv in rubric["comparison"]["invariants"]:
        name, rel = inv["name"], inv["file"]
        series = {}
        for label, root in (("reference", reference), ("candidate", candidate)):
            p = root / rel
            if not p.is_file():
                failures.append(f"{name}: {label} is missing {rel}")
                continue
            try:
                series[label] = load_column(p, inv)
            except (OSError, ValueError) as exc:
                failures.append(f"{name}: {label}: cannot load {rel}: {exc}")
        if len(series) != 2:
            continue
        if not all(np.all(np.isfinite(v)) for v in series.values()):
            failures.append(f"{name}: non-finite values")
            continue
        mode = inv.get("mode", "agreement")
        if mode == "agreement":
            stat = inv.get("statistic", "final")
            ref_v, cand_v = STATS[stat](series["reference"]), STATS[stat](series["candidate"])
            bound = float(inv.get("atol", 0.0)) + float(inv["rtol"]) * abs(ref_v)
            err = abs(cand_v - ref_v)
            distance = max(distance, err / abs(ref_v) if ref_v else err)
            frac = (err / bound) if bound > 0 else (0.0 if err == 0 else float("inf"))
            bound_fraction = max(bound_fraction, frac)
            details[name] = {"mode": mode, "statistic": stat, "reference": ref_v, "candidate": cand_v, "abs_error": err, "bound": bound, "bound_fraction": frac}
            if err > bound:
                failures.append(f"{name}: |{cand_v:.6e} - {ref_v:.6e}| = {err:.3e} exceeds bound {bound:.3e}")
        elif mode == "drift":
            limit = float(inv["max_relative_drift"])
            drifts = {}
            for label, v in series.items():
                x0 = v[0]
                drifts[label] = float(np.max(np.abs(v - x0)) / (abs(x0) if x0 != 0 else 1.0))
            frac = (max(drifts.values()) / limit) if limit > 0 else (0.0 if max(drifts.values()) == 0 else float("inf"))
            bound_fraction = max(bound_fraction, frac)
            details[name] = {"mode": mode, "max_relative_drift": drifts, "bound": limit, "bound_fraction": frac}
            for label, d in drifts.items():
                if d > limit:
                    failures.append(f"{name}: {label} drifts {d:.3e} relative, above {limit:.3e}")
        else:
            failures.append(f"{name}: unknown mode {mode!r}")
    passed = not failures
    result = {"passed": passed, "policy": "invariants", "distance": distance, "bound_fraction": bound_fraction, "invariants": details,
              "reason": "all invariants within bound" if passed else "; ".join(failures)}
    Path(a.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["reason"], file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
