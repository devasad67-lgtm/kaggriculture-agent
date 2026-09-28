import sys,json,io,contextlib,glob
sys.path.insert(0,'rnd'); import replaytest
fn=replaytest.load('bots/L48_df/main.py'); E=fn.__globals__['_EDGE']
f='ladder/l48mc/episode-113462974-replay.json'
r=json.load(open(f,encoding='utf8')); s=r['steps']; n=r['info']['TeamNames']
me=[i for i,x in enumerate(n) if 'asad' in x.lower()][0]
for t in (440,445,450):
    obs=s[t][me]['observation']
    tape=E._tape(obs)
    print(t,'tape len',len(tape))
    if tape: print('  tape',json.dumps(tape[t])[:300])
    print('  real',json.dumps(s[t+1][me]['action'])[:300])
