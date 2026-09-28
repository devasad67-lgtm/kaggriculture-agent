import json,sys,collections
who=sys.argv[1];tot=collections.Counter();n=0;runs=[]
for f in sys.argv[2:]:
    r=json.load(open(f,encoding='utf8'));N=r['info']['TeamNames'];ps=[i for i,x in enumerate(N) if who in x]
    if not ps: continue
    p=ps[0];s=r['steps'];n+=1;emp=collections.Counter()
    for d in range(8,29):
        fm=s[d*24+12][0]['observation']['farms'][p]
        for y,row in enumerate(fm['tiles']):
            for x,t in enumerate(row):
                if t is None: emp[(x,y)]+=1
    q=collections.Counter(("N" if y<5 else "S")+("W" if x<5 else "E") for (x,y),c in emp.items() for _ in range(c))
    tot+=q; runs.append(sum(1 for c in emp.values() if c>=10))
print('games',n,'empty tile-days d8-28 by quadrant (avg):',{k:round(v/n,1) for k,v in tot.items()},'| tiles empty >=10 of 21 days per game:',runs)
