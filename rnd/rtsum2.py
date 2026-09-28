# replay-test summary split by which sub originally played the game
import sys,json,glob,os
src={}
for d in ('l8','l8o2','l48'):
    for f in glob.glob(f'ladder/{d}/*.json'): src[os.path.basename(f)]=d
rank=json.load(open('ladder/crawl/rank.json'))
for p in [a for a in sys.argv[1:] if not a.startswith('--')]:
    xs=[json.loads(l) for l in open(p)]; xs=[x for x in xs if 'new' in x]
    if '--valid' in sys.argv: xs=[x for x in xs if x.get('shops_same',True)]
    print(p)
    for d in ('l8','l8o2','l48','ALL','top700'):
        ys=[x for x in xs if d=='ALL' or src.get(x['f'])==d or (d=='top700' and rank.get(x['opp'],[9999])[0]<=700)]
        if not ys: continue
        ow=sum(x['orig'][0]>x['orig'][1] for x in ys); nw=sum(x['new'][0]>x['new'][1] for x in ys)
        dm=sum((x['new'][0]-x['new'][1])-(x['orig'][0]-x['orig'][1]) for x in ys)/len(ys)
        print(f"   {d:6s} n={len(ys):3d} origW={ow:3d} newW={nw:3d} ({nw-ow:+d})  margin {dm:+6.0f}/game")
