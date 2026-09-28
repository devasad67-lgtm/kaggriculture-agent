import json,glob,collections,sys
sys.path.insert(0,'/d/kaggle/rnd'); from prof import prof
agg=collections.Counter(); aggq=collections.Counter(); n=0
rows=[]
for f in sorted(glob.glob(sys.argv[1])):
    try: a,b=prof(f)
    except Exception as e: continue
    w,l=(a,b) if a['reward']>=b['reward'] else (b,a)
    n+=1
    for k in set(w['sold'])|set(l['sold']):
        rw=w['sold'].get(k,0)*w['avgp'].get(k,0); rl=l['sold'].get(k,0)*l['avgp'].get(k,0)
        agg[k]+=rw-rl; aggq[k]+=w['sold'].get(k,0)-l['sold'].get(k,0)
    rows.append((w['name'],l['name'],w['reward']-l['reward']))
print('games',n)
for k,v in agg.most_common(): print(k.ljust(11),'rev diff/game',round(v/n),'qty diff/game',round(aggq[k]/n,1))
