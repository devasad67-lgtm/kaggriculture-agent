import json,glob,statistics as S
rows={d:[] for d in (3,5,8,11,14,17,20)}
for f in sorted(glob.glob('ladder/l48mc/*.json'))[:40]:
    r=json.load(open(f,encoding='utf8')); s=r['steps']; n=r['info']['TeamNames']
    me=[i for i,x in enumerate(n) if 'asad' in x.lower()][0]
    for d in rows:
        o=s[d*24+12][me]['observation']; F=o['farms'][me]
        q=F['unlocked_quadrants']; tl=F['tiles']
        def quad(x,y): return ('N' if y<5 else 'S')+('W' if x<5 else 'E')
        empty=sum(1 for y in range(10) for x in range(10) if tl[y][x] is None and quad(x,y) in q and not (4<=x<=5 and 4<=y<=5))
        geese=sum(1 for row in tl for t in row if isinstance(t,dict) and t.get('animal')=='GOOSE')
        rows[d].append((empty,F['money'],len(F.get('hands') or []),geese,len(q)))
for d,v in rows.items():
    print(f"day{d:2d} empty tiles med {S.median(x[0] for x in v):4.0f}  money med {S.median(x[1] for x in v):7.0f}  hands {S.median(x[2] for x in v):3.0f}  geese {S.median(x[3] for x in v):3.0f}  quads {S.median(x[4] for x in v)}")
