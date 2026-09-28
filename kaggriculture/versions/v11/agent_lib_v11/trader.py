"""Builds the market order list: hire, land, seed/animal restocking, wheat
purchase for feed shortfall, and produce liquidation. Capped at
state.max_market_orders (extras would be silently dropped by the env anyway,
but we prioritize explicitly so the *right* orders survive the cap)."""
from . import market_model as mm
from .constants import ANIMALS, CROPS, CROP_BASE_PRICE, ANIMAL_PRODUCT_BASE_PRICE, PRICE_FLOOR, hire_cost

OPPONENT_PRESSURE_THRESHOLD = 3  # opponent tiles/animals of a product before we treat it as a glut risk

SEED_BUFFER = 8          # keep enough seed in stock that several units planting in parallel
                          # never race the shared pool down to zero before they arrive
WHEAT_FEED_BUFFER = 4     # extra wheat to keep beyond today's exact feed need
SHED_PRESSURE_START = 75  # start selling more aggressively once shed total passes this


def _base_price(item):
    return CROP_BASE_PRICE.get(item) or ANIMAL_PRODUCT_BASE_PRICE.get(item) or 100


def _occupied_animal_count(state):
    n = 0
    for row in state.tiles:
        for tile in row:
            if isinstance(tile, dict) and "animal" in tile:
                n += 1
    return n


def _crop_demand_from_layout(memory):
    demand = {}
    for role in memory.layout.values():
        if role.get("role") == "CROP":
            demand[role["crop"]] = demand.get(role["crop"], 0) + 1
    return demand


def _opponent_pressure(state):
    """Rough proxy for upcoming supply from the opponent's *visible* farm
    (tiles are public; their shed is not). A product the opponent is growing
    a lot of is a product whose price is likely to crash soon when they
    harvest and dump it — better to sell ours a bit earlier/cheaper than to
    hold out for a price that won't be there."""
    counts = {}
    for row in state.opp_tiles:
        for tile in row:
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") == "PLANT":
                counts[tile["crop"]] = counts.get(tile["crop"], 0) + 1
            elif "animal" in tile:
                product = ANIMALS[tile["animal"]]["product"]
                counts[product] = counts.get(product, 0) + 1
    return counts


