import json,glob,os,sys
d=sys.argv[1]; wf={json.loads(l)['f']:json.loads(l) for l in open('rnd/rt/wf_all.jsonl')}
for f in sorted(glob.glob(d+'/*.json')):
    if f.endswith('.prof.json'): continue
    r=json.load(open(f)); s=r['steps']; n=r['info']['TeamNames']
    me=[i for i,x in enumerate(n) if 'asad' in x.lower()][0]; op=1-me
    b=wf[os.path.basename(f)]['new']
    print(os.path.basename(f)[8:17],'swap money',r['rewards'][me],r['rewards'][op],'| wf baseline',b, '| delta me',round(r['rewards'][me]-b[0]),'margin',round((r['rewards'][me]-r['rewards'][op])-(b[0]-b[1])))
    for (x,y) in ((4,0),(3,2)):
        row=[]
        for dd in (1,6,9,10,11,12,13,14,15,16,17,18,20):
            t=s[dd*24+12][0]['observation']['farms'][me]['tiles'][y][x]
            row.append(f"d{dd}:{(t.get('crop') or t.get('kind'))[:5]+'/'+str(t.get('yield_units','')) if isinstance(t,dict) else t}")
        print('   ',(x,y),' '.join(row))
