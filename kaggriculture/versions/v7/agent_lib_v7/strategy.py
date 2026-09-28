"""Top-level orchestration: builds the tile layout, decides the day's Plan,
and drives tasks -> scheduler -> trader -> validator into a final action dict.
Every stage is wrapped so a failure degrades gracefully instead of raising."""
from . import economics, geometry as geo, market_model as mm, scheduler, tasks, trader, validator
from .constants import ANIMALS, CROPS, CROP_BASE_PRICE, ANIMAL_PRODUCT_BASE_PRICE
from .memory import Memory
from .state import parse

ENDGAME_TURNS = 36          # last 1.5 days: full liquidation, stop new investment
LATE_TURNS = 96             # last 4 days: stop planting things that won't mature, taper hiring
# Wheat is the fastest crop (first_yield_day=2 -> 48 turns) plus enough slack to
# actually walk to the tile, water it, harvest, walk back and sell before the
# game ends. Below this, planting anything new is pure waste (seed cost with
# no chance of a harvest, and a unit-turn spent walking there for nothing).
PLANT_CUTOFF_TURNS = 60
ANIMAL_TILE_CAP_PER_QUADRANT = 3
PEN_BUFFER = 2   # coops/pastures pre-built ahead of the current animal target


# Per-tile-day profit estimates assume we can sell every unit at the current
# quoted price, which is only true in the limit of a single tile. Selling at
# volume (many tiles of the same crop) crashes the price, especially for
# low-T premium goods (melon/strawberry/wool) whose naive estimate would
# otherwise dwarf everything else and starve the crop mix of diversity /
# fast-cycling staples. Clip before using the estimate for any allocation
# decision so one crop can't dominate purely from a stale single-tile figure.
CROP_PROFIT_CAP = 30.0
MAX_CROP_SHARE = 0.35


def _capped_profit(crop, price):
    return min(CROP_PROFIT_CAP, economics.crop_profit_per_tile_day(crop, price))


def _crop_weights(state):
    weights = {}
    for crop in CROPS:
        price = state.prices.get(crop, CROP_BASE_PRICE[crop])
        weights[crop] = max(0.05, _capped_profit(crop, price))
    total = sum(weights.values()) or 1.0
    weights = {c: w / total for c, w in weights.items()}
    # Cap any single crop's share and redistribute the excess proportionally.
    excess = 0.0
    for c, w in weights.items():
        if w > MAX_CROP_SHARE:
            excess += w - MAX_CROP_SHARE
            weights[c] = MAX_CROP_SHARE
    if excess > 0:
        under = {c: w for c, w in weights.items() if w < MAX_CROP_SHARE}
        under_total = sum(under.values()) or 1.0
        for c in under:
            weights[c] += excess * (under[c] / under_total)
    return weights


def _assign_crop_roles(tiles, weights):
    n = len(tiles)
    if n == 0:
        return {}
    counts = {c: int(w * n) for c, w in weights.items()}
    remainder = n - sum(counts.values())
    order_by_frac = sorted(weights.items(), key=lambda kv: -(kv[1] * n - int(kv[1] * n)))
    i = 0
    while remainder > 0:
        c = order_by_frac[i % len(order_by_frac)][0]
        counts[c] += 1
        remainder -= 1
        i += 1
    pools = dict(counts)
    order = []
    while sum(pools.values()) > 0:
        for c in CROPS:
            if pools.get(c, 0) > 0:
                order.append(c)
                pools[c] -= 1
    return {t: c for t, c in zip(tiles, order)}


def _placed_animal_counts(state):
    counts = {"GOOSE": 0, "COW": 0, "SHEEP": 0}
    for row in state.tiles:
        for tile in row:
            if isinstance(tile, dict) and tile.get("animal") in counts:
                counts[tile["animal"]] += 1
    return counts


