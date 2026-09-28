"""Cross-check our constants copy against the installed kaggle_environments source,
so drift between the vendored engine and our copy is caught immediately."""
import pytest

from agent_lib import constants as ours

try:
    from kaggle_environments.envs.kaggriculture import kaggriculture as env_src
    HAVE_ENV = True
except Exception:
    HAVE_ENV = False


pytestmark = pytest.mark.skipif(not HAVE_ENV, reason="kaggle_environments not installed")


def test_crops_match():
    assert ours.CROPS == env_src.CROPS


def test_animals_match():
    assert ours.ANIMALS == env_src.ANIMALS


def test_market_params_match():
    assert ours.MARKET_PARAMS == env_src.MARKET_PARAMS


def test_shops_match():
    assert ours.SHOPS == env_src.SHOPS


def test_land_order_and_prices_match():
    assert ours.LAND_ORDER == env_src.LAND_ORDER
    assert ours.LAND_PRICES == env_src.LAND_PRICES


def test_fib_matches():
    for n in range(10):
        assert ours.fib(n) == env_src._fib(n)


def test_hire_cost_matches():
    for n in range(6):
        for mult in (1, 2, 5):
            assert ours.hire_cost(n, mult) == env_src._hire_cost(n, mult)


def test_defaults_match_json_spec():
    import json
    import os
    json_path = os.path.join(os.path.dirname(env_src.__file__), "kaggriculture.json")
    with open(json_path) as f:
        spec = json.load(f)
    cfg = spec["configuration"]
    checks = {
        "episodeSteps": spec["configuration"]["episodeSteps"],
        "actTimeout": cfg["actTimeout"],
        "boardSize": cfg["boardSize"]["default"],
        "startingMoney": cfg["startingMoney"]["default"],
        "maxMarketOrdersPerTurn": cfg["maxMarketOrdersPerTurn"]["default"],
        "turnsPerDay": cfg["turnsPerDay"]["default"],
        "shedCapacity": cfg["shedCapacity"]["default"],
        "weedSpawnChance": cfg["weedSpawnChance"]["default"],
        "townShopUnlockInterval": cfg["townShopUnlockInterval"]["default"],
        "townShopSellInterval": cfg["townShopSellInterval"]["default"],
        "townCenterSellInterval": cfg["townCenterSellInterval"]["default"],
        "farmHandCostMult": cfg["farmHandCostMult"]["default"],
    }
    for key, expected in checks.items():
        assert ours.DEFAULTS[key] == expected, key
