import sys,io,contextlib,importlib.util,json
sys.path.insert(0,'D:/kaggle/ladder/yz')
with contextlib.redirect_stdout(io.StringIO()): import ledger
def load(path,name):
    sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
seed=int(sys.argv[2])
with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
    from kaggle_environments import make
    A=load(f'bots/{sys.argv[1]}/main.py','A');B=load('bots/L48_wf/main.py','B')
    env=make("kaggriculture",configuration={"seed":seed,"episodeSteps":720},debug=False)
    env.run([A.agent,B.agent])
r=json.loads(json.dumps(env.toJSON()))
a=ledger.ledger(r,0);b=ledger.ledger(r,1)
print('rewards',r['rewards'],A._INNER_NS['_TF_REPORT'])
for k in sorted(set(a[0])|set(b[0])): 
    if abs(a[0][k]-b[0][k])>50: print('  rev',k,round(a[0][k]),round(b[0][k]),round(a[0][k]-b[0][k]))
for k in sorted(set(a[1])|set(b[1])):
    if abs(a[1][k]-b[1][k])>50: print('  cost',k,round(a[1][k]),round(b[1][k]),round(a[1][k]-b[1][k]))
s=r['steps'];print('shops end',s[-1][0]['observation']['town']['unlocked_shops'])
print('tomato units ours',round(a[2]['TOMATO']),'theirs',round(b[2]['TOMATO']))
fm=lambda t:s[t][0]['observation']['farms'][0]
for t in (455,480,600,648,672,696,710,719):
    row=[]
    for y in (7,8,9):
        for x in range(5,10):
            c=fm(t)['tiles'][y][x]
            row.append('.' if c is None else (c.get('kind')[:2] if c.get('kind')!='PLANT' else 'T%d%s'%(c.get('yield_units',0),'w' if c.get('watered_today') else '')))
    print(t,' '.join(row))
