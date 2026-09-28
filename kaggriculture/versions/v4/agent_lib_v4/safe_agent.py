"""Minimal, stateless wheat loop. Guaranteed to return a valid action dict and
never raise, given a well-formed obs. This is the fallback main.py reaches for
when the full Brain pipeline throws."""


def safe_action(obs):
    try:
        player = obs.get("player", 0) if isinstance(obs, dict) else getattr(obs, "player", 0)
        farms = obs.get("farms", []) if isinstance(obs, dict) else getattr(obs, "farms", [])
        private = (obs.get("private", {}) if isinstance(obs, dict) else getattr(obs, "private", {})) or {}
        day = obs.get("day", 0) if isinstance(obs, dict) else getattr(obs, "day", 0)

        if not farms or player is None or player >= len(farms):
            return {"farmer": ["PASS"], "hands": [], "market": []}

        me = farms[player]
        fx, fy = me["farmer"]
        tile = me["tiles"][fy][fx]
        seeds = private.get("seeds", {}) or {}
        shed = private.get("shed", {}) or {}
        money = me.get("money", 0)

        market = []
        wheat_in_shed = shed.get("WHEAT", 0)
        if wheat_in_shed > 0:
            market.append(["SELL", "WHEAT", wheat_in_shed])
        if seeds.get("WHEAT", 0) == 0 and money >= 10:
            market.append(["BUY_SEED", "WHEAT", 1])

        farmer = ["PASS"]
        if tile is None and seeds.get("WHEAT", 0) > 0:
            farmer = ["PLANT", "WHEAT"]
        elif isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop") == "WHEAT":
            age = day - tile.get("planted_day", day)
            if age >= 2 and tile.get("yield_units", 0) > 0:
                farmer = ["HARVEST"]
            elif not tile.get("watered_today", False):
                farmer = ["WATER"]

        return {"farmer": farmer, "hands": [], "market": market}
    except Exception:
        return {"farmer": ["PASS"], "hands": [], "market": []}
