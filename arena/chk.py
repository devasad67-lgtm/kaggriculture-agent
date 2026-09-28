import sys,io,contextlib
sys.path.insert(0,'.'); from tourney import resolve
b=sys.argv[1]
with contextlib.redirect_stdout(io.StringIO()):
    from kaggle_environments import make
    env=make("kaggriculture",configuration={"seed":3,"episodeSteps":720},debug=False)
    env.run([resolve(b),resolve('dp_L720a')])
import importlib
print(b, env.steps[-1][0].reward, env.steps[-1][1].reward, env.steps[-1][0].status)
