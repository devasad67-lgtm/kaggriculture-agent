import json,sys,collections
who=sys.argv[1];days=[5,8,12,16,20,24];A={d:collections.Counter() for d in days};n=0;H={d:0 for d in days}
for f in sys.argv[2:]:
    r=json.load(open(f,encoding='utf8'));N=r['info']['TeamNames'];ps=[i for i,x in enumerate(N) if who in x]
    if not ps: continue
    p=ps[0];s=r['steps'];n+=1
    for d in days:
        fm=s[d*24+12][0]['observation']['farms'][p];H[d]+=len(fm['hands'])+1
        for row in fm['tiles']:
            for x in row:
                if x=='LOCKED': continue
                if x is None: A[d]['empty']+=1
                elif x.get('kind')=='PLANT': A[d][x.get('crop')]+=1
                else: A[d][x.get('kind')]+=1; A[d]['animals']+=len(x.get('animals',[]) or [])
keys=sorted(set().union(*A.values()))
print('day   '+' '.join(f"{k[:7]:>7s}" for k in keys)+'  units')
for d in days: print(f"d{d:<4d} "+' '.join(f"{A[d][k]/n:7.1f}" for k in keys)+f"  {H[d]/n:5.1f}")
