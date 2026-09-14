"""Execute one unmodified SAB runner with a bounded process-group lifetime."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

def main():
    source=sys.argv[1]
    checks=sys.argv[2]
    output=sys.argv[3]
    cap=sys.argv[4]
    out_dir=output
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    checks=Path(checks).resolve(); name=checks.name
    env=os.environ.copy()
    env.update(SOURCE_DIR=str(Path(source).resolve()),CHECK_DIR=str(checks),OUT_DIR=str(output.resolve()))
    started=time.monotonic()
    with (output/'run.log').open('w') as log:
        proc=subprocess.Popen(['bash',str(checks/'run.sh'),'nominal'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            code=proc.wait(timeout=float(cap))
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGKILL)
            proc.wait(timeout=5)
            code=124
    record={'check':name,'status':'ok' if code==0 else 'failed','exit':code,'wall':time.monotonic()-started}
    # The upstream runner couples configure, build, and run. On failure we do
    # not guess that compilation succeeded or reinterpret a crash as floor 0.
    if code==0: record['build']='ok'
    (output/'_run_status.json').write_text(json.dumps(record)+'\n')
    if code==0:
        with open(os.path.join(out_dir,'run.ok'),'w') as sentinel:
            sentinel.write('ok\n')
    return code

if __name__=='__main__': raise SystemExit(main())
