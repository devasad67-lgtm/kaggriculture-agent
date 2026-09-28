import json,glob,sys,collections
who=sys.argv[1];files=sys.argv[2:]
def side(r,p):
    s=r['steps'];rev=0;c=collections.Counter()
    for t in range(1,len(s)):
        ob=s[t-1][0]['observation'];sh=dict(s[t-1][p]['observation']['private']['shed'])
        for o in (s[t][p]['action'] or {}).get('market') or []:
            if not o: continue
            if o[0]=='SELL':
                k=min(int(o[2]),sh.get(o[1],0));sh[o[1]]=sh.get(o[1],0)-k;rev+=k*ob['market']['prices'][o[1]]
            elif o[0]=='HIRE': c['HIRE']+=1
            else: c[o[0]+':'+(str(o[1]) if len(o)>1 else '')]+=int(o[2]) if len(o)>2 else 1
    fm=s[-1][0]['observation']['farms'][p]
    hands=[len(s[min(d*24+12,len(s)-1)][0]['observation']['farms'][p]['hands']) for d in (2,5,8,12,16,20,25)]
    return rev,r['rewards'][p],c,hands
A=collections.Counter();B=collections.Counter();n=0;ra=rb=fa=fb=0;HA=[0]*7;HB=[0]*7
for f in files:
    r=json.load(open(f,encoding='utf8'));N=r['info']['TeamNames'];ps=[i for i,x in enumerate(N) if who in x]
    if not ps: continue
    p=ps[0];n+=1
    x=side(r,p);y=side(r,1-p);ra+=x[0];rb+=y[0];fa+=x[1];fb+=y[1];A+=x[2];B+=y[2]
    for i in range(7): HA[i]+=x[3][i];HB[i]+=y[3][i]
print('games',n,'| revenue',round(ra/n),round(rb/n),'| final',round(fa/n),round(fb/n),'| implied spend',round((ra-fa)/n),round((rb-fb)/n))
print('hands on day 2,5,8,12,16,20,25:',[round(h/n,1) for h in HA],[round(h/n,1) for h in HB])
for k in sorted(set(A)|set(B)): print(f"  {k:22s} {A[k]/n:7.1f} {B[k]/n:7.1f}")
