"""Three opponent archetypes, statistically parametrized from real ladder
replays of players who beat us (never copying their code — see NOTES.md).
Each reuses the shared, well-tested pipeline (state.parse, tasks.generate,
scheduler.assign, trader.orders, validator.finalize) and only swaps out the
two decision points that vary: the tile layout and the day's Plan. This is
NOT meant to be a peer to strategy.Brain in sophistication — it's a fast,
honest sparring partner so local benchmarks stop lying about the ladder.

  - CropOnlyBrain  (Moritz Huber pattern): zero animals, ever. Aggressive
    land buying (up to all 4 quadrants). Heavy hiring. Crop mix weighted
    toward wheat/carrot/tomato/melon.
  - LeanBrain      (Sneha Bhargava4 pattern): small footprint (few hands,
    1-2 quadrants), but sells patiently (high min-price fraction) instead
    of dumping volume — low activity, preserved margin.
  - AnimalOnlyBrain (ADOLE Edache pattern): zero crops, ever. Every
    unlocked tile becomes a pen. Aggressive animal buying across all three
    types from day 0.
"""
from . import economics, geometry as geo, scheduler, tasks, trader, validator
from .constants import ANIMALS
from .memory import Memory
from .state import parse


class _ArchetypeBrainBase:
    def __init__(self, config=None):
        self.memory = Memory()
        self.config = config

    def act(self, obs):
        memory = self.memory
        try:
            state = parse(obs, self.config)
        except Exception:
            return {"farmer": ["PASS"], "hands": [], "market": []}

        try:
            memory.update(state)
        except Exception:
            pass

        try:
            if state.hour == 0 or not memory.layout:
                self.build_layout(state, memory)
        except Exception:
            memory.layout = memory.layout or {}

        try:
            plan = self.decide_plan(state, memory)
        except Exception:
            plan = {"liquidation": state.turns_left <= 36, "hands_target": 0,
                    "buy_land": False, "animal_targets": {}, "sell_min_fraction": 0.3}

        try:
            task_lists = tasks.generate(state, memory)
        except Exception:
            task_lists = {"water": [], "harvest_plant": [], "harvest_animal": [], "feed": [],
                          "collect_fert": [], "care": [], "dig_weed": [], "build_coop": [],
                          "build_pasture": [], "plant": [], "fertilize": [], "empty_structures": []}

        try:
            unit_actions = scheduler.assign(state, task_lists, memory)
        except Exception:
            unit_actions = {u.uid: ["PASS"] for u in state.units}

        try:
            market_orders = trader.orders(state, plan, memory)
        except Exception:
            market_orders = []

        farmer_action = unit_actions.get(0, ["PASS"])
        hand_actions = [unit_actions.get(i + 1, ["PASS"]) for i in range(len(state.units) - 1)]

        try:
            farmer_action, hand_actions, market_orders = validator.finalize(
                state, farmer_action, hand_actions, market_orders
            )
        except Exception:
            farmer_action, hand_actions, market_orders = ["PASS"], [["PASS"] for _ in hand_actions], []

        return {"farmer": farmer_action, "hands": hand_actions, "market": market_orders}

    def build_layout(self, state, memory):
        raise NotImplementedError

    def decide_plan(self, state, memory):
        raise NotImplementedError


def _all_unlocked_tiles(state):
    tiles = []
    for q in state.unlocked_quadrants:
        tiles.extend(geo.quadrant_tiles(q, state.board_size))
    return tiles


