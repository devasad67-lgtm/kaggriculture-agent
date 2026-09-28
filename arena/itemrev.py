import json,sys,collections
tot=collections.Counter()
for f in sys.argv[1:]:
    r=json.load(open(f)); s=r['steps']
    for p in (0,1):
        for t in range(1,720):
            ob=s[t-1][0]['observation']; mk=ob['market']; inv=dict(mk['inventory'])
            shed=dict(s[t-1][p]['observation']['private']['shed'])
            for o in (s[t][p]['action'] or {}).get('market') or []:
                if o and o[0]=='SELL':
                    n=min(int(o[2]),shed.get(o[1],0)); shed[o[1]]=shed.get(o[1],0)-n
                    tot[(o[1],p)]+=n*mk['prices'][o[1]]
    print(f, [s[-1][p]['reward'] for p in (0,1)])
items=sorted({k[0] for k in tot})
for it in items: print(it.ljust(11), 'me', tot[(it,0)], 'opp', tot[(it,1)], 'diff', tot[(it,0)]-tot[(it,1)])
