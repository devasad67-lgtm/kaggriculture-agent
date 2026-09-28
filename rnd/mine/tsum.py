import json,os
wf={json.loads(l)['f']:json.loads(l) for l in open('rnd/rt/wf_all.jsonl')}
xs=[json.loads(l) for l in open('rnd/mine/feat.jsonl')]
G=[x for x in xs if x['same_layout10']>=95 and x.get('me_first_TOMATO',99)<=18]
for x in G:
    r=json.load(open('ladder/l48mc/'+x['f'],encoding='utf8')); s=r['steps']; n=r['info']['TeamNames']
    me=[i for i,t in enumerate(n) if 'asad' in t.lower()][0]; op=1-me
    rev={me:0,op:0}; first={}; units={me:0,op:0}
    for t in range(430,719):
        pr=s[t][0]['observation']['market']['prices'].get('TOMATO',0)
        for p in (me,op):
            sh=s[t][p]['observation']['private']['shed'].get('TOMATO',0)
            for o in (s[t+1][p]['action'] or {}).get('market') or []:
                if o and o[0]=='SELL' and o[1]=='TOMATO':
                    q=min(int(o[2]),sh)
                    if q>0: rev[p]+=q*pr; units[p]+=q; first.setdefault(p,t)
    w=wf[x['f']]['new']
    print(f"{x['opp'][:14]:14s} L48_wf {'WIN ' if w[0]>w[1] else 'LOSS'} {w[0]-w[1]:+6.0f} | tomato us {units[me]:2d}u ${rev[me]:5.0f} first d{first.get(me,0)//24}h{first.get(me,0)%24} | opp {units[op]:2d}u ${rev[op]:5.0f} first d{first.get(op,0)//24}h{first.get(op,0)%24} | diff ${rev[me]-rev[op]:+5.0f}")
