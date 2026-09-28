# parallel replay test: python rnd/rtbatch.py <bot_main.py> <out.jsonl> <dir|file>... [--n N] [--top K]
import sys,glob,json,os
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0,'rnd')
def job(a):
    import replaytest
    try: return replaytest.run(*a)
    except Exception as e: return dict(f=os.path.basename(a[1]),err=repr(e))
if __name__=='__main__':
    bot,out=sys.argv[1],sys.argv[2]; args=sys.argv[3:]; n=None
    if '--n' in args: i=args.index('--n'); n=int(args[i+1]); args=args[:i]+args[i+2:]
    fs=[]
    for a in args: fs+=sorted(glob.glob(a+'/*.json')) if os.path.isdir(a) else [a]
    if n: fs=fs[:n]
    done=set()
    if os.path.exists(out): done={json.loads(l)['f'] for l in open(out)}
    fs=[f for f in fs if os.path.basename(f) not in done]
    with ProcessPoolExecutor(4) as ex, open(out,'a') as o:
        for x in ex.map(job,[(bot,f) for f in fs]):
            o.write(json.dumps(x)+'\n'); o.flush()
