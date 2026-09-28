import sys,io,contextlib,json,time
sys.path.insert(0,'arena')
from tourney import resolve
a,b,seed=sys.argv[1],sys.argv[2],int(sys.argv[3])
with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
    from kaggle_environments import make
    env=make("kaggriculture",configuration={"seed":seed,"episodeSteps":720},debug=False)
    t=time.time();env.run([resolve(a),resolve(b)])
s=env.steps
sh=s[432][0].observation['town']['unlocked_shops']
print('seed',seed,'shops@d18',sh,'rewards',[x.reward for x in s[-1]],'status',[x.status for x in s[-1]],round(time.time()-t),'s')
for p in (0,1):
    fm=s[600][0].observation['farms'][p]
    print(' p',p,'quads',fm['unlocked_quadrants'],'SE rows5-9 @d25:',[' '.join(('.' if c is None else 'L' if c=='LOCKED' else (c.get('crop') or c.get('animal') or c.get('kind'))[:2]) for c in fm['tiles'][y][5:]) for y in range(5,10)])
    hires=[sum(1 for t in range(d*24+1,min(d*24+25,len(s))) for o in (s[t][p].action or {}).get('market') or [] if o and o[0]=='HIRE') for d in range(16,30)]
    print('   hires d16-29',hires)
