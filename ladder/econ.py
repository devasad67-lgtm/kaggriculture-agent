import json,glob,sys,collections
def rep(f,who):
    r=json.load(open(f,encoding='utf8')); n=r['info']['TeamNames']
    p=[i for i,x in enumerate(n) if who in x][0]; s=r['steps']
    money=[round(s[min(d*24+23,719)][0]['observation']['farms'][p]['money']/1000,1) for d in range(0,30,2)]
    sells=collections.Counter(); hires=0; buys=collections.Counter()
    for t in range(1,720):
        for o in (s[t][p]['action'] or {}).get('market') or []:
            if not o: continue
            if o[0]=='SELL': sells[o[1]]+=int(o[2])
            elif o[0]=='HIRE': hires+=1
            else: buys[(o[0],o[1] if len(o)>1 else '')]+=int(o[2]) if len(o)>2 else 1
    return n[p],r['rewards'][p],money,dict(sells),hires,dict(buys)
for f,w in [(sys.argv[1],sys.argv[2])]:
    for x in rep(f,w): print(x)
