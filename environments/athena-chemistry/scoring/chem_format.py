"""Strict parser/comparator for Athena chemistry hst and final tab frames."""

import glob
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
    with open(path, "rb") as handle:
        return handle.read()


_ISO_TIMESTAMP = re.compile(
    rb"(?i)(?P<label>\b(?:created(?:[_ ]at)?|timestamp|wall[_ ]time|date)\s*[=:]\s*)"
    rb"\d{4}-\d{2}-\d{2}[T ][0-9:.+-]+Z?")


def canonical_bytes(raw):
    """Erase wall-clock timestamps only; physical time/cycle stays byte-exact."""
    return _ISO_TIMESTAMP.sub(lambda match: match.group("label") + b"<TIMESTAMP>", raw)


def _finite(values, label):
    if not all(math.isfinite(value) for value in values):
        raise Invalid(f"{label} contains NaN or Inf")


def _ascii(raw, label):
    try:
        return raw.decode("ascii")
    except UnicodeDecodeError as ex:
        raise Invalid(f"{label} is not ASCII") from ex


def _history(path):
    raw = _regular(path, 32 * 1024 * 1024)
    lines = _ascii(raw, os.path.basename(path)).splitlines()
    if len(lines) < 4 or lines[0] != "# Athena++ history data":
        raise Invalid("history lacks the Athena descriptor and evolution rows")
    headings = tuple(re.findall(r"\[\d+\]=([^\s]+)", lines[1]))
    if not headings:
        raise Invalid("history has no column headings")
    rows = []
    for line in lines[2:]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = line.split()
        if len(fields) != len(headings):
            raise Invalid("history row width changed")
        try:
            values = tuple(float(field) for field in fields)
        except ValueError as ex:
            raise Invalid("history row is nonnumeric") from ex
        _finite(values, "history")
        rows.append(values)
    if len(rows) < 2 or abs(rows[0][0]) > 1.0e-14:
        raise Invalid("history must contain t=0 and at least one evolved row")
    if any(right[0] <= left[0] for left, right in zip(rows, rows[1:])):
        raise Invalid("history times are not strictly increasing")
    evolved = tuple(value for row in rows[1:] for value in row)
    return {"raw": raw, "stable": canonical_bytes(raw),
            "headings": headings, "rows": tuple(rows), "values": evolved}


def _tab(path):
    raw = _regular(path)
    text = _ascii(raw, os.path.basename(path))
    comments, rows, width = [], [], None
    for line in text.splitlines():
        if not line.strip():
            continue
        if line.lstrip().startswith("#"):
            comments.append(line)
            continue
        try:
            values = tuple(float(field) for field in line.split())
        except ValueError as ex:
            raise Invalid(f"{os.path.basename(path)} has nonnumeric data") from ex
        _finite(values, os.path.basename(path))
        if width is None:
            width = len(values)
        if not width or len(values) != width:
            raise Invalid(f"{os.path.basename(path)} row width changed")
        rows.append(values)
    if not comments or not rows or width is None:
        raise Invalid(f"{os.path.basename(path)} lacks header or cells")
    if "Athena++" not in comments[0]:
        raise Invalid(f"{os.path.basename(path)} lacks Athena descriptor")
    headings = tuple(re.findall(r"\[\d+\]=([^\s]+)", " ".join(comments)))
    return {"raw": raw, "stable": canonical_bytes(raw),
            "comments": tuple(comments), "headings": headings,
            "rows": tuple(rows), "width": width}


def _tab_number(path):
    match = re.fullmatch(r".+\.block(\d+)\.out1\.(\d{5})\.tab",
                         os.path.basename(path))
    if not match:
        raise Invalid(f"unexpected tab name {os.path.basename(path)}")
    return int(match.group(1)), int(match.group(2))


