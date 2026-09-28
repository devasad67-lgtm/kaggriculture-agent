import json,glob,sys,multiprocessing as mp
def f(fn):
    try:
        r=json.load(open(fn,encoding='utf8'));s=r['steps']
        if len(s)<433: return None
        o=s[432][0]['observation'];sh=o['town']['unlocked_shops']
        return r['info']['seed'],sum(x in('PIZZA_SHOP','FARMERS_MARKET') for x in sh),o['market']['prices']['TOMATO']
    except Exception: return None
if __name__=='__main__':
    files=[x for d in ('l48','l8','l8o','l8o2','l8omc','mm','reps','top','dsm2','wfmc','now') for x in glob.glob(f'ladder/{d}/*.json')]
    old=set(json.load(open('arena/seeds_tom3.json')))
    with mp.Pool(4) as p: R=[x for x in p.map(f,files) if x]
    seen={};[seen.setdefault(s,(n,pr)) for s,n,pr in R]
    hi=[s for s,(n,pr) in seen.items() if n>=3 and s not in old]
    print('unique seeds',len(seen),'tomato3+ new',len(hi),'with price>=90:',sum(seen[s][1]>=90 for s in hi))
    json.dump(hi,open('arena/seeds_tom3b.json','w'))
