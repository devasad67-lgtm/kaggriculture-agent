"""python btest.py <bot> <opp> <seed>  -> run a game, print our farm per day"""
import sys,io,contextlib,json,collections,shutil
sys.path.insert(0,'.'); from tourney import resolve
a,b,seed=sys.argv[1],sys.argv[2],int(sys.argv[3])
if a=='beast': shutil.copy('D:/kaggle/beast/main.py','D:/kaggle/bots/beast/main.py')
err=io.StringIO()
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
    from kaggle_environments import make
    env=make("kaggriculture",configuration={"seed":seed,"episodeSteps":720},debug=True)
    env.run([resolve(a),resolve(b)])
s=env.steps
print('rewards',s[-1][0].reward,s[-1][1].reward,s[-1][0].status)
e=err.getvalue()
if 'Traceback' in e: print(e[-1500:])
for d in list(range(0,30,2))+[29]:
    t=min(d*24+12,719); ob=s[t][0].observation; f=ob['farms'][0]
    c=collections.Counter()
    for row in f['tiles']:
        for x in row:
            if x is None: c['empty']+=1
            elif x=='LOCKED': pass
            elif 'animal' in x: c[x['animal'][:2]]+=1
            elif x.get('kind')=='PLANT': c[x['crop'][:4]]+=1
            else: c[x['kind'][:4]]+=1
    print('d%2d $%6d opp$%6d h%2d q%d'%(d,f['money'],ob['farms'][1]['money'],len(f['hands']),len(f['unlocked_quadrants'])),dict(c),{k[:4]:v for k,v in ob['private']['shed'].items() if v})
