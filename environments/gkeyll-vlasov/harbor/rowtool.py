#!/usr/bin/env python3
"""Build Gkeyll Vlasov or run one frozen vendored SAB row."""

import json
import os
import shutil
import signal
import subprocess
import sys

APP = "vlasov"
PROFILE = "vlasov-serial"


def copy_source(tree, target):
    keep_build = os.path.isfile(os.path.join(
        tree, "build", APP, f"libg0{APP}.so"))
    ignored = [".git", "_build", "run"]
    if not keep_build:
        ignored += ["build", "build-ieee"]
    shutil.copytree(tree, target, symlinks=True,
                    ignore=shutil.ignore_patterns(*ignored))


def rebuild(source, profile, jobs=2):
    if profile != PROFILE:
        raise SystemExit(f"unknown build profile: {profile}")
    subprocess.run(["make", f"-j{int(jobs)}", APP], cwd=source, check=True)
    library = os.path.join(source, "build", APP, f"libg0{APP}.so")
    if not os.path.isfile(library):
        raise SystemExit(f"build produced no {library}")


def build(tree, profile, build_dir, jobs=2):
    if profile != PROFILE:
        raise SystemExit(f"unknown build profile: {profile}")
    if os.path.isdir(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)
    source = os.path.join(build_dir, "source")
    copy_source(tree, source)
    multiarch = subprocess.check_output(
        ["dpkg-architecture", "-qDEB_HOST_MULTIARCH"], text=True).strip()
    arch = "-march=native" + (" -D__arm64__" if os.uname().machine in ("aarch64", "arm64") else "")
    configure = ["./configure", "--prefix=/usr", f"--app={APP}",
                 f"ARCH_FLAGS={arch}", "--lapack-inc=/usr/include",
                 f"--lapack-lib=/usr/lib/{multiarch}",
                 "--lapack-lib-name=openblas -llapacke",
                 "--superlu-inc=/usr/include/superlu",
                 f"--superlu-lib=/usr/lib/{multiarch}",
                 "--superlu-lib-name=superlu"]
    subprocess.run(configure, cwd=source, check=True)
    rebuild(source, profile, jobs)


def run(builds_root, case_dir, check_dir, run_dir, timeout=None):
    row = json.load(open(os.path.join(case_dir, "row.json"), encoding="utf-8"))
    check, profile = row["check"], row["profile"]
    if os.path.basename(check_dir) != check:
        raise SystemExit("row/check directory identity mismatch")
    source = os.path.abspath(os.path.join(builds_root, profile, "source"))
    if os.path.isdir(run_dir):
        shutil.rmtree(run_dir)
    os.makedirs(run_dir)
    env = os.environ.copy()
    env.update(SOURCE_DIR=source, OUT_DIR=os.path.abspath(run_dir),
               CHECK_DIR=os.path.abspath(check_dir), SAB_MAKE_JOBS="2",
               OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", LANG="C.UTF-8")
    proc = subprocess.Popen(["bash", os.path.join(check_dir, "run.sh"), "nominal"],
                            cwd=check_dir, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, env=env,
                            start_new_session=True)
    try:
        stdout, stderr = proc.communicate(timeout=float(timeout) if timeout else None)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        stdout, stderr = proc.communicate()
        open(os.path.join(run_dir, "run.log"), "wb").write(stdout + stderr)
        raise SystemExit(124)
    open(os.path.join(run_dir, "run.log"), "wb").write(stdout + stderr)
    if proc.returncode:
        sys.stderr.buffer.write(stderr)
        raise SystemExit(proc.returncode)
    rubric = json.load(open(os.path.join(check_dir, "rubric.json"), encoding="utf-8"))
    missing = [item["path"] for item in rubric["comparison"]["files"]
               if not os.path.isfile(os.path.join(run_dir, item["path"]))]
    if missing:
        raise SystemExit(f"{check}: missing outputs: {missing}")
    with open(os.path.join(run_dir, "run.ok"), "w", encoding="utf-8") as handle:
        handle.write(f"check={check}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    if sys.argv[1] == "build":
        args = sys.argv[2:]
        build(args[0], args[1], args[2], int(args[3]) if len(args) > 3 else 2)
    elif sys.argv[1] == "rebuild":
        args = sys.argv[2:]
        rebuild(args[0], args[1], int(args[2]) if len(args) > 2 else 2)
    elif sys.argv[1] == "run":
        args = sys.argv[2:]
        run(args[0], args[1], args[2], args[3],
            float(args[4]) if len(args) > 4 else None)
    else:
        raise SystemExit(__doc__)
