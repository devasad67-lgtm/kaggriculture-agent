import json,sys,glob,collections,statistics as S
sys.path.insert(0,'D:/kaggle/ladder/yz')
import io,contextlib
with contextlib.redirect_stdout(io.StringIO()): import ledger
K=ledger.K
def rev(I,q):
    t=0
    for k in range(q): t+=K.market_price('TOMATO',I+k)
    return t
G=collections.defaultdict(list)
for f in sys.argv[1:]:
    r=json.load(open(f,encoding='utf8'));s=r['steps'];N=r['info']['TeamNames'];p=[i for i,x in enumerate(N) if 'asad' in x]
    if not p: continue
    p=p[0]
    sh=s[432][0]['observation']['town']['unlocked_shops'];n=sum(x in('PIZZA_SHOP','FARMERS_MARKET') for x in sh)
    se18=any(isinstance(c,dict) and c.get('crop')=='TOMATO' for row in s[500][0]['observation']['farms'][p]['tiles'] for c in row)
    inv={d:s[d*24+12][0]['observation']['market']['inventory']['TOMATO'] for d in (12,18,22,26)}
    pr={d:s[d*24+12][0]['observation']['market']['prices']['TOMATO'] for d in (12,18,22,26)}
    G[(n,se18)].append((inv,pr,rev(inv[26],40),rev(inv[22],40)))
print('PIZZA+FARMERS by d18 | tomato proj fired | games | median tomato price d12/18/22/26 | median $ for +40 units sold d26 | d22')
for k in sorted(G):
    v=G[k];print(k,len(v),[S.median(x[1][d] for x in v) for d in (12,18,22,26)],round(S.median(x[2] for x in v)),round(S.median(x[3] for x in v)))
print('marginal: extra units sold AFTER our 75 + rival 75 (d26 inventory + 150); also after only our 75')
for k in sorted(G):
    if not k[1]: continue
    v=G[k]
    for q in (40,60,120):
        a=S.median(rev(x[0][26]+150,q) for x in v); b=S.median(rev(x[0][26]+75,q) for x in v)
        print(k,'extra',q,'units: $',round(a),'(rival also runs project) / $',round(b),'(rival does not)')
