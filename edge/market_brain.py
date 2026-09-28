"""Market brain: decides how many premium units to SELL each turn.

Model
  * exact engine price curves (MARKET_PARAMS) and the town demand schedule
    (every unlocked shop consumes on step % 4 == 0, town center on step % 24 == 0);
  * opponent tracker: the opponent's harvests are visible on its tiles and its sales are
    visible as market-inventory changes (minus our sales, plus town consumption), so its
    hidden shed stock = harvested - sold;
  * allocator: every unit we hold is assigned greedily to the slot (now, or a future
    demand tick inside the horizon) where its marginal price is highest, given the
    forecast inventory path (opponent dumps its stock + visible yield soon, our own
    visible yield arrives soon, town demand drains). Only units assigned to "now" are sold.

Guards: never hold when that would leave less cash than the tape plans to spend in the
next day, never let the shed exceed `hold_cap`, and liquidate everything near the end.
"""
import math

MP = {
    "WHEAT": (25, 400, "sqrt", 0.80, "log", 0.20),
    "CARROT": (35, 450, "hinge", 1.00, "sqrt", 0.70),
    "TOMATO": (60, 200, "hinge", 0.40, "sqrt", 0.60),
    "STRAWBERRY": (120, 100, "sqrt", 0.70, "linear", 1.60),
    "MELON": (250, 300, "log", 0.20, "sq", 3.60),
    "EGG": (50, 332, "hinge", 0.40, "log", 0.20),
    "MILK": (160, 122, "sqrt", 0.60, "linear", 1.60),
    "WOOL": (200, 105, "log", 0.20, "sq", 3.20),
    "FERTILIZER": (100, 200, "linear", 0.40, "linear", 0.40),
}
I0 = 10000
SHOPS = {
    "BAKERY": ("EGG", "WHEAT"), "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"), "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"), "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"), "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}
SOURCE = {"STRAWBERRY": "STRAWBERRY", "MELON": "MELON", "TOMATO": "TOMATO", "CARROT": "CARROT",
          "MILK": "COW", "WOOL": "SHEEP", "EGG": "GOOSE"}
SEED = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
ANIMAL = {"GOOSE": 300, "COW": 400, "SHEEP": 500}
LAND = (1000, 2000, 4000)


def _shape(f, x, T):
    x = max(0.0, x)
    if f == "linear":
        return x
    if f == "sq":
        return x * x
    if f == "sqrt":
        return math.sqrt(x)
    if f == "log":
        return math.log(1.0 + x)
    if f == "hinge":
        u = x / T
        return u + 8.0 * max(0.0, u - 1.0) ** 2
    return x


def price(item, inv):
    base, T, bf, bt, af, at = MP[item]
    if inv < I0:
        p = base + bt * base / _shape(bf, T, T) * _shape(bf, I0 - inv, T)
    else:
        p = base - at * base / _shape(af, T, T) * _shape(af, inv - I0, T)
    return max(1, int(round(p)))


def demand(item, step, shops):
    d = 0
    if step % 4 == 0:
        for s in shops:
            pr = SHOPS.get(s, ())
            if item in pr:
                d += 2 if len(pr) == 1 else 1
    if step % 24 == 0 and item != "FERTILIZER":
        d += 1
    return d


def _g(v, k, d=None):
    if isinstance(v, dict):
        return v.get(k, d)
    g = getattr(v, "get", None)
    return g(k, d) if callable(g) else getattr(v, k, d)


