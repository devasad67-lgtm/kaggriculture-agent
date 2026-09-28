# print sell events per product for both players: day.hour qty price inv
import json,sys
f=sys.argv[1]; prods=sys.argv[2].split(',')
r=json.load(open(f,encoding='utf8')); s=r['steps']; n=r['info']['TeamNames']
print(n, r['rewards'])
for t in range(1,len(s)):
    ob=s[t-1][0]['observation']; mk=ob['market']
    ev=[]
    for p in (0,1):
        for o in (s[t][p]['action'] or {}).get('market') or []:
            if o and o[0]=='SELL' and o[1] in prods:
                sh=s[t-1][p]['observation']['private']['shed'].get(o[1],0)
                q=min(int(o[2]) if len(o)>2 else 1,sh)
                if q>0: ev.append(f"P{p}:{o[1][:5]} x{q}")
    if ev:
        print(f"d{(t-1)//24:2d}h{(t-1)%24:2d} " + ' '.join(f"{k[:5]}={mk['prices'][k]}/{mk['inventory'][k]-10000:+d}" for k in prods), ' | ', ' '.join(ev))
