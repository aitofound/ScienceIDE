"""Strict Athena++ self-gravity history/final-VTK evolution parser."""

import glob
import math
import os
import re
import struct


class Invalid(Exception):
    pass


def _regular(path, limit=128 * 1024 * 1024):
    if not os.path.isfile(path) or os.path.islink(path):
        raise Invalid(f"missing regular file {os.path.basename(path)}")
    size = os.path.getsize(path)
    if size <= 0 or size > limit:
        raise Invalid(f"invalid size for {os.path.basename(path)}")
    return open(path, "rb").read()


def _finite(values, label):
    if not all(math.isfinite(value) for value in values):
        raise Invalid(f"{label} contains NaN or Inf")


def _history(run_dir, rubric):
    name = rubric["output_contract"]["history"]
    raw = _regular(os.path.join(run_dir, name), 16 * 1024 * 1024)
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise Invalid("history is not ASCII") from exc
    lines = text.splitlines()
    if len(lines) < 4 or lines[0] != "# Athena++ history data":
        raise Invalid("history lacks the pinned descriptor and data rows")
    headings = re.findall(r"\[\d+\]=([^\s]+)", lines[1])
    expected = ["time", "dt", "mass", "1-mom", "2-mom", "3-mom",
                "1-KE", "2-KE", "3-KE", "tot-E", "grav-E"]
    if headings != expected:
        raise Invalid(f"history columns {headings} differ from {expected}")
    rows = []
    for line in lines[2:]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = line.split()
        if len(fields) != len(headings):
            raise Invalid("history row width changed")
        try:
            values = tuple(float(field) for field in fields)
        except ValueError as exc:
            raise Invalid("history row is nonnumeric") from exc
        _finite(values, "history")
        rows.append(values)
    if len(rows) < 2 or abs(rows[0][0]) > 1.0e-14:
        raise Invalid("history must contain t=0 and at least one evolved row")
    if any(b[0] <= a[0] for a, b in zip(rows, rows[1:])):
        raise Invalid("history times are not strictly increasing")
    frames = [{"key": f"hst:{index}", "kind": "history", "values": values}
              for index, values in enumerate(rows[1:], 1)]
    return raw, tuple(headings), tuple(rows), frames


class _Cursor:
    def __init__(self, raw, label):
        self.raw = raw
        self.pos = 0
        self.label = label

    def line(self):
        end = self.raw.find(b"\n", self.pos)
        if end < 0:
            raise Invalid(f"{self.label}: truncated ASCII header")
        blob = self.raw[self.pos:end]
        self.pos = end + 1
        try:
            return blob.decode("ascii")
        except UnicodeDecodeError as exc:
            raise Invalid(f"{self.label}: non-ASCII header") from exc

    def floats(self, count):
        end = self.pos + 4 * count
        if end > len(self.raw):
            raise Invalid(f"{self.label}: truncated float payload")
        values = struct.unpack(f">{count}f", self.raw[self.pos:end])
        self.pos = end
        if self.pos < len(self.raw) and self.raw[self.pos:self.pos + 1] == b"\n":
            self.pos += 1
        _finite(values, self.label)
        return values


def _vtk(path):
    raw = _regular(path)
    label = os.path.basename(path)
    cur = _Cursor(raw, label)
    if cur.line() != "# vtk DataFile Version 2.0":
        raise Invalid(f"{label}: wrong VTK version")
    header = cur.line()
    match = re.fullmatch(
        r"# Athena\+\+ data at time=([^ ]+)  cycle=(\d+)  variables=cons ", header)
    if not match:
        raise Invalid(f"{label}: wrong Athena VTK header")
    try:
        time_value = float(match.group(1))
        cycle = int(match.group(2))
    except ValueError as exc:
        raise Invalid(f"{label}: bad simulation time/cycle") from exc
    _finite((time_value,), label)
    if cur.line() != "BINARY" or cur.line() != "DATASET RECTILINEAR_GRID":
        raise Invalid(f"{label}: VTK must be binary rectilinear grid")
    dims_line = cur.line().split()
    if len(dims_line) != 4 or dims_line[0] != "DIMENSIONS":
        raise Invalid(f"{label}: malformed dimensions")
    try:
        face_dims = tuple(int(value) for value in dims_line[1:])
    except ValueError as exc:
        raise Invalid(f"{label}: noninteger dimensions") from exc
    if any(value <= 0 for value in face_dims):
        raise Invalid(f"{label}: nonpositive dimensions")
    values = []
    for axis, count in zip("XYZ", face_dims):
        if cur.line() != f"{axis}_COORDINATES {count} float":
            raise Invalid(f"{label}: malformed {axis} coordinates")
        values.extend(cur.floats(count))
    cell_dims = tuple(max(value - 1, 1) for value in face_dims)
    cells = cell_dims[0] * cell_dims[1] * cell_dims[2]
    if cur.line() != f"CELL_DATA {cells}":
        raise Invalid(f"{label}: wrong cell count")
    fields = []
    while cur.pos < len(raw):
        descriptor = cur.line().split()
        if len(descriptor) != 3 or descriptor[2] != "float" or \
                descriptor[0] not in ("SCALARS", "VECTORS"):
            raise Invalid(f"{label}: malformed field descriptor")
        kind, name = descriptor[:2]
        count = cells
        if kind == "SCALARS":
            if cur.line() != "LOOKUP_TABLE default":
                raise Invalid(f"{label}: missing scalar lookup table")
        else:
            count *= 3
        payload = cur.floats(count)
        fields.append((kind, name, count))
        values.extend(payload)
    expected = [("SCALARS", "dens", cells),
                ("SCALARS", "Etot", cells),
                ("VECTORS", "mom", 3 * cells),
                ("SCALARS", "phi", cells)]
    if fields != expected:
        raise Invalid(f"{label}: conserved field layout {fields} differs")
    return raw, {"time": time_value, "cycle": cycle,
                 "face_dims": face_dims, "cell_dims": cell_dims,
                 "fields": tuple(fields), "values": tuple(values)}


