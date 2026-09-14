#!/usr/bin/env python3
"""Remove public answer-key surfaces and source backup/variant copies."""

import os
import shutil
import sys


root = os.path.abspath(sys.argv[1])
for rel in (item for item in sys.argv[2].split(";") if item):
    if os.path.isabs(rel) or ".." in rel.split("/"):
        raise SystemExit(f"unsafe strip path: {rel}")
    target = os.path.abspath(os.path.join(root, rel))
    if os.path.commonpath([root, target]) != root:
        raise SystemExit(f"strip path escapes root: {rel}")
    if os.path.isdir(target) and not os.path.islink(target):
        shutil.rmtree(target)
    elif os.path.lexists(target):
        os.unlink(target)

suffixes = (".new.c", ".old.c", ".new.cpp", ".old.cpp", ".orig", ".bak")
for directory, _, names in os.walk(root):
    for name in names:
        if name.endswith(suffixes):
            os.unlink(os.path.join(directory, name))
