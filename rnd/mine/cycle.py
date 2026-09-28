# every action on a given tile by each player, days a..b, with tile state after
import json,glob,sys
ep,x,y,a,b=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5])
f=glob.glob(f'ladder/l48mc/*{ep}*.json')[0]
r=json.load(open(f,encoding='utf8')); s=r['steps']; nm=r['info']['TeamNames']
me=[i for i,t in enumerate(nm) if 'asad' in t.lower()][0]; op=1-me
K=lambda t:(f"{t.get('crop')} age{0} y{t.get('yield_units')} w{int(t.get('watered_today'))} fert<{t.get('fertilized_until_day')}" if isinstance(t,dict) and t.get('kind')=='PLANT' else str(t.get('kind') if isinstance(t,dict) else t))
for p,lab in ((op,'OPP'),(me,'US')):
    print('==',lab,(x,y))
    for t in range(a*24,b*24):
        F=s[t][p]['observation']['farms'][p]; units=[F['farmer']]+list(F.get('hands') or [])
        act=s[t+1][p]['action'] or {}
        for u,c in enumerate([act.get('farmer')]+list(act.get('hands') or [])):
            if c and u<len(units) and tuple(units[u])==(x,y) and c[0] not in ('NORTH','SOUTH','EAST','WEST','PASS'):
                after=s[t+1][p]['observation']['farms'][p]['tiles'][y][x]
                before=F['tiles'][y][x]
                print(f"  d{t//24}h{t%24:2d} u{u:2d} {' '.join(map(str,c)):18s} before[{K(before)}] after[{K(after)}]")
