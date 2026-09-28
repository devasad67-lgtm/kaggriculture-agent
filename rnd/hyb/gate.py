# per-game live results for route FROUTE vs default, plus the board's first two shops
import sys,os,json,multiprocessing as mp,io,contextlib
sys.path.insert(0,'D:/kaggle/arena')
def job(a):
    cand,opp,seed,seat,fr=a
    os.environ['FROUTE']=str(fr)
    os.chdir('D:/kaggle/arena')
    from tourney import resolve
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        from kaggle_environments import make
        env=make('kaggriculture',configuration={'seed':seed,'episodeSteps':720})
        ags=[resolve(cand),resolve(opp)] if seat==0 else [resolve(opp),resolve(cand)]
        env.run(ags)
    fin=[x.reward for x in env.steps[-1]]
    shops=tuple(env.steps[150][0].observation['town']['unlocked_shops'][:2])
    me,op=(fin[0],fin[1]) if seat==0 else (fin[1],fin[0])
    return dict(fr=fr,opp=opp,seed=seed,seat=seat,me=me,op=op,shops=shops)
if __name__=='__main__':
    out=sys.argv[1]; opps=sys.argv[2].split(','); skip,n=int(sys.argv[3]),int(sys.argv[4])
    seeds=json.load(open('D:/kaggle/arena/ladder_seeds.json'))[skip:skip+n]
    jobs=[('L48_wf_fr',o,s,seat,fr) for fr in (-1,103) for o in opps for s in seeds for seat in (0,1)]
    with mp.Pool(4,maxtasksperchild=1) as pool, open(out,'a') as f:
        for x in pool.imap_unordered(job,jobs):
            f.write(json.dumps(x)+'\n'); f.flush()
