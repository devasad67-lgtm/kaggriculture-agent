import json,sys,collections,statistics as S
days=[6,10,14,18,22,26,29];P=collections.defaultdict(lambda:collections.defaultdict(list))
items=['TOMATO','EGG','CARROT','STRAWBERRY','MILK','WOOL','MELON','WHEAT']
for f in sys.argv[1:]:
    r=json.load(open(f,encoding='utf8'));s=r['steps']
    for d in days:
        ob=s[min(d*24+12,len(s)-1)][0]['observation'];sh=ob['town']['unlocked_shops']
        for it in items: P[it][d].append(ob['market']['prices'][it])
print('median / p90 market price by day')
for it in items: print(f"{it:10s}",' '.join(f"d{d}:{S.median(P[it][d]):4.0f}/{sorted(P[it][d])[int(.9*len(P[it][d]))]:4.0f}" for d in days))
