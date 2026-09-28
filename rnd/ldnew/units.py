import json,sys,glob
ep,it,a,b=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4])
f=glob.glob(f'ladder/*/episode-{ep}-replay.json')[0]
r=json.load(open(f,encoding='utf8')); s=r['steps']; n=r['info']['TeamNames']
me=[i for i,x in enumerate(n) if 'asad' in x.lower()][0]; op=1-me
for p,lab in ((me,'ME'),(op,'OP')):
    print(lab)
    for t in range(a,b):
        o=s[t][p]['observation']; inv=o['private'].get('inventories',[]) or []
        F=o['farms'][p]; pos=[F['farmer']]+list(F.get('hands') or [])
        act=s[t+1][p]['action'] or {}; cm=[act.get('farmer')]+list(act.get('hands') or [])
        row=[f"u{u}{tuple(pos[u])}{dict(inv[u] or {}).get(it,0):2d}:{(cm[u] or ['-'])[0][:5]}" for u in range(len(pos)) if u<len(inv) and dict(inv[u] or {}).get(it,0)>0]
        print(f" t{t} h{t%24}", ' '.join(row))
