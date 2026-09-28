# genuinely free tiles: empty (None) at every sampled step from day D to the end
import json,sys,collections
who=sys.argv[1];rows=[]
for f in sys.argv[2:]:
    r=json.load(open(f,encoding='utf8'));N=r['info']['TeamNames'];ps=[i for i,x in enumerate(N) if who in x]
    if not ps: continue
    p=ps[0];s=r['steps']
    ever=set();free={}
    for t in range(len(s)-1,-1,-1):
        fm=s[t][0]['observation']['farms'][p]
        for y,row in enumerate(fm['tiles']):
            for x,c in enumerate(row):
                if c is not None: ever.add((x,y))
        if t%24==0:
            free[t//24]=[(x,y) for y in range(10) for x in range(10) if (x,y) not in ever and fm['tiles'][y][x] is None]
    hires=[sum(1 for t in range(d*24+1,min(d*24+25,len(s))) for o in (s[t][p]['action'] or {}).get('market') or [] if o and o[0]=='HIRE') for d in range(30)]
    shops=s[240][0]['observation']['town']['unlocked_shops']
    q=s[719][0]['observation']['farms'][p]['unlocked_quadrants']
    rows.append((f.split('-')[1],free,hires,shops,q))
    fr=lambda d:len(free.get(d,[]))
    def qd(d): return collections.Counter(("N" if y<5 else "S")+("W" if x<5 else "E") for x,y in free.get(d,[]))
    print(f.split('-')[1],'quads',q,'free@d8,10,12,15,18,22:',[fr(d) for d in (8,10,12,15,18,22)],'d10',dict(qd(10)),'d18',dict(qd(18)),'hires d10,15,20:',hires[10],hires[15],hires[20],'shops',[x[:5] for x in shops])
json.dump([(a,{k:v for k,v in b.items()},c,d,e) for a,b,c,d,e in rows],open('ladder/yz/free.json','w'))
