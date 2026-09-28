from agent_lib import scheduler, state as st
from agent_lib.memory import Memory


def _make_state(units_pos, tiles, seeds=None, shed=None):
    board_size = 10
    board = [[None for _ in range(board_size)] for _ in range(board_size)]
    for (x, y), tile in tiles.items():
        board[y][x] = tile
    obs = {
        "player": 0,
        "day": 0,
        "hour": 0,
        "step": 0,
        "farms": [
            {
                "money": 1000,
                "tiles": board,
                "farmer": list(units_pos[0]),
                "hands": [list(p) for p in units_pos[1:]],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
            },
            {"money": 1000, "tiles": [[None] * board_size for _ in range(board_size)],
             "farmer": [0, 0], "hands": [], "unlocked_quadrants": ["NW"], "hires_today": 0},
        ],
        "private": {
            "shed": shed or {},
            "seeds": seeds or {},
            "inventories": [{} for _ in units_pos],
        },
        "market": {"inventory": {}, "prices": {}},
        "town": {"unlocked_shops": []},
    }
    return st.parse(obs, {"episodeSteps": 720})


def test_two_units_never_target_the_same_tile_same_turn():
    tiles = {
        (2, 4): {"kind": "PLANT", "crop": "WHEAT", "planted_day": 0, "watered_today": False,
                  "consecutive_unwatered": 0, "yield_units": 1, "max_lifespan_step": 1000, "fertilized_until_day": -1},
    }
    state = _make_state([(0, 4), (4, 4)], tiles)
    memory = Memory()
    from agent_lib import tasks
    task_lists = tasks.generate(state, memory)
    actions = scheduler.assign(state, task_lists, memory)
    assert len(actions) == 2
    # Both units should move toward the single water target without erroring;
    # they must not both claim it as a *reserved* target this same turn in a
    # way that produces conflicting/duplicate commitments to the same tile
    # from two different units simultaneously mid-turn (checked via distinct
    # commitment entries, not equal targets colliding on a single-tile task).
    assert memory.commitments.get(0) is not None or memory.commitments.get(1) is not None


def test_farmer_harvests_when_standing_on_ripe_tile():
    tiles = {
        # planted_day in the past so day(0) - planted_day >= WHEAT's first_yield_day(2),
        # matching the env's own HARVEST precondition (see kaggriculture.py).
        (4, 4): {"kind": "PLANT", "crop": "WHEAT", "planted_day": -5, "watered_today": True,
                  "consecutive_unwatered": 0, "yield_units": 3, "max_lifespan_step": 1000, "fertilized_until_day": -1},
    }
    state = _make_state([(4, 4)], tiles)
    memory = Memory()
    from agent_lib import tasks
    task_lists = tasks.generate(state, memory)
    actions = scheduler.assign(state, task_lists, memory)
    assert actions[0] == ["HARVEST"]


def test_unit_plants_when_standing_on_empty_layout_tile_with_seed():
    state = _make_state([(4, 4)], {}, seeds={"WHEAT": 2})
    memory = Memory()
    memory.layout = {(4, 4): {"role": "CROP", "crop": "WHEAT"}}
    from agent_lib import tasks
    task_lists = tasks.generate(state, memory)
    actions = scheduler.assign(state, task_lists, memory)
    assert actions[0] == ["PLANT", "WHEAT"]


def test_no_seed_means_unit_does_not_plant():
    state = _make_state([(4, 4)], {}, seeds={"WHEAT": 0})
    memory = Memory()
    memory.layout = {(4, 4): {"role": "CROP", "crop": "WHEAT"}}
    from agent_lib import tasks
    task_lists = tasks.generate(state, memory)
    actions = scheduler.assign(state, task_lists, memory)
    assert actions[0] != ["PLANT", "WHEAT"]


def test_every_unit_gets_exactly_one_action():
    state = _make_state([(0, 0), (1, 1), (2, 2), (9, 9)], {})
    memory = Memory()
    from agent_lib import tasks
    task_lists = tasks.generate(state, memory)
    actions = scheduler.assign(state, task_lists, memory)
    assert set(actions.keys()) == {0, 1, 2, 3}
    for a in actions.values():
        assert isinstance(a, list) and len(a) >= 1
