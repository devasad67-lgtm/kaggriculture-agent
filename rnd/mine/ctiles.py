import json,glob,os,sys
K=lambda t:((t.get('crop') or t.get('animal') or t.get('kind'))[:4]+('/'+str(t.get('yield_units')) if t.get('kind')=='PLANT' else '')) if isinstance(t,dict) else str(t)[:4]
for ep in sys.argv[1:]:
    f=glob.glob(f'rnd/mine/ml/*{ep}*.json')[0]
    r=json.load(open(f)); s=r['steps']; nm=r['info']['TeamNames']
    me=[i for i,x in enumerate(nm) if 'asad' in x.lower()][0]; op=1-me
    tiles={}
    for t in range(456,24*24):
        a=s[t+1][op]['action'] or {}
        F=s[t][op]['observation']['farms'][op]; units=[F['farmer']]+list(F.get('hands') or [])
        for u,c in enumerate([a.get('farmer')]+list(a.get('hands') or [])):
            if c and c[0]=='PLANT' and len(c)>1 and c[1]=='CARROT' and u<len(units) and F['tiles'][units[u][1]][units[u][0]] is None:
                tiles.setdefault(tuple(units[u]),(t//24,u))
    print(os.path.basename(f)[8:17],nm[op][:12],'opp early carrot tiles (day,unit):',tiles)
    for (x,y),(d,u) in sorted(tiles.items()):
        print('   ',(x,y),'OUR tile d19..26:',[K(s[dd*24+12][0]['observation']['farms'][me]['tiles'][y][x]) for dd in range(19,27)])
