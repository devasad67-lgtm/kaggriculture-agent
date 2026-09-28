import json,sys,collections
r=json.load(open(sys.argv[1])); s=r['steps']
for p in (0,1):
    u=collections.Counter(); rev=collections.Counter()
    for t in range(1,720):
        sh=dict(s[t-1][p]['observation']['private']['shed'])
        m0=s[t-1][0]['observation']['farms'][p]['money']; m1=s[t][0]['observation']['farms'][p]['money']
        for o in (s[t][p]['action'] or {}).get('market') or []:
            if o and o[0]=='SELL':
                q=min(int(o[2]),sh.get(o[1],0)); sh[o[1]]-=q; u[o[1]]+=q
    print('player',p,'final',s[-1][p]['reward'],'units sold',dict(u.most_common()))
