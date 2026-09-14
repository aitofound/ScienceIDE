#!/usr/bin/env python3
"""Apply one exact-string transform spec to an Athena source tree."""

import json
import os
import subprocess
import sys


spec, root = sys.argv[1], sys.argv[2]
transform = json.load(open(spec))
if "edits" in transform:
    for edit in transform["edits"]:
        path = os.path.join(root, edit["file"])
        text = open(path, encoding="utf-8").read()
        count = text.count(edit["old"])
        if count != 1:
            sys.exit(f"{path}: pattern occurs {count} times, need exactly 1")
        open(path, "w", encoding="utf-8").write(
            text.replace(edit["old"], edit["new"], 1))
elif "diff" in transform:
    result = subprocess.run(
        ["patch", "-p1", "--no-backup-if-mismatch", "-f"],
        input=transform["diff"], text=True, cwd=root)
    if result.returncode:
        sys.exit("patch failed")
else:
    sys.exit("transform carries neither edits nor diff")
print(f"applied {spec} to {root}")
