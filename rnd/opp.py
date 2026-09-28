import json,glob,sys,collections
rows=[]
for f in sorted(glob.glob(sys.argv[1]+'/*.json')):
    try: r=json.load(open(f,encoding='utf8'))
    except Exception: continue
    names=r.get('info',{}).get('TeamNames') or []
    if len(names)<2: continue
    me=[i for i,n in enumerate(names) if 'asad' in n.lower()]
    if not me: continue
    me=me[0]; op=1-me; rw=r['rewards']
    rows.append((names[op],rw[me],rw[op],me,f.split('-')[-2] if '-' in f else f))
W=sum(x[1]>x[2] for x in rows); print(sys.argv[1],'games',len(rows),'W',W,'L',len(rows)-W)
agg=collections.defaultdict(list)
for x in rows: agg[x[0]].append(x)
for n,xs in sorted(agg.items(),key=lambda kv:sum(a[1]-a[2] for a in kv[1])):
    l=[x for x in xs if x[1]<x[2]]
    if l: print(f"{n[:28]:28s} L{len(l)}/{len(xs)}", ' '.join(f"{x[1]-x[2]:+.0f}(me{x[1]:.0f},s{x[3]})" for x in l))
