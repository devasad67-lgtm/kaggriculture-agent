"""Edge layer: wraps an inner Kaggriculture agent and post-processes its market orders.

The inner agent is exec'd from its own source into a private namespace, so its module
state is isolated from ours. Every edge layer is wrapped in try/except: on any error we
return the inner action unchanged.

Layers (toggled by settings):
  lead_steps    : for premium goods, sell now the lots the inner tape plans to SELL in
                  steps t+2..t+lead_steps (the inner already leads by one step itself).
                  Against a copy of the same tape this sells our lot before the copy's
                  identical lot depresses the price. The inner never errors on selling
                  stock that is already gone: the engine just aborts that order.
  premium_first : move premium SELL orders to the front of the market list, highest
                  current price first (orders run in lockstep by index across players).
"""
import copy

PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")


def _get(v, k, d=None):
    if isinstance(v, dict):
        return v.get(k, d)
    g = getattr(v, "get", None)
    if callable(g):
        return g(k, d)
    return getattr(v, k, d)


def _i(v, d=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return d


class Edge:
    def __init__(self, inner_agent, settings, chassis_getter=None):
        self.inner = inner_agent
        self.s = settings
        self.chassis_getter = chassis_getter
        self.errors = 0

    def __call__(self, obs, config=None):
        action = self.inner(obs, config)
        try:
            out = self.post(obs, action)
        except Exception:
            self.errors += 1
            out = action
        sab = self.s.get("_sabotage_hires")
        sab = {int(k): v for k, v in sab.items()} if sab else None
        if sab and isinstance(out, dict) and _i(_get(obs, "day", 0)) in sab:
            m, k = [], 0
            for o in out.get("market") or []:
                if o and o[0] == "HIRE":
                    k += 1
                    if k > sab[_i(_get(obs, "day", 0))]:
                        continue
                m.append(o)
            out = dict(out, market=m)
            self._sab_removed = max(0, k - sab[_i(_get(obs, "day", 0))])
        if self.s.get("adapt"):
            try:
                sh = dict(_get(_get(obs, "private", {}) or {}, "shed", {}) or {})
                sold = {}
                for o in (out.get("market") or []) if isinstance(out, dict) else []:
                    if o and o[0] == "SELL" and len(o) >= 3:
                        q = min(max(0, _i(o[2])), sh.get(o[1], 0))
                        sh[o[1]] = sh.get(o[1], 0) - q
                        sold[o[1]] = sold.get(o[1], 0) + q
                self._my_sold = sold
            except Exception:
                self.errors += 1
        if self.s.get("brain"):
            try:
                if not hasattr(self, "_brain"):
                    self._brain = MarketBrain(self.s)
                out = self._brain.apply(obs, out, self._tape(obs))
            except Exception:
                self.errors += 1
        veto = self.s.get("animal_veto")
        if veto and isinstance(out, dict):
            try:
                out = self._veto(obs, out, veto)
            except Exception:
                self.errors += 1
        if self.s.get("defer"):
            try:
                if not hasattr(self, "_defer"):
                    self._defer = DeferCollect(self.s)
                out = self._defer.apply(obs, out, self._tape(obs), getattr(self, "_courier", None))
            except Exception:
                self.errors += 1
        if self.s.get("courier"):
            try:
                if not hasattr(self, "_courier"):
                    self._courier = Courier(self.s)
                self._courier.skip = self._defer.shifted() if hasattr(self, "_defer") else set()
                out = self._courier.apply(obs, out, self._tape(obs))
            except Exception:
                self.errors += 1
        if self.s.get("ferthand"):
            try:
                if not hasattr(self, "_fh"):
                    self._fh = FertHand(self.s)
                out = self._fh.apply(obs, out)
            except Exception:
                self.errors += 1
        if self.s.get("meter"):
            try:
                if not hasattr(self, "_meter"):
                    self._meter = Meter(self.s)
                out = self._meter.apply(obs, out)
            except Exception:
                self.errors += 1
        if self.s.get("rescue"):
            try:
                if not hasattr(self, "_rescue"):
                    self._rescue = Rescue(self.s)
                self._rescue.extra_hires = getattr(self, "_sab_removed", 0)
                self._sab_removed = 0
                out = self._rescue.apply(obs, copy.deepcopy(out))
            except Exception:
                self.errors += 1
        if self.s.get("arb"):
            try:
                if not hasattr(self, "_arb"):
                    self._arb = WheatArb(self.s)
                out = self._arb.apply(obs, out)
            except Exception:
                self.errors += 1
        return out

    def _veto(self, obs, action, veto):
        """Skip BUY_ANIMAL <kind> from day veto[kind]['from_day'] when none of veto[kind]['shops'] is open.
        The tape still builds the structure (tile stays occupied, shop RNG unchanged); its later
        PICKUP/PLACE/FEED/HARVEST on the missing animal are engine no-ops."""
        day = _i(_get(obs, "day", 0))
        shops = set(_get(_get(obs, "town", {}) or {}, "unlocked_shops", []) or [])
        m = []
        for o in action.get("market") or []:
            if o and o[0] == "BUY_ANIMAL" and len(o) >= 2 and o[1] in veto:
                rule = veto[o[1]]
                if day >= rule.get("from_day", 6) and not (shops & set(rule.get("shops", ()))):
                    self.vetoed = getattr(self, "vetoed", 0) + (_i(o[2], 1) if len(o) > 2 else 1)
                    continue
            m.append(o)
        action = dict(action)
        action["market"] = m
        return action

    def _tape(self, obs):
        ch = self.chassis_getter() if self.chassis_getter else None
        if ch is None:
            return []
        st = ch.players.get(_i(_get(obs, "player", 0))) or {}
        return ch.routes.get(st.get("route")) or []

    def _tape_sells(self, obs, step_from, step_to):
        """Planned SELL qty per item in the inner's current route for [step_from, step_to]."""
        ch = self.chassis_getter() if self.chassis_getter else None
        if ch is None:
            return {}
        player = _i(_get(obs, "player", 0))
        st = ch.players.get(player) or {}
        route = st.get("route")
        tape = ch.routes.get(route)
        if not tape:
            return {}
        out = {}
        for t in range(step_from, min(step_to + 1, len(tape))):
            a = tape[t] if isinstance(tape[t], dict) else {}
            for o in a.get("market") or []:
                if o and o[0] == "SELL" and len(o) >= 3:
                    out[o[1]] = out.get(o[1], 0) + max(0, _i(o[2]))
        return out

    SHOPS = {"BAKERY": ("EGG", "WHEAT"), "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
             "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"), "YARN_STORE": ("WOOL",),
             "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"), "PET_CAFE": ("CARROT",),
             "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"), "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY")}

    def _tape_lots(self, obs, item, a, b):
        ch = self.chassis_getter() if self.chassis_getter else None
        if ch is None:
            return {}
        st = ch.players.get(_i(_get(obs, "player", 0))) or {}
        tape = ch.routes.get(st.get("route"))
        out = {}
        for t in range(a, min(b + 1, len(tape or []))):
            x = tape[t] if isinstance(tape[t], dict) else {}
            q = sum(max(0, _i(o[2])) for o in x.get("market") or [] if o and o[0] == "SELL" and len(o) >= 3 and o[1] == item)
            if q:
                out[t] = q
        return out

    def _rival_leads(self, obs, step):
        """Infer the rival's premium sells from public market inventory (delta + town consumption - ours),
        match each against our own tape (a same-family rival runs the same tape) and vote on the rival's lead.
        Returns {item: lead to use} once there is evidence that the rival sells ahead of us."""
        mk = _get(obs, "market", {}) or {}
        inv = dict(_get(mk, "inventory", {}) or {})
        shops = list(_get(_get(obs, "town", {}) or {}, "unlocked_shops", []) or [])
        prev = getattr(self, "_prev_inv", None)
        self._prev_inv = inv
        votes = self.__dict__.setdefault("_votes", {})
        items = self.s.get("premium_items", ())
        if prev is not None and step >= 1:
            k = step - 1
            mine = getattr(self, "_my_sold", {}) or {}
            for it in items:
                cons = 0
                if k % 4 == 0:
                    for sh in shops:
                        pr = self.SHOPS.get(sh, ())
                        if it in pr:
                            cons += 2 if len(pr) == 1 else 1
                if k % 24 == 0:
                    cons += 1
                rq = _i(inv.get(it, 0)) - _i(prev.get(it, 0)) + cons - mine.get(it, 0)
                if rq <= 0:
                    continue
                lots = self._tape_lots(obs, it, k + 1, k + self.s.get("adapt_max", 48))
                for t, q in lots.items():
                    if q == rq:
                        j = t - k
                        v = votes.setdefault(it, {})
                        v[j] = v.get(j, 0) + 1
        out = {}
        L = self.s.get("lead_steps", 0)
        cap = self.s.get("adapt_max", 48)
        allv = {}
        for it in items:
            for j, c in (votes.get(it) or {}).items():
                allv[j] = allv.get(j, 0) + c
        if sum(allv.values()) >= self.s.get("adapt_min_votes", 4):
            best = max(allv, key=lambda j: (allv[j], -j))
            want = min(cap, max(L, best + self.s.get("adapt_margin", 2)))
            for it in items:
                out[it] = want
            if self.s.get("adapt_log") and step % 24 == 0:
                with open(self.s["adapt_log"], "a") as f:
                    f.write("%d %s %d" % (step, sorted(allv.items(), key=lambda x: -x[1])[:4], want) + chr(10))
        return out

    def post(self, obs, action):
        if not isinstance(action, dict):
            return action
        action = copy.deepcopy(action)
        market = [list(o) for o in (action.get("market") or [])]
        prices = dict(_get(_get(obs, "market", {}) or {}, "prices", {}) or {})
        shed = dict(_get(_get(obs, "private", {}) or {}, "shed", {}) or {})
        step = _i(_get(obs, "step", 0))
        items = self.s.get("premium_items", ())
        L = self.s.get("lead_steps", 0)
        lead_of = {}
        if self.s.get("adapt"):
            try:
                lead_of = self._rival_leads(obs, step)
            except Exception:
                self.errors += 1
        if L >= 2 and step < 718:
            future = self._tape_sells(obs, step + 2, step + max([L] + list(lead_of.values())))
            if lead_of:
                future = {it: self._tape_sells(obs, step + 2, step + lead_of.get(it, L)).get(it, 0) for it in items}
            selling = {}
            for o in market:
                if o and o[0] == "SELL" and len(o) >= 3:
                    selling[o[1]] = selling.get(o[1], 0) + max(0, _i(o[2]))
            for item in items:
                want = future.get(item, 0)
                if want <= 0 or _i(prices.get(item, 0)) < self.s.get("min_price", 2):
                    continue
                avail = max(0, _i(shed.get(item, 0)) - selling.get(item, 0))
                qty = min(avail, want)
                if qty <= 0:
                    continue
                merged = False
                for o in market:
                    if o and o[0] == "SELL" and o[1] == item:
                        o[2] = _i(o[2]) + qty
                        merged = True
                        break
                if not merged:
                    market.append(["SELL", item, qty])
        if self.s.get("premium_first"):
            is_p = lambda o: bool(o) and o[0] == "SELL" and len(o) >= 3 and o[1] in items
            prem = sorted([o for o in market if is_p(o)], key=lambda o: -_i(prices.get(o[1], 0)))
            market = prem + [o for o in market if not is_p(o)]
        op = self.s.get("opening")
        if op and step == 0:
            rest = [o for o in market if not (o and o[0] in ("BUY_PRODUCT", "SELL") and len(o) > 1 and o[1] == "WHEAT")]
            market = [list(o) for o in op] + rest
        action["market"] = market[:10]
        return action


