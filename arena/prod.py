import json,sys,collections
r=json.load(open(sys.argv[1])); s=r['steps']; t0=int(sys.argv[2])
for p in (0,1):
    prod=collections.Counter()
    for t in range(t0,720):
        f0=s[t-1][0]['observation']['farms'][p]
        a=s[t][p]['action'] or {}
        pos=[f0['farmer']]+f0['hands']
        for ui,act in enumerate([a.get('farmer')]+list(a.get('hands') or [])):
            if not act or ui>=len(pos): continue
            x,y=pos[ui]; tl=f0['tiles'][y][x]
            if act[0]=='HARVEST' and isinstance(tl,dict):
                k=tl.get('crop') or {'GOOSE':'EGG','COW':'MILK','SHEEP':'WOOL'}.get(tl.get('animal'))
                prod[k]+=tl.get('yield_units',0)
            if act[0]=='COLLECT_FERTILIZER' and isinstance(tl,dict) and tl.get('fertilizer_available'): prod['FERT']+=1
    print('P',p,dict(prod.most_common()), 'total units',sum(prod.values()))
