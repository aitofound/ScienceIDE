"""Image-local genmake2 and final-state execution helpers."""

import glob
import json
import os
import re
import shutil
import subprocess
import time


def build_profile(source, case_dir, build_dir, jobs=4):
    shutil.rmtree(build_dir, ignore_errors=True)
    os.makedirs(build_dir, exist_ok=True)
    local = os.path.join(case_dir, "mods", "genmake_local")
    if os.path.isfile(local):
        shutil.copy2(local, os.path.join(build_dir, "genmake_local"))
    commands = [
        [os.path.join(source, "tools", "genmake2"), "-rootdir", source,
         "-mods", os.path.join(case_dir, "mods"), "-optfile",
         os.path.join(source, "tools", "build_options", "linux_amd64_gfortran"),
         "-extra_flag=-ffp-contract=off"],
        ["make", "depend"], ["make", "-j", str(jobs)],
    ]
    started, output = time.monotonic(), []
    for command in commands:
        result = subprocess.run(command, cwd=build_dir, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output.append(result.stdout)
        if result.returncode:
            return {"exit": result.returncode,
                    "wall": round(time.monotonic() - started, 4),
                    "tail": "".join(output)[-4000:]}
    return {"exit": 0, "wall": round(time.monotonic() - started, 4)}


def run_profile(binary, case_dir, out_dir, timeout=120.0):
    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir)
    run_dir = out_dir + ".run"
    shutil.rmtree(run_dir, ignore_errors=True)
    shutil.copytree(os.path.join(case_dir, "input"), run_dir)
    started = time.monotonic()
    status = {"check": os.path.basename(case_dir), "status": "crash", "ranks": 1}
    try:
        result = subprocess.run([binary], cwd=run_dir, capture_output=True,
                                text=True, timeout=timeout)
        normal = "PROGRAM MAIN: Execution ended Normally" in result.stdout
        status.update(exit=result.returncode,
                      status="ok" if result.returncode == 0 and normal else "crash",
                      tail=(result.stdout + result.stderr)[-1200:])
    except subprocess.TimeoutExpired:
        status.update(exit="timeout", status="timeout")
    status["wall"] = round(time.monotonic() - started, 4)
    if status["status"] == "ok":
        found = {}
        for path in glob.glob(os.path.join(run_dir, "*.data")):
            match = re.match(r"^[A-Za-z_0-9]+[.](\d{10})[.]data$",
                             os.path.basename(path))
            if match:
                found.setdefault(match.group(1), []).append(path)
        if not found:
            status["status"] = "missing_output"
        else:
            final = max(found)
            status["final_iteration"] = final
            for path in sorted(found[final]):
                meta = path[:-5] + ".meta"
                if not os.path.isfile(meta):
                    status["status"] = "missing_output"
                    break
                shutil.copy2(path, os.path.join(out_dir, os.path.basename(path)))
                shutil.copy2(meta, os.path.join(out_dir, os.path.basename(meta)))
    with open(os.path.join(out_dir, "_run_status.json"), "w") as handle:
        json.dump(status, handle, indent=1, sort_keys=True)
        handle.write("\n")
    shutil.rmtree(run_dir, ignore_errors=True)
    return status
