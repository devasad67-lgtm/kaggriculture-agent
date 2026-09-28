import json,sys,collections,importlib.util,io,contextlib
with contextlib.redirect_stdout(io.StringIO()):
    sys.argv_=sys.argv; import ledger
who=sys.argv[1]
for f in sys.argv[2:]:
    r=json.load(open(f,encoding='utf8'));N=r['info']['TeamNames'];ps=[i for i,x in enumerate(N) if who in x]
    if not ps: continue
    p=ps[0];s=r['steps']
    land=[t//24 for t in range(1,720) if len(s[t][0]['observation']['farms'][p]['unlocked_quadrants'])>len(s[t-1][0]['observation']['farms'][p]['unlocked_quadrants'])]
    if len(land)<3: continue
    # SE tile activity after purchase
    fm=s[-1][0]['observation']['farms'][p]
    rev,cost,units=ledger.ledger(r,p); ro,co,uo=ledger.ledger(r,1-p)
    # opp land
    ol=[t//24 for t in range(1,720) if len(s[t][0]['observation']['farms'][1-p]['unlocked_quadrants'])>len(s[t-1][0]['observation']['farms'][1-p]['unlocked_quadrants'])]
    print(f.split('-')[1],'land',land,'opp land',ol,'| TOM rev',round(rev['TOMATO']),'units',round(units['TOMATO']),'seed',cost['SEED:TOMATO'],'| opp TOM rev',round(ro['TOMATO']),'| margin',r['rewards'][p]-r['rewards'][1-p])