def parse_output(run_dir, rubric):
    if not run_dir or not os.path.isdir(run_dir):
        raise Invalid("output directory missing")
    hst_raw, headings, hst_rows, frames = _history(run_dir, rubric)
    paths = sorted(glob.glob(os.path.join(run_dir, "*.vtk")))
    expected_blocks = int(rubric["expected_final_vtk_blocks"])
    if len(paths) != expected_blocks:
        raise Invalid(f"found {len(paths)} final VTK blocks, expected {expected_blocks}")
    block_map = {}
    output_numbers = set()
    for path in paths:
        match = re.fullmatch(r".+\.block(\d+)\.out2\.(\d{5})\.vtk",
                             os.path.basename(path))
        if not match:
            raise Invalid(f"unexpected VTK name {os.path.basename(path)}")
        block, output_number = int(match.group(1)), int(match.group(2))
        if block in block_map:
            raise Invalid(f"duplicate VTK block {block}")
        output_numbers.add(output_number)
        block_map[block] = _vtk(path)
    if set(block_map) != set(range(expected_blocks)) or len(output_numbers) != 1:
        raise Invalid("VTK block set or final output index is not canonical")
    times = {round(parsed[1]["time"], 14) for parsed in block_map.values()}
    cycles = {parsed[1]["cycle"] for parsed in block_map.values()}
    if len(times) != 1 or len(cycles) != 1:
        raise Invalid("final VTK blocks disagree on simulation time/cycle")
    for block in sorted(block_map):
        parsed = block_map[block][1]
        frames.append({"key": f"vtk:block{block}", "kind": "vtk",
                       "values": (parsed["time"], float(parsed["cycle"]))
                                 + parsed["values"]})
    stable = [(rubric["output_contract"]["history"], hst_raw)]
    stable += [(os.path.basename(paths[block]), block_map[block][0])
               for block in sorted(block_map)]
    stable_bytes = b"".join(name.encode() + b"\0" + raw + b"\0"
                            for name, raw in stable)
    signature = (headings, len(hst_rows),
                 tuple((frame["key"], frame["kind"], len(frame["values"]))
                       for frame in frames),
                 tuple(block_map[b][1]["face_dims"] for b in sorted(block_map)),
                 tuple(block_map[b][1]["fields"] for b in sorted(block_map)))
    return {"frames": tuple(frames), "signature": signature,
            "stable_bytes": stable_bytes, "history_raw": hst_raw,
            "vtk_raw": tuple(block_map[b][0] for b in sorted(block_map)),
            "history_rows": hst_rows}


def compare(reference, candidate, rubric):
    if reference["signature"] != candidate["signature"]:
        return {"conforming": False, "error": "history/frame layout differs",
                "frame_matches": (), "worst_abs": 0.0, "exact": False}
    matches = []
    worst = 0.0
    for ref_frame, cand_frame in zip(reference["frames"], candidate["frames"]):
        kind = ref_frame["kind"]
        tol = rubric["tolerances"]
        rtol = float(tol["history_rtol" if kind == "history" else "vtk_rtol"])
        atol = float(tol["history_atol" if kind == "history" else "vtk_atol"])
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
