# run one replay test with a bot and print per-product revenue/units vs original, shed peaks, hires
import sys,json,io,contextlib,collections
sys.path.insert(0,'rnd'); import replaytest as R
from prof import prof
bot,f=sys.argv[1],sys.argv[2]
r=json.load(open(f,encoding='utf8')); n=r['info']['TeamNames']; me=[i for i,x in enumerate(n) if 'asad' in x.lower()][0]; op=1-me
s=r['steps']; fn=R.load(bot)
def rec(obs,conf=None):
    t=obs.get('step',0); a=s[t+1][op]['action'] if t+1<len(s) else None
    return a or {'farmer':['PASS'],'hands':[],'market':[]}
cfg=dict(r['configuration']); cfg['seed']=r['info']['seed']
with contextlib.redirect_stdout(io.StringIO()):
    env=R.make('kaggriculture',configuration=cfg); ag=[None,None]; ag[me]=fn; ag[op]=rec; env.run(ag)
new={'info':r['info'],'rewards':[x['reward'] for x in env.steps[-1]],'steps':[[{'observation':x['observation'],'action':x['action'],'status':x['status']} for x in st] for st in env.steps]}
json.dump(new,open('rnd/_diag.json','w'))
a=prof(f)[me]; b=prof('rnd/_diag.json')[me]
print('orig',a['reward'],'new',b['reward'])
for k in sorted(set(a['sold'])|set(b['sold'])):
    print(f"{k:11s} orig {a['sold'].get(k,0):4d}@{a['avgp'].get(k,0):4d}  new {b['sold'].get(k,0):4d}@{b['avgp'].get(k,0):4d}")
print('hires orig',a['hires']); print('hires new ',b['hires'])
sh=[sum(new['steps'][t][me]['observation']['private']['shed'].values()) for t in range(0,720,24)]
print('shed@h0',sh)
E=fn.__globals__.get('_EDGE'); print('brain stats',getattr(getattr(E,'_brain',None),'stats',None),'errors',E.errors)
