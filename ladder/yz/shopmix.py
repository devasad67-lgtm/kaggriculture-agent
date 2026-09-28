import json,glob,sys,collections
who=sys.argv[1]
rows=[]
for f in sys.argv[2:]:
    r=json.load(open(f,encoding='utf8'));N=r['info']['TeamNames'];ps=[i for i,x in enumerate(N) if who in x]
    if not ps: continue
    p=ps[0];s=r['steps']
    shops=[];last=[]
    for t in range(0,720,24):
        u=s[t][0]['observation']['town']['unlocked_shops']
        if len(u)>len(last): shops.append((t//24,u[-1]));last=list(u)
    buy=collections.Counter();land=[]
    for t in range(1,720):
        for o in (s[t][p]['action'] or {}).get('market') or []:
            if o and o[0] in('BUY_SEED','BUY_ANIMAL'): buy[o[1]]+=int(o[2])
        q0=s[t-1][0]['observation']['farms'][p]['unlocked_quadrants'];q1=s[t][0]['observation']['farms'][p]['unlocked_quadrants']
        if len(q1)>len(q0): land.append(t//24)
    rows.append((shops[:4],dict(buy),land,r['rewards'][p]-r['rewards'][1-p]))
for sh,b,l,m in rows:
    print(' '.join(f"d{d}:{n[:6]}" for d,n in sh).ljust(44),'TOM',b.get('TOMATO',0),'GOO',b.get('GOOSE',0),'CAR',b.get('CARROT',0),'STR',b.get('STRAWBERRY',0),'MEL',b.get('MELON',0),'COW',b.get('COW',0),'SHP',b.get('SHEEP',0),'land',l,f"{m:+.0f}")
