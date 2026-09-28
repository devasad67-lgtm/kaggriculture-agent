# Kaggriculture Agent — Notes & Experiment Log

## Environment setup

- `kaggle-environments` pulls in a **huge** transitive dependency tree on a plain
  `pip install` (jax, flax, transformers, litellm, gymnax, open_spiel, pettingzoo,
  pokerkit, torch-adjacent stuff — apparently shared deps across every env
  bundled in the package, including unrelated LLM/RL environments). On Windows
  this blew past `MAX_PATH` (260 chars) while unpacking `orbax-checkpoint`'s
  nested test-fixture paths and pip aborted with an `OSError`. Windows long-path
  support (`HKLM\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled`)
  is **off** on this machine and enabling it needs an admin registry edit
  (outside the venv) — did not do this without asking.
  - **Fix used**: `pip install --no-deps kaggle-environments kaggle`, then
    verified by import + running an episode. The kaggriculture env only needs
    stdlib (`json`, `math`, `random`, `os.path`) — confirmed by reading
    `kaggriculture.py`'s import block. `kaggle` CLI similarly imports fine
    with its own light deps already satisfied transitively.
  - Importing `kaggle_environments` prints noisy `OpenSpiel exception: Unknown
    game '...'` warnings to stdout at import time (unrelated open_spiel proxy
    registrations failing because `--no-deps` skipped `open_spiel`). Harmless,
    but ugly — ignore/filter in any tooling that parses stdout.
  - venv at `D:\kaggle\.venv`. Installed: `kaggle-environments==1.32.7`,
    `kaggle==2.2.4`, both via `--no-deps`.

## Where the source lives

