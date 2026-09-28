# exact per-product revenue/cost difference (us - opp) in mirror games via resim
import sys,json,glob,collections,os
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0,'rnd')
def one(f):
    import resim
    r,env,log=resim.resim(f); n=r['info']['TeamNames']; me=[i for i,x in enumerate(n) if 'asad' in x.lower()][0]
    d=collections.Counter(); tm=collections.Counter()
    for t,p,op,item,price in log:
        sgn=1 if p==me else -1
        key=('+' if op=='SELL' else '-')+item
        d[key]+=sgn*price*(1 if op=='SELL' else -1)
        if op=='SELL': tm[(item,t//24)]+=sgn*price
    return os.path.basename(f),n[1-me],r['rewards'][me]-r['rewards'][1-me],dict(d),{f"{k[0]}@{k[1]}":v for k,v in tm.items() if v}
if __name__=='__main__':
    fs=[l.strip() for l in open(sys.argv[1])]
    with ProcessPoolExecutor(2) as ex:
        for x in ex.map(one,fs): print(json.dumps(x),flush=True)
