#!/usr/bin/env python3
"""Build one pinned self-gravity variant or run one frozen Jeans row."""

import glob
import json
import os
import shutil
import subprocess
import sys


VARIANTS = {
    "mg_serial": ["--prob=jeans", "--grav=mg"],
    "mg_mpi": ["--prob=jeans", "--grav=mg", "-mpi"],
    "fft_mpi": ["--prob=jeans", "--grav=fft", "-fft", "-mpi",
                "--fftw_path=/usr"],
}


def _copy_source(tree, target):
    source_abs = os.path.abspath(tree)

    def ignore(path, names):
        omitted = {".git", "bin", "obj"}
        if os.path.abspath(path) == source_abs:
            omitted |= {"_build", "run"}
        return sorted(omitted & set(names))

    shutil.copytree(tree, target, symlinks=True, ignore=ignore)


def build(tree, variant, build_dir, jobs=4):
    if variant not in VARIANTS:
        raise SystemExit(f"unknown build variant: {variant}")
    if os.path.isdir(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)
    source = os.path.join(build_dir, "source")
    obj = os.path.join(build_dir, "obj")
    binary_dir = os.path.join(build_dir, "bin")
    _copy_source(tree, source)
    configure = [sys.executable, "configure.py"] + VARIANTS[variant]
    configure += ["--coord=cartesian", "--cflag=-O2 -g0 -ffp-contract=off"]
    subprocess.run(configure, cwd=source, check=True)
    subprocess.run(["make", f"-j{int(jobs)}", f"EXE_DIR={binary_dir}/",
                    f"OBJ_DIR={obj}/"], cwd=source, check=True)
    if not os.access(os.path.join(binary_dir, "athena"), os.X_OK):
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
    shutil.copy(os.path.join(case_dir, "athinput.jeans"),
                os.path.join(run_dir, "athinput.jeans"))
    command = [binary, "-i", "athinput.jeans"] + list(row["argv_overrides"])
    if int(row["ranks"]) > 1:
        command = ["mpirun", "--allow-run-as-root", "--oversubscribe", "-n",
                   str(row["ranks"])] + command
    result = subprocess.run(command, cwd=run_dir, capture_output=True, text=True,
                            timeout=float(timeout) if timeout else None)
    open(os.path.join(run_dir, "stdout.txt"), "w").write(result.stdout)
    open(os.path.join(run_dir, "stderr.txt"), "w").write(result.stderr)
    if result.returncode:
        sys.stderr.write(result.stdout + result.stderr)
        raise SystemExit(result.returncode)
    hst = os.path.join(run_dir, row["problem_id"] + ".hst")
    if not os.path.isfile(hst):
        raise SystemExit("run produced no history evolution")
    numbered = []
    for path in glob.glob(os.path.join(run_dir, "*.vtk")):
        try:
            number = int(os.path.basename(path).removesuffix(".vtk").rsplit(".", 1)[1])
        except (IndexError, ValueError):
            continue
        numbered.append((number, path))
    if not numbered:
        raise SystemExit("run produced no conserved VTK frames")
    final_number = max(number for number, _ in numbered)
    final = []
    for number, path in numbered:
        if number == final_number:
            final.append(path)
        else:
            os.unlink(path)
    if len(final) != int(row["expected_final_vtk_blocks"]):
        raise SystemExit(f"final VTK block count {len(final)} differs from row contract")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    argv = sys.argv[2:]
    if sys.argv[1] == "build":
        build(argv[0], argv[1], argv[2], int(argv[3]) if len(argv) > 3 else 4)
    elif sys.argv[1] == "run":
        run(argv[0], argv[1], argv[2],
            float(argv[3]) if len(argv) > 3 else None)
    else:
        raise SystemExit(__doc__)
