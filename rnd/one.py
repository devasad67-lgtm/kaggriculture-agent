import sys,json,io,contextlib,os
sys.path.insert(0,'D:/kaggle/arena'); sys.path.insert(0,'D:/kaggle/rnd')
from tourney import resolve
a,b,seed,out=sys.argv[1],sys.argv[2],int(sys.argv[3]),sys.argv[4]
with contextlib.redirect_stdout(io.StringIO()):
    from kaggle_environments import make
    env=make("kaggriculture",configuration={"seed":seed,"episodeSteps":720},debug=True)
    env.run([resolve(a),resolve(b)])
r=env.toJSON(); r['info']=dict(r.get('info') or {}); r['info']['TeamNames']=[a,b]
json.dump(r,open(out,'w'))
print(a,b,[s.reward for s in env.steps[-1]])
