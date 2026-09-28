# per route: day 20-23 wheat plantings (step, unit) whose tile is harvested at age<=3 -> safe to plant carrot
import sys,os,json,io,contextlib,multiprocessing as mp
def job(a):
    r,seed=a
    os.environ['FROUTE']=str(r); os.chdir('D:/kaggle/arena'); sys.path.insert(0,'D:/kaggle/arena')
    from tourney import resolve
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        from kaggle_environments import make
        env=make('kaggriculture',configuration={'seed':seed,'episodeSteps':720}); env.run([resolve('L48_wf_fr'),resolve('L48_wf')])
    st=env.steps; p=0; plants={}; out=[]
    for t in range(20*24,27*24):
        F=st[t][p].observation['farms'][p]; units=[F['farmer']]+list(F['hands'] or [])
        a=st[t+1][p].action or {}
        cm=[a.get('farmer')]+list(a.get('hands') or [])
        for u,c in enumerate(cm):
            if not c or u>=len(units): continue
            xy=tuple(units[u]); tl=F['tiles'][xy[1]][xy[0]]
            if c[0]=='PLANT' and len(c)>1 and c[1]=='WHEAT' and tl is None and t<24*24: plants[xy]=(t,u)
            elif c[0] in('HARVEST','DIG') and xy in plants and isinstance(tl,dict) and tl.get('crop')=='WHEAT':
                t0,u0=plants.pop(xy); age=(t//24)-(t0//24)
                out.append(dict(route=r,seed=seed,plant_step=t0,unit=u0,tile=xy,harvest_step=t,age=age,op=c[0],y=tl.get('yield_units')))
    return out
if __name__=='__main__':
    seeds=json.load(open('D:/kaggle/arena/ladder_seeds.json'))
    routes=list(range(0,13))+list(range(100,129))
    jobs=[(r,seeds[40]) for r in routes]+[(r,seeds[41]) for r in routes]
    with mp.Pool(4,maxtasksperchild=1) as pool, open('D:/kaggle/rnd/mine/ctable.jsonl','w') as f:
        for rows in pool.imap_unordered(job,jobs):
            for x in rows: f.write(json.dumps(x)+'\n')
            f.flush()
