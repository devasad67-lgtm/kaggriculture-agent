import json,glob,sys
def load(f):
    r=json.load(open(f,encoding='utf8')); n=r['info']['TeamNames']; me=[i for i,x in enumerate(n) if 'asad' in x.lower()][0]; return r,me,1-me,n
for f in sorted(glob.glob('reps/*.json')):
    r,me,op,n=load(f)
    if n[0]==n[1]: continue
    rw=r['rewards']; tag='L' if rw[me]<rw[op] else 'W'
    s=r['steps']
    first={}
    for t in range(1,720):
        a=s[t][me]['action'] or {}; b=s[t][op]['action'] or {}
        for k in ('farmer','hands'):
            if k not in first and json.dumps(a.get(k))!=json.dumps(b.get(k)): first[k]=t
        am=[o for o in (a.get('market') or [])]; bm=[o for o in (b.get('market') or [])]
        if 'market' not in first and json.dumps(am)!=json.dumps(bm): first['market']=(t,am,bm)
    print(tag,n[op][:14].ljust(14),int(rw[me]-rw[op]),'farm',first.get('farmer'),'hands',first.get('hands'),'mkt',str(first.get('market'))[:150])
