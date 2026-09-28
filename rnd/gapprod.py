import sys,glob,json,collections
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0,'rnd'); from prof import prof
rank=json.load(open('ladder/crawl/rank.json'))
def one(f):
    try: return f,prof(f)
    except Exception: return f,None
if __name__=='__main__':
    fs=[f for d in sys.argv[1:] for f in glob.glob(d+'/*.json')]
    B=collections.defaultdict(lambda:collections.defaultdict(float)); N=collections.Counter()
    with ProcessPoolExecutor(6) as ex:
        for f,res in ex.map(one,fs):
            if not res: continue
            me=[x for x in res if 'asad' in x['name'].lower()]; op=[x for x in res if 'asad' not in x['name'].lower()]
            if len(me)!=1 or len(op)!=1: continue
            me,op=me[0],op[0]; rk=rank.get(op['name'],[9999])[0]
            band='top700' if rk<=700 else 'rest'
            res_=('W' if me['reward']>op['reward'] else 'L')
            for key in (band, band+res_):
                N[key]+=1
                for k in set(me['sold'])|set(op['sold']):
                    B[key][k]+=me['sold'].get(k,0)*me['avgp'].get(k,0)-op['sold'].get(k,0)*op['avgp'].get(k,0)
                B[key]['_TOTAL']+=me['reward']-op['reward']
    for key in sorted(N):
        print(f"== {key} n={N[key]}: "+'  '.join(f"{k}:{v/N[key]:+.0f}" for k,v in sorted(B[key].items(),key=lambda kv:kv[1])))
