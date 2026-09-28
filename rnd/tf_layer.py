

# ---- TF: tomato fill (L48_wf + surgical layer) --------------------------------------
# On boards where the V219 SE tomato project commits (>=3 PIZZA/FARMERS by day 18), SE rows
# 7..(7+TF_ROWS-1), x=5..9 stay empty for the rest of the game (verified on 40 ladder games).
# Plant extra tomatoes there and tend them with ONE extra hand hired after every other hire of
# the day (tape + V219). Nothing native is replaced; tomatoes are sold with V219's tomato sales.
TF_ROWS = 2
TF_ON = True
TF_MIN_PRICE = 90  # commit only when shops have already drained tomatoes (day-18 price)
_TF_PARENT = agent
_TF_STATES = {}
_TF_REPORT = dict(tf_commits=0, tf_hire_requests=0, tf_workers=0, tf_hire_shortfalls=0, tf_plants=0,
                  tf_budget_declines=0, tf_errors=0)


def _tf_targets():
    out = []
    for i, y in enumerate(range(7, 7 + TF_ROWS)):
        xs = range(5, 10) if i % 2 == 0 else range(9, 4, -1)
        out += [(x, y) for x in xs]
    return out


def _tf_request(obs, action, st, v219):
    step = int(obs['step']); day = step // 24
    farm = obs['farms'][obs['player']]
    if st.get('requested_day') == day or day < 18 or day > 29:
        return action
    pend = v219.get('pending')
    hour = step % 24
    if pend and pend.get('step') == step:
        # piggy-back on the step where V219 requested its crew: our HIRE goes after its HIREs
        actor = pend['first_actor'] + pend['count']
    else:
        # own request on days V219 does not hire (or after it already did): only once every
        # native/V219/R51 hire of the day is done, so no other layer's actor indices move
        if not st.get('committed') or pend:
            return action
        if not (v219.get('requested_day') == day or hour >= 7) or hour > 12:
            return action
        planned = _v219_native_day(_IMPL.chassis.players[int(obs['player'])], day)
        if any(o and o[0] == 'HIRE' for a in planned[hour + 1:] for o in a.get('market', [])):
            return action
        if any(o and o[0] == 'HIRE' for o in action['market']):
            return action
        if (_R51_INPUT_STATES.get(int(obs['player'])) or {}).get('pending'):
            return action
        actor = len(farm['hands']) + 1
    if not st.get('committed'):
        if day != 18:
            return action
        if int(obs['market']['prices'].get('TOMATO', 0)) < TF_MIN_PRICE:
            return action
        buying_se = any(o and o[0] == 'BUY_LAND' for o in action['market']) and 'SE' not in farm['unlocked_quadrants']
        if any(not (farm['tiles'][y][x] is None or (buying_se and farm['tiles'][y][x] == 'LOCKED')) for x, y in _tf_targets()):
            return action
    n = len(_tf_targets())
    extra = [['HIRE']]
    if not st.get('committed'):
        extra = [['BUY_SEED', 'TOMATO', n]] + extra
    if len(action['market']) + len(extra) > MAX_ORDERS:
        return action
    hires_before = farm['hires_today'] + sum(bool(o) and o[0] == 'HIRE' for o in action['market'])
    budget = sum(_v219_fib(k) for k in range(farm['hires_today'], hires_before + 1))
    if not st.get('committed'):
        budget += 50 * n
    for o in action['market']:
        if not o:
            continue
        if o[0] == 'BUY_PRODUCT':
            budget += int(o[2]) * (int(obs['market']['prices'][o[1]]) + 10)
        elif o[0] == 'BUY_ANIMAL':
            budget += int(o[2]) * {'COW': 400, 'SHEEP': 500, 'GOOSE': 300}[o[1]]
        elif o[0] == 'BUY_SEED':
            budget += int(o[2]) * {'WHEAT': 10, 'CARROT': 20, 'TOMATO': 50, 'STRAWBERRY': 100, 'MELON': 80}[o[1]]
        elif o[0] == 'BUY_LAND':
            budget += 4000
    if farm['money'] < budget + 3000:
        _TF_REPORT['tf_budget_declines'] += 1
        return action
    st['requested_day'] = day
    st['pending'] = {'step': step, 'actor': actor}
    if not st.get('committed'):
        st['committed'] = True
        _TF_REPORT['tf_commits'] += 1
    _TF_REPORT['tf_hire_requests'] += 1
    out = copy.deepcopy(action)
    out['market'] = list(out['market']) + extra
    return out


