"""Beast v4: adaptive Kaggriculture agent (own implementation).

Strategy principles (learned from ladder statistics, implemented from scratch):
  * diversify production so no single market crashes (9 products)
  * buy cows/sheep early while milk/wool are dear; melons + strawberries for mid-game cash;
    tomatoes, carrots, geese and wheat to fill the land later
  * feed an animal on a given day only when the extra product is worth the wheat;
    never let one go two days unfed (it would escape)
  * spend fertilizer on crops when the extra yield is worth more than selling it
Workers: snake-path segments per unit + greedy distance-discounted task choice.
"""
import math
import os

BOARD = 10
HALF = BOARD // 2
ACCESS = [(HALF - 1, HALF - 1), (HALF, HALF - 1), (HALF - 1, HALF), (HALF, HALF)]
QUADS = {"NW": ACCESS[0], "NE": ACCESS[1], "SW": ACCESS[2], "SE": ACCESS[3]}
LAND_PRICES = [1000, 2000, 4000]
CROPS = {
    "WHEAT": {"seed": 10, "fyd": 2, "myd": 4, "my": 6, "on": False, "iv": 0, "span": 4},
    "CARROT": {"seed": 20, "fyd": 2, "myd": 3, "my": 4, "on": False, "iv": 0, "span": 3},
    "TOMATO": {"seed": 50, "fyd": 8, "myd": 8, "my": 4, "on": True, "iv": 1, "span": 10},
    "STRAWBERRY": {"seed": 100, "fyd": 10, "myd": 10, "my": 4, "on": True, "iv": 2, "span": 15},
    "MELON": {"seed": 80, "fyd": 10, "myd": 12, "my": 6, "on": False, "iv": 0, "span": 12},
}
ANIMALS = {
    "GOOSE": {"cost": 300, "st": "COOP", "held": 4, "prod": "EGG", "fyd": 4, "iv": 1},
    "COW": {"cost": 400, "st": "PASTURE", "held": 6, "prod": "MILK", "fyd": 8, "iv": 2},
    "SHEEP": {"cost": 500, "st": "PASTURE", "held": 6, "prod": "WOOL", "fyd": 6, "iv": 3},
}
PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
MOVES = {(1, 0): "EAST", (-1, 0): "WEST", (0, 1): "SOUTH", (0, -1): "NORTH"}

DEFAULTS = {
    "layout": {
        "NW": [("COW", 2), ("SHEEP", 2), ("MELON", 12), ("WHEAT", 9)],
        "NE": [("COW", 6), ("SHEEP", 4), ("STRAWBERRY", 10), ("WHEAT", 5)],
        "SW": [("GOOSE", 3), ("STRAWBERRY", 10), ("WHEAT", 6), ("CARROT", 6)],
        "SE": [("GOOSE", 3), ("TOMATO", 6), ("CARROT", 6), ("WHEAT", 10)],
    },
    "hands_max": 12,
    "dist_cost": 9.0,
    "own_bonus": 45.0,
    "feed_margin": 1.15,
    "fert_mult": 1.6,
    "land_buffer": 300,
    "land_days": (4, 7, 9),   # earliest day for each land purchase
}


def dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def fib_sum(n):
    a, b, s = 1, 1, 0
    for _ in range(max(0, n)):
        s += a
        a, b = b, a + b
    return s


def quad_of(p):
    return ("N" if p[1] < HALF else "S") + ("W" if p[0] < HALF else "E")


def quad_tiles(quad):
    ax, ay = QUADS[quad]
    xs = range(0, HALF) if quad[1] == "W" else range(HALF, BOARD)
    ys = range(0, HALF) if quad[0] == "N" else range(HALF, BOARD)
    return sorted(((x, y) for x in xs for y in ys), key=lambda p: (dist(p, (ax, ay)), p))


def crop_for(role, day):
    """Crop to plant on a crop-role tile today, or None."""
    if role == "MELON" and day > 3:
        role = "WHEAT"
    if role in CROPS and day + CROPS[role]["span"] <= 29:
        return role
    if day + 3 <= 29:
        return "CARROT"
    if day + 2 <= 28:
        return "WHEAT"
    return None


