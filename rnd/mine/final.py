import json,glob,os,collections
tot=collections.Counter(); n=0
for f in sorted(glob.glob('rnd/mine/ml/*.json')):
    if f.endswith('.prof.json'): continue
    r=json.load(open(f)); s=r['steps']; nm=r['info']['TeamNames']
    me=[i for i,x in enumerate(nm) if 'asad' in x.lower()][0]; op=1-me; n+=1
    F=lambda t,p:s[t][0]['observation']['farms'][p]['money']
    g0=F(695,me)-F(695,op); g1=r['rewards'][me]-r['rewards'][op]
    print(f"{os.path.basename(f)[8:17]} {nm[op][:12]:12s} gap at d28h23 {g0:+7.0f} -> final {g1:+7.0f} (day29 {g1-g0:+6.0f})")
    for t in range(696,719):
        pr=s[t][0]['observation']['market']['prices']
        rows=[]
        for p in (me,op):
            sh=s[t][p]['observation']['private']['shed']
            L=[(o[1],min(int(o[2]),sh.get(o[1],0))) for o in (s[t+1][p]['action'] or {}).get('market') or [] if o and o[0]=='SELL' and len(o)>2 and sh.get(o[1],0)>0]
            rows.append(L)
        dg=(F(t+1,me)-F(t+1,op))-(F(t,me)-F(t,op))
        if rows[0]!=rows[1] or abs(dg)>=100:
            print(f"   h{t%24:2d} dgap {dg:+6.0f} us {rows[0]} | opp {rows[1]}")
