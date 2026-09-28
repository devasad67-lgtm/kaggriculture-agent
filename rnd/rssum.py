import json,sys,collections,statistics as st
xs=[json.loads(l) for l in open(sys.argv[1])]; xs=[x for x in xs if 'new' in x]
shops={}
for f in set(x['f'] for x in xs):
    pass
base={x['f']:x['new'][0]-x['new'][1] for x in xs if x['route']==-1}
by=collections.defaultdict(list)
for x in xs:
    if x['f'] in base: by[x['route']].append(((x['new'][0]-x['new'][1]),base[x['f']],x['new'][0]))
print('route  n  wins  meanMargin  vsDefault  myMoney')
for r,v in sorted(by.items(),key=lambda kv:-st.mean(a-b for a,b,_ in kv[1])):
    print(f"{r:5d} {len(v):3d} {sum(a>0 for a,_,_ in v):4d} {st.mean(a for a,_,_ in v):+10.0f} {st.mean(a-b for a,b,_ in v):+9.0f} {st.mean(m for *_,m in v):8.0f}")
