import sys,io,contextlib,json,multiprocessing as mp
sys.path.insert(0,'arena')
from tourney import resolve
def run(seed):
    import os
    dn=os.open(os.devnull,os.O_WRONLY);os.dup2(dn,1);os.dup2(dn,2)
    from kaggle_environments import make
    env=make("kaggriculture",configuration={"seed":seed,"episodeSteps":720},debug=False)
    env.run([resolve('L48_wf'),resolve('L48_wf')])
    s=env.steps;o=s[432][0].observation
    sh=o['town']['unlocked_shops'];n=sum(x in('PIZZA_SHOP','FARMERS_MARKET') for x in sh)
    return seed,n,o['market']['prices']['TOMATO'],o['market']['inventory']['TOMATO'],s[624][0].observation['market']['prices']['TOMATO']
if __name__=='__main__':
    seeds=json.load(open('arena/seeds_tom3.json'))
    g=json.load(open('arena/g_tf2.json'))['L48_tf|L48_wf'];m={s:a-b for a,b,s in g}
    with mp.Pool(4,maxtasksperchild=1) as p:
        for seed,n,pr,inv,p26 in sorted(p.map(run,seeds),key=lambda r:m[r[0]]):
            print(seed,'shops',n,'tomato price d18',pr,'inv',inv,'price d26',p26,'margin',round(m[seed]))
