import json,glob,os,collections
rows=[]
for p in glob.glob('rnd/mine/ml/*.prof.json'):
    x=json.load(open(p)); A=x['prof'][x['me']]; B=x['prof'][1-x['me']]
    rows.append((A['sold'].get('STRAWBERRY',0)-B['sold'].get('STRAWBERRY',0), A['sold'].get('STRAWBERRY',0)*A['avgp'].get('STRAWBERRY',0)-B['sold'].get('STRAWBERRY',0)*B['avgp'].get('STRAWBERRY',0), p.replace('.prof.json','')))
rows.sort(key=lambda r:r[1])
print('per game strawberry units diff / revenue diff (us-opp):',[(u,round(v)) for u,v,_ in rows])
for u,v,f in rows[2:5]:
    r=json.load(open(f)); s=r['steps']; nm=r['info']['TeamNames']
    me=[i for i,t in enumerate(nm) if 'asad' in t.lower()][0]; op=1-me
    hv={me:collections.Counter(),op:collections.Counter()}; pl={me:collections.Counter(),op:collections.Counter()}
    for t in range(0,719):
        for p in (me,op):
            F=s[t][p]['observation']['farms'][p]; units=[F['farmer']]+list(F.get('hands') or [])
            a=s[t+1][p]['action'] or {}
            for k,c in enumerate([a.get('farmer')]+list(a.get('hands') or [])):
                if not c or k>=len(units): continue
                x_,y_=units[k]; tl=F['tiles'][y_][x_]
                if isinstance(tl,dict) and tl.get('crop')=='STRAWBERRY' and c[0]=='HARVEST': hv[p][t//24]+=tl.get('yield_units',0)
                if c[0]=='PLANT' and len(c)>1 and c[1]=='STRAWBERRY' and tl is None: pl[p][t//24]+=1
    print(os.path.basename(f)[8:17],nm[op][:12],'units',u,'rev',round(v))
    print('   plant US ',dict(sorted(pl[me].items()))); print('   plant OPP',dict(sorted(pl[op].items())))
    d=[k for k in sorted(set(hv[me])|set(hv[op])) if hv[me][k]!=hv[op][k]]
    print('   harvest days that differ (us,opp):',{k:(hv[me][k],hv[op][k]) for k in d})
