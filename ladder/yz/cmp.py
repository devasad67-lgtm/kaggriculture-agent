import json,glob,sys,collections,statistics as S
# per game: revenue by item for each side (sell qty capped by shed * price), money curve
def side(r,p):
    s=r['steps'];rev=collections.Counter();q=collections.Counter()
    for t in range(1,len(s)):
        ob=s[t-1][0]['observation']; sh=dict(s[t-1][p]['observation']['private']['shed'])
        for o in (s[t][p]['action'] or {}).get('market') or []:
            if o and o[0]=='SELL':
                k=min(int(o[2]),sh.get(o[1],0)); sh[o[1]]=sh.get(o[1],0)-k
                q[o[1]]+=k; rev[o[1]]+=k*ob['market']['prices'][o[1]]
    money=[s[min(d*24+23,len(s)-1)][0]['observation']['farms'][p]['money'] for d in range(30)]
    return rev,q,money
who=sys.argv[1]; files=sys.argv[2:]
A=collections.Counter();B=collections.Counter();n=0;MA=[0]*30;MB=[0]*30;rows=[]
for f in files:
    r=json.load(open(f,encoding='utf8'));N=r['info']['TeamNames']
    ps=[i for i,x in enumerate(N) if who in x]
    if not ps: continue
    p=ps[0];o=1-p;n+=1
    ra,qa,ma=side(r,p);rb,qb,mb=side(r,o)
    A+=ra;B+=rb
    for d in range(30): MA[d]+=ma[d];MB[d]+=mb[d]
    rows.append((N[o][:18],r['rewards'][p],r['rewards'][o]))
print('games',n)
for k in sorted(set(A)|set(B),key=lambda k:-(A[k]+B[k])): print(f"  {k:12s} {who[:8]} {A[k]/n:8.0f}  opp {B[k]/n:8.0f}  diff {(A[k]-B[k])/n:+7.0f}")
print('  TOTAL rev',round(sum(A.values())/n),round(sum(B.values())/n))
print('money by day (k$):')
for d in range(0,30,2): print(f"  d{d:2d} {MA[d]/n/1000:6.1f} {MB[d]/n/1000:6.1f} {(MA[d]-MB[d])/n/1000:+5.1f}")
for x in rows: print('  ',x)
