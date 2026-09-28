import json,sys,collections
who=sys.argv[1];n=0;c=collections.Counter()
for f in sys.argv[2:]:
    r=json.load(open(f,encoding='utf8'));N=r['info']['TeamNames'];ps=[i for i,x in enumerate(N) if who in x]
    if not ps: continue
    p=ps[0];s=r['steps'];n+=1
    for t in range(9*24+1,27*24+1):
        a=s[t][p]['action'] or {}
        for u in [a.get('farmer',['PASS'])]+list(a.get('hands') or []):
            c[(u[0] if isinstance(u,list) and u else 'PASS')]+=1
tot=sum(c.values())
print(who,'days 9-26 per day:',', '.join(f"{k} {v/n/18:.0f}" for k,v in c.most_common()))
