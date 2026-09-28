"""Exact replica of the kaggriculture market price curve + sell/buy planning helpers.

Must reproduce kaggriculture.py's market_price()/_commit_unit() exactly:
  price(inv) = base + sign*amp*f(|inv-I0|), floored at PRICE_FLOOR, rounded to nearest int.
  sell quoted at pre-sell inventory; each unit sold shifts inventory by +1 (unless price==floor).
  buy quoted at post-buy inventory (inventory - 1 for the unit about to be bought).
"""
import math

from .constants import MARKET_PARAMS, PRICE_FLOOR, HINGE_GAIN


def _shape(func, x, T=None):
    x = max(0.0, x)
    if func == "linear":
        return x
    if func == "sq":
        return x * x
    if func == "sqrt":
        return math.sqrt(x)
    if func == "log":
        return math.log(1.0 + x)
    if func == "log10":
        return math.log10(1.0 + x)
    if func == "hinge":
        if not T or T <= 0:
            return x
        u = x / T
        return u + HINGE_GAIN * max(0.0, u - 1.0) ** 2
    return x


def price(item, inventory, params=None):
    """Sell/buy-reference price at a given market inventory level, floored+rounded."""
    p = (params or MARKET_PARAMS)[item]
    base = p["base"]
    I0 = p["I0"]
    T = p["T"]
    if inventory < I0:
        f = p["below_func"]
        amp = p["below_target"] * base / _shape(f, T, T)
        val = base + amp * _shape(f, I0 - inventory, T)
    else:
        f = p["above_func"]
        amp = p["above_target"] * base / _shape(f, T, T)
        val = base - amp * _shape(f, inventory - I0, T)
    return max(PRICE_FLOOR, int(round(val)))


def marginal_sell_price_after(item, k, inventory, params=None):
    """Price of the (k+1)-th unit sold, i.e. price at inventory+k (ignoring floor no-add rule
    for simplicity of lookahead; used for planning, not for exact commit)."""
    return price(item, inventory + k, params)


def revenue_of_selling(item, n, inventory, params=None):
    """Exact revenue (and ending inventory) of selling n units solo (no opponent interleaving),
    replicating _commit_unit's per-unit sequential logic: quote at current inventory, pay it,
    inventory += 1 unless price was at the floor."""
    if n <= 0:
        return 0, inventory
    total = 0
    inv = inventory
    for _ in range(n):
        p = price(item, inv, params)
        total += p
        if p > PRICE_FLOOR:
            inv += 1
    return total, inv


def cost_of_buying(item, n, inventory, params=None):
    """Exact cost (and ending inventory) of buying n units of WHEAT/FERTILIZER solo.
    Buy price is quoted at post-buy inventory (inventory - 1 for the first unit)."""
    if n <= 0:
        return 0, inventory
    total = 0
    inv = inventory
    for _ in range(n):
        inv -= 1
        p = price(item, inv, params)
        total += p
    return total, inv


def best_sell_count(item, have, inventory, min_price, params=None, max_n=None):
    """Largest n (0 <= n <= have) such that every unit sold has price >= min_price,
    stopping as soon as the marginal price would drop below the threshold."""
    if have <= 0:
        return 0
    cap = have if max_n is None else min(have, max_n)
    inv = inventory
    n = 0
    for _ in range(cap):
        p = price(item, inv, params)
        if p < min_price:
            break
        n += 1
        if p > PRICE_FLOOR:
            inv += 1
    return n


def predict_town_drain(shops, turns_ahead, shop_interval=4, center_interval=24):
    """Units removed per product over the next `turns_ahead` turns, from shops + town center.
    Approximation: assumes shop list and intervals stay constant (true within a game except
    for shop unlocks, which the caller should re-evaluate as `shops` changes)."""
    from .constants import SHOPS, TOWN_CENTER_PRODUCTS

    drain = {}
    n_shop_ticks = turns_ahead // shop_interval
    if n_shop_ticks > 0:
        for shop_name in shops:
            products = SHOPS.get(shop_name, [])
            multiplier = 2 if len(products) == 1 else 1
            for item in products:
                drain[item] = drain.get(item, 0) + multiplier * n_shop_ticks

    n_center_ticks = turns_ahead // center_interval
    if n_center_ticks > 0:
        for item in TOWN_CENTER_PRODUCTS:
            drain[item] = drain.get(item, 0) + n_center_ticks

    return drain
