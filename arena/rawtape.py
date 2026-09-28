"""Raw tape experiments. python rawtape.py <replay> <seat_team> <opp: 'tape'|botname> <seed|orig>"""
import json,sys,io,contextlib
sys.path.insert(0,'.'); from tourney import resolve
rep,team,opp,sd=sys.argv[1:5]
r=json.load(open(rep,encoding='utf8')); n=r['info']['TeamNames']; p=n.index(team)
seed=r['info']['seed'] if sd=='orig' else int(sd)
def tape_of(q):
    T=[]
    for t in range(1,720):
        a=r['steps'][t][q]['action'] or {}
        T.append({'farmer':a.get('farmer',['PASS']),'hands':a.get('hands',[]),'market':[o for o in (a.get('market') or []) if o]})
    return T
def mk(T):
    def ag(obs,cfg=None):
        s=obs['step']; return T[s] if s<len(T) else {'farmer':['PASS'],'hands':[],'market':[]}
    return ag
A=[None,None]; A[p]=mk(tape_of(p)); A[1-p]=mk(tape_of(1-p)) if opp=='tape' else resolve(opp)
with contextlib.redirect_stdout(io.StringIO()):
    from kaggle_environments import make
    env=make("kaggriculture",configuration={"seed":seed,"episodeSteps":720},debug=False)
    env.run(A)
s=env.steps; orig=r['steps']
print('orig rewards',r['rewards'],' new',[s[-1][i].reward for i in (0,1)])
# first divergence of our seat's farm money / tiles vs original
for t in range(1,720):
    a=s[t][0].observation['farms'][p]; b=orig[t][0]['observation']['farms'][p]
    if a['money']!=b['money'] or json.dumps(a['tiles'])!=json.dumps(b['tiles']):
        print('first divergence step',t,'money new',a['money'],'orig',b['money']); break
for d in range(0,30,3):
    t=d*24+23; print('day',d,'new',round(s[t][0].observation['farms'][p]['money']),'orig',round(orig[t][0]['observation']['farms'][p]['money']))
