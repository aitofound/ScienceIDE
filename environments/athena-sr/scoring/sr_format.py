"""Strict parser for Athena++ SR native final-state tab frames."""

import math
import os
import re


class Invalid(Exception):
    pass


def _regular(path, limit=128 * 1024 * 1024):
    if not os.path.isfile(path) or os.path.islink(path):
        raise Invalid(f"missing regular file {os.path.basename(path)}")
    size = os.path.getsize(path)
    if size <= 0 or size > limit:
        raise Invalid(f"invalid size for {os.path.basename(path)}")
    return open(path, "rb").read()


def _canonical(raw, rubric):
    """Apply only declared measured timestamp masks; physical data stay scored."""
    canonical = raw
    for expression in rubric.get("canonicalization", {}).get(
            "wall_timestamp_regexes", []):
        canonical = re.sub(expression.encode("ascii"), b"<TIMESTAMP>", canonical)
    return canonical


def _frame(path, rubric):
    raw = _regular(path)
    label = os.path.basename(path)
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as ex:
        raise Invalid(f"{label}: frame is not ASCII") from ex
    headers, rows, widths, values = [], [], set(), []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            headers.append(stripped)
            continue
        fields = stripped.split()
        try:
            numeric = tuple(float(field) for field in fields)
        except ValueError as ex:
            raise Invalid(f"{label}: nonnumeric frame row") from ex
        if not all(math.isfinite(value) for value in numeric):
            raise Invalid(f"{label}: frame contains NaN or Inf")
        widths.add(len(numeric))
        rows.append(numeric)
        values.extend(numeric)
    if not headers or not any("Athena++" in line for line in headers):
        raise Invalid(f"{label}: missing Athena++ frame descriptor")
    if not rows or len(widths) != 1:
        raise Invalid(f"{label}: empty or ragged frame")
    return {
        "raw": raw,
        "canonical": _canonical(raw, rubric),
        "headers": tuple(headers),
        "row_count": len(rows),
        "width": next(iter(widths)),
        "values": tuple(values),
    }


def parse_output(run_dir, rubric):
    if not run_dir or not os.path.isdir(run_dir):
        raise Invalid("output directory missing")
    expected = list(rubric["output_contract"]["frames"])
    present = sorted(os.listdir(run_dir))
    if present != sorted(expected):
        raise Invalid(f"artifact set {present} differs from {sorted(expected)}")
    frames, stable, signature, raw_frames = [], [], [], []
    for name in expected:
        parsed = _frame(os.path.join(run_dir, name), rubric)
        frames.append({"key": name, "kind": "final-state",
                       "values": parsed["values"]})
        stable.append(name.encode("ascii") + b"\0" + parsed["canonical"] + b"\0")
        signature.append((name, parsed["row_count"], parsed["width"],
                          parsed["headers"]))
        raw_frames.append(parsed["raw"])
    return {"frames": tuple(frames), "signature": tuple(signature),
            "stable_bytes": b"".join(stable), "frame_raw": tuple(raw_frames)}


def compare(reference, candidate, rubric):
    if reference["signature"] != candidate["signature"]:
        return {"conforming": False, "error": "final-frame layout differs",
                "frame_matches": (), "worst_abs": 0.0, "exact": False}
    atol = float(rubric["tolerances"]["atol"])
    rtol = float(rubric["tolerances"].get("rtol", 0.0))
    matches, worst = [], 0.0
    for ref_frame, cand_frame in zip(reference["frames"], candidate["frames"]):
        good = True
        for ref_value, cand_value in zip(ref_frame["values"], cand_frame["values"]):
            error = abs(cand_value - ref_value)
            worst = max(worst, error)
            if error > atol + rtol * abs(ref_value):
                good = False
        matches.append(good)
    return {"conforming": True, "frame_matches": tuple(matches),
            "worst_abs": worst,
            "exact": candidate["stable_bytes"] == reference["stable_bytes"]}
