# Play team's recorded tape (from replay A) in game B's seed vs B's recorded opponent of that team... 
# python rnd/tapecross.py <team> <replayA> <replayB>   (B must contain team; we replace team's side with tape A)
import json,sys,io,contextlib,os
sys.path.insert(0,'rnd')
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    from kaggle_environments import make
def tape_of(f,team):
    r=json.load(open(f,encoding='utf8')); p=[i for i,x in enumerate(r['info']['TeamNames']) if team in x][0]
    return [ (r['steps'][t][p]['action'] or {'farmer':['PASS'],'hands':[],'market':[]}) for t in range(1,len(r['steps']))]
def run(team,fa,fb,inner=None):
    tape=tape_of(fa,team)
    r=json.load(open(fb,encoding='utf8')); s=r['steps']; n=r['info']['TeamNames']
    me=[i for i,x in enumerate(n) if team in x][0]; op=1-me
    def mine(obs,conf=None):
        t=obs.get('step',0); return tape[t] if t<len(tape) else {'farmer':['PASS'],'hands':[],'market':[]}
    if inner: mine=inner
    def rec(obs,conf=None):
        t=obs.get('step',0); a=s[t+1][op]['action'] if t+1<len(s) else None
        return a or {'farmer':['PASS'],'hands':[],'market':[]}
    cfg=dict(r['configuration']); cfg['seed']=r['info']['seed']
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        env=make('kaggriculture',configuration=cfg); ag=[None,None]; ag[me]=mine; ag[op]=rec; env.run(ag)
    fin=[x['reward'] for x in env.steps[-1]]
    sh=lambda rr: rr[0]['observation']['town']['unlocked_shops'][:2]
    return dict(a=os.path.basename(fa)[8:17],b=os.path.basename(fb)[8:17],opp=n[op],orig=(r['rewards'][me],r['rewards'][op]),new=(fin[me],fin[op]),shopsA=sh(json.load(open(fa,encoding='utf8'))['steps'][150]),shopsB=sh(s[150]))
if __name__=='__main__':
    print(json.dumps(run(sys.argv[1],sys.argv[2],sys.argv[3])))
