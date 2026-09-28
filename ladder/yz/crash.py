# units sold per item bucketed by price / base (from ledger-style attribution with sell-time price)
import json,sys,collections
sys.path.insert(0,'D:/kaggle/ladder/yz')
import io,contextlib
with contextlib.redirect_stdout(io.StringIO()): import ledger
K=ledger.K
who=sys.argv[1];U=collections.defaultdict(collections.Counter);R=collections.defaultdict(collections.Counter);n=0
for f in sys.argv[2:]:
    r=json.load(open(f,encoding='utf8'));N=r['info']['TeamNames'];ps=[i for i,x in enumerate(N) if who in x]
    if not ps: continue
    p=ps[0];s=r['steps'];n+=1
    for t in range(1,len(s)):
        ob=s[t-1][0]['observation']; sh0=s[t-1][p]['observation']['private']['shed']; sh1=s[t][p]['observation']['private']['shed']
        for o in (s[t][p]['action'] or {}).get('market') or []:
            if o and o[0]=='SELL':
                k=o[1]; sold=max(0,min(int(o[2]),sh0.get(k,0)-sh1.get(k,0)+int(o[2]))) if False else None
                pr=ob['market']['prices'][k]; b=K.MARKET_PARAMS[k]['base']; x=pr/b
                bk='<0.3' if x<.3 else '0.3-0.7' if x<.7 else '0.7-1.3' if x<1.3 else '>1.3'
                q=int(o[2]); U[k][bk]+=q; R[k][bk]+=q*pr
print(who,'games',n,'ORDERED sell units per game by price/base bucket (upper bound on units)')
for k in U:
    tot=sum(U[k].values())
    print(f"  {k:10s} "+'  '.join(f"{b}:{U[k][b]/n:6.1f}u ${R[k][b]/n:6.0f}" for b in ['<0.3','0.3-0.7','0.7-1.3','>1.3']))
