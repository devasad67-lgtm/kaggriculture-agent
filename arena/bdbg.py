import sys,io,contextlib,json,collections,shutil
sys.path.insert(0,'.'); from tourney import resolve
shutil.copy('D:/kaggle/beast/main.py','D:/kaggle/bots/beast/main.py')
with contextlib.redirect_stdout(io.StringIO()):
    from kaggle_environments import make
    env=make("kaggriculture",configuration={"seed":2000,"episodeSteps":int(sys.argv[1])},debug=True)
    env.run([resolve('beast'),resolve('dp_L720a')])
s=env.steps
for t in [int(x) for x in sys.argv[2:]]:
    ob=s[t][0].observation; f=ob['farms'][0]
    print('step',t,'day',t//24,'h',t%24,'$',f['money'],'hands',f['hands'],'farmer',f['farmer'])
    for y,row in enumerate(f['tiles']):
        for x,tl in enumerate(row):
            if isinstance(tl,dict) and 'animal' in tl: print(' ',(x,y),{k:tl[k] for k in ('fed_today','cared_today','yield_units','consecutive_unfed','fertilizer_available')})
    print(' inv',ob['private']['inventories'],'shed',{k:v for k,v in ob['private']['shed'].items() if v})
    print(' my action',s[t+1][0].action if t+1<len(s) else None)
