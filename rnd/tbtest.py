# run a bot in DSM's seat vs DSM-game opponent's recorded actions on that game's seed
import sys,json,io,contextlib
sys.path.insert(0,'rnd'); import replaytest as R
bot=sys.argv[1]
for f in sys.argv[2:]:
    r=json.load(open(f,encoding='utf8')); s=r['steps']; n=r['info']['TeamNames']; me=n.index('DSM'); op=1-me
    fn=R.load(bot)
    def rec(obs,conf=None):
        t=obs.get('step',0); a=s[t+1][op]['action'] if t+1<len(s) else None
        return a or {'farmer':['PASS'],'hands':[],'market':[]}
    cfg=dict(r['configuration']); cfg['seed']=r['info']['seed']
    with contextlib.redirect_stdout(io.StringIO()):
        env=R.make('kaggriculture',configuration=cfg); ag=[None,None]; ag[me]=fn; ag[op]=rec; env.run(ag)
    fin=[x['reward'] for x in env.steps[-1]]
    so=s[-1][0]['observation']['town']['unlocked_shops']; sn=env.steps[-1][0]['observation']['town']['unlocked_shops']
    print(f.split('-')[-2], n[op][:14], 'orig', r['rewards'][me], r['rewards'][op], 'new', fin[me], fin[op], 'shops_same', so==sn, flush=True)
