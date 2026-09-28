import sys,io,contextlib,importlib.util,os
os.environ['BEAST_DEBUG']='1'
spec=importlib.util.spec_from_file_location('hy','D:/kaggle/bots/hybrid10/main.py'); hy=importlib.util.module_from_spec(spec); spec.loader.exec_module(hy)
sys.path.insert(0,'.'); from tourney import resolve
with contextlib.redirect_stdout(io.StringIO()):
    from kaggle_environments import make
    env=make("kaggriculture",configuration={"seed":2000,"episodeSteps":720},debug=True)
    env.run([hy.agent,resolve('dp_L720a')])
print('reward',env.steps[-1][0].reward)
for d,v in sorted(hy._beast.DEBUG.items(), key=lambda kv: str(kv[0]).zfill(3)): print(d,v)
