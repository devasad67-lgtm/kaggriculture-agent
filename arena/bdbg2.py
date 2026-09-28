import sys,io,contextlib,json,collections,shutil,importlib.util
sys.path.insert(0,'.'); from tourney import resolve
shutil.copy('D:/kaggle/beast/main.py','D:/kaggle/bots/beast/main.py')
with contextlib.redirect_stdout(io.StringIO()):
    from kaggle_environments import make
    env=make("kaggriculture",configuration={"seed":2000,"episodeSteps":int(sys.argv[1])},debug=True)
    env.run([resolve('beast'),resolve(sys.argv[2])])
s=env.steps
# per-day: eggs sold, wheat bought, geese bought, hires, money
agg=collections.defaultdict(collections.Counter)
for t in range(1,len(s)):
    for o in (s[t][0].action or {}).get('market') or []:
        agg[(t-1)//24][o[0]+':'+(o[1] if len(o)>1 else '')]+= int(o[2]) if len(o)>2 else 1
for d in sorted(agg): print(d, dict(agg[d]))
for d in range(0,30,2):
    ob=s[d*24+1][0].observation
    print('d',d,'$',ob['farms'][0]['money'],{k:ob['market']['prices'][k] for k in ('EGG','WHEAT','FERTILIZER')})
# money change per step on day 22
prev=None
for t in range(22*24,23*24):
    m=s[t][0].observation['farms'][0]['money']
    if prev is not None and m!=prev: print(t, m-prev, (s[t][0].action or {}).get('market'))
    prev=m
