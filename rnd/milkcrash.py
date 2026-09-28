import sys,glob,json,collections,statistics as st
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0,'rnd'); from prof import prof
def one(f):
    try: res=prof(f)
    except Exception: return None
    me=[x for x in res if 'asad' in x['name'].lower()]; op=[x for x in res if 'asad' not in x['name'].lower()]
    if len(me)!=1: return None
    me=me[0]; op=op[0] if op else me
    return {k:(me['sold'].get(k,0),me['avgp'].get(k,0)) for k in ('MILK','WOOL','STRAWBERRY','EGG','CARROT')}, me['reward']-op['reward']
if __name__=='__main__':
    fs=[f for d in sys.argv[1:] for f in glob.glob(d+'/*.json')]
    with ProcessPoolExecutor(2) as ex: rs=[x for x in ex.map(one,fs) if x]
    for k in ('MILK','WOOL','STRAWBERRY','EGG','CARROT'):
        ps=[r[0][k][1] for r in rs if r[0][k][0]>0]
        b=collections.Counter(min(p//25,6) for p in ps)
        print(k,'games',len(ps),'avg price dist:',' '.join(f"${25*i}-{25*i+24}:{b[i]}" for i in sorted(b)))
