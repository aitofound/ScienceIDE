"""Execute unchanged SAB checks and publish mandatory per-check run status."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

def run(tree, checkdir, out, timeout):
    output = Path(out)
    output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, SOURCE_DIR=tree, CHECK_DIR=checkdir, OUT_DIR=str(out))
    logpath = output / "run.log"
    with logpath.open("wb") as log:
        proc = subprocess.Popen(["bash", str(Path(checkdir) / "run.sh"), "nominal"],
                                env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = proc.wait(timeout=float(timeout))
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=5)
            code = 124
    built = "SAB_BUILD_SECONDS=" in logpath.read_text()
    if code == 0 and not built:
        code = 2
    status = {"check": Path(checkdir).name, "build": "ok" if built else "failed",
              "status": "ok" if code == 0 else "failed", "exit": code}
    (output / "_run_status.json").write_text(json.dumps(status) + "\n")
    if code == 0:
        with open(os.path.join(out, "run.ok"), "w") as marker:
            marker.write("ic=nominal\nexit=0\n")
    return code

if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]))
