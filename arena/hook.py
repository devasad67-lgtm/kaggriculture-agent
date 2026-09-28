import sys,io,contextlib,importlib.util
for b in sys.argv[1:]:
    spec=importlib.util.spec_from_file_location('m_'+b.replace('-','_'),f'D:/kaggle/bots/{b}/main.py'); m=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()): spec.loader.exec_module(m)
    with contextlib.redirect_stdout(io.StringIO()):
        from kaggle_environments import make
        env=make("kaggriculture",configuration={"seed":3,"episodeSteps":300},debug=False)
        env.run([m.agent,'random'])
    print(b,'chassis:',m._chassis() is not None,'edge errors:',m._EDGE.errors)
