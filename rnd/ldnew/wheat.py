import json,glob,collections,os
rows=[]
for p in glob.glob('rnd/ldnew/*.prof.json'):
    x=json.load(open(p)); dn=os.path.basename(p).split('_')[0]
    r=json.load(open(f"ladder/{dn}/{x['f']}",encoding='utf8')); s=r['steps']; me=x['me']
    c=[collections.Counter(),collections.Counter()]
    for t in range(1,len(s)):
        for p_ in (0,1):
            for o in (s[t][p_]['action'] or {}).get('market') or []:
                if o and len(o)>2 and o[1]=='WHEAT': c[p_][o[0]]+=int(o[2])
    A,B=c[me],c[1-me]
    rows.append((x['prof'][1-me]['name'][:16],x['prof'][me]['reward']-x['prof'][1-me]['reward'],A['SELL'],A['BUY_PRODUCT'],B['SELL'],B['BUY_PRODUCT']))
rows.sort(key=lambda r:r[1])
for r in rows[:40]: print('%-16s %+7.0f  me sell %5d buy %5d | op sell %5d buy %5d'%r)
