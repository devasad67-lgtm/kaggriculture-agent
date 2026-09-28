"""Per-unit greedy controller: farmer acts first, then hands in order. Each
unit either does something useful on the tile it's standing on ("bird in
hand"), or moves toward a task target. Movement has no obstacles in this game
(locked tiles are passable, units never block each other), so a single greedy
Manhattan step always makes progress toward any target.

Targets are "sticky": once a unit commits to a target tile it keeps walking
there turn after turn (persisted in memory.commitments) instead of
recomputing "nearest" from scratch every turn. Without this, a unit whose
nearest-candidate set flickers turn to turn (e.g. seed stock arriving for a
different crop than the one it was already walking toward) will reverse
direction every turn and never arrive anywhere.

Shed logistics (fetching wheat/fertilizer/animals for delivery) are real
prioritized jobs interleaved into the same priority list as field work, not
an afterthought fallback that only fires when a unit has literally nothing
else to do. An earlier version had exactly that afterthought design, and on
a busy farm units almost never reached it: tests/test_livestock_delivery.py
caught a backlog of 15+ animals sitting unclaimed in the shed next to empty,
already-built pens, because "go pick up the animal I already paid for" never
won out over routine watering/harvesting.
"""
from . import geometry as geo
from .constants import ANIMALS
from .state import tile_at

# The env only auto-drops unit inventory into the shed at a *full* day
# boundary ((step+1) % turnsPerDay == 0). With the default 720 = 30*24 steps
# exactly, the game ends mid-way through day 30's last few hours (see
# interpreter()'s "-2" step offset in kaggriculture.py) and that final
# partial day never reaches its own end-of-day event — so anything still
# sitting in a unit's inventory at game end is silently lost, never sold,
# never counted. A unit must start heading back once its own distance to the
# shed leaves no slack: distance_to_shed + RUSH_BUFFER >= turns_left. This is
# strictly better than one flat turn count for everyone — a unit already
# near the shed can keep working productively much longer than one that's
# clear across a fully-expanded board (up to 8 tiles from any corner).
RUSH_BUFFER = 2
DROP_THRESHOLD = 6
WHEAT_FETCH_BATCH = 8
FERTILIZER_FETCH_BATCH = 4


def _inventory_total(unit):
    return sum(unit.inventory.values())


def _carries_any_animal(unit):
    return any(unit.inventory.get(a, 0) > 0 for a in ANIMALS)


def _needed_animal_pickup(state, empty_structures):
    """First animal type (deterministic order) with shed stock AND a
    matching empty structure actually waiting for it."""
    wanted = {a for (_, _, a) in empty_structures}
    for animal in ANIMALS:
        if animal in wanted and state.shed.get(animal, 0) > 0:
            return animal
    return None


def _should_rush_to_shed(state, unit, pos):
    if _inventory_total(unit) <= 0:
        return False
    dist = geo.manhattan(pos, geo.nearest_shed_tile(pos, state.board_size))
    return dist + RUSH_BUFFER >= state.turns_left


def _bird_in_hand(state, unit, tile, sets, layout, empty_structures):
    action = _tile_action(state, unit, tile, sets, layout)
    if action is not None:
        return action

    pos = (unit.x, unit.y)
    if not geo.is_shed_adjacent(pos, state.board_size):
        return None

    # Nothing tile-specific to do here, but we're standing right at the
    # shed — handle whichever shed-side job applies before walking away.
    total = _inventory_total(unit)
    final_rush = _should_rush_to_shed(state, unit, pos)
    if total > 0 and (final_rush or total >= DROP_THRESHOLD):
        return ["DROP"]

    if sets["feed"] and unit.inventory.get("WHEAT", 0) == 0 and state.shed.get("WHEAT", 0) > 0:
        return ["PICKUP", "WHEAT", min(WHEAT_FETCH_BATCH, state.shed.get("WHEAT", 0))]

    if sets["fertilize"] and unit.inventory.get("FERTILIZER", 0) == 0 and state.shed.get("FERTILIZER", 0) > 0:
        return ["PICKUP", "FERTILIZER", min(FERTILIZER_FETCH_BATCH, state.shed.get("FERTILIZER", 0))]

    if not _carries_any_animal(unit):
        needed = _needed_animal_pickup(state, empty_structures)
        if needed:
            return ["PICKUP", needed, 1]

    return None


