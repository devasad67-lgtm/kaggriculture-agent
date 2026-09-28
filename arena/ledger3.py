import json,sys,collections
r=json.load(open(sys.argv[1])); s=r['steps']; t0=int(sys.argv[2]) if len(sys.argv)>2 else 1
SEED={'WHEAT':10,'CARROT':20,'TOMATO':50,'STRAWBERRY':100,'MELON':80}; AN={'GOOSE':300,'COW':400,'SHEEP':500}; LAND=[1000,2000,4000]
def fib(n):
    a,b=1,1
    for _ in range(n): a,b=b,a+b
    return a
for p in (0,1):
    sp=collections.Counter(); sold=collections.Counter()
    for t in range(t0,720):
        o0=s[t-1][0]['observation']; o1=s[t][0]['observation']
        f0=o0['farms'][p]; f1=o1['farms'][p]
        P0=s[t-1][p]['observation']['private']; P1=s[t][p]['observation']['private']
        dm=f1['money']-f0['money']
        if len(f1['unlocked_quadrants'])>len(f0['unlocked_quadrants']): sp['land']+=LAND[len(f0['unlocked_quadrants'])-1]
        h0=f0['hires_today'] if t%24!=0 else 0
        hc=sum(fib(k) for k in range(h0, f1['hires_today'])); sp['hire']+=hc
        seedc=0
        for c in SEED:
            planted=sum(1 for y in range(10) for x in range(10) if isinstance(f1['tiles'][y][x],dict) and f1['tiles'][y][x].get('crop')==c and f1['tiles'][y][x].get('planted_day')==(t-1)//24 and not (isinstance(f0['tiles'][y][x],dict) and f0['tiles'][y][x].get('crop')==c and f0['tiles'][y][x].get('planted_day')==(t-1)//24))
            b=P1['seeds'].get(c,0)-P0['seeds'].get(c,0)+planted
            if b>0: seedc+=b*SEED[c]; sp['seed']+=b*SEED[c]
        anc=0
        for a in AN:
            placed=sum(1 for y in range(10) for x in range(10) if isinstance(f1['tiles'][y][x],dict) and f1['tiles'][y][x].get('animal')==a)-sum(1 for y in range(10) for x in range(10) if isinstance(f0['tiles'][y][x],dict) and f0['tiles'][y][x].get('animal')==a)
            inv1=P1['shed'].get(a,0)+sum(i.get(a,0) for i in P1['inventories']); inv0=P0['shed'].get(a,0)+sum(i.get(a,0) for i in P0['inventories'])
            esc=0
            b=inv1-inv0+max(0,placed)
            if b>0: anc+=b*AN[a]; sp['animal']+=b*AN[a]
        # market product trades: residual
        resid=dm+hc+seedc+anc+(LAND[len(f0['unlocked_quadrants'])-1] if len(f1['unlocked_quadrants'])>len(f0['unlocked_quadrants']) else 0)
        if resid>=0: sold['net_market_in']+=resid
        else: sp['product_buy']+=-resid
    print('P',p,'money@t0',int(s[t0-1][0]['observation']['farms'][p]['money']),'final',s[-1][p]['reward'],'sales+',int(sold['net_market_in']),'spend',dict(sp))
