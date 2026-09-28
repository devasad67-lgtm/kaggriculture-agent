import json,glob,os,sys
it=sys.argv[1]
agg={'me':[0,0],'op':[0,0]}
for f in sorted(glob.glob('rnd/mine/ml/*.json'))[:int(sys.argv[2])]:
    if f.endswith('.prof.json'): continue
    r=json.load(open(f)); s=r['steps']; nm=r['info']['TeamNames']
    me=[i for i,x in enumerate(nm) if 'asad' in x.lower()][0]; op=1-me
    line={}
    for p,lab in ((me,'me'),(op,'op')):
        L=[]
        for t in range(600,719):
            sh=s[t][p]['observation']['private']['shed'].get(it,0); pr=s[t][0]['observation']['market']['prices'][it]
            for o in (s[t+1][p]['action'] or {}).get('market') or []:
                if o and o[0]=='SELL' and o[1]==it:
                    q=min(int(o[2]),sh)
                    if q>0: L.append(f"d{t//24}h{t%24}:{q}@{pr}"); agg[lab][0]+=q; agg[lab][1]+=q*pr
        line[lab]=L
    print(os.path.basename(f)[8:17],'US ',' '.join(line['me'])); print('          OPP',' '.join(line['op']))
print('totals (units, $ at quoted price) days 25-29:',agg)
