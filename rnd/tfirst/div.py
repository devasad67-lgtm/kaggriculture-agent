# first step where opponent's farm differs from ours (mirror games only): what differs
import json,glob,sys,csv
rank={r['ep']:int(r['rank']) for r in csv.DictReader(open('ladder/crawl/live_now.csv',encoding='utf8'))}
def sig(t):
    if t is None: return '.'
    if t=='LOCKED': return 'L'
    return (t.get('kind','')[:2])+(t.get('crop') or t.get('animal') or '')[:2]
for f in sorted(glob.glob(sys.argv[1]+'/*.json')):
    r=json.load(open(f,encoding='utf8'));s=r['steps'];N=r['info']['TeamNames']
    me=[i for i,x in enumerate(N) if 'asad' in x.lower()][0];op=1-me
    ep=f.split('-')[1];m=int(r['rewards'][me]-r['rewards'][op])
    o=s[24][0]['observation'];a=o['farms'][me]['tiles'];b=o['farms'][op]['tiles']
    if sum(sig(a[y][x])!=sig(b[y][x]) for y in range(len(a)) for x in range(len(a)))>1: continue
    first=None;cnt={}
    for t in range(1,len(s)):
        o=s[t][0]['observation'];a=o['farms'][me]['tiles'];b=o['farms'][op]['tiles']
        d=[(x,y,sig(a[y][x]),sig(b[y][x])) for y in range(len(a)) for x in range(len(a)) if sig(a[y][x])!=sig(b[y][x])]
        if len(d)>=2 and first is None: first=(t,d[:3])
    print(ep,N[op][:14],rank.get(ep,-1),m,'W' if m>0 else 'L','firstdiv',first[0] if first else None,'d%.1f'%(first[0]/24) if first else '',first[1] if first else '',flush=True)
