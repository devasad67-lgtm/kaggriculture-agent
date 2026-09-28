import json,glob,sys,collections,statistics as S
sys.path.insert(0,'D:/kaggle/ladder/yz')
import io,contextlib
with contextlib.redirect_stdout(io.StringIO()): import ledger
COND={'tomato':(('PIZZA_SHOP','FARMERS_MARKET'),'TOMATO',('SEED','TOMATO')),'cow':(('PIZZA_SHOP','ICE_CREAM_SHOP','SMOOTHIE_SHOP'),'MILK',('ANIMAL','COW')),
      'carrot':(('PET_CAFE','FARMERS_MARKET'),'CARROT',('SEED','CARROT')),'goose':(('BAKERY','BRUNCH_SPOT'),'EGG',('ANIMAL','GOOSE')),'sheep':(('YARN_STORE',),'WOOL',('ANIMAL','SHEEP'))}
def scan(who,files):
    out=[]
    for f in files:
        r=json.load(open(f,encoding='utf8'));s=r['steps'];N=r['info']['TeamNames'];ps=[i for i,x in enumerate(N) if who in x]
        if not ps or len(s)<700: continue
        p=ps[0];sh6=s[150][0]['observation']['town']['unlocked_shops']
        a=ledger.ledger(r,p);b=ledger.ledger(r,1-p)
        buys=collections.defaultdict(lambda:collections.Counter())
        for t in range(1,len(s)):
            for o in (s[t][p]['action'] or {}).get('market') or []:
                if o and o[0] in('BUY_SEED','BUY_ANIMAL'): buys[o[1]][(t-1)//24]+=int(o[2])
        out.append(dict(sh6=sh6,a=a,b=b,buys=buys,win=r['rewards'][p]>r['rewards'][1-p]))
    return out
Y=scan('Yizhou',glob.glob('ladder/yz/episode-*.json'));U=scan('asad',glob.glob('ladder/wflive/*.json'))
print('games Yizhou',len(Y),'us(L48_wf)',len(U))
print(f"{'family':7s} {'cond(d3/d6 shop)':17s} | {'n Y/U':7s} | {'units by d12 Y/U':17s} {'first day Y/U':14s} | {'item rev Y-opp':>14s} {'U-opp':>7s} | {'opp avg price vs Y':>18s} {'vs U':>6s}")
for fam,(shops,item,(kind,name)) in COND.items():
    for cond in (True,False):
        yy=[g for g in Y if any(x in shops for x in g['sh6'])==cond];uu=[g for g in U if any(x in shops for x in g['sh6'])==cond]
        if not yy or not uu: continue
        f=lambda G:S.mean(sum(v for d,v in g['buys'][name].items() if d<=12) for g in G)
        fd=lambda G:S.median([min(g['buys'][name]) if g['buys'][name] else 99 for g in G])
        rd=lambda G:S.mean(g['a'][0][item]-g['b'][0][item] for g in G)
        op=lambda G:S.mean([g['b'][0][item]/g['b'][2][item] for g in G if g['b'][2][item]>5] or [0])
        print(f"{fam:7s} {'present' if cond else 'absent':17s} | {len(yy):2d}/{len(uu):3d} | {f(yy):6.1f} / {f(uu):6.1f}   {fd(yy):4.0f} / {fd(uu):4.0f}   | {rd(yy):+14.0f} {rd(uu):+7.0f} | {op(yy):18.0f} {op(uu):6.0f}")
