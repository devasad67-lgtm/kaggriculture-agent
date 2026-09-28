# per tomato-crew game (we sell TOMATO on days>=26): tomato SELL timing/price us vs opponent, days 26-29
import json,glob,sys
for f in sorted(glob.glob(sys.argv[1]+'/*.json')):
    r=json.load(open(f,encoding='utf8'));s=r['steps'];n=r['info']['TeamNames']
    me=[i for i,x in enumerate(n) if 'asad' in x.lower()][0];op=1-me
    rows={0:[],1:[]}
    for t in range(624,len(s)-1):
        a_step=s[t+1]
        price=s[t][0]['observation']['market']['prices']['TOMATO']
        for p in (me,op):
            a=a_step[p]['action'] or {}
            for o in a.get('market',[]):
                if o[:2]==['SELL','TOMATO'] and o[2]>0: rows[p==op].append((t,o[2],price))
    if not rows[0]:continue
    us=sum(q for _,q,_ in rows[0]); them=sum(q for _,q,_ in rows[1])
    def w(R): 
        q=sum(x[1] for x in R); return (sum(x[1]*x[2] for x in R)/q if q else 0)
    fu=rows[0][0][0]; fo=rows[1][0][0] if rows[1] else None
    print(f.split('-')[1], 'margin',r['rewards'][me]-r['rewards'][op],'us',us,f'{w(rows[0]):.0f}','opp',them,f'{w(rows[1]):.0f}','first us',fu,'opp',fo)
