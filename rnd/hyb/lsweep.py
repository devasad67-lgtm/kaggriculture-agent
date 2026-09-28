# live route sweep: L48_wf_fr (FROUTE=r) vs L48_wf on ladder seeds. python rnd/hyb/lsweep.py out.jsonl skip nseeds routes|all [seat]
import sys,os,json,multiprocessing as mp
sys.path.insert(0,'D:/kaggle/arena')
def job(a):
    seed,r,seat=a; os.environ['FROUTE']=str(r)
    from tourney import play
    x=play(('L48_wf_fr','L48_wf',seed) if seat==0 else ('L48_wf','L48_wf_fr',seed))
    me,op=(x['ra'],x['rb']) if seat==0 else (x['rb'],x['ra'])
    return dict(seed=seed,route=r,seat=seat,me=me,op=op,sa=x['sa'],sb=x['sb'])
if __name__=='__main__':
    out,skip,n,rs=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]
    seat=int(sys.argv[5]) if len(sys.argv)>5 else 0
    seeds=json.load(open('arena/ladder_seeds.json'))[skip:skip+n]
    routes=[-1]+list(range(0,13))+list(range(100,129)) if rs=='all' else [int(v) for v in rs.split(',')]
    routes=[r for r in routes if r!=101 or True]
    done=set()
    if os.path.exists(out): done={(json.loads(l)['seed'],json.loads(l)['route'],json.loads(l)['seat']) for l in open(out)}
    jobs=[(s,r,seat) for s in seeds for r in routes if (s,r,seat) not in done]
    os.chdir('arena')
    with mp.Pool(4,maxtasksperchild=1) as pool, open(os.path.join('..',out),'a') as o:
        for x in pool.imap_unordered(job,jobs):
            o.write(json.dumps(x)+'\n'); o.flush()
