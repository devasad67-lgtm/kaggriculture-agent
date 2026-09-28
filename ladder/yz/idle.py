import json,sys,collections
who=sys.argv[1];n=0;C={};
for f in sys.argv[2:]:
    r=json.load(open(f,encoding='utf8'));N=r['info']['TeamNames'];ps=[i for i,x in enumerate(N) if who in x]
    if not ps: continue
    p=ps[0];s=r['steps'];n+=1
    for d in range(0,30,3):
        c=C.setdefault(d,collections.Counter())
        for t in range(d*24+1,min(d*24+73,720)):
            a=s[t][p]['action'] or {}
            for u in [a.get('farmer',['PASS'])]+list(a.get('hands') or []):
                op=(u or ['PASS'])[0] if isinstance(u,list) else 'PASS'
                c['PASS' if op=='PASS' else 'MOVE' if op=='MOVE' else 'WORK']+=1
for d in sorted(C):
    c=C[d];t=sum(c.values())
    print(f"days {d}-{d+2}: unit-steps/day {t/n/3:6.0f}  PASS {c['PASS']/t:5.1%}  MOVE {c['MOVE']/t:5.1%}  WORK {c['WORK']/t:5.1%}  idle unit-steps/day {c['PASS']/n/3:5.0f}")
