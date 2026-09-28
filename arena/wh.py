import json,sys,collections
r=json.load(open(sys.argv[1])); s=r['steps']; t0=int(sys.argv[2]); crop=sys.argv[3]
for p in (0,1):
    c=collections.Counter()
    for t in range(t0,720):
        f0=s[t-1][0]['observation']['farms'][p]; a=s[t][p]['action'] or {}
        pos=[f0['farmer']]+f0['hands']
        for ui,act in enumerate([a.get('farmer')]+list(a.get('hands') or [])):
            if not act or ui>=len(pos) or act[0]!='HARVEST': continue
            x,y=pos[ui]; tl=f0['tiles'][y][x]
            if isinstance(tl,dict) and tl.get('crop')==crop:
                c[((t-1)//24-tl['planted_day'], tl['yield_units'])]+=1
    print('P',p,sorted(c.items()))
