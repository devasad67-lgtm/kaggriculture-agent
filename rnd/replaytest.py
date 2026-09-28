# Counterfactual ladder test: our live bot vs the opponent's recorded actions, same seed.
# python rnd/replaytest.py <bot_main.py> <replay.json>...   -> per game: orig margin, new margin
import json,sys,io,contextlib,time,os
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    from kaggle_environments import make
    from kaggle_environments.agent import get_last_callable
def load(path):
    src=open(path,encoding='utf-8').read()
    with contextlib.redirect_stdout(io.StringIO()):
        return get_last_callable(src,path=path)
def run(bot_path,f):
    r=json.load(open(f,encoding='utf8')); s=r['steps']; n=r['info']['TeamNames']
    me=[i for i,x in enumerate(n) if 'asad' in x.lower()][0]; op=1-me
    fn=load(bot_path)
    def rec(obs,conf=None):
        t=obs.get('step',0)
        a=s[t+1][op]['action'] if t+1<len(s) else None
        return a or {'farmer':['PASS'],'hands':[],'market':[]}
    cfg=dict(r['configuration']); cfg['seed']=r['info']['seed']
    with contextlib.redirect_stdout(io.StringIO()):
        env=make('kaggriculture',configuration=cfg)
        agents=[None,None]; agents[me]=fn; agents[op]=rec
        env.run(agents)
    fin=[x['reward'] for x in env.steps[-1]]
    so=list(s[-1][0]['observation']['town']['unlocked_shops']); sn=list(env.steps[-1][0]['observation']['town']['unlocked_shops'])
    k=next((i for i,(a,b) in enumerate(zip(so,sn)) if a!=b),min(len(so),len(sn)) if len(so)!=len(sn) else None)
    E=fn.__globals__.get('_EDGE'); tel={}
    if E is not None:
        tel['err']=E.errors
        c=getattr(E,'_courier',None); m=getattr(E,'_meter',None)
        if c: tel['trips']=c.trips; tel['cunits']=c.units
        if m: tel['mcut']=m.cut
        tel['veto']=getattr(E,'vetoed',0)
        fh=getattr(E,'_fh',None)
        if fh: tel['fh_hired']=fh.hired; tel['fh_ferts']=fh.ferts
        df=getattr(E,'_defer',None)
        if df: tel['dskips']=df.skips
        cf=getattr(E,'_cfill',None)
        if cf: tel['cfill']=cf.total; tel['cgate']=getattr(cf,'gated_step',None); tel['mirror']=getattr(cf,'mirror',None)
    return dict(tel=tel,f=os.path.basename(f),opp=n[op],orig=(r['rewards'][me],r['rewards'][op]),new=(fin[me],fin[op]),status=env.steps[-1][me]['status'],shops_same=so==sn,shop_div=k)
if __name__=='__main__':
    bot=sys.argv[1]
    for f in sys.argv[2:]:
        t=time.time(); x=run(bot,f)
        print(json.dumps(x),f"{time.time()-t:.0f}s",flush=True)
