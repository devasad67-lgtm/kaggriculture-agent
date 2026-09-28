import json,sys,glob,collections
ep=sys.argv[1]; f=glob.glob(f'ladder/l48mc/*{ep}*')[0]
r=json.load(open(f,encoding='utf8')); s=r['steps']; n=r['info']['TeamNames']
me=[i for i,x in enumerate(n) if 'asad' in x.lower()][0]; op=1-me
tiles=set()
for t in range(400,719):
    a=s[t+1][op]['action'] or {}
    for o in a.get('market') or []:
        if o and len(o)>1 and o[1]=='TOMATO': print(f' t{t} d{t//24}h{t%24} market {o}')
    F=s[t][op]['observation']['farms'][op]; units=[F['farmer']]+list(F.get('hands') or [])
    cm=[a.get('farmer')]+list(a.get('hands') or [])
    for u,c in enumerate(cm):
        if not c or u>=len(units): continue
        x,y=units[u]; tl=F['tiles'][y][x]
        if c[0]=='PLANT' and len(c)>1 and c[1]=='TOMATO':
            tiles.add((x,y)); print(f' t{t} d{t//24}h{t%24} unit{u} PLANT TOMATO at {(x,y)} (was {tl})')
        elif (x,y) in tiles and c[0] in ('WATER','HARVEST','FERTILIZE'):
            print(f' t{t} d{t//24}h{t%24} unit{u} {c[0]} {(x,y)}')
# what did OUR bot have on those tiles
for (x,y) in tiles:
    print('our tile',(x,y),[ (d,(lambda t:(t.get('crop') or t.get('kind')) if isinstance(t,dict) else t)(s[d*24+12][0]['observation']['farms'][me]['tiles'][y][x])) for d in (16,17,18,19,20,22,24,26,28)])
