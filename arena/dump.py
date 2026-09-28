import sys,io,contextlib,json
sys.path.insert(0,'.'); from tourney import resolve
a,b,seed,out=sys.argv[1],sys.argv[2],int(sys.argv[3]),sys.argv[4]
with contextlib.redirect_stdout(io.StringIO()):
    from kaggle_environments import make
    env=make("kaggriculture",configuration={"seed":seed,"episodeSteps":720},debug=False)
    env.run([resolve(a),resolve(b)])
json.dump(env.toJSON(),open(out,'w'))
print(a,b,seed,env.steps[-1][0].reward,env.steps[-1][1].reward)
