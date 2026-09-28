import json,glob,itertools
G=[]
for f in sorted(glob.glob('top/*.json'))[:20]:
    r=json.load(open(f,encoding='utf8')); n=r['info']['TeamNames']
    if 'DSM' not in n: continue
    p=n.index('DSM')
    G.append(([json.dumps({k:(r['steps'][t][p]['action'] or {}).get(k) for k in ('farmer','hands')},sort_keys=True) for t in range(1,720)],
              [json.dumps((r['steps'][t][p]['action'] or {}).get('market')) for t in range(1,720)], f))
def pref(a,b):
    for i,(x,y) in enumerate(zip(a,b)):
        if x!=y: return i+1
    return 719
fa=[];ma=[]
for (a1,m1,_),(a2,m2,_) in itertools.combinations(G,2):
    fa.append(pref(a1,a2)); ma.append(pref(m1,m2))
fa.sort(); ma.sort()
print('games',len(G)); print('farm-identical prefix steps',fa[::max(1,len(fa)//10)]); print('market prefix',ma[::max(1,len(ma)//10)])
