import json,glob,sys,collections
from concurrent.futures import ProcessPoolExecutor
rank=json.load(open('ladder/crawl/rank.json'))
def sig(tiles):
    return tuple(tuple((x.get('crop') or x.get('animal') or x['kind']) if isinstance(x,dict) else x for x in row) for row in tiles)
def one(f):
    try: r=json.load(open(f,encoding='utf8'))
    except Exception: return None
    n=r['info']['TeamNames']; me=[i for i,x in enumerate(n) if 'asad' in x.lower()]
    if not me: return None
    me=me[0]; op=1-me; s=r['steps']
    same=[]
    for d in (2,5,8,12,16,20):
        t=d*24+12; fs=s[t][0]['observation']['farms']
        same.append(sig(fs[me]['tiles'])==sig(fs[op]['tiles']))
    return (n[op],r['rewards'][me],r['rewards'][op],same)
if __name__=='__main__':
    fs=[f for d in sys.argv[1:] for f in glob.glob(d+'/*.json')]
    with ProcessPoolExecutor(3) as ex: res=[x for x in ex.map(one,fs) if x]
    cat=collections.defaultdict(list)
    for nm,a,b,same in res:
        k='mirror_all' if all(same) else ('mirror_to_d8' if all(same[:3]) else ('mirror_d2' if same[0] else 'different'))
        cat[k].append((a,b,nm))
    for k,v in cat.items():
        w=sum(a>b for a,b,_ in v); m=sum(a-b for a,b,_ in v)/len(v)
        print(f"{k:13s} n={len(v):3d} W={w} ({100*w/len(v):.0f}%) avg margin {m:+.0f}  median |margin| {sorted(abs(a-b) for a,b,_ in v)[len(v)//2]:.0f}")
