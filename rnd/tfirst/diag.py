import sys,json,io,contextlib;sys.path.insert(0,'rnd');import replaytest as R
from kaggle_environments import make
bot,f=sys.argv[1],sys.argv[2]
r=json.load(open(f,encoding='utf8'));s=r['steps'];n=r['info']['TeamNames'];me=[i for i,x in enumerate(n) if 'asad' in x.lower()][0];op=1-me
fn=R.load(bot)
def rec(obs,conf=None):
    t=obs.get('step',0);a=s[t+1][op]['action'] if t+1<len(s) else None
    return a or {'farmer':['PASS'],'hands':[],'market':[]}
cfg=dict(r['configuration']);cfg['seed']=r['info']['seed']
with contextlib.redirect_stdout(io.StringIO()):
    env=make('kaggriculture',configuration=cfg);ag=[None,None];ag[me]=fn;ag[op]=rec;env.run(ag)
tot=0
for t in range(600,len(env.steps)-1):
    for o in (env.steps[t+1][me]['action'] or {}).get('market') or []:
        if o and o[:2]==['SELL','TOMATO']:
            tot+=o[2];print(t,t//24,t%24,o,env.steps[t][0]['observation']['market']['prices']['TOMATO'])
print('total',tot)