class Beast:
    def __init__(self, cfg=None):
        self.cfg = dict(DEFAULTS)
        self.cfg.update(cfg or {})
        self.reset()

    def reset(self):
        self.last_step = -1
        self.roles = {}
        self.tgt = {}
        self.seg_key = None
        self.owner = {}

    # ------------------------------------------------------------------ layout
    def adopt(self, tiles):
        """Take over a farm built by someone else: roles follow what is on each tile."""
        kind2 = {"COOP": "GOOSE"}
        for y in range(BOARD):
            for x in range(BOARD):
                t = tiles[y][x]
                if isinstance(t, dict):
                    if "animal" in t:
                        self.roles[(x, y)] = t["animal"]
                    elif t.get("kind") == "PLANT":
                        self.roles[(x, y)] = t["crop"]
                    elif t.get("kind") == "COOP":
                        self.roles[(x, y)] = "GOOSE"
                    elif t.get("kind") == "PASTURE":
                        self.roles[(x, y)] = "COW"

    def _roles_for(self, quads):
        for q in quads:
            tl = quad_tiles(q)
            if tl[0] in self.roles:
                continue
            spec = self.cfg["layout"].get(q, [])
            roles = []
            for r, n in spec:
                roles += [r] * n
            roles += ["WHEAT"] * (len(tl) - len(roles))
            for p, r in zip(tl, roles):
                self.roles[p] = r

    # ------------------------------------------------------------------ feeding policy
    def _feed_today(self, t, day, prices):
        if t["fed_today"]:
            return False
        if t["consecutive_unfed"] >= 1:
            return True
        a = ANIMALS[t["animal"]]
        dsf = day + 1 - t["placed_day"] - a["fyd"]
        if dsf < -1:
            return False                      # young: feed every other day only
        worth = prices.get(a["prod"], 0) > self.cfg["feed_margin"] * prices.get("WHEAT", 30)
        if worth:
            return True
        return dsf >= 0 and dsf % a["iv"] == 0  # production day: feed so the care bonus lands

    # ------------------------------------------------------------------ main
    def act(self, obs):
        step = int(obs["step"])
        if step <= self.last_step or step == 0:
            self.reset()
        self.last_step = step
        cfg = self.cfg
        me = int(obs["player"])
        farm = obs["farms"][me]
        priv = obs["private"]
        prices = obs["market"]["prices"]
        day, hour = step // 24, step % 24
        final_day = day >= 29
        tiles = farm["tiles"]
        shed = dict(priv["shed"])
        seeds = dict(priv["seeds"])
        invs = priv["inventories"]
        money = float(farm["money"])
        self._roles_for(farm["unlocked_quadrants"])
        units = [tuple(farm["farmer"])] + [tuple(h) for h in farm["hands"]]
        carried = {}
        for inv in invs:
            for k, v in inv.items():
                carried[k] = carried.get(k, 0) + v
        p_wheat = prices.get("WHEAT", 30)
        p_fert = prices.get("FERTILIZER", 50)

        # ---------------------------------------------------------- census
        animals, plants = [], []
        empty_st = {}
        for y in range(BOARD):
            for x in range(BOARD):
                t = tiles[y][x]
                if isinstance(t, dict):
                    if "animal" in t:
                        animals.append(((x, y), t))
                    elif t.get("kind") == "PLANT":
                        plants.append(((x, y), t))
                    elif t.get("kind") in ("COOP", "PASTURE"):
                        r = self.roles.get((x, y))
                        if r in ANIMALS:
                            empty_st.setdefault(r, []).append((x, y))
        n_anim = len(animals)
        waiting = {a: shed.get(a, 0) + carried.get(a, 0) for a in ANIMALS}

        # ---------------------------------------------------------- tasks
        tasks = []  # (pos, action, priority, need)
        plant_need = {}
        feeds_today = 0
        for p, t in animals:
            a = ANIMALS[t["animal"]]
            if not final_day and self._feed_today(t, day, prices):
                feeds_today += 1
                tasks.append((p, ["FEED"], 99 if t["consecutive_unfed"] >= 1 else 92, "WHEAT"))
                goose_alt = t["animal"] == "GOOSE" and prices.get("EGG", 0) <= cfg["feed_margin"] * p_wheat
                if not t["cared_today"] and not goose_alt:
                    tasks.append((p, ["CARE"], 84, None))
            elif t["fed_today"] and not t["cared_today"] and not final_day and t["animal"] != "GOOSE":
                tasks.append((p, ["CARE"], 84, None))
            if t.get("fertilizer_available"):
                tasks.append((p, ["COLLECT_FERTILIZER"], 70, None))
            if t["yield_units"] > 0 and (t["yield_units"] >= 2 or final_day or day >= 28):
                full = t["yield_units"] >= a["held"] - 1
                tasks.append((p, ["HARVEST"], 88 if full or final_day else 62, None))
        for p, t in plants:
            cd = CROPS[t["crop"]]
            age = day - t["planted_day"]
            yu = t.get("yield_units", 0)
            if cd["on"] and t.get("max_lifespan_step", -1) >= 0 and yu <= 0:
                tasks.append((p, ["DIG"], 60, None))     # spent ongoing crop: clear for replant
                continue
            if not t["watered_today"] and not final_day:
                tasks.append((p, ["WATER"], 96 if t["consecutive_unwatered"] >= 1 else 80, None))
            if not final_day and t.get("fertilized_until_day", -1) < day:
                gain = self._fert_gain(t, cd, age, yu)
                if t["crop"] == "MELON" and (cd["myd"] + 1) // 2 <= age < cd["myd"] and yu < cd["my"]:
                    gain = max(gain, 1)
                if gain > 0 and gain * prices.get(t["crop"], 0) > cfg["fert_mult"] * p_fert:
                    tasks.append((p, ["FERTILIZE"], 83, "FERTILIZER"))
            if yu > 0 and age >= cd["fyd"]:
                if cd["on"]:
                    last = t.get("max_lifespan_step", -1) >= 0
                    if yu >= 2 or last or final_day or day >= 28:
                        tasks.append((p, ["HARVEST"], 86 if last else 66, None))
                elif final_day or yu >= cd["my"] or (age >= cd["myd"] and t["watered_today"]) or age > cd["myd"]:
                    tasks.append((p, ["HARVEST"], 86, None))
        # structures, planting, weeds on role tiles
        n_struct_needed = {a: max(0, waiting[a] - len(empty_st.get(a, []))) for a in ANIMALS}
        for p, role in self.roles.items():
            x, y = p
            t = tiles[y][x]
            if t == "LOCKED":
                continue
            if isinstance(t, dict) and t.get("kind") == "WEED":
                tasks.append((p, ["DIG"], 64, None))
                continue
            if t is not None:
                continue
            if role in ANIMALS:
                a = ANIMALS[role]
                if day + a["fyd"] + 4 <= 29:
                    tasks.append((p, ["BUILD_" + a["st"]], 66, None))
                continue
            if final_day:
                continue
            crop = crop_for(role, day)
            if crop is None:
                continue
            plant_need[crop] = plant_need.get(crop, 0) + 1
            tasks.append((p, ["PLANT", crop], 76, "SEED:" + crop))
        for a, ps in empty_st.items():
            for p in ps:
                tasks.append((p, ["PLACE", a], 94, a))

        # ---------------------------------------------------------- money
        sells = []
        cash = money
        feed_keep = feeds_today + n_anim + 4
        fert_keep = sum(1 for tk in tasks if tk[1][0] == "FERTILIZE")
        for item in PRODUCTS:
            have = shed.get(item, 0)
            keep = feed_keep if item == "WHEAT" else (fert_keep if item == "FERTILIZER" else 0)
            q = have - min(have, keep)
            if q > 0 and prices.get(item, 0) > 1:
                sells.append(["SELL", item, q])
                cash += q * prices[item] * 0.85
        idle_roles = sum(1 for p, r in self.roles.items()
                         if tiles[p[1]][p[0]] is None or (isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get("kind") == "WEED"))
        want_h = self._want_hands(n_anim, len(plants), idle_roles)
        reserve = n_anim * p_wheat + 40 + (fib_sum(want_h) if hour > 3 else 0)
        spend = []
        hires = []
        if hour <= 3 and not final_day:
            have_h = int(farm.get("hires_today", 0))
            h = want_h
            while h > have_h and fib_sum(h) - fib_sum(have_h) > cash * 0.4:
                h -= 1
            n_new = max(0, h - have_h)
            hires = [["HIRE"]] * n_new
            cash -= fib_sum(have_h + n_new) - fib_sum(have_h)
        wheat_have = shed.get("WHEAT", 0) + carried.get("WHEAT", 0)
        need_w = feeds_today + n_anim // 2 - wheat_have
        if not final_day and need_w > 0:
            q = int(min(need_w, max(0, cash - 10) // (p_wheat + 2)))
            if q > 0:
                spend.append(["BUY_PRODUCT", "WHEAT", q])
                cash -= q * (p_wheat + 2)
        # seeds (cheap first)
        for crop in sorted(plant_need, key=lambda c: CROPS[c]["seed"]):
            q = plant_need[crop] - seeds.get(crop, 0)
            if q > 0:
                q = int(min(q, max(0, cash - reserve * 0.5) // CROPS[crop]["seed"]))
                if q > 0:
                    spend.append(["BUY_SEED", crop, q])
                    cash -= q * CROPS[crop]["seed"]
        # animals for built, empty structures
        for a in ("SHEEP", "COW", "GOOSE"):
            slots = len(empty_st.get(a, [])) - waiting[a]
            if slots <= 0 or day + ANIMALS[a]["fyd"] + 4 > 29:
                continue
            q = int(min(slots, max(0, cash - reserve) // ANIMALS[a]["cost"]))
            if q > 0:
                spend.append(["BUY_ANIMAL", a, q])
                cash -= q * ANIMALS[a]["cost"]
        # land
        n_extra = len(farm["unlocked_quadrants"]) - 1
        if n_extra < 3 and day <= 18 and day >= cfg["land_days"][n_extra]:
            price = LAND_PRICES[n_extra]
            if cash - reserve > price + cfg["land_buffer"]:
                spend.append(["BUY_LAND"])
                cash -= price

        # ---------------------------------------------------------- assignment
        if self.seg_key != (day, len(units)):
            self.seg_key = (day, len(units))
            self.owner = self._segments(tiles, units)
        claimed = set()
        seed_left = dict(seeds)
        for o in spend:
            if o[0] == "BUY_SEED":
                pass  # bought seeds arrive after this step's actions
        shed_left = dict(shed)
        seg_need = {}
        for tk in tasks:
            if tk[3] in ("WHEAT", "FERTILIZER"):
                o = self.owner.get(tk[0], -1)
                seg_need[(o, tk[3])] = seg_need.get((o, tk[3]), 0) + 1
        place_open = {a: len(ps) for a, ps in empty_st.items()}
        actions = []
        steps_left = 23 - hour
        dc = cfg["dist_cost"]
        for ui, pos in enumerate(units):
            inv = dict(invs[ui]) if ui < len(invs) else {}
            prev = self.tgt.get(ui) if hour > 0 else None
            best, bscore = None, -1e9
            for ti, (p, act, pr, need) in enumerate(tasks):
                if ti in claimed:
                    continue
                if need in ("WHEAT", "FERTILIZER") or need in ANIMALS:
                    if inv.get(need, 0) <= 0:
                        continue
                elif need and seed_left.get(need[5:], 0) <= 0:
                    continue
                d = dist(pos, p)
                if d > steps_left:
                    continue
                sc = pr - dc * d
                if self.owner.get(p) == ui or act[0] == "PLACE":
                    sc += cfg["own_bonus"]
                if prev is not None and prev == (p, act[0]):
                    sc += 15
                if sc > bscore:
                    best, bscore = ti, sc
            acc = min(ACCESS, key=lambda q: dist(pos, q))
            dacc = dist(pos, acc)
            shed_act, shed_pr = None, -1e9
            if final_day and hour >= 16 and sum(inv.values()) > 0:
                shed_act, shed_pr = ["DROP"], 400
            else:
                for a in ANIMALS:
                    if shed_left.get(a, 0) > 0 and place_open.get(a, 0) > 0 and inv.get(a, 0) <= 0:
                        shed_act, shed_pr = ["PICKUP", a, min(shed_left[a], place_open[a], 4)], 96 + cfg["own_bonus"]
                        break
                if shed_act is None:
                    for item in ("WHEAT", "FERTILIZER"):
                        n = seg_need.get((ui, item), 0)
                        if n > 0 and inv.get(item, 0) <= 0 and shed_left.get(item, 0) > 0:
                            shed_act = ["PICKUP", item, min(shed_left[item], n + 1)]
                            shed_pr = (97 if item == "WHEAT" else 80) + cfg["own_bonus"]
                            break
            if shed_act is not None and shed_pr - dc * dacc > bscore:
                if dacc == 0:
                    actions.append(shed_act)
                    if shed_act[0] == "PICKUP":
                        shed_left[shed_act[1]] -= shed_act[2]
                        if shed_act[1] in ANIMALS:
                            place_open[shed_act[1]] -= shed_act[2]
                else:
                    actions.append(self._move(pos, acc))
                continue
            if best is None:
                actions.append(["PASS"])
                continue
            claimed.add(best)
            p, act, pr, need = tasks[best]
            self.tgt[ui] = (p, act[0]) if pos != p else None
            if need and need.startswith("SEED:"):
                seed_left[need[5:]] -= 1
            actions.append(list(act) if pos == p else self._move(pos, p))

        room = max(0, 10 - len(sells) - len(spend))
        market = (sells + spend + hires[:room])[:10]
        if DEBUG is not None:
            st = DEBUG.setdefault(day, {"pass": 0, "move": 0, "work": 0})
            for a in actions:
                k = "pass" if a[0] == "PASS" else ("move" if a[0] in ("NORTH", "SOUTH", "EAST", "WEST") else "work")
                st[k] += 1
            if hour == 23:
                st["unfed2"] = sum(1 for _, t in animals if not t["fed_today"] and t["consecutive_unfed"] >= 1)
                st["unwatered"] = sum(1 for _, t in plants if not t["watered_today"])
                st["units"] = len(units)
                st["money"] = int(money)
        return {"farmer": actions[0], "hands": actions[1:], "market": market}

    @staticmethod
    def _fert_gain(t, cd, age, yu):
        if cd["on"]:
            gain = 0
            for k in range(3):
                a2 = age + k
                n = a2 + 1 - cd["fyd"]
                if n >= 0 and n % cd["iv"] == 0 and n // cd["iv"] + 1 <= cd["my"]:
                    gain += 1
            return gain
        lo = (cd["myd"] + 1) // 2
        if age > cd["myd"]:
            return 0
        rem = max(0, cd["myd"] - max(age, lo) + 1)
        base = min(cd["my"], yu + rem)
        extra = min(cd["my"], yu + rem + min(3, rem))
        return extra - base

    def _want_hands(self, n_anim, n_plants, idle=0):
        work = n_anim * 4.0 + n_plants * 2.0 + idle * 2.5 + 10
        return max(1, min(self.cfg["hands_max"], int(math.ceil(work / 20.0)) - 1))

    def _segments(self, tiles, units):
        path = []
        for q in ("NW", "NE", "SE", "SW"):
            ax, ay = QUADS[q]
            xs = list(range(0, HALF)) if q[1] == "W" else list(range(HALF, BOARD))
            ys = list(range(0, HALF)) if q[0] == "N" else list(range(HALF, BOARD))
            if ax == xs[-1]:
                xs = xs[::-1]
            if ay == ys[-1]:
                ys = ys[::-1]
            for i, y in enumerate(ys):
                for x in (xs if i % 2 == 0 else xs[::-1]):
                    t = tiles[y][x]
                    if t == "LOCKED":
                        continue
                    if isinstance(t, dict) and "animal" in t:
                        w = 3.5
                    elif isinstance(t, dict) and t.get("kind") == "PLANT":
                        w = 2.0
                    else:
                        w = 1.5
                    path.append(((x, y), w))
        total = sum(w for _, w in path) or 1.0
        n = max(1, len(units))
        per = total / n
        chunks, cur, acc = [], [], 0.0
        for p, w in path:
            cur.append(p)
            acc += w
            if acc >= per * (len(chunks) + 1) and len(chunks) < n - 1:
                chunks.append(cur)
                cur = []
        chunks.append(cur)
        owner, free = {}, list(range(n))
        for ch in chunks:
            if not ch or not free:
                continue
            u = min(free, key=lambda i: dist(units[i], ch[0]))
            free.remove(u)
            for p in ch:
                owner[p] = u
        return owner

    @staticmethod
    def _move(pos, target):
        dx, dy = target[0] - pos[0], target[1] - pos[1]
        if dx:
            return [MOVES[(1 if dx > 0 else -1, 0)]]
        if dy:
            return [MOVES[(0, 1 if dy > 0 else -1)]]
        return ["PASS"]


DEBUG = {} if os.environ.get("BEAST_DEBUG") else None
_AGENTS = {}


def agent(observation, configuration=None):
    try:
        p = int(observation["player"])
        b = _AGENTS.get(p)
        if b is None:
            b = _AGENTS[p] = Beast()
        return b.act(observation)
    except Exception:
        import traceback
        traceback.print_exc()
        return {"farmer": ["PASS"], "hands": [], "market": []}
