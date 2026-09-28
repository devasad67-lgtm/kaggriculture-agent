import json,glob,collections
for f in sorted(glob.glob('ladder/dsm2/*.json'))[:12]:
    r=json.load(open(f,encoding='utf8')); s=r['steps']; n=r['info']['TeamNames']
    p=[i for i,x in enumerate(n) if 'DSM' in x]
    if not p: continue
    p=p[0]; out=[]
    for d in (8,12,16,20,24):
        F=s[d*24+12][0]['observation']['farms'][p]; tl=F['tiles']
        se=collections.Counter((t.get('crop') or t.get('animal') or t['kind']) for y in range(5,10) for x in range(5,10) for t in [tl[y][x]] if isinstance(t,dict))
        out.append(f"d{d}:q{len(F['unlocked_quadrants'])} h{len(F.get('hands') or [])} {dict(se)}")
    print(round(r['rewards'][p]),' | '.join(out))
