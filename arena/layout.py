import json,sys,collections
r=json.load(open(sys.argv[1],encoding='utf8')); n=r['info']['TeamNames']; p=n.index(sys.argv[2]) if sys.argv[2] in n else [i for i,x in enumerate(n) if 'asad' in x.lower()][0]
print(n[p], r['rewards'][p], 'shops', r['steps'][-1][0]['observation']['town']['unlocked_shops'])
for d in range(0,30,2):
    t=d*24+12; f=r['steps'][t][0]['observation']['farms'][p]
    c=collections.Counter()
    for row in f['tiles']:
        for x in row:
            if x is None: c['empty']+=1
            elif x=='LOCKED': pass
            elif 'animal' in x: c[x['animal']]+=1
            elif x.get('kind')=='PLANT': c[x['crop']]+=1
            else: c[x['kind']]+=1
    print('day',d,'$',round(f['money']),'hands',len(f['hands']),'quads',len(f['unlocked_quadrants']),dict(c))
