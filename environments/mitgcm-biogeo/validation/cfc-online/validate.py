#!/usr/bin/env python3
"""Check cfc-online: the PASS POLICY half of the check (pointwise).

Compares every graded value of the candidate with the reference:
    |candidate - reference| <= atol + rtol * |reference|      for every value
with atol/rtol read from rubric.json. The graded files are every
<field>.<iteration>.data of the final iteration present in the reference,
minus the fields listed under comparison.not_graded (forcing echoes) and, inside a
multi-record diagnostics file, the records named in comparison.not_graded_records; the
candidate must provide the same set. Each .data file is raw big-endian
floating point as MITgcm's mdsio writes it, with the precision and shape taken
from the .meta sidecar. Standard library and numpy only; reads only this check
directory. Writes a result with "passed", "reason" and "distance" (the largest
absolute error seen), which selfcheck records as the measured spread.

    python3 validate.py --reference DIR --candidate DIR --rubric rubric.json --out result.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np

DATA_RE = re.compile(r"^([A-Za-z_0-9]+)\.(\d{10})\.data$")


def meta(path: Path) -> tuple[str, list[int], list[str]]:
    text = path.with_suffix(".meta").read_text(encoding="utf-8")
    prec = re.search(r"dataprec\s*=\s*\[\s*'(\w+)'", text)
    dims = re.search(r"dimList\s*=\s*\[(.*?)\]", text, re.S)
    if not prec or not dims:
        raise ValueError(f"unreadable meta for {path.name}")
    nums = [int(x) for x in re.findall(r"\d+", dims.group(1))]
    shape = nums[0::3]
    flds = re.search(r"fldList\s*=\s*\{(.*?)\}", text, re.S)
    records = [x.strip() for x in re.findall(r"'([^']*)'", flds.group(1))] if flds else []
    return prec.group(1), shape, records


def record_mask(arr: np.ndarray, records: list[str], excluded: list[str]) -> np.ndarray:
    """True where a value is graded: every value, minus the named records of a multi-record file."""
    keep = np.ones(arr.size, dtype=bool)
    if records and excluded and arr.size % len(records) == 0:
        per = arr.size // len(records)
        for i, r in enumerate(records):
            if r in excluded:
                keep[i * per:(i + 1) * per] = False
    return keep


def load(path: Path) -> np.ndarray:
    prec, shape, _ = meta(path)
    dtype = {"float64": ">f8", "float32": ">f4"}[prec]
    arr = np.fromfile(path, dtype=dtype).astype(np.float64)
    expected = int(np.prod(shape)) if shape else arr.size
    if arr.size % expected != 0:
        raise ValueError(f"{path.name}: {arr.size} values do not fit shape {shape}")
    return arr


def final_dump(root: Path) -> tuple[str, dict[str, Path]]:
    found = {}
    for p in root.iterdir():
        m = DATA_RE.match(p.name)
        if m:
            found.setdefault(m.group(2), {})[m.group(1)] = p
    if not found:
        return "", {}
    it = max(found)
    return it, found[it]


def main() -> int:
    ap = argparse.ArgumentParser()
    for flag in ("--reference", "--candidate", "--rubric", "--out"):
        ap.add_argument(flag, required=True)
    a = ap.parse_args()
    rubric = json.loads(Path(a.rubric).read_text(encoding="utf-8"))
    comparison = rubric["comparison"]
    atol, rtol = float(comparison["atol"]), float(comparison.get("rtol", 0.0))
    not_graded = set(comparison.get("not_graded", []))
    not_graded_records = comparison.get("not_graded_records", {}) or {}
    required = set(comparison.get("required_fields", []))
    reference, candidate = Path(a.reference), Path(a.candidate)
    worst, failures, details = 0.0, [], {}
    ref_it, ref_files = final_dump(reference)
    cand_it, cand_files = final_dump(candidate)
    if not ref_files:
        failures.append("reference has no <field>.<iteration>.data dump")
    if not cand_files:
        failures.append("candidate has no <field>.<iteration>.data dump")
    if ref_files and cand_files and ref_it != cand_it:
        failures.append(f"candidate final iteration {cand_it} differs from reference {ref_it}")
    graded = sorted(f for f in ref_files if f not in not_graded)
    missing_required = sorted(required - set(graded))
    if missing_required:
        failures.append(f"reference dump lacks required fields: {', '.join(missing_required)}")
    if not failures:
        for field in graded:
            rel = ref_files[field].name
            if field not in cand_files:
                failures.append(f"{rel}: missing on candidate")
                continue
            try:
                r, c = load(ref_files[field]), load(cand_files[field])
            except (OSError, ValueError, KeyError) as exc:
                failures.append(f"{rel}: cannot load: {exc}")
                continue
            if r.shape != c.shape:
                failures.append(f"{rel}: shape {c.shape} differs from reference {r.shape}")
                continue
            if not np.all(np.isfinite(c)):
                failures.append(f"{rel}: candidate contains non-finite values")
                continue
            err = np.abs(c - r)
            if field in not_graded_records:
                _, _, records = meta(ref_files[field])
                keep = record_mask(r, records, list(not_graded_records[field]))
                err = np.where(keep, err, 0.0)
            over = int(np.count_nonzero(err > atol + rtol * np.abs(r)))
            max_err = float(err.max()) if err.size else 0.0
            scale = float(np.abs(r).max()) if r.size else 0.0
            details[rel] = {"values": int(r.size), "max_abs_error": max_err, "max_abs_reference": scale,
                            "values_over_bound": over}
            if over:
                failures.append(f"{rel}: {over} of {r.size} values exceed atol={atol:g} rtol={rtol:g} (max |err| {max_err:.3e})")
            worst = max(worst, max_err)
    passed = not failures
    result = {"passed": passed, "policy": "pointwise", "atol": atol, "rtol": rtol, "distance": worst,
              "final_iteration": ref_it, "files": details,
              "reason": "all graded values within bound" if passed else "; ".join(failures)}
    Path(a.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["reason"], file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