def _animal_targets(state, memory):
    """Day-based schedule gives an *upper bound* on how many of each animal
    we're willing to commit tiles to (keeps the mix sane early game before
    there's real price data); economics.should_buy_animal (current market
    price vs. feed cost vs. days left) gates whether we actually grow toward
    that bound this turn. Already-committed tiles are never abandoned even if
    ROI has since soured — ripping out a live animal for a stale estimate
    would be worse than just not adding another.

    The ramp shape (cow/sheep from day 0, goose from ~day 5, all approaching
    ~9 by day 10-12) is calibrated against a real ladder replay between the
    #1 and #2 ranked agents (episode 111645359, engine 1.32.7): both bought
    their first cows and sheep in the first few turns of day 0 (2-3 cows,
    3 sheep, 5-6 pastures built immediately), not day 5+ as an earlier,
    unvalidated version of this schedule assumed — confirmed independently
    against our own economics.should_buy_animal, which already approves all
    three animal types at day-0 base prices with a full season ahead
    (payback ~9-12 days vs. 30 days left). That earlier cap was pure
    self-inflicted conservatism with no economic basis. Physical tile
    availability (ensure_animal_tiles only reserves from currently-unlocked
    land) naturally throttles this further before land is bought, so no
    quadrant-count multiplier is needed here."""
    day = state.day
    day_caps = {
        "COW": min(9, 2 + day),
        "SHEEP": min(9, 3 + day // 2),
        "GOOSE": min(9, max(0, day - 4)),
    }
    # Freeze the buy target at animals *actually placed on the board* when
    # ROI turns unfavorable — not at memory.animal_tiles' raw tile count,
    # which runs ahead of that (see PEN_BUFFER: a few pens are pre-built
    # before their animals are bought, and that reserved-but-empty slack
    # must never leak into how many animals trader.py tries to buy).
    already = _placed_animal_counts(state)

    wheat_price = state.prices.get("WHEAT", 25)
    targets = {}
    for animal, cap in day_caps.items():
        product = ANIMALS[animal]["product"]
        price = state.prices.get(product, ANIMAL_PRODUCT_BASE_PRICE[product])
        favorable = economics.should_buy_animal(animal, price, wheat_price, state.turns_left, state.turns_per_day)
        targets[animal] = cap if favorable else already.get(animal, 0)
    return targets


def ensure_animal_tiles(state, memory):
    targets = _animal_targets(state, memory)
    memory.animal_targets = targets
    if state.turns_left < LATE_TURNS:
        return  # stop committing new tiles to animals once too little season remains

    have = {"GOOSE": 0, "COW": 0, "SHEEP": 0}
    for animal in memory.animal_tiles.values():
        have[animal] = have.get(animal, 0) + 1

    all_tiles = []
    for q in state.unlocked_quadrants:
        all_tiles.extend(geo.quadrant_tiles(q, state.board_size))
    shed_tiles = set(geo.shed_access_tiles(state.board_size))
    all_tiles.sort(key=lambda t: (geo.manhattan(t, geo.nearest_shed_tile(t, state.board_size)), t))

    # Building a coop/pasture costs a turn but zero money — pre-building a
    # couple ahead of the current animal target means a bought animal never
    # has to wait on pen construction before it can be placed. An empty pen
    # is a cheap option, not waste (confirmed against the worst measured
    # change in the source notes: gating pen-building on a cash cushion).
    used = set(memory.animal_tiles.keys())
    for animal, target in targets.items():
        need = (target + PEN_BUFFER) - have.get(animal, 0)
        if need <= 0:
            continue
        for t in all_tiles:
            if need <= 0:
                break
            if t in used or t in shed_tiles:
                continue
            tile = state.tiles[t[1]][t[0]] if t[1] < len(state.tiles) and t[0] < len(state.tiles[t[1]]) else "LOCKED"
            if tile != "LOCKED" and tile is not None:
                continue  # already occupied by something else; leave it
            memory.animal_tiles[t] = animal
            used.add(t)
            need -= 1


def build_layout(state, memory):
    if not hasattr(memory, "animal_tiles"):
        memory.animal_tiles = {}
    ensure_animal_tiles(state, memory)

    layout = {}
    for (x, y), animal in memory.animal_tiles.items():
        structure = ANIMALS[animal]["structure"]
        layout[(x, y)] = {"role": structure, "animal": animal}

    all_tiles = []
    for q in state.unlocked_quadrants:
        all_tiles.extend(geo.quadrant_tiles(q, state.board_size))
    crop_tiles = [t for t in all_tiles if t not in memory.animal_tiles]
    crop_tiles.sort(key=lambda t: (geo.manhattan(t, geo.nearest_shed_tile(t, state.board_size)), t))

    if state.turns_left < PLANT_CUTOFF_TURNS:
        crop_roles = {}  # too late for anything new to mature; tend/sell existing crops only
    elif state.turns_left < LATE_TURNS:
        # Only short-cycle crops (wheat/carrot) can still fit a full cycle in.
        weights = {"WHEAT": 0.6, "CARROT": 0.4, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0}
        crop_roles = _assign_crop_roles(crop_tiles, weights)
    else:
        crop_roles = _assign_crop_roles(crop_tiles, _crop_weights(state))

    for t, crop in crop_roles.items():
        layout[t] = {"role": "CROP", "crop": crop}

    memory.layout = layout


# Real-ladder-informed caps (see NOTES.md "v6" entry): top agents run roughly
# 12-14 hands; the 14th/15th cost ~$610/$987 (fib growth), so cap just past
# where a full board can plausibly keep everyone busy. Each unit is assumed
# to productively cover about TILES_PER_UNIT tiles/day (movement + one action
# per turn budget); a farm that owes more work than hands can reach is a
# reason to *not* buy more land, not a reason to hire past the point it pays.
TILES_PER_UNIT = 6
HANDS_CAP = 13
LAND_WORKLOAD_RATIO_CAP = 1.35   # refuse new land once owed-work/capacity exceeds this
HIRE_CUTOFF_HOUR = 20            # don't start new hires with under ~4 hours left in the day


def decide_plan(state, memory):
    turns_left = state.turns_left
    liquidation = turns_left <= ENDGAME_TURNS
    late = turns_left <= LATE_TURNS

    # Use planned tile count (not just currently-occupied ones) so hiring
    # bootstraps from day 0 instead of waiting for tiles to already be busy.
    n_planned = len(memory.layout)
    hands_target = 0 if liquidation else max(0, min(HANDS_CAP, n_planned // TILES_PER_UNIT))
    if late and not liquidation:
        hands_target = min(hands_target, 3)
    if state.hour >= HIRE_CUTOFF_HOUR:
        # Don't grow the target this late in the day — a hand hired now gets
        # too few turns to earn back even the cheap early fib cost, and
        # vanishes at midnight regardless.
        hands_target = min(hands_target, state.hires_today)

    buy_land = False
    if not late and state.day >= 4 and state.money > 0:
        n_extra = len(state.unlocked_quadrants) - 1
        capacity = (1 + hands_target) * TILES_PER_UNIT
        workload_ratio = (n_planned / capacity) if capacity > 0 else float("inf")
        if workload_ratio <= LAND_WORKLOAD_RATIO_CAP:
            avg_profit = 0.0
            weights = _crop_weights(state)
            for crop, w in weights.items():
                avg_profit += w * _capped_profit(crop, state.prices.get(crop, CROP_BASE_PRICE[crop]))
            if n_extra < 3:
                from .constants import LAND_PRICES
                cost = LAND_PRICES[n_extra]
                if state.money >= cost * 1.5 and economics.should_buy_land(n_extra, state.money, avg_profit, turns_left, state.turns_per_day):
                    buy_land = True

    return {
        "liquidation": liquidation,
        "late": late,
        "hands_target": hands_target,
        "buy_land": buy_land,
        "animal_targets": memory.animal_targets,
        "sell_min_fraction": 0.30,
    }


class Brain:
    def __init__(self, config=None):
        self.memory = Memory()
        self.config = config

    def act(self, obs):
        memory = self.memory
        try:
            state = parse(obs, self.config)
        except Exception as e:
            memory.note_error("parse", e)
            from .safe_agent import safe_action
            return safe_action(obs)

        try:
            memory.update(state)
        except Exception as e:
            memory.note_error("memory", e)

        try:
            if state.hour == 0 or not memory.layout:
                build_layout(state, memory)
        except Exception as e:
            memory.note_error("layout", e)
            memory.layout = memory.layout or {}

        try:
            plan = decide_plan(state, memory)
        except Exception as e:
            memory.note_error("plan", e)
            plan = {"liquidation": state.turns_left <= ENDGAME_TURNS, "late": False,
                    "hands_target": 0, "buy_land": False, "animal_targets": {}, "sell_min_fraction": 0.3}

        try:
            task_lists = tasks.generate(state, memory)
        except Exception as e:
            memory.note_error("tasks", e)
            task_lists = {"water": [], "harvest_plant": [], "harvest_animal": [], "feed": [],
                          "collect_fert": [], "care": [], "dig_weed": [], "build_coop": [],
                          "build_pasture": [], "plant": [], "empty_structures": []}

        try:
            unit_actions = scheduler.assign(state, task_lists, memory)
        except Exception as e:
            memory.note_error("scheduler", e)
            unit_actions = {u.uid: ["PASS"] for u in state.units}

        try:
            market_orders = trader.orders(state, plan, memory)
        except Exception as e:
            memory.note_error("trader", e)
            market_orders = []

        farmer_action = unit_actions.get(0, ["PASS"])
        hand_actions = [unit_actions.get(i + 1, ["PASS"]) for i in range(len(state.units) - 1)]

        try:
            farmer_action, hand_actions, market_orders = validator.finalize(
                state, farmer_action, hand_actions, market_orders
            )
        except Exception as e:
            memory.note_error("validator", e)
            farmer_action, hand_actions, market_orders = ["PASS"], [["PASS"] for _ in hand_actions], []

        return {"farmer": farmer_action, "hands": hand_actions, "market": market_orders}
