import pytest

from agent_lib import state as st

try:
    from kaggle_environments import make
    HAVE_ENV = True
except Exception:
    HAVE_ENV = False

pytestmark = pytest.mark.skipif(not HAVE_ENV, reason="kaggle_environments not installed")


def test_parse_initial_obs_both_players():
    env = make("kaggriculture", configuration={"episodeSteps": 10}, debug=False)
    env.reset(num_agents=2)
    for player in range(2):
        obs = env.state[player].observation
        gs = st.parse(obs, env.configuration)
        assert gs.player == player
        assert gs.step == 0
        assert gs.day == 0
        assert gs.hour == 0
        assert gs.money == 3000.0
        assert gs.board_size == 10
        assert gs.turns_per_day == 24
        assert gs.units[0].uid == 0
        assert gs.units[0].is_farmer
        assert gs.unlocked_quadrants == ["NW"]
        assert len(gs.tiles) == 10 and len(gs.tiles[0]) == 10


def test_parse_after_some_steps_has_hands_and_prices():
    env = make("kaggriculture", configuration={"episodeSteps": 60}, debug=False)

    def agent(obs):
        return {"farmer": ["PASS"], "hands": [], "market": [["HIRE"]]}

    env.run([agent, "pass"])
    obs = env.steps[5][0].observation
    gs = st.parse(obs, env.configuration)
    assert gs.step == 5
    assert "WHEAT" in gs.prices
    assert gs.prices["WHEAT"] > 0
    assert gs.market_inventory["WHEAT"] > 0


def test_parse_tolerates_missing_private():
    obs = {"player": 0, "day": 0, "hour": 0, "step": 0, "farms": [{"money": 100, "tiles": [[None]], "farmer": [0, 0], "hands": [], "unlocked_quadrants": ["NW"], "hires_today": 0}, {}]}
    gs = st.parse(obs, {"episodeSteps": 720})
    assert gs.money == 100
    assert gs.shed == {}
    assert gs.seeds == {}
