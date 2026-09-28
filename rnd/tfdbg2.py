import sys,io,contextlib,importlib.util
def load(path,name):
    sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
seed=int(sys.argv[2])
with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
    from kaggle_environments import make
    A=load(f'bots/{sys.argv[1]}/main.py','A');B=load('bots/L48_wf/main.py','B')
    NS=A._INNER_NS
    log=[]
    orig=NS['_tf_request']
    def spy(obs,action,st,v219):
        d=int(obs['step'])//24
        if d>=18 and v219.get('pending'): log.append((obs['step'],v219['pending'].get('step'),len(action['market']),obs['farms'][obs['player']]['money'],[o[0] for o in action['market']]))
        return orig(obs,action,st,v219)
    NS['_tf_request']=spy
    env=make("kaggriculture",configuration={"seed":seed,"episodeSteps":720},debug=False)
    env.run([A.agent,B.agent])
print([x.reward for x in env.steps[-1]]);print(NS['_TF_REPORT']);print('v219',{k:v for k,v in NS['_V219_REPORT'].items() if v})
for l in log[:12]: print(l)
