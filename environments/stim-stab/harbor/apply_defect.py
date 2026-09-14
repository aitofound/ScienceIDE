#!/usr/bin/env python3
"""Apply one exact-string transform spec to a Stim source tree."""

import json
import os
import subprocess
import sys


spec, root = sys.argv[1], sys.argv[2]
transform = json.load(open(spec))
if "edits" in transform:
    for edit in transform["edits"]:
        path = os.path.join(root, edit["file"])
        raw = open(path, "rb").read()
        newline = "\r\n" if b"\r\n" in raw else "\n"
        old = edit["old"].replace("\r\n", "\n").replace("\n", newline).encode()
        new = edit["new"].replace("\r\n", "\n").replace("\n", newline).encode()
        count = raw.count(old)
        if count != 1:
            sys.exit(f"{path}: pattern occurs {count} times, need exactly 1")
        open(path, "wb").write(raw.replace(old, new, 1))
elif "diff" in transform:
    result = subprocess.run(
        ["patch", "-p1", "--no-backup-if-mismatch", "-f"],
        input=transform["diff"], text=True, cwd=root)
    if result.returncode:
        sys.exit("patch failed")
else:
    sys.exit("transform carries neither edits nor diff")
print(f"applied {spec} to {root}")
