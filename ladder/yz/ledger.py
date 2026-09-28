# exact-ish per-item revenue from money deltas: sales(step) = dmoney + costs(step), split over that step's SELL orders by quoted value
import json,sys,collections,importlib.util
spec=importlib.util.spec_from_file_location('k','D:/kaggle/.venv/Lib/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py');K=importlib.util.module_from_spec(spec);spec.loader.exec_module(K)
def ledger(r,p):
    s=r['steps'];rev=collections.Counter();cost=collections.Counter();units=collections.Counter()
    for t in range(1,len(s)):
        o0=s[t-1][0]['observation'];o1=s[t][0]['observation']
        f0=o0['farms'][p];f1=o1['farms'][p]
        dm=f1['money']-f0['money'];c=0;hires=f0['hires_today'] if (t-1)%24!=23 else 0
        sells=[]
        # crude buy-product cost: engine quote at inventory-1
        for o in (s[t][p]['action'] or {}).get('market') or []:
            if not o: continue
            if o[0]=='HIRE':
                h=K._hire_cost(hires)
                if f1['hires_today']>hires or True: pass
                c_h=h; cost['HIRE']+=c_h; c+=c_h; hires+=1
            elif o[0]=='BUY_LAND':
                n=len(f0['unlocked_quadrants'])-1+ (cost['LANDn'] if False else 0)
            elif o[0]=='BUY_SEED': v=K.CROPS[o[1]]['seed']*int(o[2]); cost['SEED:'+o[1]]+=v; c+=v
            elif o[0]=='BUY_ANIMAL': v=K.ANIMALS[o[1]]['cost']*int(o[2]); cost['ANIMAL:'+o[1]]+=v; c+=v
            elif o[0]=='BUY_PRODUCT': v=o0['market']['prices'][o[1]]*int(o[2]); cost['PROD:'+o[1]]+=v; c+=v
            elif o[0]=='SELL': sells.append((o[1],int(o[2])))
        # land: detect quadrant unlocks
        nl=len(f1['unlocked_quadrants'])-len(f0['unlocked_quadrants'])
        if nl>0:
            v=sum(K.LAND_PRICES[len(f0['unlocked_quadrants'])-1+i] for i in range(nl)); cost['LAND']+=v; c+=v
        sales=dm+c
        if sells and sales>0:
            w=[q*o0['market']['prices'][k] for k,q in sells]; W=sum(w) or 1
            for (k,q),x in zip(sells,w): rev[k]+=sales*x/W; units[k]+=sales*x/W/max(1,o0['market']['prices'][k])
    return rev,cost,units
if __name__=='__main__':
    who=sys.argv[1];A=collections.Counter();B=collections.Counter();CA=collections.Counter();CB=collections.Counter();n=0;fa=fb=0
    for f in sys.argv[2:]:
        r=json.load(open(f,encoding='utf8'));N=r['info']['TeamNames'];ps=[i for i,x in enumerate(N) if who in x]
        if not ps: continue
        p=ps[0];n+=1;a=ledger(r,p);b=ledger(r,1-p);A+=a[0];B+=b[0];CA+=a[1];CB+=b[1];fa+=r['rewards'][p];fb+=r['rewards'][1-p]
    print('games',n,'final',round(fa/n),round(fb/n))
    print('REVENUE');[print(f"  {k:12s} {A[k]/n:8.0f} {B[k]/n:8.0f} {(A[k]-B[k])/n:+7.0f}") for k in sorted(set(A)|set(B),key=lambda k:-(A[k]+B[k]))]
    print('  total',round(sum(A.values())/n),round(sum(B.values())/n))
    print('COSTS');[print(f"  {k:16s} {CA[k]/n:8.0f} {CB[k]/n:8.0f} {(CA[k]-CB[k])/n:+7.0f}") for k in sorted(set(CA)|set(CB),key=lambda k:-(CA[k]+CB[k]))]
    print('  total',round(sum(CA.values())/n),round(sum(CB.values())/n))
