import json,sys
r=json.load(open(sys.argv[1])); s=r['steps']
ob=lambda t:s[t][0]['observation']
print('money diff (me-opp) by day:',[round(ob(min(d*24+23,719))['farms'][0]['money']-ob(min(d*24+23,719))['farms'][1]['money']) for d in range(30)])
c=0
for t in range(1,720):
    a=[o for o in (s[t][0]['action'] or {}).get('market') or [] if o]; b=[o for o in (s[t][1]['action'] or {}).get('market') or [] if o]
    fa=json.dumps({k:(s[t][0]['action'] or {}).get(k) for k in('farmer','hands')}); fb=json.dumps({k:(s[t][1]['action'] or {}).get(k) for k in('farmer','hands')})
    if a!=b or fa!=fb:
        c+=1
        if c<=int(sys.argv[2]): print(t,'d',t//24,'h',t%24,'ME',a,'| OP',b,'' if fa==fb else 'FARMDIFF', round(ob(t)['farms'][0]['money']-ob(t)['farms'][1]['money']))
print('diff steps',c)
