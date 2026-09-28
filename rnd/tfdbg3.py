import sys,io,contextlib,importlib.util,collections
def load(path,name):
    sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
seed=int(sys.argv[2])
with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
    from kaggle_environments import make
    A=load(f'bots/{sys.argv[1]}/main.py','A');B=load('bots/L48_wf/main.py','B')
    NS=A._INNER_NS;log=collections.defaultdict(list)
    ow=NS['_tf_worker']
    def spy(obs,st,actor,v219):
        c=ow(obs,st,actor,v219);log[int(obs['step'])//24].append((int(obs['step'])%24,c[0]));return c
    NS['_tf_worker']=spy
    env=make("kaggriculture",configuration={"seed":seed,"episodeSteps":720},debug=False)
    env.run([A.agent,B.agent])
for d in sorted(log):
    c=collections.Counter(x[1] for x in log[d]);print(d,'first hour',log[d][0][0],dict(c))
