#!/usr/bin/env python3
"""Apply one exact-edit transform to a source tree."""

import json
import os
import sys


spec_path, root = sys.argv[1], sys.argv[2]
spec = json.load(open(spec_path, encoding="utf-8"))
if "edits" not in spec:
    raise SystemExit("transform carries no exact edits")
for edit in spec["edits"]:
    path = os.path.join(root, edit["file"])
    text = open(path, encoding="utf-8").read()
    count = text.count(edit["old"])
    if count != 1:
        raise SystemExit(f"{path}: old text occurs {count} times, need exactly 1")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text.replace(edit["old"], edit["new"], 1))
print(f"applied {spec_path} to {root}")
