"""Scan GameState + the planned layout (in memory) for actionable tile
opportunities. Pure function of state -> categorized coordinate lists; no
unit assignment happens here (that's scheduler.py's job)."""
from .constants import ANIMALS, CROPS
from .state import tile_at


def _fertilize_worthwhile(state, tile, crop_data):
    """True if applying FERTILIZE now would still land before the tile's
    yield caps out or stops accumulating bonus (mirrors the env's own bonus
    formulas in kaggriculture.py: _apply_unit_action's WATER branch and
    _daily_refresh_plants)."""
    if tile.get("fertilized_until_day", -1) >= state.day:
        return False  # already covered through today
    if tile.get("yield_units", 0) >= crop_data["max_yield"]:
        return False  # already at the (fertilized) cap, no room left
    if crop_data["ongoing"]:
        return tile.get("max_lifespan_step", -1) < 0  # still in its production window, not decaying yet
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
                if not tile.get("watered_today"):
                    water.append((x, y))
                crop_data = CROPS[tile["crop"]]
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
                if not tile.get("fed_today"):
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