def _tile_action(state, unit, tile, sets, layout):
    pos = (unit.x, unit.y)

    if tile is None:
        if pos in sets["plant"]:
            crop = sets["plant"][pos]
            if state.seeds.get(crop, 0) > 0:
                del sets["plant"][pos]
                return ["PLANT", crop]
            return None
        if pos in sets["build_coop"]:
            sets["build_coop"].discard(pos)
            return ["BUILD_COOP"]
        if pos in sets["build_pasture"]:
            sets["build_pasture"].discard(pos)
            return ["BUILD_PASTURE"]
        return None

    if not isinstance(tile, dict):
        return None
    kind = tile.get("kind")

    if kind == "WEED":
        if pos in sets["dig_weed"]:
            sets["dig_weed"].discard(pos)
            return ["DIG"]
        return None

    if kind == "PLANT":
        if pos in sets["harvest_plant_urgent"]:
            sets["harvest_plant_urgent"].discard(pos)
            return ["HARVEST"]
        if pos in sets["water"]:
            sets["water"].discard(pos)
            return ["WATER"]
        if pos in sets["fertilize"] and unit.inventory.get("FERTILIZER", 0) > 0:
            sets["fertilize"].discard(pos)
            return ["FERTILIZE"]
        if pos in sets["harvest_plant_normal"]:
            sets["harvest_plant_normal"].discard(pos)
            return ["HARVEST"]
        return None

    if kind in ("COOP", "PASTURE"):
        if "animal" not in tile:
            role = layout.get(pos)
            wanted = role.get("animal") if role else None
            candidates = [wanted] if wanted else [a for a, d in ANIMALS.items() if d["structure"] == kind]
            for a in candidates:
                if a and unit.inventory.get(a, 0) > 0:
                    return ["PLACE", a]
            return None
        if pos in sets["feed"] and unit.inventory.get("WHEAT", 0) > 0:
            sets["feed"].discard(pos)
            return ["FEED"]
        if pos in sets["harvest_animal"]:
            sets["harvest_animal"].discard(pos)
            return ["HARVEST"]
        if pos in sets["collect_fert"]:
            sets["collect_fert"].discard(pos)
            return ["COLLECT_FERTILIZER"]
        if pos in sets["care"]:
            sets["care"].discard(pos)
            return ["CARE"]
        return None

    return None


def _nearest(pos, candidates):
    best, best_d = None, None
    for c in candidates:
        d = geo.manhattan(pos, c)
        if best is None or d < best_d or (d == best_d and c < best):
            best, best_d = c, d
    return best


def _move_toward(pos, target, board_size):
    if pos == target:
        return None
    d = geo.step_toward(pos, target)
    return [d] if d else None


def _nearest_plantable(pos, plant_dict, seeds, reserved):
    scored = [
        (geo.manhattan(pos, p), p)
        for p in plant_dict
        if p not in reserved and seeds.get(plant_dict[p], 0) > 0
    ]
    if not scored:
        scored = [
            (geo.manhattan(pos, p), p)
            for p in plant_dict
            if seeds.get(plant_dict[p], 0) > 0
        ]
    if not scored:
        return None
    scored.sort(key=lambda t: (t[0], t[1]))
    return scored[0][1]


# Ordered kinds for the generic priority-travel search. "plant", "fetch_*"
# and "dig_weed_blocking" are handled specially inside the loop below.
#
# fetch_animal sits right after water: delivering an already-bought animal
# to a waiting pen is bounded, high-value work (money already spent; the
# only thing missing is a PICKUP+walk+PLACE), and letting it get starved by
# routine work is exactly the bug tests/test_livestock_delivery.py caught.
# build_coop/build_pasture stay just after it for the same reason on the
# construction side. fetch_wheat/fetch_fertilizer sit lower — feed/fertilize
# only matter once there's a pending job needing them, so they're ordered
# near those jobs rather than competing with core farm upkeep.
_PRIORITY_KINDS = [
    "harvest_plant_urgent",
    "water",
    "fetch_animal",
    "build_coop",
    "build_pasture",
    "harvest_plant_normal",
    "harvest_animal",
    "collect_fert",
    "fetch_wheat",
    "dig_weed_blocking",
    "plant",
    "fetch_fertilizer",
    "dig_weed",
    "care",
]


def _commit_valid(kind, target, state, sets, empty_structures, unit, layout):
    if kind == "go_drop":
        return _should_rush_to_shed(state, unit, (unit.x, unit.y))
    if kind == "feed":
        return target in sets["feed"] and unit.inventory.get("WHEAT", 0) > 0
    if kind == "fertilize_carry":
        return target in sets["fertilize"] and unit.inventory.get("FERTILIZER", 0) > 0
    if kind.startswith("place:"):
        animal = kind.split(":", 1)[1]
        if unit.inventory.get(animal, 0) <= 0:
            return False
        return any((x, y) == target and a == animal for (x, y, a) in empty_structures)
    if kind == "fetch_wheat":
        return bool(sets["feed"]) and unit.inventory.get("WHEAT", 0) == 0 and state.shed.get("WHEAT", 0) > 0
    if kind == "fetch_fertilizer":
        return bool(sets["fertilize"]) and unit.inventory.get("FERTILIZER", 0) == 0 and state.shed.get("FERTILIZER", 0) > 0
    if kind.startswith("fetch_animal:"):
        animal = kind.split(":", 1)[1]
        if _carries_any_animal(unit):
            return False
        return state.shed.get(animal, 0) > 0 and any(a == animal for (_, _, a) in empty_structures)
    if kind == "plant":
        crop = sets["plant"].get(target)
        return crop is not None and state.seeds.get(crop, 0) > 0
    if kind == "dig_weed_blocking":
        return target in sets["dig_weed"] and target in layout
    if kind in sets:
        s = sets[kind]
        return target in s
    return False


