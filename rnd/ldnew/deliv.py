# per item: in games where both farms produce it, how often does the rival's first daily shed arrival come earlier than ours
import json,glob,collections,sys
items=('MILK','WOOL','EGG','STRAWBERRY','CARROT','TOMATO','MELON')
stat={it:[0,0,0,0] for it in items}   # opp earlier days, we earlier, same, total steps diff
files=sorted(glob.glob('ladder/l48mc/*.json'))[:int(sys.argv[1])]
for f in files:
    r=json.load(open(f,encoding='utf8')); s=r['steps']; n=r['info']['TeamNames']
    me=[i for i,x in enumerate(n) if 'asad' in x.lower()][0]; op=1-me
    for d in range(8,28):
        first={}
        for p in (me,op):
            prev=None
            for t in range(d*24+1,d*24+23):
                o=s[t][p]['observation']; sh=o['private']['shed']
                sold=collections.Counter()
                for od in (s[t][p]['action'] or {}).get('market') or []:
                    if od and od[0]=='SELL' and len(od)>2: sold[od[1]]+=int(od[2])
                for it in items:
                    if (p,it) in first: continue
                    v=sh.get(it,0)
                    if prev is not None and v+min(sold[it],prev.get(it,0)+50)>prev.get(it,0) and (v>prev.get(it,0) or sold[it]>prev.get(it,0)):
                        first[(p,it)]=t
                prev=dict(sh)
        for it in items:
            a,b=first.get((me,it)),first.get((op,it))
            if a is None or b is None: continue
            if b<a: stat[it][0]+=1
            elif a<b: stat[it][1]+=1
            else: stat[it][2]+=1
            stat[it][3]+=a-b
for it,v in stat.items():
    tot=v[0]+v[1]+v[2]
    if tot: print(f"{it:10s} days={tot:4d} rival earlier {v[0]:4d}  we earlier {v[1]:4d}  same {v[2]:4d}  mean(our-rival) {v[3]/tot:+.2f} steps")
