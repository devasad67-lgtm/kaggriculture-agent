import json,glob,sys
f=[x for x in glob.glob('reps/*.json') if sys.argv[1] in x][0]
r=json.load(open(f,encoding='utf8')); n=r['info']['TeamNames']; me=[i for i,x in enumerate(n) if 'asad' in x.lower()][0]; op=1-me
s=r['steps']; lo=int(sys.argv[2]) if len(sys.argv)>2 else 0
print(n[op], r['rewards'][me]-r['rewards'][op])
c=0
for t in range(max(1,lo),720):
    a=[o for o in (s[t][me]['action'] or {}).get('market') or [] if o]; b=[o for o in (s[t][op]['action'] or {}).get('market') or [] if o]
    if json.dumps(a)!=json.dumps(b):
        ob=s[t][0]['observation']; pm=s[t-1][0]['observation']
        print(t, 'day',t//24,'h',t%24,'ME',a,'| OP',b, '| $',round(ob['farms'][me]['money']-ob['farms'][op]['money']))
        c+=1
        if c>int(sys.argv[3] if len(sys.argv)>3 else 80): break
