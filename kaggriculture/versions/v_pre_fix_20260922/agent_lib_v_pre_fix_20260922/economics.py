"""ROI heuristics used by strategy.py to gate investment decisions. These use
current market prices (never base prices) and days remaining in the season."""
from .constants import ANIMALS, CROPS, LAND_PRICES, fib


def crop_cycle_days(crop):
    cd = CROPS[crop]
    if cd["ongoing"]:
        # Last scheduled production day after planting.
        return cd["first_yield_day"] + cd["interval"] * (cd["max_yield"] - 1) + 1
    return cd["max_yield_day"] + 1


def crop_expected_revenue(crop, price, fertilized=False):
    """Rough expected revenue for one full life cycle on one tile, at a fixed
    current price (ignores price decay from our own selling)."""
    cd = CROPS[crop]
    if cd["ongoing"]:
        per_yield = 2 if fertilized else 1
        return price * per_yield * cd["max_yield"]
    # one-time: base 1 + bonus days in window (unfertilized 1/day, fertilized 2/day)
    window_start = (cd["max_yield_day"] + 1) // 2
    bonus_days = cd["max_yield_day"] - window_start + 1
    per_day = 2 if fertilized else 1
    total_units = min(cd["max_yield"], 1 + bonus_days * per_day)
    return price * total_units


def crop_profit_per_tile_day(crop, price, fertilized=False):
    cycle = crop_cycle_days(crop)
    revenue = crop_expected_revenue(crop, price, fertilized)
    cost = CROPS[crop]["seed"]
    return (revenue - cost) / max(1, cycle)


def animal_daily_profit(animal, egg_price, wheat_price, days_since_first=30):
    """Steady-state daily profit once producing: product sold + 1 fertilizer/day
    sold at ~40% of its own base (conservative), minus feed cost (1 wheat/day)."""
    a = ANIMALS[animal]
    product_per_day = 1.0 / a["interval"]
    fert_value = 40  # conservative flat estimate; real price read by caller if needed
    return product_per_day * egg_price + fert_value - wheat_price


def animal_payback_days(animal, egg_price, wheat_price, build_cost=0):
    cost = ANIMALS[animal]["cost"] + build_cost
    daily = animal_daily_profit(animal, egg_price, wheat_price)
    if daily <= 0:
        return float("inf")
    # first_yield_day is a delay before any production starts.
    return ANIMALS[animal]["first_yield_day"] + cost / daily


def should_buy_animal(animal, egg_price, wheat_price, turns_left, turns_per_day, build_cost=0):
    days_left = turns_left / turns_per_day
    payback = animal_payback_days(animal, egg_price, wheat_price, build_cost)
    return payback < days_left * 0.7  # leave margin; don't cut it razor-thin


def land_payback_days(quadrant_index, avg_profit_per_tile_day, tiles_per_quadrant=25):
    cost = LAND_PRICES[quadrant_index]
    daily = avg_profit_per_tile_day * tiles_per_quadrant
    if daily <= 0:
        return float("inf")
    return cost / daily


def should_buy_land(quadrant_index, money, avg_profit_per_tile_day, turns_left, turns_per_day):
    if quadrant_index >= len(LAND_PRICES):
        return False
    cost = LAND_PRICES[quadrant_index]
    if money < cost * 1.3:  # keep a buffer so we don't strand ourselves
        return False
    days_left = turns_left / turns_per_day
    payback = land_payback_days(quadrant_index, avg_profit_per_tile_day)
    return payback < days_left * 0.6


def hire_marginal_cost(n_already_today, mult=1):
    return mult * fib(n_already_today)


def should_hire(n_already_today, backlog_tasks, value_per_task=15, mult=1):
    """Hire while the marginal hand's cost is comfortably below the value it can
    unlock for the day (backlog_tasks estimates unclaimed task count)."""
    cost = hire_marginal_cost(n_already_today, mult)
    return backlog_tasks > 0 and cost < value_per_task * 20  # a hand gets ~20 useful actions/day
