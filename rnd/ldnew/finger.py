import json,glob,collections,statistics as S
def fp(f,who):
    r=json.load(open(f,encoding='utf8')); s=r['steps']; n=r['info']['TeamNames']
    p=[i for i,x in enumerate(n) if who(x)]
    if not p: return None
    p=p[0]; out={}
    for d in (1,2,3,4,5,6,8,10,12,14):
        F=s[d*24+12][0]['observation']['farms'][p]
        c=collections.Counter((t.get('crop') or t.get('animal') or t['kind']) for row in F['tiles'] for t in row if isinstance(t,dict))
        out[d]=dict(cash=F['money'],q=len(F['unlocked_quadrants']),h=len(F.get('hands') or []),W=c['WHEAT'],C=c['CARROT'],S=c['STRAWBERRY'],M=c['MELON'],T=c['TOMATO'],G=c['GOOSE'],Cw=c['COW'],Sh=c['SHEEP'])
    return out,r['rewards'][p]
def agg(files,who,lab):
    rs=[x for x in (fp(f,who) for f in files) if x]
    print(f"== {lab}: {len(rs)} games, final money median {S.median(m for _,m in rs):.0f}")
    for d in (1,2,3,4,5,6,8,10,12,14):
        m={k:S.median(r[d][k] for r,_ in rs) for k in rs[0][0][d]}
        print(f"  d{d:2d} "+' '.join(f"{k}={v:.0f}" for k,v in m.items()))
#agg(sorted(glob.glob('ladder/dsm2/*.json')),lambda x:'DSM' in x,'DSM')
#agg(sorted(glob.glob('ladder/l48mc/*.json'))[:21],lambda x:'asad' in x.lower(),'OURS (L48_mc)')
import sys
if len(sys.argv)>1: agg(sorted(glob.glob(sys.argv[1]+'/*.json')),lambda x:x.startswith(sys.argv[2]),sys.argv[2])