`D:\kaggle\.venv\Lib\site-packages\kaggle_environments\envs\kaggriculture\`
  - `kaggriculture.py` — interpreter, all game logic (source of truth).
  - `kaggriculture.json` — spec: config schema, **`actTimeout: 1`**,
    **`remainingOverageTime: 60`** (observation field, not just config).
  - `AGENTS.md`, `README.md` — human docs, consistent with the .py source in
    every case checked.

## Confirmed against source (prompt vs. reality)

Everything in the task prompt's game-rules section matches the installed
source **exactly** — crop/animal tables, yield-window formulas, market price
function (verified `MARKET_PARAMS` dict char-for-char against the prompt's
table), watering/feeding grace rules, care-bonus bookkeeping, turn processing
order, shed/hiring/spawn mechanics. No corrections needed there.

A few things the prompt didn't spell out, confirmed by reading the code:

1. **Per-turn time limit is real and tight.** `actTimeout = 1` second per
   turn, plus a shared **`remainingOverageTime` bank of 60 seconds for the
   whole 720-turn game** (observed directly: `obs["remainingOverageTime"]`
   starts at 60 and is presumably debited when a turn exceeds `actTimeout`).
   Budget: never approach 1s; target low tens of milliseconds so the overage
   bank is never touched by normal variance. `env.configuration` also exposes
   `runTimeout` (whole-run limit, framework-level, not agent-controlled).
2. **`obs["step"]`** is supplied directly by the framework (present in the
   live dict alongside `remainingOverageTime`), incrementing every turn
   across the whole game (`day*turnsPerDay+hour == step`, verified).
3. **Invalid/illegal actions are silent no-ops** everywhere — no exception,
   no error status. `_apply_unit_action` returns early on any illegal
   precondition. Confirms validator.py's job is to avoid *wasting turns*,
   not to avoid crashes.
4. **The bundled `"starter"` built-in agent is a CARROT loop**, not the WHEAT
   loop shown in the task prompt / AGENTS.md walkthrough. `agents = {"pass":
   pass_agent, "random": random_agent, "starter": starter_agent}` in
   `kaggriculture.py`, and `starter_agent` plants/waters/harvests CARROT only,
   never touches the market beyond buying carrot seed + selling carrot. The
   task prompt's WHEAT-loop snippet is real but is *not* what `"starter"`
   resolves to in `env.run([..., "starter"])` — bench.py must use the actual
   built-in for any comparison called "starter".
5. **`random_agent` behavior** (for benchmarking realism): farmer_ops pool is
   `[NORTH, SOUTH, EAST, WEST, WATER, HARVEST, PASS]`; 10% chance per turn to
   queue `BUY_SEED` of a random affordable crop; if any seed is available,
   30% chance to `PLANT` it instead of a random farmer_op. Hands (if any —
   random agent never hires) get a uniformly random farmer_op with no PLANT.
6. Market order queue processing is **per-unit lockstep across both
   players**, atomic ops (`HIRE`, `BUY_LAND`) resolved once per order slot in
   player-index order *before* the per-unit SELL/BUY loop for that slot.
   Effectively: order index 0 of both players' market lists resolves together
   (one unit each, interleaved) before index 1 starts. This matters for
   modeling opponent price impact — our sell of unit `k` of an order and the
   opponent's simultaneous sell of unit `k` of their same-index order see the
   *same* pre-commit price each unit-step, then inventory shifts by both
   players' commits at once.
7. `BUY_ANIMAL`/`BUY_PRODUCT`/`BUY_SEED` all respect `shedCapacity` (bought
   goods land in the shed and are rejected once the shed is full — not
   silently wasted money, the whole unit purchase step just fails and the
   order aborts for that player from that point).
8. Fertilizer applied via `FERTILIZE` extends `fertilized_until_day` to
   `day+2` (i.e. current day + 2 more = 3 days inclusive), and repeated
   `FERTILIZE` calls only ever extend forward (`max(...)`), never shrink.
9. `_new_plant`'s `max_lifespan_step` for one-time crops is set at creation to
   `(day + max_yield_day + 1) * turns_per_day` — i.e. it's computed once up
   front, not derived from watering history.
10. Agent call convention: every built-in agent (`pass_agent`, `random_agent`,
    `starter_agent`) takes a single `obs` positional arg. `main.py` supports
    both `agent(obs)` and `agent(obs, config)` defensively per the spec, but
    single-arg is what's actually used.

## Project layout

Following the architecture spec exactly:
```
kaggriculture/
  main.py, agent_lib/*, tests/*, bench.py, package.py, versions/, NOTES.md
```

## Build log

- [x] Section 0: env installed, source read fully, notes written.
- [x] constants.py, state.py, geometry.py + tests (22 passed).
- [x] market_model.py + exact-price tests, cross-checked against the real
      `market_price`/`_commit_unit` functions in the installed env (25 tests total incl. constants/state).
- [x] safe_agent.py + main.py + bench.py -> first candidate (wheat-loop safe
      agent alone: beats `pass`/`random` 100%, loses to `starter` 100%,
      ~$3.3-3.4k after 720 turns — expected, single tile, no hands).
- [x] tasks.py, scheduler.py, validator.py, trader.py, economics.py,
      strategy.py (full `Brain`) — first working end-to-end candidate.
- [ ] more benchmark iterations / tuning
- [ ] package.py + tarball validation
- [ ] test_scheduler.py, test_validator.py, test_full_game.py

## Milestone: main.py (full Brain) vs built-ins, 720 turns, 4 games each

| Matchup | main.py win rate | main.py mean $ | opponent mean $ |
|---|---|---|---|
| vs pass | 100% | 36,178 | 3,000 |
| vs random | 100% | 33,809 | 2 |
| vs starter (CARROT loop) | 100% | 33,252 | 3,490 |

Step timing: avg 0.5-0.63ms, max ~36-71ms per turn — far under the 1s
`actTimeout` and nowhere near touching the 60s `remainingOverageTime` bank.

### Bugs found & fixed while getting here

1. **Naive per-tile profit model wildly overrated MELON** (single-tile-isolation
   estimate ignoring our own price impact at volume: ~109/tile/day vs
   wheat's 18, carrot's 21). This poisoned two things: (a) the layout's
   crop-mix weighting, over-committing tiles to a crop with a 10-day first
   yield and no early income; (b) the land-buying ROI check, which used the
   same inflated average and triggered `BUY_LAND` on day 0 before any income
   existed. **Fix**: clip `crop_profit_per_tile_day` at `CROP_PROFIT_CAP=30`
   before using it for any allocation/ROI decision (`strategy._capped_profit`),
   cap any single crop's layout share at 35% with proportional redistribution,
   and gate `buy_land` behind `state.day >= 4` so it only fires once there's
   real income data. See `agent_lib/strategy.py`.
2. **Hiring bootstrap chicken-and-egg**: `hands_target` was originally based
   on *currently-occupied* tiles, which is 0 on turn 0 — so hands never got
   hired to help plant the very tiles that would make `hands_target` nonzero.
   Fixed by basing it on planned layout size (`len(memory.layout)`) instead,
   which is populated immediately from `unlocked_quadrants`.
3. **Target-selection oscillation**: the scheduler originally recomputed
   "nearest task" from scratch every turn with no memory. Early game, 5 units
   (farmer + 4 hands) all spawn within 1-2 tiles of each other and race for
   the same handful of nearby tasks; by the time a unit that "claimed" a
   target on turn N arrives on turn N+1, another unit has often already
   finished it, and picking a brand-new "nearest" target from scratch can
   reverse the walking direction every single turn (visible as farmer
   alternating WEST/EAST/WEST for 20+ turns without ever completing anything).
   **Fix**: added sticky per-unit commitments (`memory.commitments`,
   `agent_lib/scheduler.py`) — a unit keeps walking toward its previously
   chosen target across turns unless that target is genuinely no longer
   valid (task done by someone else, resource gone), instead of re-searching
   every turn. Residual thrash in the very first few turns (units converging
   on the same tiny initial task set) is expected and mostly harmless —
   confirmed by the bench results above.
4. Also fixed alongside the oscillation bug: **seed buffer too thin** for 5
   simultaneous planters — `SEED_BUFFER` raised from 3 to 8 and the
   restock target changed from `tiles_wanted // 3 + 1` to `tiles_wanted`, so
   the shared seed pool doesn't hit 0 (invalidating a unit's PLANT commitment
   partway through its walk) just because other units are drawing from it
   concurrently.
5. **`main.py`'s `__file__` pattern crashes at load time.** `kaggle_environments`
   loads `main.py` by reading its source text and `exec()`-ing it directly
   (see `kaggle_environments/agent.py:get_last_callable`) — `__file__` is
   *not* defined in that exec's globals, so the architecture spec's literal
   `os.path.dirname(os.path.abspath(__file__))` raises `NameError` immediately
   and the whole submission fails to load (this is fatal at agent-construction
   time, outside any try/except inside `agent()`). Fixed with a
   `try/except NameError` fallback to `os.getcwd()`. Note the loader *does*
   add the file's own directory to `sys.path` for that exec call regardless,
   so `agent_lib` imports resolve either way once the NameError is handled.

## Versioning mechanism

`versions/vN/` holds a frozen copy of `main.py` + `agent_lib` at some point in
time. The copied package is renamed `agent_lib_vN` (not `agent_lib`) and
`versions/vN/main.py`'s import updated to match — this is required because
`kaggle_environments` loads each `main.py` by `exec`-ing its source with the
file's directory appended to `sys.path`, and imported modules get cached in
`sys.modules` by name for the life of the Python process. If two different
`main.py` files (current + a frozen snapshot) both did `import agent_lib`,
whichever loaded first would "win" and the second would silently reuse the
first one's cached module instead of its own frozen copy — invisible bug in
any version-vs-version bench. Verified the mechanism itself by benchmarking
`main.py` against `versions/v1/main.py` (an exact snapshot of the same code):
result was a tie in both games with identical mean money, as expected.

## Package validation

`python package.py` builds `submission.tar.gz` (0.02 MiB, well under the 100
MiB cap), extracts it to a clean temp dir, and runs a self-play game from
there through `kaggle_environments.make(...).run([path, path])` — passed.

## Kaggle submission workflow (prepared, NOT run — waiting on explicit go-ahead)

```bash
# Confirm competition + entry status
kaggle competitions list -s "kaggriculture"
kaggle competitions list --group entered   # must show kaggriculture (accept rules on the site first)

# Single-file submit (main.py has no external deps beyond agent_lib, so prefer the tarball):
kaggle competitions submit kaggriculture -f main.py -m "<description>"

# Multi-file (preferred — main.py + agent_lib/):
python package.py                          # builds + validates submission.tar.gz
kaggle competitions submit kaggriculture -f submission.tar.gz -m "<description>"

# Status / diagnostics
kaggle competitions submissions kaggriculture
kaggle competitions episodes <SUBMISSION_ID>
kaggle competitions replay <EPISODE_ID> -p ./replays
kaggle competitions logs <EPISODE_ID> 0 -p ./logs
kaggle competitions leaderboard kaggriculture -s
```

Reminders: rules must be accepted on kaggle.com/competitions/kaggriculture
before the first submit; 5 submissions/day cap, only the latest 2 stay active
for the leaderboard, so don't spam. Entry deadline 2026-09-23, final
submission deadline 2026-09-30 (both 23:59 UTC per the prompt — verify on the
competition page before the actual deadline, since I haven't independently
confirmed those dates against Kaggle).

## Ladder loss diagnosis session (Phase 0 + real replay autopsy, v13 -> v14)

Live ladder rating dropped to ~370 after several losses. Confirmed via the
Kaggle CLI (token now configured) and direct replay analysis:

### Phase 0 (submission mechanics) — all clean
- Engine confirmed 1.32.7 (matches ladder).
- `main.py` now writes every caught exception (full traceback) and a
  running fallback counter to stderr, plus a `VERSION` string logged once
  per game — previously the fallback-to-safe_agent path was completely
  silent, so a real strategic loss and a silent crash-to-fallback were
  indistinguishable from the ladder logs alone. Verified the new logging
  actually fires via a forced-exception test.
- Added `tools/ladder_smoke.py`: extracts `submission.tar.gz` into a clean
  temp dir, plays a full game exactly the way the Kaggle loader does, and
  programmatically greps the captured stderr for fallback lines — fails
  loudly if any fallback occurred, VERSION never appeared, or any turn
  exceeded `actTimeout`. Passes clean on the current build.
- Confirmed `agent` is still the last module-level callable (regression
  test already existed from earlier session).
- Local per-turn timing (mean 0.69ms) closely matches the real ladder logs'
  reported ~0.6ms — ruled out "ladder silently running a slow/fallback path"
  as a cause.
- **Verified the actual uploaded `submission.tar.gz` (user-provided file)
  hashes to the exact same source as v13** — confirmed via `source_hash()`
  and a full `diff` of every file (only `main.py` differs, by the stderr/
  VERSION logging added *after* that upload — zero logic difference). So
  the ladder losses analyzed below are genuinely v13's real behavior, not a
  different/stale codebase.

### False alarm, corrected: no "SELL with zero stock" bug
Initial manual inspection of episode 111672473's replay seemed to show
`SELL WHEAT 53` issued while the agent's own shed showed `WHEAT: 0` at the
same recorded step — looked like a serious bug (selling wheat we don't
have). Root cause was in the *analysis tooling*, not the agent:
`kaggle_environments` records `steps[t][player]['action']` as the action
taken in response to `steps[t-1][player]['observation']`, not `steps[t]`'s
own — confirmed empirically (a SELL amount exactly equalled `shed[t-1] -
WHEAT_FEED_BUFFER`, not `shed[t] - WHEAT_FEED_BUFFER`). Fixed
`analysis/autopsy.py` to use the correct prior-entry pricing/pairing and
documented the convention prominently so it isn't rediscovered the hard
way again. Every SELL order, re-checked against the *correct* prior-step
shed value, was fully backed by available stock (0 over-requests) — the
agent's own sell logic is correct.

### Real finding underneath: wheat is heavily over-traded relative to top play
Even after the pairing fix, wheat volume is anomalously high — one lost
ladder game showed 6,781 wheat sold (opponent: 276) against only ~626
traceable acquisition (110 from matched harvest events + 516 bought back),
and even our own v13 self-play sample independently showed 935 wheat sold
(vs. a typical opponent's ~200-300) with elevated PICKUP/DROP counts. The
exact accounting gap in the ladder game isn't fully resolved (likely
undercounted harvest attribution — hand-position/action-array zipping
across up to 13 hands is the most likely source of measurement error, not
necessarily missing money), but the qualitative pattern — wheat
buy-then-mostly-sell-back churn, paying the bid/ask-style spread
repeatedly — is confirmed in both. Root cause identified: `trader.py`
step 5 (buy wheat when low for feed) and step 6 (sell wheat down to the
same buffer) fight each other in a feedback loop. Not yet fixed as of this
entry — flagged for a follow-up, separate from the animal-ramp experiment
below.

### DSM 8-game aggregate (much more robust than the earlier single-game calibration)
Downloaded and analyzed 8 full replays of the current #1 ladder player
(DSM), who won all 8. Built `analysis/aggregate_top1.py` to average stats
across them (tracking DSM by team name, since their player index varies):

- Final money: mean **$119,991** (median $120,216, range $91k-$144k) — the
  earlier single-game calibration ($92.5k) undersold the real target.
- **Working share 53.5%, moving 44.2%, idle 2.3% — consistent within a
  tight band across all 8 games**, confirming this is the load-bearing
  stat, not noise from one game.
- Animals bought (mean/game): **sheep 14.5 (their single most-bought
  animal), cow 9.2, goose 4.4** — meaningfully different ratio than the
  earlier single-game readout suggested (goose is a minor piece, not a
  major one).
- Hands ramp fast and hold: 5 (day 0) -> 7 (day 2-4) -> 9 (day 6) -> 12.8
  (day 10) -> steady ~12 through day 26 -> only tapers to ~11 right at the
  very end (day 28).
- Herd already has cow=2, sheep=3 on day 0 (immediate commitment), ramping
  to cow~7.5, sheep~11 by day 10-12 and holding roughly flat until a late
  taper.

**New, important context for the earlier v10 failure**: re-measured
current v13's own throughput (not the abandoned v6-v12 experimental
bundle) via self-play and found **48.0% working share** — much closer to
DSM's 53.5% than the ~34% figure that motivated abandoning the aggressive
ramp entirely. v13 (the current, simpler, bug-fixed baseline) apparently
already has meaningfully better throughput than the more elaborate v6-v12
bundle did (likely because that bundle's redundant shed-fetch dispatching,
fixed later, was itself part of the throughput problem). This means the
earlier "copying the aggressive ramp is a regression" conclusion was
correct *for that specific bundle*, but may not hold against the current,
better baseline — worth a fresh, narrower test.

**v14**: v13 + an animal-buy ramp shape recalibrated against the 8-game
DSM aggregate above (cow/sheep ramping from day 0, capped 8/14; goose
capped at 5, starting day 6 — previously goose started *earlier* than
cow/sheep in the day-based schedule, day 2 vs day 5, which explains why
earlier self-play showed goose-heavy buying (15 goose vs. 2 cow in one
v13 self-play sample) despite the animal-buy-priority-order fix: that fix
only prevents skipping to a *cheaper* animal when a priority one is
unaffordable, it doesn't change the fact that cow/sheep simply had zero
target for the first 5 days while goose already had a nonzero target from
day 2). **Benchmark vs v13: 0/40 (0.0%), mu=-27,849, sigma=5,368 — worse
than the original v10 failure**, mean money $8,088 vs v13's $35,938.

This is the **second** independently-designed aggressive-animal-timing
experiment (different exact ramp shape, tested against a materially better
throughput baseline than the first) to fail catastrophically. Conclusion:
this isn't primarily a throughput problem — something more fundamental is
missing relative to DSM's execution (most likely candidate: the wheat
buy/sell churn bug identified above, which actively bleeds money on every
cycle and would compound badly under a much larger, more expensive animal
commitment competing for the same scarce early cash). **Not pursuing
further aggressive-timing copies until the wheat churn bug is fixed and
re-measured — v13 remains the current best and what's packaged.** This is
exactly the kind of result the "change one variable, benchmark, keep only
provable wins" discipline exists to catch before it ships.

## Opponent archetypes from replays of players who beat us (Phase 2)

Analyzed the 3 real ladder opponents who beat us (episodes 111672473,
111673745, 111676022) and found three *completely different* winning
strategies, all beating v13:

- **Moritz Huber**: zero animals ever, aggressive land buying (all 4
  quadrants by day 12), heavy hiring (264 HIRE orders), crop-grind (2089
  WATER, 485 PLANT), melon-heavy. $23,240.
- **Sneha Bhargava4**: tiny footprint (2-6 hands, only 2 quadrants, low
  action counts overall), but sells patiently — milk averaged $293/unit,
  wool $212/unit (barely denting the market) instead of dumping volume.
  Working share only 31.1% (looks "inefficient") yet still beat us with
  $33,454.
- **ADOLE Edache**: zero crops ever (WATER=0, PLANT=0), pure animal
  husbandry (18 cow, 13 goose, 10 sheep bought), heavy FEED/CARE/
  COLLECT_FERTILIZER loop. Best trajectory of the three: $43,714, steadily
  climbing from day 4 onward.

Built `agent_lib/archetypes.py` (`CropOnlyBrain`, `LeanBrain`,
`AnimalOnlyBrain`) as statistically-parametrized sparring partners —
reusing the shared, already-tested pipeline (`state.parse`,
`tasks.generate`, `scheduler.assign`, `trader.orders`, `validator.finalize`)
and only swapping the layout/plan decision points, per the "parametrize
from replay statistics, never copy code" instruction. Wired into `bench.py`
via `ARCHETYPE_NAMES` so they load like any built-in (`--b crop_only` etc).

`crop_only` and `lean` reach realistic order-of-magnitude results in local
testing (crop_only ~$44k, lean ~$24k over 720 turns vs starter). `animal_only`
needed one fix (zero wheat farming meant sustained BUY_PRODUCT demand
pushed wheat price above trader.py's buy ceiling, starving the herd down to
1 animal and keeping it there — gave it a small 12-tile self-grown wheat
patch instead of touching the shared, production trader.py) but is still
weaker than its real counterpart even after that; treated as a "good
enough, non-crashing" approximate opponent rather than a perfect replica,
given time constraints — noted as a known limitation, not a hidden one.

**First real benchmark of v13 against something other than our own
lineage/starter — and it found a real, reproducible weakness:**

| Opponent | v13 result |
|---|---|
| `lean` (Sneha Bhargava4 pattern) | Win 72.5% |
| `animal_only` (ADOLE Edache pattern, weaker impl.) | Win 100% |
| `crop_only` (Moritz Huber pattern) | **Lose 20.0%** (mu=-8,569) |
| `starter` | Win 100% |

### Root cause of the crop_only loss, found via head-to-head autopsy

Ran a single representative v13-vs-crop_only game and compared hands/day:

- **v13 (lost, $13,503)**: hands 5 -> 11 (day 10-24) -> **2 (day 28) -> 1
  (day 29)** — collapses in exactly the days the game gets decided.
- **crop_only (won, $30,758)**: hands 5 -> 13 (day 10-24) -> **13 (day 28)**
  -> 1 (day 29) — holds until the very last day.

v13 still carries v5's original late-game hands taper (`hands_target`
capped to 3 once `turns_left <= LATE_TURNS` (4 days), forced to 0 once
`turns_left <= ENDGAME_TURNS` (1.5 days)). crop_only's plan has no such
taper. In the final ~5 days, v13 is working with 1-2 units while the
opponent still runs 13 — a massive harvest/sell volume gap in exactly the
window that decides the game (confirmed: v13's own bank was volatile/
crashing day 12->20, crop_only's climbed smoothly the whole game).

This is the *same* structural issue targeted by the abandoned v10/v11
attempt — but that attempt bundled the taper removal together with an
aggressive animal-buying ramp that independently failed catastrophically,
so the combined package lost and the (probably-good) taper removal never
got tested in isolation. **v16** = v13 with *only* the taper removed
(nothing else changed), benchmarked against both v13 (regression check)
and crop_only (does it fix the actual weakness): **(running)**.

## Real-replay-driven debugging session (v6-v10)

Context: live ladder rating ~444 after 3 games; a competitor's self-reported
notes (v2 prompt) warned local self-play win rate can badly mislead vs. real
ladder performance, and supplied one real replay's aggregate stats (episode
111645359: DSM $92,503 vs Majkel1337 $88,950, engine 1.32.7 — confirmed our
installed version matches exactly) as calibration. Built `analysis/autopsy.py`
to compute the same behavioral table (unit-turns, moving/working/idle share,
action-type counts, HIRE orders, animals bought, quadrants/hands/herd by day,
sold qty+avg price) from either a real `kaggle competitions replay` JSON or a
local self-play run — verified against the real replay first (numbers matched
the source's reported table almost exactly, e.g. HIRE orders 297 vs reported
297), then run against our own agent for direct comparison. This is what
actually drove every fix below — several were invisible in the 20-seed
paired-margin numbers alone (a bundle can win *and* still be badly miscalibrated
in ways a real ladder opponent would punish differently) and only surfaced by
comparing our agent's own day-by-day numbers against a real winning agent's.

**v6 (first bundle: fertilizer-restriction, endgame DROP/rush, hiring
cap+late-day gate, land workload check, pen buffer, animal-timing ramp
overhaul, feed wind-down) lost badly to v5: 5.0% win rate over 20 paired
seeds** (mu=-9261, sigma=5968). This is exactly the kind of result the
prompt's evaluation protocol exists to catch — several of these changes were
individually well-reasoned but combined into a real regression. Root cause
chain, found via the autopsy tool comparing our own agent's day-by-day stats
against the real replay's:

1. **Hire budget guard was strangling hiring at low cash.** `if cost >
   money * 0.5: break` in trader.py's HIRE loop meant that once money got
   tight (which happens early under an aggressive day-0 animal-buying
   ramp), hiring stopped almost immediately even though fib costs stay cheap
   in absolute terms — hand count was seen oscillating 5->2->5 in early
   testing. Real top agents keep 6-8+ hands even with the bank near zero.
   **Fix**: gate on plain affordability (`cost > money`) only; HIRE already
   runs first in trader.py's order list, which is enough to reserve its own
   budget.
2. **Animal-buying loop silently fell through to a cheaper animal type**
   when a higher-priority one was merely unaffordable that turn (`if
   have < cap: ...; if money >= cost: buy` had no `break` on the
   unaffordable path, so the for-loop just continued to the next, cheaper
   animal). This inverted the intended herd mix: self-play showed 13-17
   goose (cheapest, $300) bought vs 7-9 cow ($400), while DSM/Majkel ran
   cow-heavy (12/8 cow, 9/9 sheep, 9/6 goose) the whole game — because goose
   purchases kept succeeding during the exact stretch when money was
   tightest. **Fix**: `break` unconditionally at the first under-target
   animal in priority order, whether or not it was affordable this turn —
   don't buy anything this turn rather than opportunistically grabbing a
   cheaper option out of order.
3. **Hands collapsed 13->4->1 in the final days** (two separate causes).
   First, an explicit `if late and not liquidation: hands_target =
   min(hands_target, 3)` plus `hands_target = 0 if liquidation` — pure
   self-inflicted conservatism with no basis in real play (DSM kept 11 hands
   through day 29 of 30). **Fix**: removed both; labor stays valuable right
   up to the final sell-off, and more hands makes that push faster, not
   slower. Second, even after that fix, `hands_target` was still derived
   from `len(memory.layout)`, which `build_layout` deliberately stops
   growing (`PLANT_CUTOFF_TURNS`) once there's no time left for a *new*
   planting to mature — correct for the planting decision, wrong as a
   workload proxy, since every already-growing crop and placed animal still
   needs tending. **Fix**: workload = `max(planned layout size, actually-
   occupied tile count)`.
4. **Feed-profit wind-down (`FEED_PROFIT_CHECK_MIN_DAY`) fired far too
   early.** Set to day 15 as an unvalidated guess; self-play showed the herd
   crater between day 16-20 (goose 6->1, cow 6->4 in one run) — well before
   DSM/Majkel's real herd shrinkage, which doesn't start until ~day 24.
   **Fix**: raised to day 22, and `animal_daily_profit`'s fertilizer value
   changed from a hardcoded $40 estimate to the live `FERTILIZER` market
   price (threaded through `should_buy_animal`/`animal_payback_days` too).
5. **Delivery bug, exactly the class flagged in the source prompt**: animal
   pickup-from-shed was only a last-resort fallback (`elif action is None:
   ...`) that a busy farm's units almost never reached — confirmed directly
   via trace: 4 empty built pastures + 3 shed cows + 0 units carrying
   anything, simultaneously, for many consecutive turns. A dedicated audit
   test (`tests/test_livestock_delivery.py`) initially caught a backlog of
   15+ undelivered animals once the more aggressive buy-ramp (item 3 in the
   original v6 bundle) made the pre-existing gap in priority actually
   matter. **Fix**: restructured scheduler.py so fetch-wheat/fetch-
   fertilizer/fetch-animal are real prioritized jobs interleaved into the
   same priority list as field work (fetch_animal right after `water`;
   build_coop/build_pasture likewise promoted, since a bought animal with no
   pen is the same failure mode), with matching bird-in-hand arrival
   handling — not a fallback that only fires when a unit has literally
   nothing else to do. Backlog now stays at 0-1 for the rest of the game in
   the same test scenario that previously showed 15+.

**v7 (v6 + fix #1 only) still lost to v5: 5.0% win rate** (mu=-11144,
sigma=6668) — confirms fixes #2-5 were the load-bearing ones, not just the
hire budget.

**v10 (v6 + all five fixes above) vs v5: (running — see Experiment log for
the confirmed result).**

Residual gap still visible against the real replay even after all five
fixes: our self-play working share is ~34% vs DSM/Majkel's ~53%, moving
share ~63% vs ~44-45% — units spend meaningfully more of their turns walking
relative to working. `PICKUP` count is also elevated (298-409 vs DSM's
~207-209), consistent with redundant shed trips: `go_drop`/`fetch_*` targets
were deliberately exempted from the scheduler's `reserved` set (since the
shed can hold multiple units at once, unlike a single tile task), but that
also means multiple units can independently commit to fetching the *same*
single batch in one turn, with only one succeeding and the rest walking for
nothing. Worth a dedicated fix in a follow-up pass (a lightweight per-turn
dispatch-once flag per fetch kind, without reintroducing the original
"nothing else to do" fallback problem) — not yet done as of this entry.

### Resolution: v10 lost 0/40 to v5 — bisected down to the minimal real fix (v13)

Rather than accept the bundle, ran the paired-seed benchmark protocol
exactly as designed — one variable at a time, against this codebase's own
prior best, since that's the only signal actually testable without a live
ladder submission:

- **v10** (all five fixes + full ladder-timing calibration) vs v5: **0/40
  (0.0%)**, mu=-14,703. Worse than the original v6 bundle.
- **v11** (v10, but animal-buy ramp reverted to v5's slow day-based
  schedule) vs v5: **11/40 (27.5%)**, mu=-4,950. Confirms the aggressive
  day-0 animal-buying ramp — copied directly from the real replay — was the
  single largest regression source. Real top agents can afford that capital
  commitment because their execution throughput (working share ~53%) makes
  it pay off fast; at this agent's current throughput (~34-38%), the same
  commitment just produces a longer, deeper cash crunch with nothing to show
  for it yet.
- **v12** (v11, hands late/liquidation taper also reverted to v5) vs v5:
  **10/40 (25.0%)** — essentially unchanged, ruling out the hands taper as
  the second culprit.
- **v13** (v5's agent_lib **exactly**, with only three surgical patches:
  the hire-budget-guard fix, the animal-buy-priority-break fix, and the
  scheduler delivery restructuring) vs v5: **31/40 (77.5%), mu=+2,011,
  Phi(mu/sigma)~=0.62** — a clear, genuine win. **Promoted to `agent_lib/` /
  `main.py`.**

Confirmed the delivery bug was real and worth fixing independent of the
buying-rate question: audited v5's own (slower) animal-buying against the
same undelivered-backlog check and found it *also* has a real, growing
backlog (0->7 over 19 days in one test run) — just slower than v10's
runaway version because it buys less aggressively, not because delivery
itself was fine. After the fix, the same test plateaus at 11 (day 20-29 of
30) instead of climbing without bound — confirmed by extending the run to a
full 720 turns before setting the regression test's threshold.

**Takeaway for the rest of this project**: a real top-ladder replay is
excellent for finding genuine bugs (all three surgical fixes in v13 came
from comparing our own autopsy numbers against DSM/Majkel's) but is
dangerous to mine for *strategy parameters* to copy directly — those
parameters are calibrated to an execution quality this agent doesn't have
yet, and copying them without matching that execution quality made things
worse, not better, exactly the failure mode the evaluation protocol (paired
seeds, mu/sigma, bisect one variable at a time) exists to catch. The
`_animal_targets` ramp, `decide_plan`'s hands-taper, and everything else
from the abandoned v6-v10 bundle are preserved in `versions/v6`
through `versions/v12` for reference but are NOT part of the current agent.
Next real opportunity: close the working/moving-share gap (throughput,
routing) first — only once that's closer to real top-agent numbers does it
make sense to revisit a more aggressive opening.

## Experiment log

- **v1** (`versions/v1/`): first full Brain (tasks/scheduler/trader/strategy,
  no fertilizer, no endgame DROP handling, no opponent-awareness). 100% vs
  pass/random/starter over 20 seeds both seats, mean $31,365 vs starter's
  $3,420 (~9.2x). Zero errors, zero exceptions, step time avg 0.60ms/max 69ms.
- **v2** (`versions/v2/`): + fertilizer usage (tasks.py's `_fertilize_worthwhile`,
  scheduler carry/pickup logic for FERTILIZER). **60.0% vs v1's 40.0%** over 20
  seeds both seats (12-8), mean money $17,474 vs $17,264 — modest but real,
  kept per the "only keep it if it wins more" rule.
- **v3** (`versions/v3/`): + endgame correctness fix. Found that the env's
  auto end-of-day inventory drop only fires on a *full* day boundary
  (`(step+1) % turnsPerDay == 0`); with `episodeSteps=720=30*24` exactly, the
  game ends mid-way through day 30's last ~22 hours and that final partial
  day never reaches its own end-of-day event — anything still in a unit's
  inventory at game end was silently lost (harvested but never dropped to
  shed, so never sellable, never counted). Added `FINAL_RUSH_TURNS=10`
  (>= the max 8-tile walk to any shed corner on a fully-expanded board):
  once `turns_left <= 10`, any unit carrying inventory heads straight for
  the shed and DROPs instead of pursuing new field tasks. Also added
  `PLANT_CUTOFF_TURNS=60` so the layout stops assigning new crop roles once
  there's no longer time for even wheat (fastest cycle) to mature, harvest,
  and sell — previously the agent could plant a seed with zero chance of
  ever earning it back. Benchmark vs v2: **(running — see below)**.
- **v4** (`versions/v4/`): + opponent-awareness in selling
  (`trader._opponent_pressure`, using the opponent's *visible* tiles/animals
  as a proxy for upcoming supply — sell a product ~40% more aggressively when
  the opponent is visibly growing a lot of it too, racing to sell before
  their harvest crashes the price for both of us). **70.0% vs v3's 30.0%**
  over 20 seeds both seats (14-6), mean $17,582 vs $17,107.
- **v5** (current `agent_lib/` / `versions/v5/`): + ROI-aware animal buying.
  The old `_animal_targets` was a pure day-based schedule (grow toward a cap
  regardless of price); replaced with a gate through
  `economics.should_buy_animal` at *current* market prices (egg/milk/wool
  price vs. wheat feed cost vs. days left), so new animal purchases stop the
  moment they're no longer profitable — while never abandoning animals
  already placed. **100.0% vs v4's 0.0%** over 20 seeds both seats (20-0),
  mean $23,100 vs $16,433. This was the single biggest jump in the whole
  chain — the old schedule was systematically overbuying animals whose
  steady-state economics didn't justify the feed cost at prevailing prices.

## Final confirmed result (v5 = current `main.py`, 20 seeds, both seats, full 720 turns)

| Matchup | win rate | mean $ (ours) | mean $ (opponent) |
|---|---|---|---|
| v5 vs `starter` | **100%** | **38,872** | 3,432 (~11.3x) |
| v5 vs v4 | 100% | 23,100 | 16,433 |
| v4 vs v3 | 70% | 17,582 | 17,107 |
| v3 vs v2 | 65% | 17,629 | 17,243 |
| v2 vs v1 | 60% | 17,474 | 17,264 |
| v1 vs `starter` (first working candidate) | 100% | 31,365 | 3,420 |

Every step in the chain (v1→v5) was accepted only after winning >50% over
20 seeds in both seats against the previous best, per the "only keep it if
it wins more" rule. Zero agent exceptions and zero invalid-action crashes in
every recorded run. Step timing throughout: avg ~0.5-0.7ms, max ~70-85ms —
comfortably inside the 1s `actTimeout` with the 60s `remainingOverageTime`
bank never touched.

`submission.tar.gz` rebuilt from the current (v5) `agent_lib/` and validated:
extracts to a clean temp dir, self-plays successfully from there
(`python package.py` — see Package validation above), 0.02 MiB (well under
the 100 MiB cap).
