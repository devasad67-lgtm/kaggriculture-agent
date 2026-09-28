import sys,json,collections
sys.path.insert(0,'rnd'); import resim
f=sys.argv[1]
r,env,log=resim.resim(f); n=r['info']['TeamNames']; me=[i for i,x in enumerate(n) if 'asad' in x.lower()][0]; op=1-me
print(n,r['rewards'])
S=collections.defaultdict(lambda:[0,0]); B=collections.defaultdict(lambda:[0,0])
for t,p,o,item,price in log:
    k=0 if p==me else 1
    if o=='SELL': S[item][k]+=price; S[item+'#'][k]+=1
    else: B[o+':'+item][k]+=price
print('REVENUE (us, DSM)'); [print(f"  {k:12s} ${v[0]:7d} ({S[k+'#'][0]:4d}u)   ${v[1]:7d} ({S[k+'#'][1]:4d}u)") for k,v in S.items() if not k.endswith('#')]
print('SPEND (us, DSM)'); [print(f"  {k:24s} ${v[0]:7d}   ${v[1]:7d}") for k,v in sorted(B.items())]
# who sells first each day per product
for item in sys.argv[2].split(','):
    print('==',item)
    byday=collections.defaultdict(list)
    for t,p,o,it,price in log:
        if o=='SELL' and it==item: byday[t//24].append((t%24,'US' if p==me else 'DSM',price))
    for d in sorted(byday):
        ev=byday[d]; agg=collections.OrderedDict()
        for h,w,pr in ev:
            key=(h,w); a=agg.setdefault(key,[0,pr,pr]); a[0]+=1; a[2]=pr
        print(f"  d{d:2d} "+' '.join(f"h{h}:{w}x{a[0]}@{a[1]}->{a[2]}" for (h,w),a in agg.items()))
