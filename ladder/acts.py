import json,sys,glob,collections
team=sys.argv[1]; files=sys.argv[2:]
tot=collections.defaultdict(collections.Counter)
for f in files:
    r=json.load(open(f,encoding='utf8')); n=r['info']['TeamNames']
    if team not in n: continue
    p=n.index(team)
    for t in range(1,720):
        a=r['steps'][t][p]['action'] or {}
        d=(t-1)//24
        for u in [a.get('farmer')]+list(a.get('hands') or []):
            if not u: continue
            k=u[0] if u[0] not in ('NORTH','SOUTH','EAST','WEST') else 'MOVE'
            tot[d][k]+=1
        tot[d]['units']+=0
    tot['n']['games']+=1
g=tot['n']['games']; print('games',g)
keys=['MOVE','PASS','WATER','HARVEST','PLANT','FEED','CARE','COLLECT_FERTILIZER','FERTILIZE','PICKUP','PLACE','DROP','DIG','BUILD_COOP','BUILD_PASTURE']
print('day '+' '.join(k[:6].rjust(6) for k in keys))
for d in range(0,30,2):
    print(str(d).rjust(3),' '.join(str(round(tot[d][k]/g)).rjust(6) for k in keys))
