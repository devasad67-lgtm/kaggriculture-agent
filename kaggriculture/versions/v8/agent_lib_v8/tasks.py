"""Scan GameState + the planned layout (in memory) for actionable tile
opportunities. Pure function of state -> categorized coordinate lists; no
unit assignment happens here (that's scheduler.py's job)."""
from . import economics
from .constants import ANIMALS, CROPS
from .state import tile_at

# Ongoing crops (tomato interval=1 day, strawberry interval=2 days) tick on a
# fixed schedule; with less than a day left, watering today essentially never
# leads to another harvestable-and-sellable production before the game ends.
WATER_ONGOING_CUTOFF_TURNS = 24

# Never stop feeding purely because of a transient price dip this early —
# only start applying the live-profitability check once there's enough of
# the season left that "stop feeding" is a real strategic wind-down and not
# noise from one bad market tick.
FEED_PROFIT_CHECK_MIN_DAY = 15


def _worth_feeding(state, animal):
    if state.day < FEED_PROFIT_CHECK_MIN_DAY:
        return True
    product = ANIMALS[animal]["product"]
    price = state.prices.get(product, 0)
    wheat_price = state.prices.get("WHEAT", 25)
    return economics.animal_daily_profit(animal, price, wheat_price) > 0


def _fertilize_worthwhile(state, tile, crop_data):
    """True if applying FERTILIZE now would still land before the tile's
    yield caps out or stops accumulating bonus (mirrors the env's own bonus
    formulas in kaggriculture.py: _apply_unit_action's WATER branch and
    _daily_refresh_plants).

    Restricted to one-time crops (wheat/carrot/melon) only. A unit carrying
    fertilizer prioritizes delivering it over other travel (see
    scheduler._pick_new_target), so fertilizing ongoing crops (tomato/
    strawberry) pulls units away from plain watering more than the doubled
    yield on those is worth — measured as a net loss, kept off."""
    if crop_data["ongoing"]:
        return False
    if tile.get("fertilized_until_day", -1) >= state.day:
        return False  # already covered through today
    if tile.get("yield_units", 0) >= crop_data["max_yield"]:
        return False  # already at the (fertilized) cap, no room left
    age = state.day - tile["planted_day"]
    return age <= crop_data["max_yield_day"]


def generate(state, memory):
    board = state.tiles
    board_size = len(board)
    layout = memory.layout

    water = []
    harvest_plant = []
    harvest_animal = []
    feed = []
    collect_fert = []
    care = []
    dig_weed = []
    build_coop = []
    build_pasture = []
    plant = []
    fertilize = []
    empty_unassigned = []

    for y in range(board_size):
        row = board[y]
        for x in range(len(row)):
            tile = row[x]
            if tile == "LOCKED":
                continue
            if tile is None:
                role = layout.get((x, y))
                if role is None:
                    empty_unassigned.append((x, y))
                elif role["role"] == "CROP":
                    plant.append((x, y, role["crop"]))
                elif role["role"] == "COOP":
                    build_coop.append((x, y))
                elif role["role"] == "PASTURE":
                    build_pasture.append((x, y))
                continue
            if not isinstance(tile, dict):
                continue
            kind = tile.get("kind")
            if kind == "WEED":
                dig_weed.append((x, y))
                continue
            if kind == "PLANT":
                crop_data = CROPS[tile["crop"]]
                # Ongoing crops (tomato/strawberry) only benefit from watering
                # on a day that leads to another scheduled production tick
                # that can still be harvested and sold before the game ends.
                # With well under a day left that's not realistic, and a unit
                # carrying fertilizer/water intent for a dead-end tile is a
                # unit not doing something that still pays.
                skip_water = crop_data["ongoing"] and state.turns_left < WATER_ONGOING_CUTOFF_TURNS
                if not tile.get("watered_today") and not skip_water:
                    water.append((x, y))
                if tile.get("yield_units", 0) > 0 and (state.day - tile["planted_day"]) >= crop_data["first_yield_day"]:
                    urgent = tile.get("max_lifespan_step", -1) >= 0 and state.step >= tile["max_lifespan_step"]
                    harvest_plant.append((x, y, urgent))
                if _fertilize_worthwhile(state, tile, crop_data):
                    fertilize.append((x, y))
                continue
            if kind in ("COOP", "PASTURE"):
                if tile.get("animal") is None or "animal" not in tile:
                    # empty structure — nothing to schedule here directly; a unit
                    # carrying the matching animal will target it via inventory logic.
                    continue
                # Feed only while it's still worth it at *live* prices. A real
                # top-ladder replay showed both leading agents' herds shrink
                # from ~day 24 of 30 onward — not from a fixed end-game date,
                # but because their own heavy selling had crashed milk/wool/
                # egg prices below feed cost by then. Mirroring that as a
                # live profitability check (not a hardcoded day) means it
                # naturally reacts to whatever the market actually does,
                # including the opponent's selling.
                if not tile.get("fed_today") and _worth_feeding(state, tile["animal"]):
                    feed.append((x, y))
                if not tile.get("cared_today"):
                    care.append((x, y))
                if tile.get("yield_units", 0) > 0:
                    harvest_animal.append((x, y))
                if tile.get("fertilizer_available"):
                    collect_fert.append((x, y))
                continue

    empty_structures = _empty_structures(board, layout)

    return {
        "water": water,
        "harvest_plant": harvest_plant,
        "harvest_animal": harvest_animal,
        "feed": feed,
        "collect_fert": collect_fert,
        "care": care,
        "dig_weed": dig_weed,
        "build_coop": build_coop,
        "build_pasture": build_pasture,
        "plant": plant,
        "fertilize": fertilize,
        "empty_structures": empty_structures,
    }


def _empty_structures(board, layout):
    """(x, y, animal_type) for built-but-unoccupied coop/pasture tiles, animal_type
    taken from the layout's plan for that tile (falls back to structure's own kind)."""
    out = []
    for y, row in enumerate(board):
        for x, tile in enumerate(row):
            if isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE") and "animal" not in tile:
                role = layout.get((x, y), {})
                animal = role.get("animal")
                if animal is None:
                    animal = "GOOSE" if tile["kind"] == "COOP" else "COW"
                out.append((x, y, animal))
    return out
