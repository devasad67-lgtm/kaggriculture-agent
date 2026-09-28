
# ---- TFD: tomato-first delivery for the V219 SE tomato crew (wool-first analogue) ----------
# Mirror rivals sell the same tomato lots on the same step; each lot moves the price 5-25%.
# Harvest every ripe tomato before watering, deliver, then water: our lots reach the market first.
TOMATO_FIRST = True
_TFD_ORIG_WORKER = _v219_worker
def _v219_worker(obs, state, actor, role):
    if not TOMATO_FIRST or role['kind'] == 'fertilizer' or role.get('needs_fertilizer') and not role.get('loaded'):
        return _TFD_ORIG_WORKER(obs, state, actor, role)
    day=int(obs['step'])//24;step=int(obs['step']);view=FarmView(obs)
    if day <= 18:
        return _TFD_ORIG_WORKER(obs, state, actor, role)
    pos=tuple(view.positions[actor]);inv=view.inventory(actor)
    ripe=[t for t in role['targets'] if isinstance(view.tiles[t[1]][t[0]],dict)
          and view.tiles[t[1]][t[0]].get('crop')=='TOMATO' and view.tiles[t[1]][t[0]].get('yield_units',0)>0]
    if ripe:
        target=min(ripe,key=lambda v:(abs(pos[0]-v[0])+abs(pos[1]-v[1]),role['targets'].index(v)))
        previous=state['last_work'].get(actor)
        if previous and previous['step']==step-1 and previous['command']==['HARVEST']:
            _V219_REPORT['confirmed_harvest_units']+=max(0,int(inv.get('TOMATO',0))-previous['tomatoes'])
        return _v219_walk(pos,target) or ['HARVEST']
    if inv.get('TOMATO',0):
        home=_v219_home(pos)
        return _v219_walk(pos,home) or ['PLACE','TOMATO',int(inv['TOMATO'])]
    return _TFD_ORIG_WORKER(obs, state, actor, role)
