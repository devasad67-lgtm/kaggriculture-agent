# strawberry: first sale day, volume, avg price, first plant day for us vs opp, top700 opps
import sys,glob,json,collections,statistics as st
from concurrent.futures import ProcessPoolExecutor
rank=json.load(open('ladder/crawl/rank.json'))
CROP=sys.argv[1]
def one(f):
    try: r=json.load(open(f,encoding='utf8'))
    except Exception: return None
    n=r['info']['TeamNames']; s=r['steps']
    out=[]
    for p in (0,1):
        sales=[]; firstplant=None; plants=collections.Counter()
        for t in range(1,len(s)):
            mk=s[t-1][0]['observation']['market']
            sh=s[t-1][p]['observation']['private']['shed'].get(CROP,0)
            for o in (s[t][p]['action'] or {}).get('market') or []:
                if o and o[0]=='SELL' and o[1]==CROP:
                    q=min(int(o[2]) if len(o)>2 else 1,sh); sh-=q
                    if q>0: sales.append(((t-1)//24,q,mk['prices'][CROP]))
        for d in range(30):
            tl=s[min(d*24+23,len(s)-1)][0]['observation']['farms'][p]['tiles']
            c=sum(1 for row in tl for x in row if isinstance(x,dict) and x.get('crop')==CROP)
            plants[d]=c
            if firstplant is None and c>0: firstplant=d
        out.append(dict(name=n[p],rw=r['rewards'][p],sales=sales,fp=firstplant,peak=max(plants.values())))
    return out
if __name__=='__main__':
    fs=[f for d in sys.argv[2:] for f in glob.glob(d+'/*.json')]
    rows=[]
    with ProcessPoolExecutor(6) as ex:
        for res in ex.map(one,fs):
            if not res: continue
            me=[x for x in res if 'asad' in x['name'].lower()]; op=[x for x in res if 'asad' not in x['name'].lower()]
            if len(me)!=1 or len(op)!=1: continue
            if rank.get(op[0]['name'],[9999])[0]>700: continue
            rows.append((me[0],op[0]))
    def summ(xs,lab):
        q=[sum(a[1] for a in x['sales']) for x in xs]; rev=[sum(a[1]*a[2] for a in x['sales']) for x in xs]
        fsd=[x['sales'][0][0] for x in xs if x['sales']]; fp=[x['fp'] for x in xs if x['fp'] is not None]
        early=[sum(a[1] for a in x['sales'] if a[0]<=17) for x in xs]
        print(f"{lab}: n={len(xs)} units {st.mean(q):.0f} avg$ {sum(rev)/max(1,sum(q)):.0f} rev {st.mean(rev):.0f} | first plant day med {st.median(fp) if fp else '-'} | first sale day med {st.median(fsd) if fsd else '-'} | units sold by d17 {st.mean(early):.1f} | peak plants {st.mean(x['peak'] for x in xs):.1f}")
    summ([a for a,b in rows],'US '); summ([b for a,b in rows],'OPP')
    L=[(a,b) for a,b in rows if a['rw']<b['rw']]
    summ([a for a,b in L],'US in losses '); summ([b for a,b in L],'OPP in losses')
    import collections as C
    for lab,idx in (('US',0),('OPP',1)):
        h=C.Counter(); hd=C.Counter()
        for pair in L:
            for d,q,p in pair[idx]['sales']:
                h[min(p//40,5)]+=q; hd[d]+=q
        tot=sum(h.values())
        print(lab,'price bands',' '.join(f"${40*k}-{40*k+39}:{100*h[k]/tot:.0f}%" for k in sorted(h)))
        print(lab,'units/day', ' '.join(f"d{d}:{hd[d]/len(L):.1f}" for d in sorted(hd)))