ACCESS = ((4, 4), (5, 4), (4, 5), (5, 5))
STEP = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}


def _d(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _toward(p, q):
    if p[0] < q[0]:
        return ["EAST"]
    if p[0] > q[0]:
        return ["WEST"]
    if p[1] < q[1]:
        return ["SOUTH"]
    if p[1] > q[1]:
        return ["NORTH"]
    return None


class Rescue:
    """Last-resort guard: an animal that is unfed with consecutive_unfed>=1 escapes tonight, a
    plant unwatered with consecutive_unwatered>=1 withers tonight. The inner tape assumes all its
    hires succeed; when one fails (cash ~$0 on day 1) nobody feeds that animal. Free (PASSing)
    units are sent to feed/water; late in the day a busy unit is taken for an animal."""

    def __init__(self, s):
        self.s = s
        self.day = -1
        self.jobs = {}  # unit index -> (x, y)

    def apply(self, obs, action):
        if not isinstance(action, dict):
            return action
        hour = _i(_get(obs, "hour", 0))
        day = _i(_get(obs, "day", 0))
        if day != self.day:
            self.day, self.jobs = day, {}
        left = 24 - hour  # actions still to come today, including this one
        me = _i(_get(obs, "player", 0))
        farm = _get(obs, "farms")[me]
        if _i(_get(farm, "hires_today", 0)) < getattr(self, "hire_req", 0) and getattr(self, "hire_day", -1) == day:
            self.short_day = day
        if getattr(self, "hire_day", -1) != day:
            self.hire_day, self.hire_req = day, 0
        self.hire_req += sum(1 for o in (action.get("market") or []) if o and o[0] == "HIRE") + getattr(self, "extra_hires", 0)
        tiles = _get(farm, "tiles")
        priv = _get(obs, "private", {}) or {}
        shed = dict(_get(priv, "shed", {}) or {})
        invs = [dict(x or {}) for x in (_get(priv, "inventories", []) or [])]
        pos = [tuple(_get(farm, "farmer"))] + [tuple(h) for h in (_get(farm, "hands", []) or [])]
        if self.s.get("rescue_only_short", True) and getattr(self, "short_day", -1) != day:
            self.jobs = {}
            return action
        acts = [action.get("farmer")] + list(action.get("hands") or [])
        acts += [["PASS"]] * (len(pos) - len(acts))
        acts = acts[:len(pos)]

        animals, plants = [], []
        for y, row in enumerate(tiles):
            for x, t in enumerate(row):
                if not isinstance(t, dict):
                    continue
                if t.get("animal") and not t.get("fed_today") and _i(t.get("consecutive_unfed")) >= 1:
                    animals.append((x, y))
                elif (t.get("kind") == "PLANT" and not t.get("watered_today") and _i(t.get("consecutive_unwatered")) >= 1
                      and _i(t.get("planted_day"), day) < day):
                    plants.append((x, y))
        if not animals and not plants:
            self.jobs = {}
            return action
        a_hour = self.s.get("rescue_hour", 12)
        p_hour = self.s.get("rescue_plant_hour", 99)
        if hour < min(a_hour, p_hour):
            return action
        risk_a = set(animals) if hour >= a_hour and day <= self.s.get("rescue_last_day", 20) else set()
        risk_p = set(plants) if hour >= p_hour and day <= self.s.get("rescue_plant_last_day", 19) else set()
        if not risk_a and not risk_p:
            self.jobs = {}
            return action
        # drop finished jobs
        self.jobs = {u: g for u, g in self.jobs.items() if u < len(pos) and (g in risk_a or g in risk_p)}

        def idle(u):
            a = acts[u]
            return (not a) or a[0] == "PASS"

        wheat_units = sum(inv.get("WHEAT", 0) for inv in invs)
        shed_wheat = shed.get("WHEAT", 0)

        def need(u, g):
            p = pos[u]
            if g in risk_p:
                return _d(p, g) + 1
            if invs[u].get("WHEAT", 0) > 0 if u < len(invs) else False:
                return _d(p, g) + 1
            acc = min(ACCESS, key=lambda a: _d(p, a) + _d(a, g))
            return _d(p, acc) + 1 + _d(acc, g) + 1

        taken = set(self.jobs.values())
        targets = [g for g in sorted(risk_a) if g not in taken] + [g for g in sorted(risk_p) if g not in taken]
        for g in targets:
            is_animal = g in risk_a
            best = None
            for u in range(len(pos)):
                if u in self.jobs:
                    continue
                n = need(u, g)
                if n > left:
                    continue
                busy = not idle(u)
                if busy and not (is_animal and left <= n + self.s.get("rescue_slack", 3)):
                    continue
                key = (busy, n)
                if best is None or key < best[0]:
                    best = (key, u)
            if best is not None:
                self.jobs[best[1]] = g

        need_wheat = 0
        for u, g in self.jobs.items():
            if g not in risk_a:
                continue
            p = pos[u]
            inv = invs[u] if u < len(invs) else {}
            if inv.get("WHEAT", 0) > 0:
                a = ["FEED"] if p == g else _toward(p, g)
            elif p in ACCESS:
                if shed_wheat > 0:
                    k = max(1, min(shed_wheat, len([h for v, h in self.jobs.items() if h in risk_a])))
                    a = ["PICKUP", "WHEAT", k]
                    shed_wheat -= k
                else:
                    a = ["PASS"]
                    need_wheat += 1
            else:
                acc = min(ACCESS, key=lambda q: _d(p, q) + _d(q, g))
                a = _toward(p, acc)
                if shed_wheat <= 0:
                    need_wheat += 1
                else:
                    shed_wheat -= 1
            acts[u] = a or ["PASS"]
        for u, g in self.jobs.items():
            if g in risk_p:
                p = pos[u]
                acts[u] = ["WATER"] if p == g else (_toward(p, g) or ["PASS"])

        if need_wheat > 0:
            market = [list(o) for o in (action.get("market") or [])]
            buying = sum(_i(o[2]) for o in market if o and o[0] == "BUY_PRODUCT" and len(o) >= 3 and o[1] == "WHEAT")
            want = need_wheat - buying
            if want > 0:
                prices = dict(_get(_get(obs, "market", {}) or {}, "prices", {}) or {})
                wp = _i(prices.get("WHEAT", 25)) + 3
                money = float(_get(farm, "money", 0) or 0)
                pre = []
                short = want * wp - money
                if short > 0:
                    for item in sorted((k for k, v in shed.items() if v > 0 and k in PRODUCTS and k != "WHEAT"),
                                       key=lambda k: -_i(prices.get(k, 0))):
                        pr = max(1, _i(prices.get(item, 1)))
                        q = min(shed[item], -(-int(short) // pr))
                        pre.append(["SELL", item, q])
                        short -= q * pr
                        if short <= 0:
                            break
                market = pre + [["BUY_PRODUCT", "WHEAT", want]] + market
                action["market"] = market[:10]
        action["farmer"] = acts[0]
        if len(pos) > 1:
            action["hands"] = acts[1:]
        return action


class Courier:
    """Detour courier: a tape worker carrying premium goods whose tape has a stretch of only
    moves/PASS long enough to walk to a shed-access tile, PLACE each premium item, and walk to the
    exact tile the tape would have reached at the end of that stretch, does so. Positions and all
    non-idle tape commands are unchanged, so the tape stays in sync; the goods reach the shed hours
    before the nightly auto-drop and can be sold the same day."""

    IDLE = ("PASS", "NORTH", "SOUTH", "EAST", "WEST")

    def __init__(self, s):
        self.s = s
        self.items = tuple(s.get("courier_items", ("STRAWBERRY", "MILK", "WOOL", "MELON", "TOMATO", "CARROT", "EGG")))
        self.plans = {}
        self.trips = 0
        self.units = 0

    @staticmethod
    def _move(p, c):
        d = STEP.get(c[0]) if c else None
        if not d:
            return p
        return (min(9, max(0, p[0] + d[0])), min(9, max(0, p[1] + d[1])))

    @staticmethod
    def _walk(p, q):
        out = []
        while p != q:
            c = _toward(p, q)
            out.append(c)
            p = Courier._move(p, c)
        return out

    def apply(self, obs, action, tape):
        if not isinstance(action, dict) or not tape:
            return action
        step = _i(_get(obs, "step", 0))
        hour = step % 24
        day = step // 24
        if getattr(self, "_day", -1) != day:
            self._day, self.plans = day, {}
        if step >= 717 or hour < self.s.get("courier_from", 1) or hour > self.s.get("courier_to", 20):
            return action
        me = _i(_get(obs, "player", 0))
        farm = _get(obs, "farms")[me]
        pos = [tuple(_get(farm, "farmer"))] + [tuple(h) for h in (_get(farm, "hands", []) or [])]
        invs = [dict(x or {}) for x in (_get(_get(obs, "private", {}) or {}, "inventories", []) or [])]
        cmds = [action.get("farmer") or ["PASS"]] + list(action.get("hands") or [])
        cmds += [["PASS"]] * (len(pos) - len(cmds))
        end = day * 24 + 23
        a0 = tape[step] if step < len(tape) and isinstance(tape[step], dict) else {}
        crew = 1 + len(a0.get("hands") or [])
        changed = False
        for u, p in enumerate(pos[:crew]):
            if u in getattr(self, "skip", ()):
                continue
            plan = self.plans.get(u)
            if plan is not None:
                k = step - plan["t0"]
                if 0 <= k < len(plan["cmds"]):
                    cmds[u] = plan["cmds"][k]
                    changed = True
                continue
            cargo = [it for it in self.items if invs[u].get(it, 0) > 0] if u < len(invs) else []
            if len(cargo) == 0 or sum(invs[u].get(it, 0) for it in cargo) < self.s.get("courier_min", 3):
                continue
            if not cmds[u] or cmds[u][0] not in self.IDLE:
                continue
            # idle stretch in the tape starting now; tape position at each step of it
            q = p
            window = []
            for t in range(step, end):
                a = tape[t] if t < len(tape) and isinstance(tape[t], dict) else {}
                units = [a.get("farmer") or ["PASS"]] + list(a.get("hands") or [])
                c = cmds[u] if t == step else (units[u] if u < len(units) else ["PASS"])
                if not c or c[0] not in self.IDLE:
                    break
                q = self._move(q, c)
                window.append(q)
            best = None
            for L in range(1, len(window) + 1):
                target = window[L - 1]
                acc = min(ACCESS, key=lambda a: _d(p, a) + _d(a, target))
                need = _d(p, acc) + len(cargo) + _d(acc, target)
                if need <= L:
                    best = (L, acc, target)
                    break
            if best is None:
                continue
            L, acc, target = best
            route = self._walk(p, acc) + [["PLACE", it, invs[u][it]] for it in cargo]
            route += self._walk(acc, target)
            route += [["PASS"]] * (L - len(route))
            self.plans[u] = {"t0": step, "cmds": route}
            self.trips += 1
            self.units += sum(invs[u][it] for it in cargo)
            cmds[u] = route[0]
            changed = True
        if changed:
            action = dict(action)
            action["farmer"] = cmds[0]
            action["hands"] = cmds[1:]
        return action



class DeferCollect:
    """Premium goods first: a tape worker carrying premium goods worth >= defer_value skips its
    COLLECT_FERTILIZER step and runs the rest of its own tape stream one step early; the shift is
    paid back at the worker's next tape PASS (it waits there), so positions re-sync with the tape.
    Units reset to the shed every night, so a shift never survives the day. Cost: 1 fertilizer per
    skip; gain: the goods reach the shed (and the market) earlier than a rival running the same tape."""

    def __init__(self, s):
        self.s = s
        self.items = tuple(s.get("defer_items", ("STRAWBERRY", "MILK", "WOOL", "MELON", "TOMATO", "CARROT", "EGG")))
        self.d = {}
        self.skips = 0

    def shifted(self):
        return {u for u, d in self.d.items() if d > 0}

    @staticmethod
    def _cmd(tape, t, u):
        a = tape[t] if 0 <= t < len(tape) and isinstance(tape[t], dict) else None
        if a is None:
            return None
        if u == 0:
            return list(a.get("farmer") or ["PASS"])
        h = a.get("hands") or []
        return list(h[u - 1] or ["PASS"]) if u - 1 < len(h) else None

    def apply(self, obs, action, tape, courier=None):
        if not isinstance(action, dict) or not tape:
            return action
        step = _i(_get(obs, "step", 0))
        day, hour = step // 24, step % 24
        if getattr(self, "_day", -1) != day:
            self._day, self.d = day, {}
        if step >= 717:
            return action
        end = day * 24 + 23
        prices = dict(_get(_get(obs, "market", {}) or {}, "prices", {}) or {})
        invs = [dict(x or {}) for x in (_get(_get(obs, "private", {}) or {}, "inventories", []) or [])]
        cmds = [list(action.get("farmer") or ["PASS"])] + [list(h or ["PASS"]) for h in (action.get("hands") or [])]
        busy = set()
        if courier is not None:
            for u, pl in (getattr(courier, "plans", {}) or {}).items():
                if 0 <= step - pl["t0"] < len(pl["cmds"]):
                    busy.add(u)
        changed = False
        for u in range(len(cmds)):
            if u in busy:
                continue
            d = self.d.get(u, 0)
            if d == 0:
                tc = self._cmd(tape, step, u)
                if tc is None or tc != cmds[u]:
                    continue
            inv = invs[u] if u < len(invs) else {}
            val = sum(_i(inv.get(it, 0)) * _i(prices.get(it, 0)) for it in self.items)
            ptr = step + d
            c = self._cmd(tape, ptr, u) if ptr <= end else ["PASS"]
            while (c and c[0] == "COLLECT_FERTILIZER" and val >= self.s.get("defer_value", 1500)
                   and d < self.s.get("defer_max", 3) and hour >= self.s.get("defer_from", 1)
                   and hour <= self.s.get("defer_to", 20) and ptr + 1 <= end
                   and (self._cmd(tape, ptr + 1, u) or ["PASS"])[0] != "PASS"
                   and self._fert_ok(tape, ptr + 1, end, u, inv)):
                d += 1
                self.skips += 1
                ptr = step + d
                c = self._cmd(tape, ptr, u) if ptr <= end else ["PASS"]
            if d == 0:
                continue
            if c is None:
                c = ["PASS"]
            if c[0] == "PASS" and ptr <= end:
                d -= 1
            self.d[u] = d
            if c != cmds[u]:
                cmds[u] = c
                changed = True
        if changed:
            action = dict(action)
            action["farmer"] = cmds[0]
            action["hands"] = cmds[1:]
        return action

    def _fert_ok(self, tape, a, end, u, inv):
        """Do not starve the worker's own later FERTILIZE commands today."""
        need = 0
        for t in range(a, end + 1):
            c = self._cmd(tape, t, u)
            if c and c[0] == "FERTILIZE":
                need += 1
            elif c and c[0] == "COLLECT_FERTILIZER":
                need -= 1
        return _i(inv.get("FERTILIZER", 0)) >= need

class FertHand:
    """Late-game fertilizer hand. When fertilizer is cheap (price <= fh_max_price) and the shed holds
    at least fh_min_fert units, hire one extra hand at the day's first step (HIRE appended last, so it
    is the newest hand). It picks up fertilizer at the shed and FERTILIZEs young WHEAT/CARROT plants
    (age <= fh_max_age, not already fertilized), which lifts their capped yield (wheat 4->6, carrot 3->4).
    It never touches tape units or tiles' occupancy, so the tape and the shop RNG are unaffected."""

    CROPS = ("WHEAT", "CARROT")

    def __init__(self, s):
        self.s = s
        self.day = -1
        self.idx = None
        self.hired = 0
        self.ferts = 0
        self.claimed = set()

    def apply(self, obs, action):
        if not isinstance(action, dict):
            return action
        step = _i(_get(obs, "step", 0))
        day, hour = step // 24, step % 24
        me = _i(_get(obs, "player", 0))
        farm = _get(obs, "farms")[me]
        hands = [tuple(h) for h in (_get(farm, "hands", []) or [])]
        priv = _get(obs, "private", {}) or {}
        shed = dict(_get(priv, "shed", {}) or {})
        invs = [dict(x or {}) for x in (_get(priv, "inventories", []) or [])]
        prices = dict(_get(_get(obs, "market", {}) or {}, "prices", {}) or {})
        tiles = _get(farm, "tiles")
        if day != self.day:
            self.day, self.idx, self.claimed = day, None, set()
            if (self.s.get("fh_from", 18) <= day <= self.s.get("fh_to", 27) and hour == 0
                    and _i(shed.get("FERTILIZER", 0)) >= self.s.get("fh_min_fert", 8)
                    and _i(prices.get("FERTILIZER", 100)) <= self.s.get("fh_max_price", 25)):
                market = [list(o) for o in (action.get("market") or [])]
                n_hire = sum(1 for o in market if o and o[0] == "HIRE")
                cost_idx = _i(_get(farm, "hires_today", 0)) + n_hire
                a, b = 1, 1
                for _ in range(cost_idx):
                    a, b = b, a + b
                if a <= self.s.get("fh_max_hire_cost", 250) and float(_get(farm, "money", 0) or 0) > a + 500 and len(market) < 10:
                    market.append(["HIRE"])
                    action = dict(action)
                    action["market"] = market
                    self.idx = len(hands) + n_hire  # index in hands list once hired
                    self.hired += 1
            return action
        if self.idx is None or self.idx >= len(hands):
            return action
        u = self.idx
        p = hands[u]
        inv = invs[u + 1] if u + 1 < len(invs) else {}
        cmd = ["PASS"]
        have = _i(inv.get("FERTILIZER", 0))
        targets = []
        for y, row in enumerate(tiles or []):
            for x, t in enumerate(row or []):
                if (isinstance(t, dict) and t.get("kind") == "PLANT" and t.get("crop") in self.CROPS
                        and day - _i(t.get("planted_day"), -99) <= self.s.get("fh_max_age", 2)
                        and _i(t.get("fertilized_until_day"), -1) < day and (x, y) not in self.claimed):
                    targets.append((x, y))
        if have <= 0:
            if targets and _i(shed.get("FERTILIZER", 0)) > 0:
                if p in ACCESS:
                    cmd = ["PICKUP", "FERTILIZER", min(_i(shed["FERTILIZER"]), self.s.get("fh_carry", 15))]
                else:
                    cmd = _toward(p, min(ACCESS, key=lambda a: _d(p, a))) or ["PASS"]
        elif targets:
            g = min(targets, key=lambda q: _d(p, q))
            if g == p:
                cmd = ["FERTILIZE"]
                self.claimed.add(g)
                self.ferts += 1
            else:
                cmd = _toward(p, g) or ["PASS"]
        hs = list(action.get("hands") or [])
        while len(hs) <= u:
            hs.append(["PASS"])
        hs[u] = cmd
        action = dict(action)
        action["hands"] = hs
        return action


class WheatArb:
    """Town-tick wheat carry: on a step where town shops consume (step % 4 == 0, after the market),
    buy N wheat; sell the same N first thing next step at the post-consumption (higher) price.
    Pure market layer: never touches units. N capped by shed room, cash and settings."""

    def __init__(self, s):
        self.s = s
        self.pending = 0
        self.trades = 0
        self.units = 0

    def apply(self, obs, action):
        if not isinstance(action, dict):
            return action
        step = _i(_get(obs, "step", 0))
        day = step // 24
        market = [list(o) for o in (action.get("market") or []) if o]
        if self.pending > 0:
            if len(market) < 10:
                market.insert(0, ["SELL", "WHEAT", self.pending])
                self.pending = 0
        elif step % 4 == 0 and self.s.get("arb_from", 1) <= day <= self.s.get("arb_to", 28) and len(market) < 10:
            shops = list(_get(_get(obs, "town", {}) or {}, "unlocked_shops", []) or [])
            k = sum(1 for sh in shops if sh in ("BAKERY", "PIZZA_SHOP", "BRUNCH_SPOT", "ICE_CREAM_SHOP", "FARMERS_MARKET"))
            k += 1 if step % 24 == 0 else 0
            if k >= self.s.get("arb_min_k", 1):
                me = _i(_get(obs, "player", 0))
                farm = _get(obs, "farms")[me]
                priv = _get(obs, "private", {}) or {}
                shed = dict(_get(priv, "shed", {}) or {})
                carried = sum(sum(max(0, _i(v)) for v in dict(x or {}).values()) for x in (_get(priv, "inventories", []) or []))
                bought = sum(_i(o[2]) for o in market if o[0] == "BUY_PRODUCT" and len(o) > 2)
                room = 100 - sum(max(0, _i(v)) for v in shed.values()) - carried - bought - self.s.get("arb_pad", 20)
                price = _i(_get(_get(obs, "market", {}) or {}, "prices", {}).get("WHEAT", 30))
                money = float(_get(farm, "money", 0) or 0)
                cash = int((money - self.s.get("arb_keep", 1500)) // max(1, price + 3))
                n = min(self.s.get("arb_max", 25), room, cash)
                if n > 0:
                    market.append(["BUY_PRODUCT", "WHEAT", n])
                    self.pending = n
                    self.trades += 1
                    self.units += n
        return dict(action, market=market)
