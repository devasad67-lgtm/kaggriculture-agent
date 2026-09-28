"""python btune.py '<json list of cfg dicts>' --opp dp_L720a --seeds 3"""
import sys,io,contextlib,json,os,argparse,multiprocessing as mp
sys.path.insert(0,'.')
def run(args):
    cfg,opp,seed,seat=args
    os.environ['BEAST_CFG']=json.dumps(cfg)
    import importlib.util
    spec=importlib.util.spec_from_file_location('bm','D:/kaggle/beast/main.py'); bm=importlib.util.module_from_spec(spec); spec.loader.exec_module(bm)
    from tourney import resolve
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        from kaggle_environments import make
        env=make("kaggriculture",configuration={"seed":seed,"episodeSteps":720},debug=False)
        agents=[bm.agent,resolve(opp)] if seat==0 else [resolve(opp),bm.agent]
        env.run(agents)
    f=env.steps[-1]; me=f[seat].reward or 0; op=f[1-seat].reward or 0
    return json.dumps(cfg),me,op
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('cfgs'); ap.add_argument('--opp',default='dp_L720a'); ap.add_argument('--seeds',type=int,default=3); ap.add_argument('--seed0',type=int,default=2000); ap.add_argument('--both',action='store_true')
    o=ap.parse_args(); cfgs=json.loads(o.cfgs)
    jobs=[(c,o.opp,o.seed0+s,seat) for c in cfgs for s in range(o.seeds) for seat in ((0,1) if o.both else (0,))]
    res={}
    with mp.Pool(4,maxtasksperchild=1) as pool:
        for k,me,op in pool.imap_unordered(run,jobs): res.setdefault(k,[]).append((me,op))
    for k,v in res.items():
        n=len(v); print(f"{sum(a for a,_ in v)/n:9.0f} {sum(a-b for a,b in v)/n:9.0f} W{sum(a>b for a,b in v)}/{n}  {k}")
