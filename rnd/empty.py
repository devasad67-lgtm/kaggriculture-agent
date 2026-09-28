import json,glob,sys
for pat in sys.argv[1:]:
    tot=bad=0
    for f in sorted(glob.glob(pat)):
        r=json.load(open(f,encoding='utf8')); n=r['info']['TeamNames']; s=r['steps']
        for p in (0,1):
            if 'asad' not in n[p].lower(): continue
            tl=s[15*24+12][0]['observation']['farms'][p]['tiles']
            e=sum(1 for row in tl for x in row if isinstance(x,dict) and x['kind'] in('PASTURE','COOP') and not x.get('animal'))
            tot+=1
            if e>=2: bad+=1; print(' ',f,n[1-p],'empty',e,r['rewards'][p],r['rewards'][1-p])
    print(pat,'games',tot,'with >=2 empty structures on d15:',bad)
