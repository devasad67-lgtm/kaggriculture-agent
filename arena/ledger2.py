import json,sys,collections
r=json.load(open(sys.argv[1])); s=r['steps']
SEED={'WHEAT':10,'CARROT':20,'TOMATO':50,'STRAWBERRY':100,'MELON':80}; AN={'GOOSE':300,'COW':400,'SHEEP':500}; LAND=[1000,2000,4000]
def fib(n):
    a,b=1,1
    for _ in range(n): a,b=b,a+b
    return a
for p in (0,1):
    sp=collections.Counter()
    for t in range(1,720):
        f0=s[t-1][0]['observation']['farms'][p]; f1=s[t][0]['observation']['farms'][p]
        # land
        if len(f1['unlocked_quadrants'])>len(f0['unlocked_quadrants']): sp['land']+=LAND[len(f0['unlocked_quadrants'])-1]
        h0=f0['hires_today'] if t%24!=0 else 0
        for k in range(h0, f1['hires_today']): sp['hire']+=fib(k)
        sh0=s[t-1][p]['observation']['private']; sh1=s[t][p]['observation']['private']
        for c in SEED:
            used=0
            d=sh1['seeds'].get(c,0)-sh0['seeds'].get(c,0)
            # planted this step
            pl=sum(1 for y in range(10) for x in range(10) if isinstance(f1['tiles'][y][x],dict) and f1['tiles'][y][x].get('crop')==c and f1['tiles'][y][x].get('planted_day')==(t-1)//24 and not (isinstance(f0['tiles'][y][x],dict) and f0['tiles'][y][x].get('crop')==c))
            bought=d+pl
            if bought>0: sp['seed:'+c]+=bought*SEED[c]
    total_spend=sum(sp.values())
    print('player',p,'final',s[-1][p]['reward'],'spend',total_spend,dict(sp))
