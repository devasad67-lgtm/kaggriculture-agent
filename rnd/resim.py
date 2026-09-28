# Re-simulate a replay with recorded actions; log every committed market unit (exact).
import json,sys,collections,os,io,contextlib
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    import kaggle_environments.envs.kaggriculture.kaggriculture as K
    from kaggle_environments import make
LOG=[]; CUR={'t':0,'farms':None}
_orig=K._commit_unit; _pm=K._process_market
def _pmh(state,env):
    CUR['farms']=state[0].observation.farms; return _pm(state,env)
def _hook(op,item,price,farm,private,market,cap=100):
    ok=_orig(op,item,price,farm,private,market,cap)
    if ok:
        p=0 if farm is CUR['farms'][0] else 1
        LOG.append((CUR['t'],p,op,item,price))
    return ok
K._commit_unit=_hook; K._process_market=_pmh
def resim(f):
    r=json.load(open(f,encoding='utf8')); s=r['steps']
    LOG.clear()
    cfg=dict(r['configuration']); cfg['seed']=r['info']['seed']
    env=make('kaggriculture',configuration=cfg)
    def mk(p):
        def ag(obs,conf=None):
            t=obs.get('step',0); CUR['t']=t
            a=s[t+1][p]['action'] if t+1<len(s) else None
            return a or {'farmer':['PASS'],'hands':[],'market':[]}
        return ag
    env.run([mk(0),mk(1)])
    return r,env,list(LOG)
def sales(log):
    out=collections.defaultdict(list)  # (p,item)->[(t,price)]
    for t,p,op,item,price in log:
        if op=='SELL': out[(p,item)].append((t,price))
    return out
if __name__=='__main__':
    r,env,log=resim(sys.argv[1]); n=r['info']['TeamNames']
    print(n,'orig',r['rewards'],'resim',[x['reward'] for x in env.steps[-1]])
    S=sales(log); items=sys.argv[2].split(',') if len(sys.argv)>2 else ['STRAWBERRY','MILK','WOOL','MELON','TOMATO','EGG','CARROT']
    for it in items:
        for p in (0,1):
            xs=S[(p,it)]
            if not xs: continue
            byday=collections.defaultdict(list)
            for t,pr in xs: byday[t//24].append((t%24,pr))
            print(f"{n[p][:12]:12s} {it:10s} n={len(xs)} avg ${sum(x[1] for x in xs)/len(xs):.0f} :: "+' '.join(f"d{d}:"+','.join(f"h{h}@{pr}" for h,pr in v[:1])+f"x{len(v)}~{sum(q for _,q in v)//len(v)}" for d,v in sorted(byday.items())))
