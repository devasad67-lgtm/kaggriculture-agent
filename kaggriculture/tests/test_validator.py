from agent_lib import state as st, validator


def _make_state(farmer_pos=(4, 4), tile=None, seeds=None, money=1000):
    board_size = 10
    board = [[None] * board_size for _ in range(board_size)]
    fx, fy = farmer_pos
    board[fy][fx] = tile
    obs = {
        "player": 0, "day": 0, "hour": 0, "step": 0,
        "farms": [
            {"money": money, "tiles": board, "farmer": list(farmer_pos), "hands": [],
             "unlocked_quadrants": ["NW"], "hires_today": 0},
            {"money": 0, "tiles": [[None] * board_size for _ in range(board_size)],
             "farmer": [0, 0], "hands": [], "unlocked_quadrants": ["NW"], "hires_today": 0},
        ],
        "private": {"shed": {}, "seeds": seeds or {}, "inventories": [{}]},
        "market": {"inventory": {}, "prices": {}},
        "town": {"unlocked_shops": []},
    }
    return st.parse(obs, {"episodeSteps": 720})


def test_plant_without_seed_becomes_pass():
    state = _make_state(seeds={"WHEAT": 0})
    unit = state.units[0]
    cleaned = validator.clean_unit_action(state, unit, ["PLANT", "WHEAT"])
    assert cleaned == ["PASS"]


def test_plant_with_seed_on_empty_tile_survives():
    state = _make_state(seeds={"WHEAT": 1})
    unit = state.units[0]
    cleaned = validator.clean_unit_action(state, unit, ["PLANT", "WHEAT"])
    assert cleaned == ["PLANT", "WHEAT"]


def test_harvest_on_empty_tile_becomes_pass():
    state = _make_state(tile=None)
    unit = state.units[0]
    cleaned = validator.clean_unit_action(state, unit, ["HARVEST"])
    assert cleaned == ["PASS"]


def test_malformed_action_becomes_pass():
    state = _make_state()
    unit = state.units[0]
    for bad in [None, [], "WATER", 42, ["UNKNOWN_OP"]]:
        assert validator.clean_unit_action(state, unit, bad) == ["PASS"]


def test_market_orders_trimmed_to_cap():
    state = _make_state()
    orders = [["SELL", "WHEAT", 1] for _ in range(15)]
    cleaned = validator.clean_market_orders(state, orders, 10)
    assert len(cleaned) == 10


def test_market_orders_drop_malformed():
    state = _make_state()
    orders = [["SELL", "WHEAT", 0], ["SELL", "WHEAT", -1], ["BOGUS", "X", 1], ["HIRE"], ["SELL", "WHEAT", 5]]
    cleaned = validator.clean_market_orders(state, orders, 10)
    assert cleaned == [["HIRE"], ["SELL", "WHEAT", 5]]


def test_finalize_returns_one_action_per_hand():
    state = _make_state()
    farmer_action, hand_actions, orders = validator.finalize(state, ["PASS"], [], [])
    assert farmer_action == ["PASS"]
    assert hand_actions == []
    assert orders == []
