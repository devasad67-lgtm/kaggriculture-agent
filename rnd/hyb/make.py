# build a hybrid bot: L48_wf until day D, then Beast adopts the farm. python rnd/hyb/make.py D out_dir [beast_cfg_json]
import sys,os,base64,zlib,json
D=int(sys.argv[1]); out=sys.argv[2]; cfg=sys.argv[3] if len(sys.argv)>3 else '{}'
l48=open('bots/L48_wf/main.py',encoding='utf-8').read().encode()
beast=open('beast/main.py',encoding='utf-8').read().encode()
b1=base64.b64encode(zlib.compress(l48,9)).decode(); b2=base64.b64encode(zlib.compress(beast,9)).decode()
src=f'''# Hybrid: tape bot (L48_wf) until day {D}, then own planner (Beast) adopts the farm.
import base64 as _b, zlib as _z, json as _j
_T={{'__name__':'_tape'}}; exec(compile(_z.decompress(_b.b64decode({b1!r})),'tape_main.py','exec'),_T)
_B={{'__name__':'_beast'}}; exec(compile(_z.decompress(_b.b64decode({b2!r})),'beast_main.py','exec'),_B)
_TAPE=[v for k,v in _T.items() if k=='agent'][0]
_D={D}
_S={{}}
def agent(observation, configuration=None):
    step=int(observation['step']); p=int(observation['player'])
    if step < _D*24:
        return _TAPE(observation, configuration)
    b=_S.get(p)
    if b is None:
        b=_S[p]=_B['Beast'](_j.loads({cfg!r}))
        b.adopt(observation['farms'][p]['tiles'])
        b.last_step=step-1
    try:
        return b.act(observation)
    except Exception:
        return {{'farmer':['PASS'],'hands':[],'market':[]}}
'''
os.makedirs(out,exist_ok=True); open(os.path.join(out,'main.py'),'w',encoding='utf-8').write(src); print('built',out)
