# Re-simulate replay-test games with a bot, save the new game as a replay json, then profile both sides.
# python rnd/lossdiag.py <bot_main.py> <outdir> <replay>...
import json,sys,os,io,contextlib
sys.path.insert(0,'rnd')
from concurrent.futures import ProcessPoolExecutor
def job(a):
    bot,f,out=a
    import replaytest
    from prof import prof
    r=json.load(open(f,encoding='utf8')); s=r['steps']; n=r['info']['TeamNames']
    me=[i for i,x in enumerate(n) if 'asad' in x.lower()][0]; op=1-me
    fn=replaytest.load(bot)
    def rec(obs,conf=None):
        t=obs.get('step',0); a=s[t+1][op]['action'] if t+1<len(s) else None
        return a or {'farmer':['PASS'],'hands':[],'market':[]}
    cfg=dict(r['configuration']); cfg['seed']=r['info']['seed']
    with contextlib.redirect_stdout(io.StringIO()):
        from kaggle_environments import make
        env=make('kaggriculture',configuration=cfg); ag=[None,None]; ag[me]=fn; ag[op]=rec; env.run(ag)
    st=[[dict(action=x['action'],observation=x['observation'],reward=x['reward']) for x in step] for step in env.steps]
    fin=[x['reward'] for x in env.steps[-1]]
    nr=dict(steps=st,info=dict(TeamNames=n,seed=cfg['seed']),rewards=fin,configuration=cfg)
    p=os.path.join(out,os.path.basename(f)); json.dump(nr,open(p,'w'),default=str)
    return os.path.basename(f),me,prof(p)
if __name__=='__main__':
    bot,out=sys.argv[1],sys.argv[2]; os.makedirs(out,exist_ok=True)
    with ProcessPoolExecutor(int(os.environ.get("LD_PROCS","3"))) as ex:
        for name,me,pr in ex.map(job,[(bot,f,out) for f in sys.argv[3:]]):
            json.dump(dict(f=name,me=me,prof=pr),open(os.path.join(out,name+'.prof.json'),'w'))
            print(name,'ok',flush=True)
