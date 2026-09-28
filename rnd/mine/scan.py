import json,math
wf={json.loads(l)['f']:json.loads(l) for l in open('rnd/rt/wf_all.jsonl')}
xs=[json.loads(l) for l in open('rnd/mine/feat.jsonl')]
for x in xs:
    r=wf[x['f']]['new']; x['lose']=int(r[0]<=r[1]); x['margin']=r[0]-r[1]
    for k in list(x):
        if k.startswith('op_') and ('me_'+k[3:]) in x and isinstance(x[k],(int,float)): x['d_'+k[3:]]=x[k]-x['me_'+k[3:]]
    x['yarn']=int('YARN_STORE' in x['shops'][:2])
    x['mirror10']=int(x['same_layout10']>=95)
L=sum(x['lose'] for x in xs); print('games',len(xs),'losses',L,f'base loss rate {L/len(xs):.0%}')
def fisher(a,b,c,d):
    # two-sided Fisher exact p for [[a,b],[c,d]]
    from math import comb
    n=a+b+c+d; r1=a+b; c1=a+c
    def p(k): return comb(r1,k)*comb(n-r1,c1-k)/comb(n,c1)
    p0=p(a); return min(1.0,sum(p(k) for k in range(max(0,c1-(n-r1)),min(r1,c1)+1) if p(k)<=p0+1e-12))
keys=sorted({k for x in xs for k in x if (k.startswith(('op_','d_')) or k in('yarn','mirror10','same_layout10')) and all(isinstance(y.get(k,0),(int,float)) for y in xs)})
res=[]
for k in keys:
    vals=sorted({x.get(k,99) for x in xs})
    for th in vals:
        for side in ('>=','<='):
            T=[x for x in xs if (x.get(k,99)>=th if side=='>=' else x.get(k,99)<=th)]; Fa=[x for x in xs if x not in T]
            if len(T)<12 or len(Fa)<12: continue
            lt=sum(x['lose'] for x in T); lf=sum(x['lose'] for x in Fa)
            res.append((lt/len(T)-lf/len(Fa),k,side,th,len(T),lt,len(Fa),lf,fisher(lt,len(T)-lt,lf,len(Fa)-lf)))
res.sort(key=lambda r:r[-1])
seen=set()
print('top conditions by p-value (loss rate when true vs false):')
for d,k,side,th,nt,lt,nf,lf,p in res:
    if k in seen: continue
    seen.add(k)
    print(f'  {k}{side}{th:<6} true: {lt}/{nt} lose ({lt/nt:.0%})  false: {lf}/{nf} ({lf/nf:.0%})  p={p:.4f}')
    if len(seen)>=15: break
print('tests run:',len(res))
