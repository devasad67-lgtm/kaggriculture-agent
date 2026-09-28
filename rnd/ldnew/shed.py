import json,sys,glob
ep,it,a,b=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4])
f=glob.glob(f'ladder/*/episode-{ep}-replay.json')[0]
r=json.load(open(f,encoding='utf8')); s=r['steps']; n=r['info']['TeamNames']
me=[i for i,x in enumerate(n) if 'asad' in x.lower()][0]; op=1-me
for t in range(a,b):
    row=[]
    for p in (me,op):
        o=s[t][p]['observation']; sh=o['private']['shed'].get(it,0)
        car=sum(dict(v or {}).get(it,0) for v in o['private'].get('inventories',[]) or [])
        row.append(f"shed{sh:3d} carried{car:3d}")
    print(f"t{t} d{t//24}h{t%24}  ME {row[0]}  | OP {row[1]}  price {s[t][0]['observation']['market']['prices'][it]}")
