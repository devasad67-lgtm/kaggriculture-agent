import json,sys
f=sys.argv[1];r=json.load(open(f,encoding='utf8'));s=r['steps'];n=r['info']['TeamNames']
me=[i for i,x in enumerate(n) if 'asad' in x.lower()][0];op=1-me
print('me idx',me)
for t in range(624,len(s)-1):
    out=[]
    for p in (me,op):
        a=s[t+1][p]['action'] or {}
        for o in a.get('market',[]):
            if o[:2]==['SELL','TOMATO'] and o[2]>0: out.append(('US' if p==me else 'OP',o[2]))
    if out:
        pr=[s[t+k][0]['observation']['market']['prices']['TOMATO'] for k in (0,1,2)]
        inv=s[t+2][0]['observation']['market']['inventory']['TOMATO']
        print(t,t//24,t%24,out,'price',pr,'mkt inv',inv, 'money',[s[t+2][p]['observation']['private'].get('money') if 'private' in s[t+2][p]['observation'] else None for p in (me,op)])
