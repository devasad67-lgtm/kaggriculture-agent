import sys,io,contextlib,importlib.util,os,collections
spec=importlib.util.spec_from_file_location('bm','D:/kaggle/beast/main.py'); bm=importlib.util.module_from_spec(spec); spec.loader.exec_module(bm)
sys.path.insert(0,'.'); from tourney import resolve
with contextlib.redirect_stdout(io.StringIO()):
    from kaggle_environments import make
    env=make("kaggriculture",configuration={"seed":int(sys.argv[2]) if len(sys.argv)>2 else 2000,"episodeSteps":720},debug=True)
    env.run([bm.agent,resolve(sys.argv[1] if len(sys.argv)>1 else 'passbot')])
s=env.steps; L=collections.Counter()
SEED={'WHEAT':10,'CARROT':20,'TOMATO':50,'STRAWBERRY':100,'MELON':80}; AN={'GOOSE':300,'COW':400,'SHEEP':500}
for t in range(1,len(s)):
    ob=s[t-1][0].observation; nob=s[t][0].observation
    sh=dict(ob['private']['shed']); sh2=dict(nob['private']['shed'])
    for o in (s[t][0].action or {}).get('market') or []:
        if o[0]=='SELL': pass
        elif o[0]=='BUY_SEED': L['seed:'+o[1]]-=0
    # derive: sold units per item = decrease in shed not explained by pickups... approximate via money delta
m0=3000
print('final',s[-1][0].reward)
# simpler: daily money + counts of purchases
for d in range(30):
    buys=collections.Counter(); sells=collections.Counter()
    for t in range(d*24+1, min(d*24+25,len(s))):
        for o in (s[t][0].action or {}).get('market') or []:
            if o[0]=='SELL': sells[o[1]]+=o[2]
            elif o[0]=='HIRE': buys['HIRE']+=1
            else: buys[o[0]+':'+(o[1] if len(o)>1 else '')]+= o[2] if len(o)>2 else 1
    print(d,int(s[min(d*24+24,len(s)-1)][0].observation['farms'][0]['money']),'BUY',dict(buys))
print('--- actual units sold/bought per day (from shed changes at market) & prices')
for d in range(0,30,3):
    t=d*24+1; ob=s[t][0].observation
    eggs=sum(1 for row in ob['farms'][0]['tiles'] for x in row if isinstance(x,dict) and x.get('animal')=='GOOSE')
    tot=collections.Counter()
    for tt in range(d*24+1,d*24+25):
        o0=s[tt-1][0].observation; o1=s[tt][0].observation
        for o in (s[tt][0].action or {}).get('market') or []:
            if o[0]=='SELL':
                q=min(o[2],o0['private']['shed'].get(o[1],0)); tot['sell:'+o[1]]+=q; tot['$sell:'+o[1]]+=q*o0['market']['prices'][o[1]]
            if o[0]=='BUY_PRODUCT': tot['$buyW']+=o[2]*o0['market']['prices'][o[1]]
    print(d,'geese',eggs,{k:v for k,v in tot.items()}, ob['market']['prices']['WHEAT'],ob['market']['prices']['EGG'])
