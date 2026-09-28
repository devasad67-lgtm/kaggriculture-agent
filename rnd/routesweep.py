# python rnd/routesweep.py <bot_main.py> <out.jsonl> <routes comma> <gamelist.txt>
import sys,json,os
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0,'rnd')
def job(a):
    bot,f,r=a; os.environ['FROUTE']=str(r)
    import replaytest
    try: x=replaytest.run(bot,f)
    except Exception as e: x=dict(f=os.path.basename(f),err=repr(e))
    x['route']=r; return x
if __name__=='__main__':
    bot,out,rs,gl=sys.argv[1:5]; rs=[int(v) for v in rs.split(',')]
    fs=[l.strip() for l in open(gl) if l.strip()]
    done=set()
    if os.path.exists(out): done={(json.loads(l)['f'],json.loads(l)['route']) for l in open(out)}
    jobs=[(bot,f,r) for f in fs for r in rs if (os.path.basename(f),r) not in done]
    with ProcessPoolExecutor(4) as ex, open(out,'a') as o:
        for x in ex.map(job,jobs,chunksize=2):
            o.write(json.dumps(x)+'\n'); o.flush()
