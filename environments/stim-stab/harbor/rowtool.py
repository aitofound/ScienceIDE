#!/usr/bin/env python3
"""Build Stim once, then run an unmodified SAB check against that build."""

import os
import shutil
import subprocess
import sys
import tempfile


def build(tree, build_dir, jobs=2, kind="both", reuse=False):
    if not reuse:
        shutil.rmtree(build_dir, ignore_errors=True)
    os.makedirs(build_dir, exist_ok=True)
    subprocess.run([
        "cmake", "-S", tree, "-B", build_dir, "-G", "Ninja",
        "-DCMAKE_BUILD_TYPE=Release",
        "-Dpybind11_DIR=" + subprocess.check_output(
            [sys.executable, "-m", "pybind11", "--cmakedir"], text=True).strip(),
        "-DCMAKE_CXX_FLAGS=-ffp-contract=off",
    ], check=True)
    targets = {"cli": ["stim"], "py": ["stim_python_bindings"],
               "both": ["stim", "stim_python_bindings"]}.get(kind)
    if targets is None:
        raise SystemExit(f"unknown build kind: {kind}")
    subprocess.run(["cmake", "--build", build_dir, "--target", *targets,
                    "-j", str(jobs)], check=True)


def run(tree, build_dir, check_dir, out_dir, timeout=900):
    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir)
    check = os.path.basename(os.path.abspath(check_dir))
    with tempfile.TemporaryDirectory(prefix="stim-row-") as scratch:
        shim = os.path.join(scratch, "shim")
        os.makedirs(shim)
        cmake = os.path.join(shim, "cmake")
        with open(cmake, "w") as handle:
            handle.write("#!/bin/sh\nexit 0\n")
        os.chmod(cmake, 0o755)
        source = open(os.path.join(check_dir, "run.sh"), encoding="utf-8").read()
        anchor = 'cp -R "$SOURCE_DIR/." "$WORK/src"'
        if source.count(anchor) != 1:
            raise SystemExit(f"{check}: SAB run.sh source-copy anchor drifted")
        source = source.replace(anchor, 'ln -s "$SOURCE_DIR" "$WORK/src"', 1)
        source = source.replace("$WORK/b", build_dir)
        script = os.path.join(scratch, "run.sh")
        with open(script, "w", encoding="utf-8") as handle:
            handle.write(source)
        env = dict(os.environ)
        env.update({"SOURCE_DIR": tree, "OUT_DIR": out_dir,
                    "CHECK_DIR": check_dir, "SAB_BUILD_JOBS": "2",
                    "PATH": shim + os.pathsep + env.get("PATH", "")})
        try:
            result = subprocess.run(["bash", script, "nominal"], env=env,
                                    capture_output=True, text=True,
                                    timeout=float(timeout))
            code = result.returncode
            log = result.stdout + result.stderr
        except subprocess.TimeoutExpired as exc:
            code = 124
            log = (exc.stdout or "") + (exc.stderr or "")
    with open(os.path.join(out_dir, "run.log"), "w", encoding="utf-8") as handle:
        handle.write(log[-5000:])
    marker = "run.ok" if code == 0 else "run.failed"
    with open(os.path.join(out_dir, marker), "w", encoding="utf-8") as handle:
        handle.write(f"check={check}\nexit={code}\n")
    if code:
        print(log[-2000:], file=sys.stderr)
        raise SystemExit(code)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    if sys.argv[1] == "build":
        build(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 2,
              sys.argv[5] if len(sys.argv) > 5 else "both")
    elif sys.argv[1] == "rebuild":
        build(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 2,
              sys.argv[5] if len(sys.argv) > 5 else "both", reuse=True)
    elif sys.argv[1] == "run":
        run(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5],
            float(sys.argv[6]) if len(sys.argv) > 6 else 900)
    else:
        raise SystemExit(__doc__)
