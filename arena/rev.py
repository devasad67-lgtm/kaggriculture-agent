# per-item revenue by player, reconstructed from shed deltas + prices seen
import json,sys,collections
r=json.load(open(sys.argv[1])); s=r['steps']
for p in (0,1):
    rev=collections.Counter(); units=collections.Counter(); late=collections.Counter()
    for t in range(1,len(s)):
        acts=(s[t][p]['action'] or {}).get('market') or []
        m0=s[t-1][p]['observation']['farms'][p]['money'] if 'farms' in s[t-1][p]['observation'] else 0
    last=s[-1][p]['observation']
    print('player',p,'reward',s[-1][p]['reward'],'leftover shed',{k:v for k,v in (last.get('private') or {}).get('shed',{}).items() if v})
