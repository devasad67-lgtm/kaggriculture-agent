import json,glob,collections
rows=[]
for f in sorted(glob.glob(''+(__import__("sys").argv[1] if len(__import__("sys").argv)>1 else "reps")+'/*.json')):
    try: r=json.load(open(f,encoding='utf8'))
    except Exception as e: continue
    names=r.get('info',{}).get('TeamNames') or []
    if len(names)<2: continue
    me=[i for i,n in enumerate(names) if 'asad' in n.lower()]
    if not me: continue
    me=me[0]; op=1-me
    rw=r.get('rewards')
    st=[s['status'] for s in r['steps'][-1]]
    rows.append((f.split('-')[1],names[op],rw[me],rw[op],st[me],st[op]))
w=sum(1 for x in rows if x[2]>x[3]); l=[x for x in rows if x[2]<x[3]]; t=len(rows)-w-len(l)
print('games',len(rows),'W',w,'L',len(l),'T',t)
for x in rows:
    if x[2]<=x[3] or x[4]!='DONE': print(x)
import statistics
print('my median reward',statistics.median(x[2] for x in rows),'opp median',statistics.median(x[3] for x in rows))
