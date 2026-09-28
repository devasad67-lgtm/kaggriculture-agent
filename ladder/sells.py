import json,sys,collections
team=sys.argv[1]; files=sys.argv[2:]
tot=collections.defaultdict(collections.Counter); rev=collections.Counter(); g=0
for f in files:
    r=json.load(open(f,encoding='utf8')); n=r['info']['TeamNames']
    if team not in n: continue
    p=n.index(team); g+=1; s=r['steps']
    for t in range(1,720):
        ob=s[t-1][0]['observation']; sh=dict(s[t-1][p]['observation']['private']['shed'])
        for o in (s[t][p]['action'] or {}).get('market') or []:
            if o and o[0]=='SELL':
                q=min(int(o[2]),sh.get(o[1],0)); sh[o[1]]=sh.get(o[1],0)-q
                tot[(t-1)//24][o[1]]+=q; rev[o[1]]+=q*ob['market']['prices'][o[1]]
print('games',g,'avg revenue by item',{k:round(v/g) for k,v in rev.most_common()}, 'total',round(sum(rev.values())/g))
for d in range(0,30,2):
    print(d,{k:round((tot[d][k]+tot[d+1][k])/g,1) for k in sorted(set(tot[d])|set(tot[d+1]))})
