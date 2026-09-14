#!/usr/bin/env python3
"""Build one Athena chemistry profile or run one frozen evolution row.

    rowtool.py build TREE PROFILE BUILD_DIR [JOBS] [CVODE_PATH]
    rowtool.py run BUILDS_ROOT CASE_DIR RUN_DIR [TIMEOUT_SEC]

Only native history and final full-precision tab frames are delivered.  The
tool is stdlib-only and is shared by native authoring, verifier, and oracle.
"""

import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile


HERE = os.path.dirname(os.path.abspath(__file__))
PROFILES_PATH = next(
    path for path in (os.path.join(HERE, "build_profiles.json"),
                      os.path.join(os.path.dirname(HERE), "build_profiles.json"))
    if os.path.isfile(path))


def profiles():
    with open(PROFILES_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def _copy_source(tree, target):
    source_abs = os.path.abspath(tree)

    def ignore(path, names):
        omitted = {".git", "bin", "obj"}
        if os.path.abspath(path) == source_abs:
            omitted |= {"_build", "run"}
        return sorted(omitted & set(names))

    shutil.copytree(tree, target, symlinks=True, ignore=ignore)


def configure_args(profile, cvode_path):
    table = profiles()
    if profile not in table:
        raise ValueError(f"unknown build profile: {profile}")
    return [arg.replace("@CVODE_PATH@", cvode_path) for arg in table[profile]]


def build(tree, profile, build_dir, jobs=4, cvode_path="/usr"):
    if os.path.isdir(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)
    source = os.path.join(build_dir, "source")
    obj = os.path.join(build_dir, "obj")
    binary_dir = os.path.join(build_dir, "bin")
    _copy_source(tree, source)
    configure = [sys.executable, "configure.py"] + configure_args(
        profile, cvode_path)
    subprocess.run(configure, cwd=source, check=True)
    subprocess.run(["make", f"-j{int(jobs)}", f"EXE_DIR={binary_dir}/",
                    f"OBJ_DIR={obj}/"], cwd=source, check=True)
    binary = os.path.join(binary_dir, "athena")
    if not os.access(binary, os.X_OK):
        raise RuntimeError("build produced no executable athena")


def _timeout_text(value):
    if value is None:
        return ""
    return value.decode(errors="replace") if isinstance(value, bytes) else value


def _output_number(path):
    stem = os.path.basename(path).removesuffix(".tab")
    try:
        return int(stem.rsplit(".", 1)[1])
    except (IndexError, ValueError):
        return None


def run(builds_root, case_dir, run_dir, timeout=None):
    with open(os.path.join(case_dir, "row.json"), encoding="utf-8") as handle:
        row = json.load(handle)
    profile = row["profile"]
    build_dir = os.path.abspath(os.path.join(builds_root, profile))
    binary = os.path.join(build_dir, "bin", "athena")
    if not os.access(binary, os.X_OK):
        raise RuntimeError(f"missing {profile} executable: {binary}")

    parent = os.path.dirname(os.path.abspath(run_dir))
    os.makedirs(parent, exist_ok=True)
    if os.path.isdir(run_dir):
        shutil.rmtree(run_dir)
    work = tempfile.mkdtemp(prefix="chem-row-", dir=parent)
    try:
        for name in os.listdir(case_dir):
            source = os.path.join(case_dir, name)
            if name == "row.json" or not os.path.isfile(source):
                continue
            shutil.copy2(source, os.path.join(work, name))
        if profile == "kida":
            source = os.path.join(
                build_dir, "source", "src", "chemistry", "network",
                "kida_network_files", "gow17")
            target = os.path.join(work, "kida_network_files", "gow17")
            shutil.copytree(source, target)

        command = [os.path.abspath(binary), "-i", "athinput.chem"]
        command += list(row.get("argv_overrides", []))
        try:
            result = subprocess.run(
                command, cwd=work, capture_output=True, text=True,
                timeout=float(timeout) if timeout else None)
            exit_code = result.returncode
            stdout, stderr = result.stdout, result.stderr
        except subprocess.TimeoutExpired as ex:
            exit_code = "timeout"
            stdout, stderr = _timeout_text(ex.stdout), _timeout_text(ex.stderr)
        if exit_code != 0:
            return {"exit": exit_code, "stdout": stdout, "stderr": stderr,
                    "frames": []}

        history = os.path.join(work, row["problem_id"] + ".hst")
        if not os.path.isfile(history):
            raise RuntimeError("run produced no history evolution")
        numbered = [(number, path) for path in glob.glob(
            os.path.join(work, "*.out1.*.tab"))
                    if (number := _output_number(path)) is not None]
        if not numbered:
            raise RuntimeError("run produced no full-precision tab frames")
        final_number = max(number for number, _ in numbered)
        final = sorted(path for number, path in numbered
                       if number == final_number)
        if len(final) != int(row["expected_final_tab_blocks"]):
            raise RuntimeError(
                f"final tab block count {len(final)} differs from row contract")

        os.makedirs(run_dir)
        shutil.copy2(history, os.path.join(run_dir, os.path.basename(history)))
        for path in final:
            shutil.copy2(path, os.path.join(run_dir, os.path.basename(path)))
        return {"exit": 0, "stdout": stdout, "stderr": stderr,
                "frames": [os.path.basename(history)]
                          + [os.path.basename(path) for path in final]}
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    try:
        if sys.argv[1] == "build":
            argv = sys.argv[2:]
            build(argv[0], argv[1], argv[2],
                  int(argv[3]) if len(argv) > 3 else 4,
                  argv[4] if len(argv) > 4 else "/usr")
        elif sys.argv[1] == "run":
            argv = sys.argv[2:]
            result = run(argv[0], argv[1], argv[2],
                         float(argv[3]) if len(argv) > 3 else None)
            if result["exit"] != 0:
                sys.stderr.write(result["stdout"] + result["stderr"])
                raise SystemExit(124 if result["exit"] == "timeout"
                                 else result["exit"])
        else:
            raise SystemExit(__doc__)
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as ex:
        raise SystemExit(str(ex)) from ex
