import sys,io,contextlib,shutil
sys.path.insert(0,'.'); from tourney import resolve
shutil.copy('D:/kaggle/beast/main.py','D:/kaggle/bots/beast/main.py')
with contextlib.redirect_stdout(io.StringIO()):
    from kaggle_environments import make
    env=make("kaggriculture",configuration={"seed":2000,"episodeSteps":720},debug=True)
    env.run([resolve('beast'),resolve('passbot')])
s=env.steps
d=int(sys.argv[1])
for t in range(d*24, d*24+24):
    ob=s[t][0].observation; f=ob['farms'][0]; a=s[t+1][0].action
    coops=sum(1 for row in f['tiles'] for x in row if isinstance(x,dict) and x.get('kind')=='COOP' and 'animal' not in x)
    geese=sum(1 for row in f['tiles'] for x in row if isinstance(x,dict) and x.get('animal')=='GOOSE')
    unfed=[(x.get('consecutive_unfed'),x.get('fed_today')) for row in f['tiles'] for x in row if isinstance(x,dict) and 'animal' in x and not x.get('fed_today')]
    print(t%24,'$',int(f['money']),'coops',coops,'geese',geese,'shedG',ob['private']['shed'].get('GOOSE'),'shedW',ob['private']['shed'].get('WHEAT'),'invG',[i.get('GOOSE',0) for i in ob['private']['inventories']],'invW',[i.get('WHEAT',0) for i in ob['private']['inventories']],'unfed',len(unfed),'mkt',[o for o in a['market'] if o[0]!='HIRE'])
