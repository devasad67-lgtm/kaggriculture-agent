# per product: steps where both sell same step / we first / they first (in the last 12 days), qty weighted
import json,sys,collections
ITEMS=['CARROT','STRAWBERRY','WHEAT','EGG','MILK','WOOL','TOMATO']
tot=collections.defaultdict(collections.Counter)
for ep in sys.argv[1:]:
    r=json.load(open(f'ladder/wflive/episode-{ep}-replay.json',encoding='utf8'));s=r['steps'];N=r['info']['TeamNames']
    me=[i for i,x in enumerate(N) if 'asad' in x.lower()][0];op=1-me
    ev={p:collections.defaultdict(list) for p in (me,op)}
    for t in range(0,len(s)-1):
        for p in (me,op):
            for o in (s[t+1][p]['action'] or {}).get('market') or []:
                if o and o[0]=='SELL' and len(o)>2 and o[2]>0: ev[p][o[1]].append((t,o[2]))
    line=[]
    for it in ITEMS:
        a=ev[me][it];b=ev[op][it]
        qa=sum(q for _,q in a);qb=sum(q for _,q in b)
        fa=a[0][0] if a else None;fb=b[0][0] if b else None
        same=len({t for t,_ in a}&{t for t,_ in b})
        line.append(f"{it[:4]} {qa}/{qb} first {fa}/{fb} same{same}/{len(a)}")
    print(ep,N[op][:10],r['rewards'][me]-r['rewards'][op]);print('   ','; '.join(line))
