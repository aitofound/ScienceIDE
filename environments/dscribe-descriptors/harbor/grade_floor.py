"""Fail closed on unknown/build/timeout/grader failure; score completed straw."""
import argparse
import json
import math
import os
import signal
import subprocess
import sys
import tempfile
import ast
from pathlib import Path
TERM_GRACE_SEC = KILL_GRACE_SEC = REAP_GRACE_SEC = 1.0

def run_process(command, timeout):
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        start_new_session=True)
    timed_out = False
    stdout = stderr = ""
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            stdout, stderr = process.communicate(timeout=TERM_GRACE_SEC)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                stdout, stderr = process.communicate(timeout=KILL_GRACE_SEC)
            except subprocess.TimeoutExpired as error:
                stdout = error.output or ""
                stderr = error.stderr or ""
                for pipe in (process.stdout, process.stderr):
                    pipe.close()
                try:
                    process.wait(timeout=REAP_GRACE_SEC)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=REAP_GRACE_SEC)
    return (124 if timed_out else process.returncode, stdout or '', stderr or '', timed_out)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--grade', required=True)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--reference', required=True)
    parser.add_argument('--checks-dir', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--check', action='append')
    parser.add_argument('--straw-status', required=True)
    parser.add_argument('--timeout', type=float, default=120)
    args = parser.parse_args()
    if args.straw_status not in ('ok','crashed: run'):
        raise RuntimeError('measurement_failed: ' + args.straw_status)
    checks=args.check
    if checks is None:
        assignments=[n for n in ast.walk(ast.parse(Path(args.grade).read_text())) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CHECKS' for t in n.targets)]
        if len(assignments)!=1: raise RuntimeError('measurement_failed: missing check identity')
        checks=ast.literal_eval(assignments[0].value)
    seen=[]
    for path in Path(args.candidate).rglob('_run_status.json'):
        status=json.loads(path.read_text())
        check=status.get('check')
        if path.parent.parent != Path(args.candidate) or check!=path.parent.name or check not in checks or check in seen:
            raise RuntimeError('measurement_failed: invalid check identity')
        if status.get('status')!='ok' or type(status.get('exit')) is not int or status['exit']!=0 or status.get('build','ok')!='ok':
            raise RuntimeError('measurement_failed: non-ok straw')
        seen.append(check)
    if set(seen)!=set(checks): raise RuntimeError('measurement_failed: incomplete straw statuses')
    with tempfile.TemporaryDirectory() as temporary:
        out, report = os.path.join(temporary,'reward.json'), os.path.join(temporary,'report.json')
        command = [sys.executable,args.grade,'--candidate',args.candidate,
            '--reference',args.reference,'--checks-dir',args.checks_dir,'--out',out,
            '--report',report,'--raw-floor-measurement']
        rc,stdout,stderr,timed_out = run_process(command,args.timeout)
        if rc or timed_out:
            raise RuntimeError('measurement_failed: floor grader '+stderr[-1000:])
        graded = json.load(open(out))
        value = graded['reward']
        per = {k:v for k,v in graded.items() if k.startswith('check_')}
        if type(value) not in (int,float) or not math.isfinite(value) or not 0 <= value < 0.65 or not per or graded.get('grader_error'):
            raise RuntimeError('invalid or uninformative measured floor')
        with open(args.out,'w') as handle:
            json.dump({'floor':value,'straw_status':args.straw_status,'per_check':per},handle,indent=2)

if __name__ == '__main__':
    main()
