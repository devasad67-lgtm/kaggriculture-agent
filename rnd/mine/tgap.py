import json,glob,os,collections
for f in sorted(glob.glob('rnd/mine/tl/*.json')):
    if f.endswith('.prof.json'): continue
    r=json.load(open(f)); s=r['steps']; n=r['info']['TeamNames']
    me=[i for i,x in enumerate(n) if 'asad' in x.lower()][0]; op=1-me
    fin=r['rewards'][me]-r['rewards'][op]
    # money gap by day
    g=[round(s[min(d*24+23,719)][0]['observation']['farms'][me]['money']-s[min(d*24+23,719)][0]['observation']['farms'][op]['money']) for d in (17,20,23,25,26,27,28,29)]
    # tomato sells: step, qty, price for each side
    ts={}
    for p in (me,op):
        L=[]
        for t in range(430,719):
            pr=s[t][0]['observation']['market']['prices'].get('TOMATO')
            for o in (s[t+1][p]['action'] or {}).get('market') or []:
                if o and o[0]=='SELL' and o[1]=='TOMATO' and int(o[2])>0:
                    sh=s[t][p]['observation']['private']['shed'].get('TOMATO',0)
                    if sh>0: L.append(f"d{t//24}h{t%24}:{min(int(o[2]),sh)}@{pr}")
        ts[p]=L
    print(os.path.basename(f)[8:17],n[op][:14],'final',fin,'gap d17..29',g)
    print('   our tomato sells ',ts[me][:8]); print('   opp tomato sells ',ts[op][:8])
