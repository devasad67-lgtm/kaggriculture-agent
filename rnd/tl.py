# averaged per-day timeline for a named team across replays
import json,glob,sys,collections
from concurrent.futures import ProcessPoolExecutor
def one(a):
    f,who=a
    try: r=json.load(open(f,encoding='utf8'))
    except: return None
    n=r['info']['TeamNames']; ps=[i for i,x in enumerate(n) if who in x]
    if not ps: return None
    p=ps[0]; s=r['steps']; out={}
    for d in (1,3,5,7,9,11,14,17,20,23,26,29):
        t=min(d*24,len(s)-1); f1=s[t][0]['observation']['farms'][p]
        c=collections.Counter()
        for row in f1['tiles']:
            for x in row:
                if isinstance(x,dict): c[x.get('animal') or x.get('crop') or x['kind']]+=1
        c['_quads']=len(f1['unlocked_quadrants']); c['_hands']=len(f1.get('hands') or [])
        c['_money']=f1.get('money',f1.get('cash',0))
        out[d]=c
    return r['rewards'][p],out
if __name__=='__main__':
    d,who=sys.argv[1],sys.argv[2]
    fs=sorted(glob.glob(d+'/*.json'))
    with ProcessPoolExecutor(6) as ex: res=[x for x in ex.map(one,[(f,who) for f in fs]) if x]
    g=len(res); print(who,d,'games',g,'avg reward',sum(x[0] for x in res)/g)
    keys=sorted(set(k for _,o in res for c in o.values() for k in c))
    days=sorted(res[0][1])
    print('day   '+' '.join(f"{k[:7]:>7s}" for k in keys))
    for dd in days: print(f"{dd:3d}   "+' '.join(f"{sum(o[dd][k] for _,o in res)/g:7.1f}" for k in keys))
