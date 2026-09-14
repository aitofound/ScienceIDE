"""Build exactly the mutable source and execute unchanged public checks."""
import json,os,signal,subprocess,sys
from pathlib import Path
def build(tree,site,jobs=2):
    env=dict(os.environ,NPY_NUM_BUILD_JOBS=str(jobs),CFLAGS='-ffp-contract=off',CXXFLAGS='-ffp-contract=off')
    subprocess.run([sys.executable,'setup.py','build_ext','--inplace'],cwd=tree,env=env,check=True)
def run(tree,site,check_dir,out_dir,timeout=1800):
    Path(out_dir).mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,SOURCE_DIR=tree,CHECK_DIR=check_dir,OUT_DIR=out_dir,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',JOBLIB_MULTIPROCESSING='0')
    proc=subprocess.Popen(['bash',str(Path(check_dir,'run.sh')),'nominal'],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
    try:
        out,err=proc.communicate(timeout=timeout); code=proc.returncode
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid,signal.SIGKILL)
        out,err=proc.communicate(timeout=5); code=124
    Path(out_dir,'_run_status.json').write_text(json.dumps({'check':Path(check_dir).name,'status':'ok' if code==0 else 'failed','exit':code,'build':'ok'}))
    Path(out_dir,'run.log').write_text(out+err)
    Path(out_dir,'run.ok' if code==0 else 'run.failed').write_text(f'exit={code}\n')
    if code: raise SystemExit(code)
if __name__=='__main__':
    if sys.argv[1] in ('build','rebuild'): build(sys.argv[2],sys.argv[3],int(sys.argv[4]))
    elif sys.argv[1]=='run': run(*sys.argv[2:6],float(sys.argv[6]))
    else: raise SystemExit('unknown command')