def _tf_worker(obs, st, actor, v219):
    """Crop worker for the fill tiles: plants on days 18-19 without starving V219 of seeds."""
    step = int(obs['step']); day = step // 24
    farm = obs['farms'][obs['player']]; private = obs['private']
    pos = tuple(farm['hands'][actor - 1]); inv = private['inventories'][actor]
    home = _v219_home(pos); dist = abs(pos[0] - home[0]) + abs(pos[1] - home[1])
    if step >= 718 - dist and inv.get('TOMATO', 0):
        return _v219_walk(pos, home) or ['PLACE', 'TOMATO', int(inv['TOMATO'])]
    v_need = 0
    if day == 18:
        v_need = sum(1 for (x, y) in v219.get('targets', []) if farm['tiles'][y][x] is None)
    targets = _tf_targets()
    todo = []
    for t in targets:
        x, y = t; tile = farm['tiles'][y][x]; cmd = None
        tomato = isinstance(tile, dict) and tile.get('crop') == 'TOMATO'
        if not tomato and day <= 19:
            if tile is None and private['seeds'].get('TOMATO', 0) > v_need:
                cmd = ['PLANT', 'TOMATO']
            elif isinstance(tile, dict) and tile.get('kind') == 'WEED':
                cmd = ['DIG']
        elif tomato:
            if day < 29 and not tile.get('watered_today') and tile.get('consecutive_unwatered', 0) >= 1:
                cmd = ['WATER']
            elif tile.get('yield_units', 0) >= (1 if day >= 28 else 2):
                cmd = ['HARVEST']
            elif day < 29 and not tile.get('watered_today'):
                cmd = ['WATER', 'opt']
        if cmd:
            todo.append((t, cmd))
    if todo:
        must = [v for v in todo if v[1] != ['WATER', 'opt']]
        pool = must or todo
        t, cmd = min(pool, key=lambda v: (abs(pos[0] - v[0][0]) + abs(pos[1] - v[0][1]), targets.index(v[0])))
        cmd = cmd[:1] if cmd[0] == 'WATER' else cmd
        w = _v219_walk(pos, t)
        if w:
            return w
        if cmd[0] == 'PLANT':
            _TF_REPORT['tf_plants'] += 1
        return cmd
    if inv.get('TOMATO', 0):
        return _v219_walk(pos, home) or ['PLACE', 'TOMATO', int(inv['TOMATO'])]
    if any(inv.values()):
        return _v219_walk(pos, home) or ['DROP']
    return ['PASS']


def _tf_entry(observation, configuration=None):
    action = _TF_PARENT(observation, configuration)
    if not TF_ON:
        return action
    try:
        step = int(observation['step']); player = int(observation['player']); day = step // 24
        st = _TF_STATES.get(player)
        if st is None or step <= st['last_step']:
            st = _TF_STATES[player] = {'last_step': step, 'worker': None, 'day': -1}
            for k in _TF_REPORT:
                _TF_REPORT[k] = 0
        st['last_step'] = step
        if day < 18 or not isinstance(action, dict):
            return action
        v219 = _V219_STATES.get(player) or {}
        if not v219.get('committed'):
            return action
        farm = observation['farms'][player]
        if st['day'] != day:
            st['day'] = day; st['worker'] = None
        p = st.pop('pending', None)
        if p:
            if len(farm['hands']) >= p['actor']:
                st['worker'] = p['actor']; _TF_REPORT['tf_workers'] += 1
            else:
                _TF_REPORT['tf_hire_shortfalls'] += 1
        action = _tf_request(observation, action, st, v219)
        a = st.get('worker')
        if a is not None and a <= len(farm['hands']):
            out = copy.deepcopy(action)
            cmds = [out.get('farmer') or ['PASS']] + list(out.get('hands') or [])
            cmds += [['PASS'] for _ in range(len(farm['hands']) + 1 - len(cmds))]
            cmds[a] = _tf_worker(observation, st, a, v219)
            out['farmer'], out['hands'] = cmds[0], cmds[1:]
            action = out
        if st.get('committed'):
            stock = projected_shed(action, FarmView(observation)).get('TOMATO', 0)
            if stock > 0 and not any(o and o[:2] == ['SELL', 'TOMATO'] for o in action['market']) \
                    and len(action['market']) < MAX_ORDERS:
                action = copy.deepcopy(action)
                action['market'].append(['SELL', 'TOMATO', stock])
        return action
    except Exception:
        _TF_REPORT['tf_errors'] += 1
        return action


_tf_entry.telemetry = _TF_REPORT
agent = _tf_entry
kaggle_submission_agent = _tf_entry
