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
            return self.post(obs, action)
        except Exception:
            self.errors += 1
            return action

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
        if L >= 2 and step < 718:
            future = self._tape_sells(obs, step + 2, step + L)
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
        action["market"] = market[:10]
        return action
