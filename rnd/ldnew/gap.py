import json,sys,glob
ep=sys.argv[1]; f=(glob.glob(f'ladder/*/episode-{ep}-replay.json')+[ep])[0]
r=json.load(open(f,encoding='utf8')); s=r['steps']; n=r['info']['TeamNames']
me=[i for i,x in enumerate(n) if 'asad' in x.lower()][0]; op=1-me
prev=0; 
for t in range(1,len(s)):
    F=s[t][0]['observation']['farms']; g=F[me]['money']-F[op]['money']
    if abs(g-prev)>=150:
        A=[o for o in (s[t][me]['action'] or {}).get('market') or [] if o]; B=[o for o in (s[t][op]['action'] or {}).get('market') or [] if o]
        pr=s[t-1][0]['observation']['market']['prices']
        print(f"t{t-1} d{(t-1)//24}h{(t-1)%24} gap {prev:+.0f}->{g:+.0f}  me{A}  op{B}  p={ {k:pr[k] for k in ('WOOL','MILK','STRAWBERRY','CARROT','EGG','MELON','TOMATO')} }")
    prev=g
print('final',r['rewards'][me]-r['rewards'][op])
