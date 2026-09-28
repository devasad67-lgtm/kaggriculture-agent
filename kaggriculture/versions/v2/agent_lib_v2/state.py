"""Parse the raw obs dict into a convenient, read-only GameState.

Tiles are kept as the raw dicts/None/"LOCKED" the env gives us (re-wrapping
every tile into a dataclass every turn is pure overhead for no benefit here);
GameState just adds derived scalars and typed access to the pieces every
other module needs repeatedly.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .constants import DEFAULTS


def cfg_get(config, key, default=None):
    if config is None:
        return DEFAULTS.get(key, default)
    if isinstance(config, dict):
        return config.get(key, DEFAULTS.get(key, default))
    return getattr(config, key, DEFAULTS.get(key, default))


def obs_get(obs, key, default=None):
    if isinstance(obs, dict):
        return obs.get(key, default)
    return getattr(obs, key, default)


@dataclass
class Unit:
    uid: int
    x: int
    y: int
    inventory: Dict[str, int]
    is_farmer: bool


@dataclass
class GameState:
    player: int
    day: int
    hour: int
    step: int
    turns_left: int
    turns_per_day: int
    board_size: int
    shed_capacity: int
    max_market_orders: int
    farm_hand_cost_mult: int

    money: float
    tiles: List[List[Any]]
    units: List[Unit]
    unlocked_quadrants: List[str]
    hires_today: int

    opp_money: float
    opp_tiles: List[List[Any]]
    opp_unlocked_quadrants: List[str]
    opp_farmer: Tuple[int, int]
    opp_hands: List[Tuple[int, int]]

    shed: Dict[str, int]
    seeds: Dict[str, int]

    prices: Dict[str, int]
    market_inventory: Dict[str, int]
    market_params: Optional[Dict[str, Any]]

    shops: List[str]

    raw: Any = field(repr=False, default=None)


def parse(obs, configuration=None) -> GameState:
    player = int(obs_get(obs, "player", 0) or 0)
    farms = obs_get(obs, "farms", []) or []
    opp_id = 1 - player

    me = farms[player] if player < len(farms) else {}
    opp = farms[opp_id] if opp_id < len(farms) else {}

    private = obs_get(obs, "private", {}) or {}
    shed = dict(private.get("shed", {}) if isinstance(private, dict) else {})
    seeds = dict(private.get("seeds", {}) if isinstance(private, dict) else {})
    inventories = private.get("inventories", [{}]) if isinstance(private, dict) else [{}]

    market = obs_get(obs, "market", {}) or {}
    prices = dict(market.get("prices", {}) if isinstance(market, dict) else {})
    market_inv = dict(market.get("inventory", {}) if isinstance(market, dict) else {})
    market_params = market.get("params") if isinstance(market, dict) else None

    town = obs_get(obs, "town", {}) or {}
    shops = list(town.get("unlocked_shops", []) if isinstance(town, dict) else [])

    turns_per_day = int(cfg_get(configuration, "turnsPerDay", 24) or 24)
    board_size = int(cfg_get(configuration, "boardSize", 10) or 10)
    shed_capacity = int(cfg_get(configuration, "shedCapacity", 100) or 100)
    max_orders = int(cfg_get(configuration, "maxMarketOrdersPerTurn", 10) or 10)
    hand_mult = int(cfg_get(configuration, "farmHandCostMult", 1) or 1)
    episode_steps = int(cfg_get(configuration, "episodeSteps", 720) or 720)

    step = obs_get(obs, "step", None)
    day = int(obs_get(obs, "day", 0) or 0)
    hour = int(obs_get(obs, "hour", 0) or 0)
    if step is None:
        step = day * turns_per_day + hour
    turns_left = max(0, episode_steps - int(step))

    farmer_pos = tuple(me.get("farmer", [0, 0]))
    hands_pos = [tuple(p) for p in me.get("hands", [])]

    units = [Unit(0, farmer_pos[0], farmer_pos[1], dict(inventories[0] if inventories else {}), True)]
    for i, pos in enumerate(hands_pos):
        inv = inventories[i + 1] if i + 1 < len(inventories) else {}
        units.append(Unit(i + 1, pos[0], pos[1], dict(inv), False))

    opp_farmer = tuple(opp.get("farmer", [0, 0])) if opp else (0, 0)
    opp_hands = [tuple(p) for p in opp.get("hands", [])] if opp else []

    return GameState(
        player=player,
        day=day,
        hour=hour,
        step=int(step),
        turns_left=turns_left,
        turns_per_day=turns_per_day,
        board_size=board_size,
        shed_capacity=shed_capacity,
        max_market_orders=max_orders,
        farm_hand_cost_mult=hand_mult,
        money=float(me.get("money", 0.0)),
        tiles=me.get("tiles", []),
        units=units,
        unlocked_quadrants=list(me.get("unlocked_quadrants", ["NW"])),
        hires_today=int(me.get("hires_today", 0)),
        opp_money=float(opp.get("money", 0.0)) if opp else 0.0,
        opp_tiles=opp.get("tiles", []) if opp else [],
        opp_unlocked_quadrants=list(opp.get("unlocked_quadrants", ["NW"])) if opp else ["NW"],
        opp_farmer=opp_farmer,
        opp_hands=opp_hands,
        shed=shed,
        seeds=seeds,
        prices=prices,
        market_inventory=market_inv,
        market_params=market_params,
        shops=shops,
        raw=obs,
    )


def tile_at(state: GameState, x: int, y: int):
    if 0 <= y < len(state.tiles) and 0 <= x < len(state.tiles[y]):
        return state.tiles[y][x]
    return "LOCKED"
