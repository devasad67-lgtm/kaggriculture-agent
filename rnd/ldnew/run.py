import json,sys,glob,os
sys.path.insert(0,'rnd')
from prof import prof
ids=json.load(open('ladder/crawl/cur_eps.json'))
for sid,dn in (('56557869','l48mc'),('56555308','l8omc')):
    for r in ids[sid]:
        if (r['me'] or 0)>=(r['op'] or 0): continue
        f=f'ladder/{dn}/episode-{r["ep"]}-replay.json'
        if not os.path.exists(f): continue
        rr=json.load(open(f,encoding='utf8')); n=rr['info']['TeamNames']
        me=[i for i,x in enumerate(n) if 'asad' in x.lower()][0]
        json.dump(dict(f=os.path.basename(f),me=me,prof=prof(f)),open(f'rnd/ldnew/{dn}_{r["ep"]}.prof.json','w'))
