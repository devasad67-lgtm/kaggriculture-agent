# fingerprint: similarity of opponent farm to ours at day D (tile kind/crop/animal), from observation only
import json,glob,csv,sys
rank={}
for row in csv.DictReader(open('ladder/crawl/live_now.csv',encoding='utf8')): rank[row['ep']]=int(row['rank'])
def sig(t):
    if t is None: return '.'
    if t=='LOCKED': return 'L'
    if isinstance(t,dict): return (t.get('kind','')[:2])+(t.get('crop') or t.get('animal') or '')[:2]
    return '?'
def sim(o,me,op):
    a=o['farms'][me]['tiles'];b=o['farms'][op]['tiles']
    n=len(a);same=sum(sig(a[y][x])==sig(b[y][x]) for y in range(n) for x in range(n) if sig(a[y][x])!='L' or sig(b[y][x])!='L')
    tot=sum(1 for y in range(n) for x in range(n) if sig(a[y][x])!='L' or sig(b[y][x])!='L')
    return same/max(tot,1), len(o['farms'][op]['hands']), len(o['farms'][me]['hands'])
out=[]
for f in sorted(glob.glob(sys.argv[1]+'/*.json')):
    r=json.load(open(f,encoding='utf8'));s=r['steps'];n=r['info']['TeamNames']
    me=[i for i,x in enumerate(n) if 'asad' in x.lower()][0];op=1-me
    ep=f.split('-')[1];m=r['rewards'][me]-r['rewards'][op]
    row=[ep,n[op][:18],rank.get(ep,-1),int(m)]
    for d in (1,2,3,6):
        o=s[d*24][0]['observation'];x=sim(o,me,op);row.append(f'{x[0]:.2f}/{x[1]}v{x[2]}')
    out.append(row);print(*row,flush=True)