def parse_output(run_dir, rubric):
    if not run_dir or not os.path.isdir(run_dir):
        raise Invalid("output directory missing")
    contract = rubric["output_contract"]
    history_name = contract["history"]
    history = _history(os.path.join(run_dir, history_name))
    paths = sorted(glob.glob(os.path.join(run_dir, "*.tab")))
    expected = int(contract["expected_final_tab_blocks"])
    if len(paths) != expected:
        raise Invalid(f"found {len(paths)} final tab blocks, expected {expected}")
    blocks, output_numbers = {}, set()
    for path in paths:
        block, output_number = _tab_number(path)
        if block in blocks:
            raise Invalid(f"duplicate tab block {block}")
        output_numbers.add(output_number)
        blocks[block] = _tab(path)
    if set(blocks) != set(range(expected)) or len(output_numbers) != 1:
        raise Invalid("tab block set or final output index is not canonical")
    signatures = {(item["width"], item["headings"])
                  for item in blocks.values()}
    if len(signatures) != 1:
        raise Invalid("tab blocks disagree on columns")

    frames = [{"key": "hst:evolution", "kind": "history",
               "values": history["values"]}]
    for block in sorted(blocks):
        frames.append({"key": f"tab:block{block}", "kind": "tab",
                       "rows": blocks[block]["rows"],
                       "width": blocks[block]["width"]})
    stable_parts = [(history_name, history["stable"])]
    stable_parts += [(os.path.basename(paths[block]), blocks[block]["stable"])
                     for block in sorted(blocks)]
    stable_bytes = b"".join(name.encode() + b"\0" + raw + b"\0"
                            for name, raw in stable_parts)
    raw_bytes = b"".join(name.encode() + b"\0" + raw + b"\0"
                         for name, raw in
                         [(history_name, history["raw"])] +
                         [(os.path.basename(paths[block]), blocks[block]["raw"])
                          for block in sorted(blocks)])
    signature = (
        history["headings"], len(history["rows"]),
        tuple((frame["key"], frame["kind"],
               len(frame.get("values", frame.get("rows", ()))))
              for frame in frames),
        tuple((block, blocks[block]["width"], len(blocks[block]["rows"]),
               blocks[block]["headings"]) for block in sorted(blocks)),
    )
    return {"frames": tuple(frames), "signature": signature,
            "stable_bytes": stable_bytes, "raw_bytes": raw_bytes,
            "history_raw": history["raw"],
            "tab_raw": tuple(blocks[block]["raw"] for block in sorted(blocks)),
            "history_rows": history["rows"]}


def _within(reference, candidate, atol, rtol):
    error = abs(candidate - reference)
    return error <= atol + rtol * abs(reference), error


def _tab_tolerance(rubric, column):
    tolerances = rubric["tolerances"]
    for group in tolerances.get("tab_column_groups", []):
        if column in group["columns"]:
            return float(group["atol"]), float(group["rtol"])
    return float(tolerances["tab_atol"]), float(tolerances["tab_rtol"])


def compare(reference, candidate, rubric):
    if reference["signature"] != candidate["signature"]:
        return {"conforming": False, "error": "history/frame layout differs",
                "frame_matches": (), "worst_abs": 0.0, "exact": False}
    matches, worst = [], 0.0
    for ref_frame, cand_frame in zip(reference["frames"], candidate["frames"]):
        good = True
        if ref_frame["kind"] == "history":
            atol = float(rubric["tolerances"]["history_atol"])
            rtol = float(rubric["tolerances"]["history_rtol"])
            pairs = zip(ref_frame["values"], cand_frame["values"])
            for ref_value, cand_value in pairs:
                passed, error = _within(ref_value, cand_value, atol, rtol)
                good = good and passed
                worst = max(worst, error)
        else:
            for ref_row, cand_row in zip(ref_frame["rows"], cand_frame["rows"]):
                for column, (ref_value, cand_value) in enumerate(
                        zip(ref_row, cand_row)):
                    atol, rtol = _tab_tolerance(rubric, column)
                    passed, error = _within(ref_value, cand_value, atol, rtol)
                    good = good and passed
                    worst = max(worst, error)
        matches.append(good)
    return {"conforming": True, "frame_matches": tuple(matches),
            "worst_abs": worst,
            "exact": candidate["stable_bytes"] == reference["stable_bytes"],
            "raw_exact": candidate["raw_bytes"] == reference["raw_bytes"]}
