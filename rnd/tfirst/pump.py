# large wheat BUY (>=40) events: our steps vs rival steps, per game
import json,glob,sys
for f in sorted(glob.glob(sys.argv[1]+'/*.json')):
    r=json.load(open(f,encoding='utf8'));s=r['steps'];N=r['info']['TeamNames']
    me=[i for i,x in enumerate(N) if 'asad' in x.lower()][0];op=1-me
    ev={}
    for p in (me,op):
        ev[p]=[(t,o[2]) for t in range(len(s)-1) for o in (s[t+1][p]['action'] or {}).get('market') or [] if o and len(o)>2 and o[0]=='BUY_PRODUCT' and o[1]=='WHEAT' and o[2]>=40]
    m=r['rewards'][me]-r['rewards'][op]
    print(f.split('-')[1],N[op][:12].replace(' ','_'),int(m),'US',ev[me],'OP',ev[op],flush=True)
