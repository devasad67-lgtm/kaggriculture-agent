#!/usr/bin/env python
"""Benchmark harness: paired-seed evaluation between two agents.

For each seed, plays BOTH seatings (a=P0,b=P1 and a=P1,b=P0) so seat
advantage cancels out of the comparison. Reports win rate AND paired-margin
statistics (mu, sigma, Phi(mu/sigma) as a less-noisy P(win) estimate under a
normal approximation) side by side — a change that raises the mean margin
while widening sigma more can still be a net loss in win probability, so
never steer on mean margin alone.

Usage:
    python bench.py --a main.py --b versions/v1/main.py --seeds 20
    python bench.py --a main.py --b starter --seeds 40 --pool holdout
"""
import argparse
import importlib.util
import json
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kaggle_environments import make  # noqa: E402

try:
    from package import source_hash
except Exception:
    source_hash = None

# Seed pools are disjoint on purpose: "tune" is for iterative development,
# "holdout" is never looked at during tuning and only used for a final
# confirmation, so tuning can't overfit to a specific seed set.
POOL_OFFSETS = {"tune": 0, "holdout": 100000}


ARCHETYPE_NAMES = ("crop_only", "lean", "animal_only")


def load_agent(spec):
    """spec is either a built-in name ("pass"/"random"/"starter"), one of our
    replay-calibrated opponent archetypes (ARCHETYPE_NAMES), or a .py path."""
    if spec in ("pass", "random", "starter"):
        return spec
    if spec in ARCHETYPE_NAMES:
        from agent_lib.archetypes import make_agent
        return make_agent(spec)
    path = os.path.abspath(spec)
    mod_name = "agent_mod_" + str(abs(hash(path)))
    module_spec = importlib.util.spec_from_file_location(mod_name, path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module.agent


def timed_agent(fn, timings, errors):
    """Wrap an agent function to record per-call wall time and exceptions."""
    if isinstance(fn, str):
        return fn  # built-in name; kaggle_environments handles timing itself

    def wrapped(obs, config=None):
        t0 = time.perf_counter()
        try:
            try:
                result = fn(obs, config)
            except TypeError:
                result = fn(obs)
        except Exception as e:
            errors.append(str(e))
            result = {"farmer": ["PASS"], "hands": [], "market": []}
        finally:
            timings.append(time.perf_counter() - t0)
        return result

    return wrapped


def _play_one(a_raw, b_raw, seed, episode_steps, swap):
    a_timings, a_errors = [], []
    b_timings, b_errors = [], []
    a_wrapped = timed_agent(a_raw, a_timings, a_errors)
    b_wrapped = timed_agent(b_raw, b_timings, b_errors)

    env = make("kaggriculture", configuration={"episodeSteps": episode_steps, "seed": seed}, debug=False)
    agents = [b_wrapped, a_wrapped] if swap else [a_wrapped, b_wrapped]
    env.run(agents)

    final = env.steps[-1]
    a_idx = 1 if swap else 0
    b_idx = 0 if swap else 1
    return {
        "a_money": final[a_idx].reward,
        "b_money": final[b_idx].reward,
        "a_status": final[a_idx].status,
        "b_status": final[b_idx].status,
        "a_errors": len(a_errors),
        "b_errors": len(b_errors),
        "a_avg_step_ms": (statistics.mean(a_timings) * 1000) if a_timings else 0.0,
        "a_max_step_ms": (max(a_timings) * 1000) if a_timings else 0.0,
        "b_avg_step_ms": (statistics.mean(b_timings) * 1000) if b_timings else 0.0,
        "b_max_step_ms": (max(b_timings) * 1000) if b_timings else 0.0,
    }


def run_paired(a_spec, b_spec, n_seeds, episode_steps, seeds=None):
    """Returns (games, pairs): `games` is every individual game played (2 per
    seed); `pairs` is one entry per seed combining both seatings, with
    `margin` = seat-cancelled (a_money - b_money)."""
    a_raw = load_agent(a_spec)
    b_raw = load_agent(b_spec)

    if seeds is None:
        seeds = list(range(1, n_seeds + 1))

    games = []
    pairs = []
    for seed in seeds:
        g1 = _play_one(a_raw, b_raw, seed, episode_steps, swap=False)
        g2 = _play_one(a_raw, b_raw, seed, episode_steps, swap=True)
        for g, swap in ((g1, False), (g2, True)):
            g = dict(g, seed=seed, swap=swap)
            if g["a_money"] is None or g["b_money"] is None:
                g["outcome"] = "error"
            elif g["a_money"] > g["b_money"]:
                g["outcome"] = "a_win"
            elif g["b_money"] > g["a_money"]:
                g["outcome"] = "b_win"
            else:
                g["outcome"] = "tie"
            games.append(g)

        valid = g1["a_money"] is not None and g1["b_money"] is not None and \
            g2["a_money"] is not None and g2["b_money"] is not None
        margin1 = (g1["a_money"] - g1["b_money"]) if valid else None
        margin2 = (g2["a_money"] - g2["b_money"]) if valid else None
        pairs.append({
            "seed": seed,
            "valid": valid,
            "margin": ((margin1 + margin2) / 2.0) if valid else None,
        })
    return games, pairs


def _phi(z):
    """Standard normal CDF, stdlib-only (no scipy)."""
    try:
        from statistics import NormalDist
        return NormalDist(0, 1).cdf(z)
    except Exception:
        # Abramowitz-Stegun erf approximation fallback.
        import math
        t = 1.0 / (1.0 + 0.3275911 * abs(z) / math.sqrt(2))
        y = 1.0 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * math.exp(-z * z / 2)
        cdf = 0.5 * (1.0 + (y if z >= 0 else -y))
        return cdf


def summarize(games, pairs, a_name, b_name):
    n = len(games)
    a_wins = sum(1 for r in games if r["outcome"] == "a_win")
    b_wins = sum(1 for r in games if r["outcome"] == "b_win")
    ties = sum(1 for r in games if r["outcome"] == "tie")
    errors = sum(1 for r in games if r["outcome"] == "error")
    a_moneys = [r["a_money"] for r in games if r["a_money"] is not None]
    b_moneys = [r["b_money"] for r in games if r["b_money"] is not None]
    a_err_total = sum(r["a_errors"] for r in games)
    b_err_total = sum(r["b_errors"] for r in games)
    a_avg_ms = statistics.mean([r["a_avg_step_ms"] for r in games]) if games else 0.0
    a_max_ms = max([r["a_max_step_ms"] for r in games], default=0.0)
    b_avg_ms = statistics.mean([r["b_avg_step_ms"] for r in games]) if games else 0.0
    b_max_ms = max([r["b_max_step_ms"] for r in games], default=0.0)

    margins = [p["margin"] for p in pairs if p["valid"]]
    mu = statistics.mean(margins) if margins else 0.0
    sigma = statistics.stdev(margins) if len(margins) > 1 else 0.0
    z = (mu / sigma) if sigma > 0 else (float("inf") if mu > 0 else (float("-inf") if mu < 0 else 0.0))
    p_win_est = _phi(z) if sigma > 0 else (1.0 if mu > 0 else (0.0 if mu < 0 else 0.5))

    print(f"\n=== {a_name} vs {b_name}  ({len(pairs)} paired seeds, {n} games) ===")
    print(f"{a_name}: {a_wins} wins  ({a_wins/n*100:.1f}%)")
    print(f"{b_name}: {b_wins} wins  ({b_wins/n*100:.1f}%)")
    print(f"ties: {ties}  errors: {errors}")
    if a_moneys:
        print(f"{a_name} money: mean={statistics.mean(a_moneys):.0f} median={statistics.median(a_moneys):.0f} min={min(a_moneys):.0f} max={max(a_moneys):.0f}")
    if b_moneys:
        print(f"{b_name} money: mean={statistics.mean(b_moneys):.0f} median={statistics.median(b_moneys):.0f} min={min(b_moneys):.0f} max={max(b_moneys):.0f}")
    print(f"paired margin (a-b, seat-cancelled): mu={mu:.0f} sigma={sigma:.0f} Phi(mu/sigma)~=P(a wins)={p_win_est:.3f}")
    print(f"{a_name} agent exceptions (caught): {a_err_total}   step time avg={a_avg_ms:.2f}ms max={a_max_ms:.2f}ms")
    print(f"{b_name} agent exceptions (caught): {b_err_total}   step time avg={b_avg_ms:.2f}ms max={b_max_ms:.2f}ms")

    return {
        "a_name": a_name, "b_name": b_name, "n_games": n, "n_pairs": len(pairs),
        "a_wins": a_wins, "b_wins": b_wins, "ties": ties, "errors": errors,
        "a_win_rate": a_wins / n if n else 0.0,
        "a_money_mean": statistics.mean(a_moneys) if a_moneys else None,
        "a_money_median": statistics.median(a_moneys) if a_moneys else None,
        "b_money_mean": statistics.mean(b_moneys) if b_moneys else None,
        "b_money_median": statistics.median(b_moneys) if b_moneys else None,
        "paired_margin_mu": mu,
        "paired_margin_sigma": sigma,
        "paired_margin_phi_p_win": p_win_est,
        "a_errors_total": a_err_total, "b_errors_total": b_err_total,
        "a_avg_step_ms": a_avg_ms, "a_max_step_ms": a_max_ms,
        "b_avg_step_ms": b_avg_ms, "b_max_step_ms": b_max_ms,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--seeds", type=int, default=20, help="number of paired seeds (2 games each)")
    ap.add_argument("--games", type=int, default=None, help="deprecated alias for --seeds")
    ap.add_argument("--steps", type=int, default=720)
    ap.add_argument("--pool", choices=["tune", "holdout"], default="tune",
                     help="disjoint seed ranges so tuning can never overfit to the confirmation set")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    n_seeds = args.games if args.games is not None else args.seeds
    offset = POOL_OFFSETS[args.pool]
    seeds = list(range(offset + 1, offset + 1 + n_seeds))

    games, pairs = run_paired(args.a, args.b, n_seeds, args.steps, seeds=seeds)
    summary = summarize(games, pairs, args.a, args.b)
    summary["pool"] = args.pool
    summary["seeds"] = seeds
    if source_hash is not None:
        try:
            summary["source_hash"] = source_hash(os.path.dirname(os.path.abspath(__file__)))
        except Exception:
            pass

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bench_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = args.out or os.path.join(
        out_dir,
        f"{os.path.basename(args.a).replace('/', '_')}_vs_{os.path.basename(args.b).replace('/', '_')}_{args.pool}_{int(time.time())}.json",
    )
    with open(out_path, "w") as f:
        json.dump({"summary": summary, "games": games, "pairs": pairs}, f, indent=2)
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
