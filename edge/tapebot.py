"""Build a tape bot from ladder replays: python tapebot.py <outname> <team> <replay.json> [<replay.json>...]
Route k = team's action stream from replay k (tape[s] = action submitted on observation step s).
Router: route 0 unless a shop-matched route exists (first two shops at step 144)."""
import json,sys,os,base64,zlib
out,team,files=sys.argv[1],sys.argv[2],sys.argv[3:]
routes={};shops={}
for k,f in enumerate(files):
    r=json.load(open(f,encoding='utf8')); n=r['info']['TeamNames']; p=n.index(team)
    tape=[]
    for t in range(1,720):
        a=r['steps'][t][p]['action'] or {}
        tape.append({'farmer':a.get('farmer',['PASS']),'hands':a.get('hands',[]),'market':[o for o in (a.get('market') or []) if o]})
    tape.append({'farmer':['PASS'],'hands':[],'market':[]})
    routes[k]=tape
    sh=tuple(r['steps'][150][0]['observation']['town']['unlocked_shops'][:2]); shops.setdefault(str(list(sh)),k)
src=open('D:/kaggle/bots/demand-preserving-turn-sale-timing/main.py',encoding='utf8').read()
blob=base64.b85encode(zlib.compress(json.dumps({'routes':routes,'shops':shops}).encode(),9)).decode()
src+=f'''
# ---- tape bot built from ladder replays of {team} ----
_TB=json.loads(zlib.decompress(base64.b85decode({blob!r})))
_TB_ROUTES={{int(k):v for k,v in _TB['routes'].items()}}
_TB_SHOPS=_TB['shops']
_TB_FIXED={os.environ.get('TB_FIXED','None')}
def _tb_router(observation,step,state):
    if _TB_FIXED is not None: return _TB_FIXED
    return state.get('route',0)
_TB_IMPL=make_agent(_TB_ROUTES,router=_tb_router,**_SETTINGS)
def agent(observation,configuration=None):
    try:
        return _TB_IMPL(observation,configuration)
    except Exception:
        return {{'farmer':['PASS'],'hands':[],'market':[]}}
'''
d=f'D:/kaggle/bots/{out}'; os.makedirs(d,exist_ok=True); open(d+'/main.py','w',encoding='utf8').write(src)
print('routes',len(routes),'shops',shops)
