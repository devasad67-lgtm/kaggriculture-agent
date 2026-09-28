import random

import pytest

from agent_lib import market_model as mm
from agent_lib.constants import MARKET_PARAMS, PRODUCTS, PRICE_FLOOR

try:
    from kaggle_environments.envs.kaggriculture import kaggriculture as env_src
    HAVE_ENV = True
except Exception:
    HAVE_ENV = False

pytestmark = pytest.mark.skipif(not HAVE_ENV, reason="kaggle_environments not installed")


def test_price_matches_env_at_various_inventories():
    rng = random.Random(42)
    for item in PRODUCTS:
        for inv in [0, 1, 100, 5000, 9999, 10000, 10001, 15000, 30000, 50000] + [
            rng.randint(0, 60000) for _ in range(30)
        ]:
            ours = mm.price(item, inv)
            theirs = env_src.market_price(item, inv)
            assert ours == theirs, f"{item} inv={inv}: {ours} != {theirs}"


def test_price_matches_env_with_overrides():
    overrides = env_src._resolve_market_params({"WOOL": {"above_target": 0.95}, "WHEAT": {"base": 40}})
    for item in PRODUCTS:
        for inv in [5000, 10000, 20000]:
            ours = mm.price(item, inv, overrides)
            theirs = env_src.market_price(item, inv, overrides)
            assert ours == theirs


def test_table_reference_prices_from_readme():
    # From README's Price Function table: P(I0-T), P(I0+T), P(I0+2T).
    expected = {
        "WHEAT":      (45, 20, 19),
        "CARROT":     (70, 10, 1),
        "TOMATO":     (84, 24, 9),
        "STRAWBERRY": (204, 1, 1),
        "MELON":      (300, 1, 1),
        "EGG":        (70, 40, 39),
        "MILK":       (256, 1, 1),
        "WOOL":       (240, 1, 1),
        "FERTILIZER": (140, 60, 20),
    }
    for item, (p_minus, p_plus, p_plus2) in expected.items():
        T = MARKET_PARAMS[item]["T"]
        I0 = MARKET_PARAMS[item]["I0"]
        assert mm.price(item, I0 - T) == p_minus, item
        assert mm.price(item, I0 + T) == p_plus, item
        assert mm.price(item, I0 + 2 * T) == p_plus2, item


def test_revenue_of_selling_matches_env_commit_loop():
    """Replicate _commit_unit's SELL branch (single player, no opponent interleaving)
    and compare cumulative revenue + ending inventory against our closed-form loop."""
    rng = random.Random(7)
    for item in ["WHEAT", "STRAWBERRY", "MELON"]:
        inv0 = rng.randint(9000, 11000)
        n = rng.randint(1, 50)

        # Reference: env-style unit-by-unit commit.
        farm = {"money": 0.0}
        private = {"shed": {item: n}}
        market = {"inventory": {item: inv0}, "prices": {}}
        for _ in range(n):
            p = env_src.market_price(item, market["inventory"][item])
            env_src._commit_unit("SELL", item, p, farm, private, market)
        expected_revenue = farm["money"]
        expected_inv = market["inventory"][item]

        got_revenue, got_inv = mm.revenue_of_selling(item, n, inv0)
        assert got_revenue == expected_revenue, item
        assert got_inv == expected_inv, item


def test_cost_of_buying_matches_env_commit_loop():
    rng = random.Random(11)
    for item in ["WHEAT", "FERTILIZER"]:
        inv0 = rng.randint(9000, 11000)
        n = rng.randint(1, 50)

        farm = {"money": 1_000_000.0}
        private = {"shed": {}}
        market = {"inventory": {item: inv0}, "prices": {}}
        for _ in range(n):
            p = env_src.market_price(item, market["inventory"][item] - 1)
            env_src._commit_unit("BUY_PRODUCT", item, p, farm, private, market)
        expected_cost = 1_000_000.0 - farm["money"]
        expected_inv = market["inventory"][item]

        got_cost, got_inv = mm.cost_of_buying(item, n, inv0)
        assert got_cost == expected_cost, item
        assert got_inv == expected_inv, item


def test_buy_then_sell_nets_zero_on_unchanged_market():
    for item in ["WHEAT", "FERTILIZER"]:
        inv0 = 10000
        cost, inv1 = mm.cost_of_buying(item, 5, inv0)
        revenue, inv2 = mm.revenue_of_selling(item, 5, inv1)
        assert inv2 == inv0
        assert cost == revenue


def test_floor_price_does_not_increase_inventory():
    # Drive STRAWBERRY inventory deep into glut so price floors, then confirm
    # continued selling doesn't move inventory once floored.
    inv = 10000 + 100 * MARKET_PARAMS["STRAWBERRY"]["T"]
    assert mm.price("STRAWBERRY", inv) == PRICE_FLOOR
    revenue, end_inv = mm.revenue_of_selling("STRAWBERRY", 10, inv)
    assert end_inv == inv
    assert revenue == 10 * PRICE_FLOOR


def test_best_sell_count_respects_threshold():
    inv = 10000
    n = mm.best_sell_count("WHEAT", have=1000, inventory=inv, min_price=20)
    revenue, end_inv = mm.revenue_of_selling("WHEAT", n, inv)
    # every sold unit should have been >= 20; the next one (if any left) should be < 20
    if n < 1000:
        next_price = mm.price("WHEAT", end_inv)
        assert next_price < 20
    # and the sale actually clears the threshold for all n units
    check_inv = inv
    for _ in range(n):
        p = mm.price("WHEAT", check_inv)
        assert p >= 20
        if p > PRICE_FLOOR:
            check_inv += 1
