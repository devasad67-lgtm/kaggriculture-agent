# Exact value of a player's wheat buy->sell-next-step trades: replay game with those trades stripped.
import json,sys,io,contextlib,copy,glob
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    from kaggle_environments import make
ep=sys.argv[1] if len(sys.argv)>1 else '113061862'; who=sys.argv[2] if len(sys.argv)>2 else 'Hikaru'
f=glob.glob(f'ladder/*/episode-{ep}-replay.json')[0]
r=json.load(open(f,encoding='utf8')); s=r['steps']; n=r['info']['TeamNames']; H=[i for i,x in enumerate(n) if who in x][0]
A=[[copy.deepcopy(s[t][p]['action'] or {'farmer':['PASS'],'hands':[],'market':[]}) for t in range(1,len(s))] for p in (0,1)]
def wh(o,kind): return o and len(o)>2 and o[0]==kind and o[1]=='WHEAT'
def strip(tape):
    for t in range(len(tape)-1):
        a=tape[t].get('market') or []; b=tape[t+1].get('market') or []
        k=min(sum(o[2] for o in a if wh(o,'BUY_PRODUCT')),sum(o[2] for o in b if wh(o,'SELL')))
        for lst,kind in ((a,'BUY_PRODUCT'),(b,'SELL')):
            left=k
            for o in lst:
                if wh(o,kind) and left>0: d=min(o[2],left); o[2]-=d; left-=d
    return tape
def play(tapes):
    ags=[(lambda T:(lambda obs,conf=None:T[obs.get('step',0)] if obs.get('step',0)<len(T) else {'farmer':['PASS'],'hands':[],'market':[]}))(T) for T in tapes]
    cfg=dict(r['configuration']); cfg['seed']=r['info']['seed']
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        env=make('kaggriculture',configuration=cfg); env.run(ags)
    return [x['reward'] for x in env.steps[-1]]
print('orig',r['rewards'],'H=',H)
print('replay',play(A))
B=copy.deepcopy(A); B[H]=strip(B[H]); print('no-arb',play(B))
