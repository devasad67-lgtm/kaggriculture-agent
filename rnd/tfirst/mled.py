import sys,json;sys.path.insert(0,'ladder/yz');import ledger
for ep in sys.argv[1:]:
    f=f'ladder/wflive/episode-{ep}-replay.json';r=json.load(open(f,encoding='utf8'));N=r['info']['TeamNames']
    p=[i for i,x in enumerate(N) if 'asad' in x.lower()][0]
    a=ledger.ledger(r,p);b=ledger.ledger(r,1-p)
    d={k:round(a[0][k]-b[0][k]) for k in set(a[0])|set(b[0]) if abs(a[0][k]-b[0][k])>=20}
    c={k:round(a[1][k]-b[1][k]) for k in set(a[1])|set(b[1]) if abs(a[1][k]-b[1][k])>=20}
    print(ep,N[1-p][:14],'margin',r['rewards'][p]-r['rewards'][1-p],'REV',d,'COST',c,flush=True)
