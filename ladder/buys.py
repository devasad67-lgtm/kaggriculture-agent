import json,sys,collections
team=sys.argv[1]; files=sys.argv[2:]
tot=collections.defaultdict(collections.Counter); g=0
for f in files:
    r=json.load(open(f,encoding='utf8')); n=r['info']['TeamNames']
    if team not in n: continue
    p=n.index(team); g+=1
    for t in range(1,720):
        a=r['steps'][t][p]['action'] or {}
        d=(t-1)//24
        for o in a.get('market') or []:
            if not o: continue
            k=o[0]+(':'+o[1] if len(o)>1 else '')
            tot[d][k]+= int(o[2]) if len(o)>2 and o[0]!='SELL' else (1 if o[0]!='SELL' else 0)
print('games',g)
keys=sorted({k for d in tot for k in tot[d]})
for d in range(30):
    print(d, {k.replace('BUY_',''):round(tot[d][k]/g,1) for k in keys if tot[d][k]})
