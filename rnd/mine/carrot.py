import json,glob,os,collections
rows=[]
for p in glob.glob('rnd/mine/ml/*.prof.json'):
    x=json.load(open(p)); A=x['prof'][x['me']]; B=x['prof'][1-x['me']]
    rows.append((A['sold'].get('CARROT',0)-B['sold'].get('CARROT',0),p.replace('.prof.json','')))
rows.sort()
for dc,f in rows[:6]:
    r=json.load(open(f)); s=r['steps']; nm=r['info']['TeamNames']
    me=[i for i,x in enumerate(nm) if 'asad' in x.lower()][0]; op=1-me
    pl={me:collections.Counter(),op:collections.Counter()}; hv={me:collections.Counter(),op:collections.Counter()}
    for t in range(300,719):
        for p in (me,op):
            a=s[t+1][p]['action'] or {}
            F=s[t][p]['observation']['farms'][p]; units=[F['farmer']]+list(F.get('hands') or [])
            for u,c in enumerate([a.get('farmer')]+list(a.get('hands') or [])):
                if not c or u>=len(units): continue
                x_,y_=units[u]; tl=F['tiles'][y_][x_]
                if c[0]=='PLANT' and len(c)>1 and c[1]=='CARROT' and tl is None: pl[p][t//24]+=1
                if c[0]=='HARVEST' and isinstance(tl,dict) and tl.get('crop')=='CARROT' and tl.get('yield_units',0)>0: hv[p][t//24]+=tl['yield_units']
    print(os.path.basename(f)[8:17],nm[op][:12],'carrot units diff',dc)
    print('   planted/day US ',dict(sorted(pl[me].items()))); print('   planted/day OPP',dict(sorted(pl[op].items())))
    print('   harvest/day US ',dict(sorted(hv[me].items()))); print('   harvest/day OPP',dict(sorted(hv[op].items())))
