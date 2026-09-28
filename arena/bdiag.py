import sys,io,contextlib,importlib.util,os
os.environ['BEAST_DEBUG']='1'
spec=importlib.util.spec_from_file_location('bm','D:/kaggle/beast/main.py'); bm=importlib.util.module_from_spec(spec); spec.loader.exec_module(bm)
sys.path.insert(0,'.'); from tourney import resolve
with contextlib.redirect_stdout(io.StringIO()):
    from kaggle_environments import make
    env=make("kaggriculture",configuration={"seed":2000,"episodeSteps":720},debug=True)
    env.run([bm.agent,resolve(sys.argv[1] if len(sys.argv)>1 else 'passbot')])
print('reward',env.steps[-1][0].reward)
for d,v in sorted(bm.DEBUG.items()): print(d,v)
