"""Fail closed on unknown/build/timeout/grader failure; score completed straw."""
import argparse
import json
import math
import os
import signal
import subprocess
import sys
import tempfile

def run_process(command, timeout):
    process = subprocess.Popen(command, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, start_new_session=True)
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            stdout, stderr = process.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                stdout, stderr = process.communicate(timeout=1)
            except subprocess.TimeoutExpired:
                for pipe in (process.stdout, process.stderr):
                    pipe.close()
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=1)
    if timed_out:
        raise RuntimeError('measurement_failed: floor grader timeout')
    return process.returncode, stderr

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--grade', required=True)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--reference', required=True)
    parser.add_argument('--checks-dir', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--check', action='append', required=True)
    parser.add_argument('--straw-status', required=True)
    parser.add_argument('--timeout', type=float, default=120)
    args = parser.parse_args()
    if args.straw_status not in ('ok','crashed: run'):
        raise RuntimeError('measurement_failed: ' + args.straw_status)
    expected = {os.path.join(check,'_run_status.json') for check in args.check}
    found = {os.path.relpath(os.path.join(root,'_run_status.json'),args.candidate)
             for root,_,names in os.walk(args.candidate) if '_run_status.json' in names}
    if found != expected:
        raise RuntimeError('measurement_failed: incomplete or duplicate straw status')
    for check in args.check:
        value = json.load(open(os.path.join(args.candidate,check,'_run_status.json')))
        crash = value.get('status')=='failed' and value.get('build')=='ok' and type(value.get('exit')) is int and value['exit'] not in (0,124)
        ok = value.get('status')=='ok' and type(value.get('exit')) is int and value['exit']==0
        if value.get('check')!=check or not (crash or ok):
            raise RuntimeError('measurement_failed: invalid straw check status')
    with tempfile.TemporaryDirectory() as temporary:
        out, report = os.path.join(temporary,'reward.json'), os.path.join(temporary,'report.json')
        command = [sys.executable,args.grade,'--candidate',args.candidate,
            '--reference',args.reference,'--checks-dir',args.checks_dir,'--out',out,
            '--report',report,'--raw-floor-measurement']
        code, stderr = run_process(command, args.timeout)
        if code:
            raise RuntimeError('measurement_failed: floor grader '+stderr[-1000:])
        graded = json.load(open(out))
        value = graded['reward']
        per = {k:v for k,v in graded.items() if k.startswith('check_')}
        if type(value) not in (int,float) or not math.isfinite(value) or not 0 <= value < 0.65 or not per or graded.get('grader_error') or graded.get('nonconforming'):
            raise RuntimeError('invalid or uninformative measured floor')
        with open(args.out,'w') as handle:
            json.dump({'floor':value,'straw_status':args.straw_status,'per_check':per},handle,indent=2)

if __name__ == '__main__':
    main()
