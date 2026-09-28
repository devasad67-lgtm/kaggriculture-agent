"""Final sanity pass: replace illegal unit actions with PASS, trim/clean market
orders to the per-turn cap and drop anything unaffordable or malformed. Invalid
actions are silent no-ops in the env anyway, so this mainly guards against
wasting turns/orders on obviously-broken output from earlier stages, and
against exceptions from malformed action shapes."""
from .constants import ANIMALS, CROPS
from .state import tile_at


def _valid_unit_action(state, unit, action):
    if not isinstance(action, list) or not action:
        return False
    op = action[0]
    if op in ("NORTH", "SOUTH", "EAST", "WEST", "PASS", "DROP"):
        return True
    if op == "PICKUP":
        return len(action) >= 2 and isinstance(action[1], str)
    if op == "PLACE":
        return len(action) >= 2 and isinstance(action[1], str)
    tile = tile_at(state, unit.x, unit.y)
    if op == "PLANT":
        if len(action) < 2 or action[1] not in CROPS:
            return False
        return tile is None and state.seeds.get(action[1], 0) > 0
    if op == "WATER":
        return isinstance(tile, dict) and tile.get("kind") == "PLANT" and not tile.get("watered_today")
    if op == "HARVEST":
        return isinstance(tile, dict) and tile.get("yield_units", 0) > 0
    if op == "FERTILIZE":
        return isinstance(tile, dict) and tile.get("kind") == "PLANT" and unit.inventory.get("FERTILIZER", 0) > 0
    if op == "DIG":
        if not isinstance(tile, dict):
            return False
        return "animal" not in tile
    if op in ("BUILD_COOP", "BUILD_PASTURE"):
        return tile is None
    if op == "FEED":
        return isinstance(tile, dict) and "animal" in tile and not tile.get("fed_today") and unit.inventory.get("WHEAT", 0) > 0
    if op == "COLLECT_FERTILIZER":
        return isinstance(tile, dict) and "animal" in tile and tile.get("fertilizer_available")
    if op == "CARE":
        return isinstance(tile, dict) and "animal" in tile and not tile.get("cared_today")
    return False


def clean_unit_action(state, unit, action):
    try:
        if _valid_unit_action(state, unit, action):
            return action
    except Exception:
        pass
    return ["PASS"]


def _order_affordable(state, order, money_left, seed_reservations):
    op = order[0]
    if op == "HIRE":
        return True  # cost varies by position in queue; trader.py sequences these correctly
    if op == "BUY_LAND":
        return True
    if len(order) < 3:
        return False
    item, n = order[1], order[2]
    if not isinstance(n, int) or n <= 0:
        return False
    if op == "BUY_SEED":
        return item in CROPS
    if op == "BUY_ANIMAL":
        return item in ANIMALS
    if op == "BUY_PRODUCT":
        return item in ("WHEAT", "FERTILIZER")
    if op == "SELL":
        return True
    return False


def clean_market_orders(state, orders, max_orders):
    cleaned = []
    for o in orders:
        if not isinstance(o, list) or not o:
            continue
        op = o[0]
        if op in ("HIRE", "BUY_LAND"):
            cleaned.append(o)
            continue
        if len(o) < 3:
            continue
        try:
            n = int(o[2])
        except (TypeError, ValueError):
            continue
        if n <= 0:
            continue
        if op not in ("BUY_SEED", "BUY_ANIMAL", "BUY_PRODUCT", "SELL"):
            continue
        cleaned.append([op, o[1], n])
        if len(cleaned) >= max_orders:
            break
    return cleaned[:max_orders]


def finalize(state, farmer_action, hand_actions, market_orders):
    farmer_action = clean_unit_action(state, state.units[0], farmer_action)
    cleaned_hands = []
    for i, unit in enumerate(state.units[1:]):
        a = hand_actions[i] if i < len(hand_actions) else ["PASS"]
        cleaned_hands.append(clean_unit_action(state, unit, a))
    cleaned_orders = clean_market_orders(state, market_orders, state.max_market_orders)
    return farmer_action, cleaned_hands, cleaned_orders