def orders(state, plan, memory):
    out = []
    money = state.money
    max_orders = state.max_market_orders

    # 1. Hire, up to plan.hands_target additional hires today. Processed
    # first and gated only by plain affordability (not some fraction of
    # cash) so it effectively reserves its own budget before seeds/animals
    # get a turn at the money below — a real top-ladder replay (episode
    # 111645359: #1 vs #2 on the live leaderboard) kept 6-8 hands even with
    # the bank near zero, which a "don't spend more than 50% of cash on
    # hands" guard would silently prevent once money got low (fib cost for
    # even a 13th hand is only $233 in absolute terms; at near-zero cash
    # that's still "more than half", but it's cheap and labor is what
    # actually generates the next dollar). Confirmed this guard was exactly
    # why hand count was oscillating 5->2->5 in early local testing.
    hires_wanted = max(0, plan.get("hands_target", 0) - state.hires_today)
    n_today = state.hires_today
    for _ in range(hires_wanted):
        cost = hire_cost(n_today, state.farm_hand_cost_mult)
        if cost > money:
            break
        out.append(["HIRE"])
        money -= cost
        n_today += 1
        if len(out) >= max_orders:
            return out[:max_orders]

    # 2. Land purchase.
    if plan.get("buy_land") and len(out) < max_orders:
        out.append(["BUY_LAND"])
        # cost deducted implicitly; exact amount not needed further here

    # 3. Seed restocking, based on layout demand.
    demand = _crop_demand_from_layout(memory)
    for crop, tiles_wanted in sorted(demand.items(), key=lambda kv: -kv[1]):
        if len(out) >= max_orders:
            break
        have = state.seeds.get(crop, 0)
        target = min(SEED_BUFFER, max(2, tiles_wanted))
        if have < target:
            cost_each = CROPS[crop]["seed"]
            n = target - have
            afford_n = int(money // max(1, cost_each))
            n = min(n, afford_n)
            if n > 0:
                out.append(["BUY_SEED", crop, n])
                money -= n * cost_each

    # 4. Animal restocking toward plan.animal_targets, one at a time (avoid shed
    #    overflow / big single-turn spend). Capped by pens *actually built*
    #    for that animal (plus a small allowance so the next purchase is
    #    ready the moment a pen finishes) — NOT by the raw day-based target
    #    or even by reserved-but-unbuilt tile coordinates, either of which
    #    can outrun how fast units can physically build pens and strand
    #    bought animals in the shed with nowhere to go (caught by
    #    tests/test_livestock_delivery.py; a reserved-tiles-only cap still
    #    let the backlog climb past 15 because building itself was the
    #    bottleneck, not land availability).
    if len(out) < max_orders:
        built_pens = _built_pen_counts(state, memory)
        for animal, target in plan.get("animal_targets", {}).items():
            have = state.shed.get(animal, 0) + _placed_count(state, animal)
            cap = min(target, built_pens.get(animal, 0) + 1)
            if have < cap:
                # Stop at the FIRST under-target animal in priority order
                # (dict order: COW, SHEEP, GOOSE — see strategy._animal_targets)
                # regardless of whether we can afford it this turn. Falling
                # through to a cheaper animal when a pricier one is merely
                # unaffordable right now silently inverts the intended mix —
                # a self-play autopsy against a real top-ladder replay
                # (episode 111645359) caught exactly this: goose (cheapest,
                # $300) got bought nearly 2x as often as cow ($400) because
                # goose purchases kept succeeding during the exact stretch
                # of the game when money was tightest, while DSM/Majkel ran
                # cow-heavy (12/8 cow vs 9/6 goose) the whole game.
                cost = ANIMALS[animal]["cost"]
                if money >= cost and sum(state.shed.values()) < state.shed_capacity:
                    out.append(["BUY_ANIMAL", animal, 1])
                    money -= cost
                break

    # 5. Wheat purchase for feed shortfall (only if we're not self-sufficient).
    if len(out) < max_orders:
        animals_needing_feed = _occupied_animal_count(state)
        have_wheat = state.shed.get("WHEAT", 0)
        needed = animals_needing_feed + WHEAT_FEED_BUFFER
        if animals_needing_feed > 0 and have_wheat < needed:
            price = state.prices.get("WHEAT", 25)
            if price <= 35:  # only buy back wheat when it's still cheap
                n = min(needed - have_wheat, int(money // max(1, price)))
                if n > 0:
                    out.append(["BUY_PRODUCT", "WHEAT", n])
                    money -= n * price

    # 6. Sell shed stock.
    shed_total = sum(state.shed.values())
    liquidation = plan.get("liquidation", False)
    opp_pressure = _opponent_pressure(state) if not liquidation else {}
    for item, have in sorted(state.shed.items(), key=lambda kv: -kv[1]):
        if len(out) >= max_orders:
            break
        if have <= 0 or item not in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"):
            continue
        inv = state.market_inventory.get(item, 10000)
        params = state.market_params
        if liquidation:
            min_price = PRICE_FLOOR
            n = have
        else:
            base = _base_price(item)
            frac = plan.get("sell_min_fraction", 0.35)
            if shed_total > SHED_PRESSURE_START:
                frac *= 0.5
            if opp_pressure.get(item, 0) >= OPPONENT_PRESSURE_THRESHOLD:
                # Opponent is growing a lot of this too; race to sell before
                # their harvest/dump crashes the price for both of us.
                frac *= 0.6
            min_price = max(PRICE_FLOOR, int(base * frac))
            n = mm.best_sell_count(item, have, inv, min_price, params)
            # keep a small working buffer of wheat for feed instead of selling it all
            if item == "WHEAT":
                n = min(n, max(0, have - WHEAT_FEED_BUFFER))
        if n > 0:
            out.append(["SELL", item, n])

    return out[:max_orders]


def _built_pen_counts(state, memory):
    """Pens physically standing on the board for each animal type (occupied
    or not), keyed off memory.animal_tiles so a pen still counts toward its
    intended animal even before anything is placed on it."""
    counts = {}
    for (x, y), animal in memory.animal_tiles.items():
        if y >= len(state.tiles) or x >= len(state.tiles[y]):
            continue
        tile = state.tiles[y][x]
        if isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE"):
            counts[animal] = counts.get(animal, 0) + 1
    return counts


def _placed_count(state, animal):
    n = 0
    for row in state.tiles:
        for tile in row:
            if isinstance(tile, dict) and tile.get("animal") == animal:
                n += 1
    return n
