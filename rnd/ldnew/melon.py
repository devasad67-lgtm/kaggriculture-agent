import json,sys,glob
for f in sorted(glob.glob('ladder/l48mc/*.json'))[:3]:
    r=json.load(open(f,encoding='utf8')); s=r['steps']; n=r['info']['TeamNames']
    me=[i for i,x in enumerate(n) if 'asad' in x.lower()][0]
    print('==',f[-25:])
    for t in range(0,24*12):
        a=s[t+1][me]['action'] or {}
        mk=[o for o in a.get('market') or [] if o and ('MELON' in o or 'STRAWBERRY' in o) and o[0]!='SELL']
        F=s[t][me]['observation']['farms'][me]; units=[F['farmer']]+list(F.get('hands') or [])
        cm=[a.get('farmer')]+list(a.get('hands') or [])
        pl=[(u,tuple(units[u]),c) for u,c in enumerate(cm) if c and c[0] in('PLANT','HARVEST') and len(c)>0 and u<len(units) and (len(c)<2 or c[1] in('MELON','STRAWBERRY') or c[0]=='HARVEST')]
        pl=[x for x in pl if x[2][0]=='PLANT' or isinstance(F['tiles'][x[1][1]][x[1][0]],dict) and F['tiles'][x[1][1]][x[1][0]].get('crop') in ('MELON','STRAWBERRY')]
        if mk or pl: print(f" t{t} d{t//24}h{t%24} market{mk} units{pl}")
