import json,sys,collections
f=sys.argv[1]
r=json.load(open(f,encoding='utf8')); s=r['steps']; n=r['info']['TeamNames']
me=[i for i,x in enumerate(n) if 'asad' in x.lower()][0]
for d in (12,18,24):
    o=s[d*24+12][me]['observation']; F=o['farms'][me]
    pos={}
    for y,row in enumerate(F['tiles']):
        for x,t in enumerate(row):
            if isinstance(t,dict) and t.get('animal'): pos[(x,y)]=t['animal']
    print('day',d,'animals',collections.Counter(pos.values()), sorted(pos.items()))
    # which units act on animal tiles today
    acts=collections.defaultdict(set)
    for t in range(d*24,d*24+24):
        ob=s[t][me]['observation']; Fo=ob['farms'][me]; units=[Fo['farmer']]+list(Fo.get('hands') or [])
        a=s[t+1][me]['action'] or {}; cm=[a.get('farmer')]+list(a.get('hands') or [])
        for u,p in enumerate(units):
            if u<len(cm) and cm[u] and cm[u][0] in ('FEED','CARE','HARVEST','COLLECT_FERTILIZER') and tuple(p) in pos:
                acts[pos[tuple(p)]].add(u)
    print('   units acting on animals',{k:sorted(v) for k,v in acts.items()})
