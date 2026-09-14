#!/usr/bin/env python3
"""Build one pinned Athena++ GR variant or run one frozen evolution row.

    rowtool.py build TREE VARIANT BUILD_DIR [JOBS]
    rowtool.py run BUILDS_ROOT CASE_DIR RUN_DIR [TIMEOUT_SEC]

The verifier and oracle share this stdlib-only implementation.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time


BUILD_VARIANTS = {
    "hydro-hllc-transform": [
        "-g", "-t", "--prob=gr_shock_tube", "--coord=minkowski", "--flux=hllc"],
    "hydro-hlle-transform": [
        "-g", "-t", "--prob=gr_shock_tube", "--coord=minkowski", "--flux=hlle"],
    "hydro-hlle-notransform": [
        "-g", "--prob=gr_shock_tube", "--coord=minkowski", "--flux=hlle"],
    "hydro-llf-transform": [
        "-g", "-t", "--prob=gr_shock_tube", "--coord=minkowski", "--flux=llf"],
    "hydro-llf-notransform": [
        "-g", "--prob=gr_shock_tube", "--coord=minkowski", "--flux=llf"],
    "mhd-hlld-transform": [
        "-b", "-g", "-t", "--prob=gr_shock_tube", "--coord=minkowski", "--flux=hlld"],
    "mhd-hlle-transform": [
        "-b", "-g", "-t", "--prob=gr_shock_tube", "--coord=minkowski", "--flux=hlle"],
    "mhd-llf-transform": [
        "-b", "-g", "-t", "--prob=gr_shock_tube", "--coord=minkowski", "--flux=llf"],
}


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _copy_source(tree, target):
    source_abs = os.path.abspath(tree)

    def ignore(path, names):
        omitted = {".git", "bin", "obj"}
        if os.path.abspath(path) == source_abs:
            omitted |= {"_build", "run"}
        return sorted(omitted & set(names))

    shutil.copytree(tree, target, symlinks=True, ignore=ignore)


def build(tree, variant, build_dir, jobs=4):
    if variant not in BUILD_VARIANTS:
        raise SystemExit(f"unknown build variant: {variant}")
    if os.path.isdir(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)
    source = os.path.join(build_dir, "source")
    obj = os.path.join(build_dir, "obj")
    binary_dir = os.path.join(build_dir, "bin")
    _copy_source(tree, source)
    configure = ([sys.executable, "configure.py"] + BUILD_VARIANTS[variant]
                 + ["--cflag=-O2 -g0 -ffp-contract=off"])
    subprocess.run(configure, cwd=source, check=True)
    subprocess.run(["make", f"-j{int(jobs)}", f"EXE_DIR={binary_dir}/",
                    f"OBJ_DIR={obj}/"], cwd=source, check=True)
    binary = os.path.join(binary_dir, "athena")
    if not os.access(binary, os.X_OK):
        raise SystemExit("build produced no executable athena")


def run(builds_root, case_dir, run_dir, timeout=None):
    row = json.load(open(os.path.join(case_dir, "row.json")))
    variant = row["build"]
    binary = os.path.abspath(os.path.join(builds_root, variant, "bin", "athena"))
    if not os.access(binary, os.X_OK):
        raise SystemExit(f"missing {variant} executable: {binary}")
    if os.path.isdir(run_dir):
        shutil.rmtree(run_dir)
    os.makedirs(run_dir)
    scratch = os.path.join(run_dir, ".runs")
    os.makedirs(scratch)
    deadline = time.monotonic() + float(timeout) if timeout else None
    for deck in row["decks"]:
        source_deck = os.path.join(case_dir, deck["input"])
        if _sha256(source_deck) != deck["sha256"]:
            raise SystemExit(f"deck checksum mismatch: {deck['input']}")
        deck_run = os.path.join(scratch, deck["id"])
        os.makedirs(deck_run)
        local_deck = os.path.join(deck_run, deck["input"])
        shutil.copyfile(source_deck, local_deck)
        command = [binary, "-i", deck["input"], "-d", "."]
        command += list(row.get("argv_overrides", []))
        remaining = None if deadline is None else deadline - time.monotonic()
        if remaining is not None and remaining <= 0:
            raise subprocess.TimeoutExpired(command, timeout)
        result = subprocess.run(command, cwd=deck_run, capture_output=True,
                                text=True, timeout=remaining)
        if result.returncode:
            sys.stderr.write(result.stdout + result.stderr)
            raise SystemExit(result.returncode)
        produced = os.path.join(deck_run, deck["frame"])
        if not os.path.isfile(produced):
            raise SystemExit(f"missing native final frame: {deck['frame']}")
        shutil.copyfile(produced, os.path.join(run_dir, deck["frame"]))
    shutil.rmtree(scratch)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    if sys.argv[1] == "build":
        argv = sys.argv[2:]
        build(argv[0], argv[1], argv[2], int(argv[3]) if len(argv) > 3 else 4)
    elif sys.argv[1] == "run":
        argv = sys.argv[2:]
        run(argv[0], argv[1], argv[2],
            float(argv[3]) if len(argv) > 3 else None)
    else:
        raise SystemExit(__doc__)
