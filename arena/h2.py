import sys,io,contextlib,importlib.util,json,collections
spec=importlib.util.spec_from_file_location('hy','D:/kaggle/bots/hybrid10/main.py'); hy=importlib.util.module_from_spec(spec); spec.loader.exec_module(hy)
sys.path.insert(0,'.'); from tourney import resolve
with contextlib.redirect_stdout(io.StringIO()):
    from kaggle_environments import make
    env=make("kaggriculture",configuration={"seed":2000,"episodeSteps":720},debug=True)
    env.run([hy.agent,resolve('dp_L720a')])
json.dump(env.toJSON(),open('hy.json','w'))
s=env.toJSON()['steps']
for p in (0,1):
    u=collections.Counter(); r=collections.Counter(); acts=collections.Counter()
    for t in range(241,720):
        sh=dict(s[t-1][p]['observation']['private']['shed']); pr=s[t-1][0]['observation']['market']['prices']
        for o in (s[t][p]['action'] or {}).get('market') or []:
            if o and o[0]=='SELL':
                q=min(int(o[2]),sh.get(o[1],0)); sh[o[1]]-=q; u[o[1]]+=q; r[o[1]]+=q*pr[o[1]]
            elif o: acts[o[0]+':'+(o[1] if len(o)>1 else '')]+= int(o[2]) if len(o)>2 else 1
        for a in [s[t][p]['action'].get('farmer')]+list(s[t][p]['action'].get('hands') or []):
            if a: acts['u:'+('MOVE' if a[0] in ('NORTH','SOUTH','EAST','WEST') else a[0])]+=1
    print('P',p,'units',dict(u.most_common()),'rev~',int(sum(r.values())))
    print('   ',{k:v for k,v in acts.most_common(30)})
