import json,glob,os,collections
cls=collections.Counter(); byday=collections.Counter(); n=0
detail=collections.defaultdict(list)
for f in sorted(glob.glob('rnd/mine/ml/*.json')):
    if f.endswith('.prof.json'): continue
    r=json.load(open(f)); s=r['steps']; nm=r['info']['TeamNames']
    me=[i for i,x in enumerate(nm) if 'asad' in x.lower()][0]; op=1-me; n+=1
    fin=r['rewards'][me]-r['rewards'][op]
    prev=0
    for t in range(1,len(s)):
        F=s[t][0]['observation']['farms']; g=F[me]['money']-F[op]['money']; dg=g-prev; prev=g
        if abs(dg)<1: continue
        def sells(p):
            sh=s[t-1][p]['observation']['private']['shed']; out={}
            for o in (s[t][p]['action'] or {}).get('market') or []:
                if o and o[0]=='SELL' and len(o)>2:
                    q=min(int(o[2]),sh.get(o[1],0))
                    if q>0: out[o[1]]=out.get(o[1],0)+q
            return out
        A,B=sells(me),sells(op)
        other=lambda p:[tuple(o[:2]) for o in (s[t][p]['action'] or {}).get('market') or [] if o and o[0]!='SELL']
        if not A and not B:
            key=('nonsell','buys/hires differ' if other(me)!=other(op) else 'other')
        else:
            items=set(A)|set(B)
            it=max(items,key=lambda k:abs(A.get(k,0)-B.get(k,0))+ (A.get(k,0)+B.get(k,0)))
            if it in A and it in B: kind='both sell same step' + (' (same qty)' if A[it]==B[it] else ' (diff qty)')
            elif it in B: kind='OPP sells, we do not'
            else: kind='WE sell, opp does not'
            key=(it,kind)
        cls[key]+=dg; byday[t//24]+=dg
        if abs(dg)>=300: detail[key].append((os.path.basename(f)[8:17],t,round(dg),A,B))
print('games',n)
print('gap change by cause (sum over all 22 losses; negative = we lost money relative to opp):')
for k,v in sorted(cls.items(),key=lambda kv:kv[1])[:16]: print(f'  {v:+9.0f}  {k}')
print('...positive:'); 
for k,v in sorted(cls.items(),key=lambda kv:-kv[1])[:8]: print(f'  {v:+9.0f}  {k}')
print('by day:',{d:round(v) for d,v in sorted(byday.items()) if abs(v)>200})
json.dump({str(k):v for k,v in detail.items()},open('rnd/mine/attr_detail.json','w'))