def _i(v, d=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return d


def _yields(tiles):
    """{(x,y): (product, yield_units)} for producing tiles."""
    out = {}
    for y, row in enumerate(tiles or []):
        for x, t in enumerate(row or []):
            if not isinstance(t, dict):
                continue
            src = t.get("animal") or t.get("crop")
            for prod, s in SOURCE.items():
                if s == src:
                    out[(x, y)] = (prod, _i(t.get("yield_units")))
    return out


class MarketBrain:
    def __init__(self, s):
        self.s = s
        self.items = tuple(s.get("brain_items", ("STRAWBERRY", "MILK", "WOOL", "MELON", "TOMATO")))
        self.prev_inv = None
        self.prev_opp = None
        self.my_sold_last = {}
        self.opp_harv = {}
        self.opp_sold = {}
        self.stats = {"held": 0, "extra": 0}

    # ---------- opponent tracking ----------
    def track(self, obs, step):
        mk = _g(obs, "market", {}) or {}
        inv = {k: _i(v) for k, v in (dict(_g(mk, "inventory", {}) or {})).items()}
        prices = dict(_g(mk, "prices", {}) or {})
        shops = list(_g(_g(obs, "town", {}) or {}, "unlocked_shops", []) or [])
        me = _i(_g(obs, "player", 0))
        opp_tiles = _g(_g(obs, "farms")[1 - me], "tiles")
        cur = _yields(opp_tiles)
        if self.prev_inv is not None:
            k = step - 1  # consumption of the step that just resolved
            for it in self.items:
                d = demand(it, k, shops)
                q = inv.get(it, 0) - self.prev_inv.get(it, 0) + d - self.my_sold_last.get(it, 0)
                if q > 0:
                    self.opp_sold[it] = self.opp_sold.get(it, 0) + q
            for pos, (prod, y0) in (self.prev_opp or {}).items():
                prod1, y1 = cur.get(pos, (prod, 0))
                if prod1 != prod:
                    y1 = 0
                if y1 < y0 and (y0 - y1) >= 1:
                    # a harvest empties the tile; slow 1-unit decay of old crops is not a harvest
                    if y1 == 0 or (y0 - y1) > 1:
                        self.opp_harv[prod] = self.opp_harv.get(prod, 0) + (y0 - y1)
        self.prev_inv = inv
        self.prev_opp = cur
        return inv, prices, shops, cur

    def opp_stock(self, it):
        return max(0, self.opp_harv.get(it, 0) - self.opp_sold.get(it, 0))

    # ---------- cash guard ----------
    def planned_spend(self, tape, step, horizon, prices):
        cost = 0.0
        hires = {}
        for t in range(step, min(step + horizon, len(tape or []))):
            a = tape[t] if isinstance(tape[t], dict) else {}
            day = t // 24
            for o in a.get("market") or []:
                if not o:
                    continue
                op = o[0]
                q = _i(o[2], 1) if len(o) > 2 else 1
                if op == "BUY_SEED":
                    cost += SEED.get(o[1], 50) * q
                elif op == "BUY_ANIMAL":
                    cost += ANIMAL.get(o[1], 400) * q
                elif op == "BUY_PRODUCT":
                    cost += (_i(prices.get(o[1], 30)) + 5) * q
                elif op == "HIRE":
                    n = hires.get(day, 0)
                    a_, b_ = 1, 1
                    for _ in range(n):
                        a_, b_ = b_, a_ + b_
                    cost += a_
                    hires[day] = n + 1
                elif op == "BUY_LAND":
                    cost += 4000
        return cost

    # ---------- allocation ----------
    def plan_item(self, it, step, inv_now, shops, my_stock, my_incoming, opp_now, opp_incoming, horizon):
        """Return how many of my_stock to sell now."""
        if my_stock <= 0:
            return 0
        end = min(718, step + horizon)
        slots = [step] + [t for t in range(step + 1, end + 1) if t % 4 == 0]
        if len(slots) == 1:
            return my_stock
        # baseline inventory path without our held units
        opp_lag = self.s.get("brain_opp_lag", 1)
        inc_lag = self.s.get("brain_inc_lag", 8)
        base = {}
        I = inv_now
        cum = 0
        extra = {}
        extra[min(step + opp_lag, end)] = extra.get(min(step + opp_lag, end), 0) + opp_now
        extra[min(step + inc_lag, end)] = extra.get(min(step + inc_lag, end), 0) + opp_incoming + my_incoming
        for t in range(step, end + 1):
            if t > step:
                I -= demand(it, t - 1, shops)
            I += extra.get(t, 0)
            base[t] = I
        assigned = {t: 0 for t in slots}
        disc = self.s.get("brain_disc", 0.0)
        for _ in range(my_stock):
            best, bv = None, -1.0
            for t in slots:
                # units already committed at or before t push inventory up at t
                above = sum(v for u, v in assigned.items() if u <= t)
                p = price(it, base[t] + above)
                if p <= 1:
                    v = 1.0
                else:
                    v = p * (1.0 - disc * (t - step) / 24.0)
                if v > bv + 1e-9:
                    best, bv = t, v
            assigned[best] += 1
        return assigned[step]

    def apply(self, obs, action, tape):
        step = _i(_g(obs, "step", 0))
        inv, prices, shops, opp_yield = self.track(obs, step)
        if not isinstance(action, dict):
            return action
        market = [list(o) for o in (action.get("market") or [])]
        priv = _g(obs, "private", {}) or {}
        shed = {k: _i(v) for k, v in dict(_g(priv, "shed", {}) or {}).items()}
        me = _i(_g(obs, "player", 0))
        farm = _g(obs, "farms")[me]
        money = float(_g(farm, "money", 0) or 0)
        my_yield = _yields(_g(farm, "tiles"))
        horizon = self.s.get("brain_horizon", 48)
        start = self.s.get("brain_start", 0)
        if step < start or step >= self.s.get("brain_end", 700):
            self.my_sold_last = self._sold(market, shed)
            return action
        tape_sell = {}
        for o in market:
            if o and o[0] == "SELL" and len(o) >= 3 and o[1] in self.items:
                tape_sell[o[1]] = tape_sell.get(o[1], 0) + max(0, _i(o[2]))
        want = {}
        for it in self.items:
            stock = shed.get(it, 0)
            if stock <= 0:
                continue
            my_inc = sum(y for p, y in my_yield.values() if p == it)
            opp_inc = sum(y for p, y in opp_yield.values() if p == it)
            q = self.plan_item(it, step, inv.get(it, I0), shops, stock, my_inc, self.opp_stock(it), opp_inc, horizon)
            if self.s.get("brain_only_more"):
                q = max(q, min(stock, tape_sell.get(it, 0)))
            want[it] = q
        # cash guard: selling less than the tape must not starve its purchases
        need = self.planned_spend(tape, step, self.s.get("brain_cash_h", 24), prices) + self.s.get("brain_cash_pad", 300)
        proj = money
        for it, q in want.items():
            proj += q * _i(prices.get(it, 1))
        for o in market:
            if o and o[0] == "SELL" and len(o) >= 3 and o[1] not in want:
                proj += min(_i(o[2]), shed.get(o[1], 0)) * _i(prices.get(o[1], 1))
        if proj < need:
            for it in sorted(want, key=lambda k: -_i(prices.get(k, 0))):
                gap = need - proj
                if gap <= 0:
                    break
                add = min(shed.get(it, 0) - want[it], max(0, tape_sell.get(it, 0) - want[it]) or shed.get(it, 0) - want[it])
                add = min(add, -(-int(gap) // max(1, _i(prices.get(it, 1)))))
                if add > 0:
                    want[it] += add
                    proj += add * _i(prices.get(it, 1))
        # shed guard
        cap = self.s.get("brain_hold_cap", 70)
        total_after = sum(shed.values()) - sum(want.values()) - sum(
            min(_i(o[2]), shed.get(o[1], 0)) for o in market if o and o[0] == "SELL" and len(o) >= 3 and o[1] not in want)
        if total_after > cap:
            over = total_after - cap
            for it in sorted(want, key=lambda k: _i(prices.get(k, 0))):
                add = min(over, shed.get(it, 0) - want[it])
                if add > 0:
                    want[it] += add
                    over -= add
                if over <= 0:
                    break
        # rewrite the market list
        new = []
        placed = set()
        for o in market:
            if o and o[0] == "SELL" and len(o) >= 3 and o[1] in self.items:
                it = o[1]
                if it in placed:
                    continue
                placed.add(it)
                # units the tape deposits and sells this same turn are not in the shed yet:
                # pass them through, the brain only controls stock already in the shed
                passthru = max(0, tape_sell.get(it, 0) - shed.get(it, 0))
                q = (want.get(it, 0) + passthru) if it in want else _i(o[2])
                if q > 0:
                    new.append(["SELL", it, q])
                continue
            new.append(o)
        for it, q in want.items():
            if it not in placed and q > 0:
                new.append(["SELL", it, q])
        for it in want:
            d = want[it] - min(tape_sell.get(it, 0), shed.get(it, 0))
            if d < 0:
                self.stats["held"] += -d
            else:
                self.stats["extra"] += d
        action = dict(action)
        action["market"] = new[:10]
        self.my_sold_last = self._sold(action["market"], shed)
        return action

    @staticmethod
    def _sold(market, shed):
        sh = dict(shed)
        out = {}
        for o in market or []:
            if o and o[0] == "SELL" and len(o) >= 3:
                q = min(max(0, _i(o[2])), sh.get(o[1], 0))
                sh[o[1]] = sh.get(o[1], 0) - q
                out[o[1]] = out.get(o[1], 0) + q
        return out


class Meter:
    """Crashed-market metering (what DSM does to us): when a premium item's price is below
    `meter_trigger` x base, sell only units whose marginal price stays >= `meter_floor` x base,
    i.e. roughly what the town just absorbed. Excess stays in the shed and is released at later
    demand ticks as the price recovers. Safety: if the shed would stay above `meter_shed_hi`,
    or on the final `meter_end` steps, the tape's sells go through unchanged."""

    def __init__(self, s):
        self.s = s
        self.items = tuple(s.get("meter_items", ("STRAWBERRY", "MILK", "WOOL", "MELON", "TOMATO")))
        self.cut = 0

    def apply(self, obs, action):
        if not isinstance(action, dict):
            return action
        step = _i(_g(obs, "step", 0))
        if step >= self.s.get("meter_end", 696):
            return action
        mk = _g(obs, "market", {}) or {}
        inv = {k: _i(v) for k, v in dict(_g(mk, "inventory", {}) or {}).items()}
        shed = {k: _i(v) for k, v in dict(_g(_g(obs, "private", {}) or {}, "shed", {}) or {}).items()}
        market = [list(o) for o in (action.get("market") or [])]
        trig = self.s.get("meter_trigger", 0.6)
        floor = self.s.get("meter_floor", 0.2)
        # shed after the tape's sells
        after = dict(shed)
        for o in market:
            if o and o[0] == "SELL" and len(o) >= 3:
                after[o[1]] = after.get(o[1], 0) - min(_i(o[2]), max(0, after.get(o[1], 0)))
        # free room = cap - shed after sells - goods in hands - goods still on our tiles (arrive today)
        priv = _g(obs, "private", {}) or {}
        carried = sum(_i(v) for inv_ in (_g(priv, "inventories", []) or []) for v in dict(inv_ or {}).values())
        me = _i(_g(obs, "player", 0))
        on_tiles = sum(y for _, y in _yields(_g(_g(obs, "farms")[me], "tiles")).values())
        room = (self.s.get("meter_shed_hi", 85) - sum(max(0, v) for v in after.values())
                - carried - on_tiles - self.s.get("meter_pad", 10))
        if self.s.get("meter_mode") == "spread":
            return self._spread(obs, action, market, shed, inv, step, trig)
        new = []
        for o in market:
            if o and o[0] == "SELL" and len(o) >= 3 and o[1] in self.items:
                it, q = o[1], _i(o[2])
                base = MP[it][0]
                I = inv.get(it, I0)
                if price(it, I) < trig * base:
                    k = 0
                    while k < q and price(it, I + k) >= floor * base:
                        k += 1
                    keep = min(q - k, max(0, room), shed.get(it, 0))
                    if keep > 0:
                        room -= keep
                        self.cut += keep
                        q -= keep
                if q > 0:
                    new.append(["SELL", it, q])
                continue
            new.append(o)
        action = dict(action)
        action["market"] = new
        return action

    def _spread(self, obs, action, market, shed, inv, step, trig):
        """DSM-style daily schedule for crashed items: the day's stock is released evenly over the
        demand ticks (hours in meter_ticks); everything left goes at meter_last_hour so the shed is
        empty before the night drop. Items above trig x base follow the tape (race)."""
        hour = step % 24
        day = step // 24
        if getattr(self, "_day", -1) != day:
            self._day, self._sold = day, {}
        ticks = tuple(self.s.get("meter_ticks", (1, 5, 9, 13, 17, 21)))
        last = self.s.get("meter_last_hour", 21)
        done = sum(1 for h in ticks if h <= hour)
        new = []
        for o in market:
            if o and o[0] == "SELL" and len(o) >= 3 and o[1] in self.items:
                it, q = o[1], _i(o[2])
                have = shed.get(it, 0)
                passthru = max(0, q - have)
                if price(it, inv.get(it, I0)) < trig * MP[it][0] and hour < last:
                    total = have + self._sold.get(it, 0)
                    target = -(-total * done // len(ticks)) if done else 0
                    allow = max(0, min(have, target - self._sold.get(it, 0)))
                    keep = max(0, min(q, have) - allow)
                    self.cut += keep
                    q = min(q, have) - keep + passthru
                if q > 0:
                    new.append(["SELL", it, q])
                    self._sold[it] = self._sold.get(it, 0) + min(q, have)
                continue
            new.append(o)
        # release held stock of crashed items on schedule even when the tape has no sell order
        listed = {o[1] for o in new if o and o[0] == "SELL" and len(o) >= 3}
        for it in self.items:
            have = shed.get(it, 0)
            if it in listed or have <= 0 or price(it, inv.get(it, I0)) >= trig * MP[it][0]:
                continue
            total = have + self._sold.get(it, 0)
            target = total if hour >= last else (-(-total * done // len(ticks)) if done else 0)
            q = max(0, min(have, target - self._sold.get(it, 0)))
            if q > 0:
                new.append(["SELL", it, q])
                self._sold[it] = self._sold.get(it, 0) + q
        action = dict(action)
        action["market"] = new[:10]
        return action
