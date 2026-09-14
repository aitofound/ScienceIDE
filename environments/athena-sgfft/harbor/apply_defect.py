#!/usr/bin/env python3
"""Apply one exact-string transform to an Athena++ source tree."""

import json
import os
import sys


transform = json.load(open(sys.argv[1]))
root = sys.argv[2]
if "edits" not in transform:
    raise SystemExit("transform carries no edits")
for edit in transform["edits"]:
    path = os.path.join(root, edit["file"])
    text = open(path, encoding="utf-8").read()
    count = text.count(edit["old"])
    if count != 1:
        raise SystemExit(f"{path}: pattern occurs {count} times, need exactly 1")
    open(path, "w", encoding="utf-8").write(
        text.replace(edit["old"], edit["new"], 1))
print(f"applied {sys.argv[1]} to {root}")
