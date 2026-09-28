import pytest

try:
    from kaggle_environments import make
    HAVE_ENV = True
except Exception:
    HAVE_ENV = False

pytestmark = pytest.mark.skipif(not HAVE_ENV, reason="kaggle_environments not installed")


def _run(opponent, steps=720, seed=1):
    from agent_lib.strategy import Brain

    brain = Brain(None)
    errors = []

    def agent(obs):
        action = brain.act(obs)
        errors.extend(brain.memory.errors[len(errors):])
        return action

    env = make("kaggriculture", configuration={"episodeSteps": steps, "seed": seed}, debug=False)
    env.run([agent, opponent])
    final = env.steps[-1]
    return env, final, errors


@pytest.mark.parametrize("opponent", ["pass", "random", "starter"])
def test_full_game_no_errors_no_exceptions(opponent):
    env, final, errors = _run(opponent, steps=720)
    assert errors == []
    assert final[0].status == "DONE"
    assert final[1].status == "DONE"
    assert final[0].reward is not None
    assert isinstance(final[0].reward, (int, float))


def test_self_play_no_errors():
    from agent_lib.strategy import Brain

    brain_a = Brain(None)
    brain_b = Brain(None)
    errors = []

    def agent_a(obs):
        action = brain_a.act(obs)
        errors.extend(brain_a.memory.errors[len(errors):])
        return action

    def agent_b(obs):
        return brain_b.act(obs)

    env = make("kaggriculture", configuration={"episodeSteps": 240, "seed": 2}, debug=False)
    env.run([agent_a, agent_b])
    final = env.steps[-1]
    assert errors == []
    assert final[0].status == "DONE" and final[1].status == "DONE"


def test_short_episode_does_not_crash():
    """Non-default episodeSteps (shorter than a full season) shouldn't break anything."""
    env, final, errors = _run("pass", steps=10, seed=3)
    assert errors == []
    assert final[0].status == "DONE"


def test_player_seat_1_also_works():
    from agent_lib.strategy import Brain

    brain = Brain(None)
    errors = []

    def agent(obs):
        action = brain.act(obs)
        errors.extend(brain.memory.errors[len(errors):])
        return action

    env = make("kaggriculture", configuration={"episodeSteps": 120, "seed": 4}, debug=False)
    env.run(["pass", agent])  # our agent is player 1 this time
    final = env.steps[-1]
    assert errors == []
    assert final[1].status == "DONE"
