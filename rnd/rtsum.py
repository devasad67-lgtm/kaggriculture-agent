import sys,json
for p in sys.argv[1:]:
    xs=[json.loads(l) for l in open(p)]; ok=[x for x in xs if 'new' in x]
    ow=sum(x['orig'][0]>x['orig'][1] for x in ok); nw=sum(x['new'][0]>x['new'][1] for x in ok)
    dm=sum((x['new'][0]-x['new'][1])-(x['orig'][0]-x['orig'][1]) for x in ok)/max(1,len(ok))
    same=sum(x['new']==x['orig'] for x in ok)
    print(f"{p}: n={len(ok)} err={len(xs)-len(ok)} origW={ow} newW={nw} margin_delta={dm:+.0f}/game identical={same}")
