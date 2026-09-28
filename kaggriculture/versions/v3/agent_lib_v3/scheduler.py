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
"""
from . import geometry as geo
from .constants import ANIMALS
from .state import tile_at


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


# The env only auto-drops unit inventory into the shed at a *full* day
# boundary ((step+1) % turnsPerDay == 0). With the default 720 = 30*24 steps
# exactly, the game ends mid-way through day 30's last few hours (see
# interpreter()'s "-2" step offset in kaggriculture.py) and that final
# partial day never reaches its own end-of-day event — so anything still
# sitting in a unit's inventory at game end is silently lost, never sold,
# never counted. FINAL_RUSH_TURNS gives every unit (max distance 8 tiles to
# its nearest shed corner on a fully-expanded board) enough turns to walk
# back and DROP before that happens.
FINAL_RUSH_TURNS = 10
DROP_THRESHOLD = 6


def _inventory_total(unit):
    return sum(unit.inventory.values())


def _bird_in_hand(state, unit, tile, sets, layout):
    action = _tile_action(state, unit, tile, sets, layout)
    if action is not None:
        return action

    # Nothing tile-specific to do here. If we're standing at the shed with
    # something worth dropping off (see FINAL_RUSH_TURNS above for why this
    # matters most in the last few turns of the game), do that instead of
    # walking away empty-handed.
    pos = (unit.x, unit.y)
    if geo.is_shed_adjacent(pos, state.board_size):
        total = _inventory_total(unit)
        final_rush = state.turns_left <= FINAL_RUSH_TURNS
        if total > 0 and (final_rush or total >= DROP_THRESHOLD):
            return ["DROP"]
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


def _go_pickup(pos, item, n, board_size):
    if geo.is_shed_adjacent(pos, board_size):
        return ["PICKUP", item, n]
    target = geo.nearest_shed_tile(pos, board_size)
    return _move_toward(pos, target, board_size) or ["PASS"]


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


# Ordered (kind, set-key) pairs for the generic priority-travel search. "plant"
# is handled specially (seed-availability aware nearest search).
_PRIORITY_KINDS = [
    "harvest_plant_urgent",
    "water",
    "harvest_plant_normal",
    "harvest_animal",
    "collect_fert",
    "dig_weed_blocking",
    "build_coop",
    "build_pasture",
    "plant",
    "dig_weed",
    "care",
]


def _commit_valid(kind, target, state, sets, empty_structures, unit, layout):
    if kind == "go_drop":
        return state.turns_left <= FINAL_RUSH_TURNS and _inventory_total(unit) > 0
    if kind == "feed":
        return target in sets["feed"] and unit.inventory.get("WHEAT", 0) > 0
    if kind == "fertilize_carry":
        return target in sets["fertilize"] and unit.inventory.get("FERTILIZER", 0) > 0
    if kind.startswith("place:"):
        animal = kind.split(":", 1)[1]
        if unit.inventory.get(animal, 0) <= 0:
            return False
        return any((x, y) == target and a == animal for (x, y, a) in empty_structures)
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
    if state.turns_left <= FINAL_RUSH_TURNS and _inventory_total(unit) > 0:
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

    for kind in _PRIORITY_KINDS:
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

    wheat_pickup_dispatched = False
    fertilizer_pickup_dispatched = False
    animal_pickup_dispatched = set()
    reserved = set()
    actions = {}
    commitments = memory.commitments

    for unit in state.units:
        pos = (unit.x, unit.y)
        tile = tile_at(state, unit.x, unit.y)
        action = _bird_in_hand(state, unit, tile, sets, layout)

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
            reserved.add(target)
            mv = _move_toward(pos, target, board_size)
            if mv:
                commitments[unit.uid] = {"pos": target, "kind": kind}
                action = mv
            else:
                commitments.pop(unit.uid, None)

        if action is None:
            if sets["feed"] and not wheat_pickup_dispatched and unit.inventory.get("WHEAT", 0) == 0 and state.shed.get("WHEAT", 0) > 0:
                wheat_pickup_dispatched = True
                action = _go_pickup(pos, "WHEAT", min(8, state.shed.get("WHEAT", 0)), board_size)
            elif sets["fertilize"] and not fertilizer_pickup_dispatched and unit.inventory.get("FERTILIZER", 0) == 0 and state.shed.get("FERTILIZER", 0) > 0:
                fertilizer_pickup_dispatched = True
                action = _go_pickup(pos, "FERTILIZER", min(4, state.shed.get("FERTILIZER", 0)), board_size)
            elif empty_structures:
                for x, y, animal in empty_structures:
                    if animal in animal_pickup_dispatched:
                        continue
                    if state.shed.get(animal, 0) > 0:
                        animal_pickup_dispatched.add(animal)
                        action = _go_pickup(pos, animal, 1, board_size)
                        break

        if action is None:
            action = ["PASS"]
            commitments.pop(unit.uid, None)
        actions[unit.uid] = action

    return actions
