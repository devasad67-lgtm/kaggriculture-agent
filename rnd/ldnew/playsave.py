# play A vs B on a seed and save a replay-like json: python playsave.py A B seed out.json
import sys,json,io,contextlib,os
sys.path.insert(0,'arena'); from tourney import resolve
a,b,seed,out=sys.argv[1],sys.argv[2],int(sys.argv[3]),sys.argv[4]
os.chdir('arena')
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    from kaggle_environments import make
    env=make('kaggriculture',configuration={'seed':seed,'episodeSteps':720})
    env.run([resolve(a),resolve(b)])
os.chdir('..')
st=[[dict(action=x['action'],observation=x['observation'],reward=x['reward']) for x in step] for step in env.steps]
json.dump(dict(steps=st,info=dict(TeamNames=['asad_'+a,b],seed=seed),rewards=[x['reward'] for x in env.steps[-1]],configuration={'seed':seed}),open(out,'w'),default=str)
print(seed,[x['reward'] for x in env.steps[-1]])
