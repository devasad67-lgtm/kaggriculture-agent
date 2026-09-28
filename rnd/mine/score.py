import json,sys
wf={json.loads(l)['f']:json.loads(l) for l in open('rnd/rt/wf_all.jsonl')}
for fn in sys.argv[1:]:
    try: xs=[json.loads(l) for l in open(fn)]
    except FileNotFoundError: continue
    err=sum('err' in x for x in xs); xs=[x for x in xs if 'new' in x]
    if not xs: print(fn,'no rows'); continue
    bw=sum(wf[x['f']]['new'][0]>wf[x['f']]['new'][1] for x in xs); cw=sum(x['new'][0]>x['new'][1] for x in xs)
    gained=sum(wf[x['f']]['new'][0]<=wf[x['f']]['new'][1] and x['new'][0]>x['new'][1] for x in xs)
    lost=sum(wf[x['f']]['new'][0]>wf[x['f']]['new'][1] and x['new'][0]<=x['new'][1] for x in xs)
    bm=sum(wf[x['f']]['new'][0]-wf[x['f']]['new'][1] for x in xs)/len(xs); cm=sum(x['new'][0]-x['new'][1] for x in xs)/len(xs)
    same=sum(x.get('shops_same',True) for x in xs)
    print(f"{fn:22s} n={len(xs):3d} err={err} | baseline W {bw:3d} L {len(xs)-bw:3d} | candidate W {cw:3d} L {len(xs)-cw:3d} | flips +{gained} -{lost} | margin {bm:+6.0f} -> {cm:+6.0f} | shops_same {same}")