def _pick_new_target(state, pos, unit, sets, empty_structures, reserved, layout):
    """Returns (target, kind) or (None, None). Does not mutate reservation state."""
    if _should_rush_to_shed(state, unit, pos):
        # Unlike tile tasks, the shed isn't single-use — many units can (and
        # during the final rush, should) converge on it at once, so this
        # target is deliberately exempt from the `reserved` exclusion below.
        return geo.nearest_shed_tile(pos, state.board_size), "go_drop"

    if unit.inventory.get("WHEAT", 0) > 0 and sets["feed"]:
        avail = sets["feed"] - reserved
        target = _nearest(pos, avail) or _nearest(pos, sets["feed"])
        if target:
            return target, "feed"

    if unit.inventory.get("FERTILIZER", 0) > 0 and sets["fertilize"]:
        avail = sets["fertilize"] - reserved
        target = _nearest(pos, avail) or _nearest(pos, sets["fertilize"])
        if target:
            return target, "fertilize_carry"

    for animal_key in ("GOOSE", "COW", "SHEEP"):
        if unit.inventory.get(animal_key, 0) > 0:
            candidates = [(x, y) for (x, y, a) in empty_structures if a == animal_key and (x, y) not in reserved]
            target = _nearest(pos, candidates)
            if target:
                return target, f"place:{animal_key}"
            break

    shed_target = geo.nearest_shed_tile(pos, state.board_size)
    for kind in _PRIORITY_KINDS:
        if kind == "fetch_animal":
            needed = _needed_animal_pickup(state, empty_structures)
            if needed and not _carries_any_animal(unit):
                return shed_target, f"fetch_animal:{needed}"
            continue
        if kind == "fetch_wheat":
            if sets["feed"] and unit.inventory.get("WHEAT", 0) == 0 and state.shed.get("WHEAT", 0) > 0:
                return shed_target, "fetch_wheat"
            continue
        if kind == "fetch_fertilizer":
            if sets["fertilize"] and unit.inventory.get("FERTILIZER", 0) == 0 and state.shed.get("FERTILIZER", 0) > 0:
                return shed_target, "fetch_fertilizer"
            continue
        if kind == "plant":
            target = _nearest_plantable(pos, sets["plant"], state.seeds, reserved)
            if target:
                return target, "plant"
            continue
        if kind == "dig_weed_blocking":
            group = {p for p in sets["dig_weed"] if p in layout}
        else:
            group = sets[kind]
        if not group:
            continue
        avail = group - reserved
        target = _nearest(pos, avail) if avail else None
        if target:
            return target, kind
    return None, None


def assign(state, task_lists, memory):
    board_size = state.board_size
    layout = memory.layout

    sets = {
        "water": set(task_lists["water"]),
        "harvest_plant_urgent": {(x, y) for (x, y, urgent) in task_lists["harvest_plant"] if urgent},
        "harvest_plant_normal": {(x, y) for (x, y, urgent) in task_lists["harvest_plant"] if not urgent},
        "harvest_animal": set(task_lists["harvest_animal"]),
        "feed": set(task_lists["feed"]),
        "collect_fert": set(task_lists["collect_fert"]),
        "care": set(task_lists["care"]),
        "dig_weed": set(task_lists["dig_weed"]),
        "build_coop": set(task_lists["build_coop"]),
        "build_pasture": set(task_lists["build_pasture"]),
        "plant": {(x, y): c for (x, y, c) in task_lists["plant"]},
        "fertilize": set(task_lists.get("fertilize", [])),
    }
    empty_structures = list(task_lists["empty_structures"])

    reserved = set()
    actions = {}
    commitments = memory.commitments

    for unit in state.units:
        pos = (unit.x, unit.y)
        tile = tile_at(state, unit.x, unit.y)
        action = _bird_in_hand(state, unit, tile, sets, layout, empty_structures)

        if action is not None:
            commitments.pop(unit.uid, None)
            actions[unit.uid] = action
            continue

        target, kind = None, None
        commit = commitments.get(unit.uid)
        if commit is not None:
            c_pos, c_kind = commit["pos"], commit["kind"]
            if c_pos not in reserved and _commit_valid(c_kind, c_pos, state, sets, empty_structures, unit, layout):
                target, kind = c_pos, c_kind
            else:
                commitments.pop(unit.uid, None)

        if target is None:
            target, kind = _pick_new_target(state, pos, unit, sets, empty_structures, reserved, layout)

        if target is not None:
            # The shed isn't single-use, so fetch/drop targets don't reserve
            # it away from other units that also need to visit this turn.
            if not (kind == "go_drop" or (isinstance(kind, str) and kind.startswith("fetch_"))):
                reserved.add(target)
            mv = _move_toward(pos, target, board_size)
            if mv:
                commitments[unit.uid] = {"pos": target, "kind": kind}
                action = mv
            else:
                commitments.pop(unit.uid, None)

        if action is None:
            action = ["PASS"]
            commitments.pop(unit.uid, None)
        actions[unit.uid] = action

    return actions
