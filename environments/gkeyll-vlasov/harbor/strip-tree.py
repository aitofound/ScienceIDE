#!/usr/bin/env python3
"""Remove unneeded top-level trees and source backup/variant copies."""

import os
import glob
import shutil
import sys


root = os.path.abspath(sys.argv[1])
paths = [item for item in sys.argv[2].split(";") if item]
for rel in paths:
    if os.path.isabs(rel) or ".." in rel.split("/"):
        sys.exit(f"unsafe strip path: {rel}")
    pattern = os.path.abspath(os.path.join(root, rel))
    targets = glob.glob(pattern) if glob.has_magic(pattern) else [pattern]
    for target in targets:
        if os.path.commonpath([root, target]) != root:
            sys.exit(f"strip path escapes root: {rel}")
        if os.path.isdir(target) and not os.path.islink(target):
            shutil.rmtree(target)
        elif os.path.lexists(target):
            os.unlink(target)

suffixes = (".new.c", ".old.c", ".new.cpp", ".old.cpp", ".orig", ".bak")
for directory, _, names in os.walk(root):
    for name in names:
        if name.endswith(suffixes):
            os.unlink(os.path.join(directory, name))