class CropOnlyBrain(_ArchetypeBrainBase):
    """Moritz Huber pattern: zero animals, land-hungry, crop-grinding."""
    CROP_WEIGHTS = {"WHEAT": 0.30, "CARROT": 0.25, "TOMATO": 0.15, "STRAWBERRY": 0.05, "MELON": 0.25}
    HANDS_CAP = 12

    def build_layout(self, state, memory):
        tiles = _all_unlocked_tiles(state)
        shed_tiles = set(geo.shed_access_tiles(state.board_size))
        tiles = [t for t in tiles if t not in shed_tiles]
        tiles.sort(key=lambda t: (geo.manhattan(t, geo.nearest_shed_tile(t, state.board_size)), t))
        order = sorted(self.CROP_WEIGHTS.items(), key=lambda kv: -kv[1])
        layout = {}
        for i, t in enumerate(tiles):
            crop = order[i % len(order)][0]
            layout[t] = {"role": "CROP", "crop": crop}
        memory.layout = layout

    def decide_plan(self, state, memory):
        turns_left = state.turns_left
        liquidation = turns_left <= 36
        n_planned = len(memory.layout)
        hands_target = 0 if liquidation else min(self.HANDS_CAP, n_planned // 6)
        buy_land = (not liquidation and state.day >= 2 and state.money > 1200
                    and len(state.unlocked_quadrants) < 4)
        return {
            "liquidation": liquidation,
            "hands_target": hands_target,
            "buy_land": buy_land,
            "animal_targets": {},
            "sell_min_fraction": 0.25,
        }


class LeanBrain(_ArchetypeBrainBase):
    """Sneha Bhargava4 pattern: small footprint, patient (high-margin) selling."""
    HANDS_CAP = 5
    MAX_QUADRANTS_EXTRA = 1

    def build_layout(self, state, memory):
        if not hasattr(memory, "animal_tiles"):
            memory.animal_tiles = {}
        have = {"GOOSE": 0, "COW": 0, "SHEEP": 0}
        for a in memory.animal_tiles.values():
            have[a] = have.get(a, 0) + 1
        targets = {"GOOSE": 0, "COW": 2, "SHEEP": 1}
        tiles = _all_unlocked_tiles(state)
        shed_tiles = set(geo.shed_access_tiles(state.board_size))
        used = set(memory.animal_tiles.keys())
        for animal, target in targets.items():
            need = target - have.get(animal, 0)
            for t in tiles:
                if need <= 0:
                    break
                if t in used or t in shed_tiles:
                    continue
                tile = state.tiles[t[1]][t[0]] if t[1] < len(state.tiles) and t[0] < len(state.tiles[t[1]]) else "LOCKED"
                if tile != "LOCKED" and tile is not None:
                    continue
                memory.animal_tiles[t] = animal
                used.add(t)
                need -= 1
        layout = {}
        for (x, y), animal in memory.animal_tiles.items():
            layout[(x, y)] = {"role": ANIMALS[animal]["structure"], "animal": animal}
        crop_tiles = [t for t in tiles if t not in memory.animal_tiles and t not in shed_tiles]
        crop_tiles.sort(key=lambda t: (geo.manhattan(t, geo.nearest_shed_tile(t, state.board_size)), t))
        weights = ["MELON", "WHEAT", "CARROT"]
        for i, t in enumerate(crop_tiles[:15]):  # deliberately small footprint
            layout[t] = {"role": "CROP", "crop": weights[i % len(weights)]}
        memory.layout = layout

    def decide_plan(self, state, memory):
        turns_left = state.turns_left
        liquidation = turns_left <= 36
        hands_target = 0 if liquidation else min(self.HANDS_CAP, 2 + state.day // 6)
        buy_land = (not liquidation and state.day >= 6 and state.money > 2500
                    and len(state.unlocked_quadrants) < 1 + self.MAX_QUADRANTS_EXTRA)
        return {
            "liquidation": liquidation,
            "hands_target": hands_target,
            "buy_land": buy_land,
            "animal_targets": {"COW": 2, "SHEEP": 1, "GOOSE": 0},
            "sell_min_fraction": 0.65,  # patient: hold out for much better prices, sell less volume
        }


class AnimalOnlyBrain(_ArchetypeBrainBase):
    """ADOLE Edache pattern: zero crops, every tile a pen, aggressive animal buying."""
    HANDS_CAP = 11

    def build_layout(self, state, memory):
        if not hasattr(memory, "animal_tiles"):
            memory.animal_tiles = {}
        day = state.day
        targets = {
            "COW": min(15, 1 + day),
            "SHEEP": min(9, max(0, day - 1)),
            "GOOSE": min(10, max(0, day - 2)),
        }
        have = {"GOOSE": 0, "COW": 0, "SHEEP": 0}
        for a in memory.animal_tiles.values():
            have[a] = have.get(a, 0) + 1
        tiles = _all_unlocked_tiles(state)
        shed_tiles = set(geo.shed_access_tiles(state.board_size))
        tiles.sort(key=lambda t: (geo.manhattan(t, geo.nearest_shed_tile(t, state.board_size)), t))
        used = set(memory.animal_tiles.keys())
        for animal, target in targets.items():
            need = target - have.get(animal, 0)
            for t in tiles:
                if need <= 0:
                    break
                if t in used or t in shed_tiles:
                    continue
                tile = state.tiles[t[1]][t[0]] if t[1] < len(state.tiles) and t[0] < len(state.tiles[t[1]]) else "LOCKED"
                if tile != "LOCKED" and tile is not None:
                    continue
                memory.animal_tiles[t] = animal
                used.add(t)
                need -= 1
        layout = {}
        for (x, y), animal in memory.animal_tiles.items():
            layout[(x, y)] = {"role": ANIMALS[animal]["structure"], "animal": animal}

        # Relying entirely on BUY_PRODUCT for feed pushes wheat price above
        # trader.py's buy ceiling as the herd grows (confirmed by trace: herd
        # shrank to 1 and stayed there from sustained starvation once buying
        # alone couldn't keep up) — a small self-grown wheat patch keeps this
        # archetype's herd alive without touching the shared trader.py logic
        # that v13's real submission also depends on.
        remaining = [t for t in _all_unlocked_tiles(state)
                     if t not in memory.animal_tiles and t not in shed_tiles]
        remaining.sort(key=lambda t: (geo.manhattan(t, geo.nearest_shed_tile(t, state.board_size)), t))
        for t in remaining[:12]:
            layout[t] = {"role": "CROP", "crop": "WHEAT"}

        memory.layout = layout
        memory.animal_targets = targets

    def decide_plan(self, state, memory):
        turns_left = state.turns_left
        liquidation = turns_left <= 36
        n_planned = len(memory.layout)
        hands_target = 0 if liquidation else min(self.HANDS_CAP, max(2, n_planned // 4))
        buy_land = (not liquidation and state.day >= 3 and state.money > 1500
                    and len(state.unlocked_quadrants) < 3)
        return {
            "liquidation": liquidation,
            "hands_target": hands_target,
            "buy_land": buy_land,
            "animal_targets": getattr(memory, "animal_targets", {}),
            "sell_min_fraction": 0.3,
        }


ARCHETYPES = {
    "crop_only": CropOnlyBrain,
    "lean": LeanBrain,
    "animal_only": AnimalOnlyBrain,
}


def make_agent(name):
    cls = ARCHETYPES[name]

    def agent(obs, config=None):
        if not hasattr(agent, "_brain"):
            agent._brain = cls(config)
        try:
            return agent._brain.act(obs)
        except Exception:
            return {"farmer": ["PASS"], "hands": [], "market": []}

    return agent
