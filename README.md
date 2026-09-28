# Kaggriculture — Farming-Economy Agent

My agent for Kaggle's **[Kaggriculture](https://www.kaggle.com/competitions/kaggriculture)** simulation competition (September 2026):
a two-player, 30-day (720-turn) farm economy where each bot plants crops, raises animals, hires farm hands, buys land
and trades on a shared market whose prices react to supply and demand. The winner is the farm with more money at the end.

## Result

**Best global rank: 253 out of 10,000+ teams (top 300, rating 2471).**

## What I built

The final bots (`bots/L48_wf`, `bots/L48_mc`, `bots/L48_cg`) are an **edge layer** wrapped around a strong public
route-table agent (Apache-2.0, notices kept inside the embedded source). The inner agent plays a proven farm plan;
the edge layer post-processes its orders every turn:

| Layer | What it does |
|---|---|
| **Lead-48 premium selling** | Sells melon, wool, milk, strawberry etc. up to 48 turns ahead of the plan, so our lots reach the market before a same-plan rival's. |
| **Crashed-market metering** | When a premium price has collapsed, releases stock evenly over the town's demand ticks instead of dumping it. |
| **Detour courier** | Lets a hand drop carried goods at the shed on the way, so they can be sold earlier. |
| **Wool-first crew** | The sheep crew delivers wool before collecting fertilizer, winning the wool price race on yarn-shop boards. |
| **Rescue guard** | Detects a failed hire on day 1 that would leave animals unfed (they escape) and repairs it. |
| **Mirror-gated carrot fill** | Detects an opponent running the same plan from the public farm state and counters its carrot swap. |
| **Cheap opening** | A cheaper first-turn wheat trade. |

Every layer is wrapped in `try/except`: if anything fails, the inner agent's action goes through unchanged.

## How I tested

- **Arena / gauntlet** (`arena/`): parallel local tournaments against the public agent field, both seats, fixed seeds.
- **Real-ladder replay test** (`rnd/replaytest.py`, `rnd/rtbatch.py`): replays our bot against the opponent's *recorded*
  actions on the *same seed* as a real ladder game. That makes selling and timing changes exactly comparable game by game
  (wins flipped vs wins lost), instead of relying on noisy local tournaments.
- **Forensics** (`ladder/`, `rnd/`): per-item money ledger rebuilt from replays, mirror-opponent fingerprinting at day 1,
  per-shop-layout win rates, and comparisons with top-10 bots (production mix, geese, land and labor timing).
- **Engine study**: market price curves, order settlement, the shop random draw and the hire cost curve, read from the
  environment source and checked against replays.

## Repository layout

```
bots/L48_*/      final submitted bots (single-file main.py)
edge/            edge-layer source, build and packaging scripts
arena/           local tournament harness
rnd/             replay test, experiment layers, analysis tools
ladder/          ladder crawling and replay forensics scripts
kaggriculture/   my first agent, benchmarks and tests
beast/           early search-agent experiment
PROGRESS.md      day-by-day research log of every experiment and its result
```

Replays, logs and third-party public notebooks and agents are not included (see `.gitignore`).

## Running a bot

```bash
pip install kaggle-environments
python -c "from kaggle_environments import make; e=make('kaggriculture'); e.run(['bots/L48_wf/main.py','bots/L48_mc/main.py']); print([s['reward'] for s in e.steps[-1]])"
```
