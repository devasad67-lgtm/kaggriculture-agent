# paired A/B: base jsonl vs cand jsonl, same files. prints the stage table.
import json,sys,csv,glob,os
base={json.loads(l)['f']:json.loads(l) for l in open(sys.argv[1])}
cand={json.loads(l)['f']:json.loads(l) for l in open(sys.argv[2])}
rank={}
for fn in glob.glob('ladder/crawl/*.csv'):
    try:
        for r in csv.DictReader(open(fn,encoding='utf8')):
            if 'ep' in r and 'rank' in r and r['rank'] not in ('',None): rank[r['ep']]=int(float(r['rank']))
    except Exception: pass
cls=dict(l.split()[:2] for l in open('rnd/tfirst/cls_all.txt'))
for r in json.load(open('ladder/now/eps.json')): rank.setdefault(str(r['ep']),r['orank'])
tom=set(l.split()[0] for l in open('rnd/tfirst/tomgames.txt')) if os.path.exists('rnd/tfirst/tomgames.txt') else set()
rows=[]
for f in base:
    if f not in cand or 'new' not in base[f] or 'new' not in cand[f]: continue
    b=base[f]['new'];c=cand[f]['new'];ep=f.split('-')[1]
    rows.append((ep,b[0]-b[1],c[0]-c[1],int(rank.get(ep,-1)),ep in tom,cand[f].get('shops_same'),cls.get(ep,'?')))
def tab(name,R):
    wb=sum(r[1]>0 for r in R);wc=sum(r[2]>0 for r in R);fl=sum(r[1]<=0<r[2] for r in R);lo=sum(r[1]>0>=r[2] for r in R)
    dm=sum(r[2]-r[1] for r in R)/max(1,len(R))
    print(f"{name:14s} n={len(R):3d} W/L base {wb}-{len(R)-wb}  cand {wc}-{len(R)-wc}  flipped {fl}  lost {lo}  net {fl-lo:+d}  dmargin {dm:+.0f}")
tab('ALL',rows);tab('rank1-100',[r for r in rows if 0<r[3]<=100]);tab('rank101-700',[r for r in rows if 100<r[3]<=700])
[tab(k,[r for r in rows if r[6]==k]) for k in ('carrotswap','pure','div','NONMIRROR')]
tab('tomato',[r for r in rows if r[4]]);tab('non-tomato',[r for r in rows if not r[4]])
for r in rows:
    if (r[1]>0)!=(r[2]>0) or abs(r[2]-r[1])>300: print('  ',r)
