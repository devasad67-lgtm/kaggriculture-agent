# Kaggriculture — progress (saved 2026-09-23 ~20:15 UTC)

## Current state
- **Final submission:** ref `56501992` (`D:\kaggle\edge\submission.tar.gz`, bot dir `D:\kaggle\bots\dp_L720a`)
  submitted 2026-09-23 19:05 UTC. Deadline: **2026-09-30 23:59 UTC**.
- Ladder: rating went 405 -> ~1552 within ~1 hour, still climbing. One close loss so far:
  episode 112577487 vs Yang Bai (-$1,567, lost in days 27-30; different bot, not a bug).

## What the agent is
- Inner engine: public Apache-2.0 bot `demand-preserving-turn-sale-timing` (tetsutani).
- Our edge layer (`D:\kaggle\edge\edge_core.py`): sells premium goods (all except WHEAT/FERTILIZER)
  as soon as held, up to what the inner tape plans to sell later (lead_steps=720).
- Local: 25/27 vs 8 public top bots; beats every shorter-lead variant.
- DO NOT enable `premium_first` (moving sells to slot 0): lost 30/30, about -$34k.

## Tools
- `D:\kaggle\arena\tourney.py` — round-robin (`--rr bots... --seeds N`)
- `D:\kaggle\arena\gauntlet.py` — candidates vs opponents (`--cands ... --opps ... --seeds N --both`)
- `D:\kaggle\edge\multi.py <lead> <crash|all> short=bot` — build an edge variant on a base
- `D:\kaggle\edge\final_check.py <bot_dir> <out_tar>` — package + Kaggle-style load/timing check
- `D:\kaggle\ladder\loss.py` — replay analysis of a lost ladder game
- Public bots: `D:\kaggle\bots\` (materialized from notebooks in `D:\kaggle\public\`)

## Next steps (when resuming)
1. `kaggle competitions episodes 56501992` -> download replays of losses into `D:\kaggle\ladder`.
2. Look for a repeated loss pattern (the one loss so far was decided in days 27-30).
3. Only resubmit if a fix wins clearly in the arena (gauntlet vs all public bots + dp_L720a).

## 2026-09-24 session (ladder rank 1346/9959, score 2147, 91W-34L)
- Losses are sub-1% margin vs same-family tape clones; top teams (DSM, M&M&P&Q: 5-5 vs each other) are private adaptive planners winning by $5-20k.
- DSM tape replay (edge/tapebot.py) scores ~$45k locally: adaptive play does not transfer. Dead end.
- New public bases (ca25, pioneers-c2, shepherds, harvest-ledger, cha22) form a rock-paper-scissors cycle with dp_L720a
  (arena/g_new.json, g_new2.json). Edge layer on new bases made them worse (37-43%). No candidate dominates -> kept 56501992.
- build.py now finds nested chassis (_pk_host/_PK3_HOST).
- Lead sweep vs current field (arena/g_dec.txt, fresh seeds 4000+): dp_L8a 32-16 (+420) vs public field, dp_L720a 16-32; but L720 beats L8 14-2 head-to-head (RPS).
- 2026-09-24 13:41 UTC: submitted dp_L8a as ref 56522649 (edge/sub_L8a.tar.gz); 56501992 (L720) left active (2170.5 at that time).
- Next: compare ladder win rates of 56522649 vs 56501992 after ~100 games each; if L8 converges higher, keep it; watch new public bots.
- 2026-09-24 late: submitted dp_L8o as ref 56528493 (edge/sub_L8o.tar.gz): lead-8 edge + opening [BUY 10, SELL 10, BUY 5 WHEAT].
  Why: our old opening (BUY 20/SELL 15) wastes ~$22 on step 0; base runs at ~$0 cash on day 0-1, so vs opponents with the cheap
  opening we sometimes can't buy feed, a cow escapes, and we lose big (-11k..-32k on ladder). dp_L8o: 35-0 vs dp-family (+16k),
  ~even vs cha22/ca25/pioneers, 73% overall (arena/g_open.txt, g_open2.txt).
- Beast (own planner, D:\kaggle\beast\main.py): ~$74k/game vs clone ~$140k; not competitive yet. Random search log arena/bsearch.jsonl.

## 2026-09-25 session (resumed after laptop shutdown)
- LB: L8a 56522649 = 2469 (~rank 533/9980); L8o 56528493 = 1166 and climbing (11-1 after 12 games, loss = vs our own L8a). #1 DSM 3068, #10 2923, #100 2693.
- ROOT CAUSE of L8a big losses: day-1 cash ~$0 -> HIRE orders fail -> the hand that should FEED cow #2 never exists -> cow escapes
  end of day 1 -> cascade (3-4 fewer animals, -$10k..-32k). 6/73 L8a games; = 6 of its 8 big losses. L8o 0/13 so far.
  Scan (rnd/losses.py): the ONLY unplanned escape in 212 of our games. Planned by tape: GOOSE escapes day 26, 1 STRAWBERRY withers day 21, carrots day 27.
- FIX: Rescue guard in edge/edge_core.py (setting rescue=true): from hour 12 (animals) / 16 (plants), days<=20/19, idle units
  feed/water at-risk tiles (consecutive_unfed>=1 & unfed / unwatered); busy unit hijacked only if time running out; buys wheat
  (selling shed items for cash if needed). Sabotage test (only 1 hire on day 1): without guard $54k + cow escaped, with guard $89k.
  Pre-rescue core saved as edge/edge_core_v2_pre_rescue.py. Bots: dp_L8r (L8o+rescue), dp_L8ra (animals only).
- NEW public: tetsutani dp updated 09-24 (bots/dp0924; me0924 and mr0924 are byte-identical copies). dp0924 beats dp_L8o 6-2 (+$875).
  v43u0924, pre0924, aai0924 lose 0-16 to L8o/L8a. Note: seat swap gives identical results (deterministic) -> no need for --both.
- Built on new base: n9_r (rescue only), n9_L8r (lead8+opening+rescue), n9_L8ar (lead8+rescue, own opening). Gauntlet -> arena/g_n9.txt
- Arena must use D:/kaggle/.venv/Scripts/python.exe. Analysis tools in D:/kaggle/rnd (prof.py per-product profile, empty.py, losses.py, one.py).
- User: don't submit until L8o's ladder result is known.
- Rescue v3 (final): gated on a FAILED HIRE today (hires_today < HIRE orders sent), animals only. Normal game: 0 action diffs vs L8o
  (verified). Sabotage: saves cow ($87k vs $54k). Earlier versions (plant rescue / missed-yesterday triggers) broke the tape:
  base waters every other day on purpose and moving an idle unit desyncs the tape's relative moves -> -$10k/game. Never move tape units in normal play.
- g_n9b (6 seeds 6100+): dp_L8r 21-9-6 (ties L8o, beats L8a 6-0 +12.7k, 3-3 vs dp0924); new-base builds n9_* worse. Kept old inner.
- Forum (topic 742856): only latest 2 subs are active, new sub retires the OLDER one; score = better of two; final = Bradley-Terry
  on win/loss; at 2250+ 40% of games decided by <$100. Replays contain info.seed -> arena/ladder_seeds.json (96 real boards),
  gauntlet.py --seedfile.
- Close L8o losses (colum2131, Prashant): identical farms/costs; lost on premium sell timing (wool/milk selling into recovered price).
  Idea: infer opponent sells exactly from public market inventory deltas (minus ours, minus town consumption) + their visible
  harvests -> track opponent premium stock -> time our sells. Lead sweep on ladder seeds running -> arena/g_lead_lad.txt.
- SEAT MATTERS in mirror games (dp_L8o vs itself: 119167 vs 120037) -> always --both.
- Lead sweep on ladder seeds (both seats, arena/g_lead2_lad.txt): L12 44%, L16 67%, L20 71%, L24 71%, L32 79% (L32 vs dp_L8o 10-0-2,
  vs r_L12 6-0, vs dp0924 8-4, vs cha22 8-4). Bots r_L<N> = old inner + opening + rescue + lead N.
- Adaptive rival-lead estimator (edge_core adapt=true) correctly reads rival lead (12 / 8) but evidence arrives late; not yet useful.
- Running g_lead3_lad (L24..L96 vs wide field incl dp_L720a, dp_L8a).
- g_lead3_lad: L48=L64=L96 identical (saturates) 95% vs 8 opps; L32 92.5%, L24 90%. Final fresh-seed check g_final48: r_L48 104-6 (94.5%) vs 11 opps.
- 2026-09-24 22:53 UTC: SUBMITTED r_L48 as ref 56533143 (edge/sub_L48r.tar.gz; final_check: 0 errors, max step 382ms). Retires L8a.
  Active pair now: L8o 56528493 + L48r 56533143.

## RESUME HERE (saved 2026-09-25 ~04:15 local / ~23:15 UTC 09-24)
- Active pair: L8o 56528493 (~2416) + r_L48 56533143 (submitted 22:53 UTC, expected to settle ~2650-2850).
- Tomorrow: 1) check scores; 2) download r_L48 episodes (kaggle competitions episodes 56533143 -> kaggle competitions replay <id> -p ladder/l48),
  run `python ladder/summ.py ladder/l48` and rnd/prof.py on losses; 3) losses vs private top bots are the next target
  (they out-produce us; see rnd/gap.py on ladder/top); 4) watch for public bots copying long leads -> re-sweep leads/opponents.
- Build any variant: python edge/build.py rnd/inner_dp.py bots/<name> '<json settings>' (settings of r_L48: premium_items 7 items,
  lead_steps 48, opening [[BUY_PRODUCT,WHEAT,10],[SELL,WHEAT,10],[BUY_PRODUCT,WHEAT,5]], rescue true).
- Test: D:/kaggle/.venv/Scripts/python.exe arena/gauntlet.py --cands X --opps ... --seedfile ladder_seeds.json --skip N --seeds 5 --both
- 2 submissions left today (UTC 09-24 ends soon; resets daily). Deadline 2026-09-30 23:59 UTC.

## 2026-09-25 ~09:30 UTC — ladder review (user: "L8a is best, last 2 subs worse")
- LB: L8a 2457.9 (retired), L8o 2404.2, L48r 2243.1. #1 Boey 3055, DSM 2936 (#10).
- Tools: rnd/crawl.py (episode metadata via API incl. opponents' submissionIds; ladder/crawl/eps.json), rnd/opp.py (losses per opp),
  rnd/pricecmp.py (per-product volume/price me vs opp), rnd/tl.py (per-day farm timeline of a team). Replays: ladder/l48, l8o2, dsm2.
- Win rate by opponent LB band (same bands => fair comparison):
  rank101-300: L8a 2/10, L8o 4/10, L48 1/2; rank301-700: L8a 46%, L8o 35%, L48 67%(n=9); 701-1500: 73/86/80%.
  => the three subs are statistically the SAME strength; score gap = opponent mix + noise (L48 met median rank 1247 vs L8a 660).
- DSM new sub 56541009: 65W of 68, beats rank 101-1500 by ~+$27k/game. Our subs are rank ~500-level bots.
- L48 big losses = self-collapse (vs DSM $62k, vs shiiin9 $54k): premium dumped into crashed market (MILK @$14, WOOL $76 vs DSM $117).
- DSM vs us timeline (rnd/tl.py): DSM 3 quads by day 9 (us day 14), 7.5 geese by day 11 (us 2.2 -> eggs uncrowded market),
  carrots from day 14, fewer sheep. Gains ~+9k more than us between day 14 and 20.

## 2026-09-25 afternoon — real-ladder replay harness + market work
- NEW TEST HARNESS (most important tool): rnd/replaytest.py + rnd/rtbatch.py <bot> <out.jsonl> <dirs> ; rnd/rtsum2.py [--valid] out.jsonl
  Our live bot vs opponent's RECORDED actions on the real seed. Reproduces ladder results exactly (verified 24/24).
  Valid for changes that keep our farm identical (sell timing); 'shops_same' flag marks games whose shop draws diverged.
- edge/rebuild.py <src_bot> <out> '<json overrides>' rebuilds any existing edge bot with current core (verified identical).
- 45% of our ladder games are vs exact mirror clones (identical farm): we win ~55%, median margin ~$650, decided d24+ strawberry/wool/carrot.
  vs different bots: 79% win.
- DSM mechanics (exact resim rnd/dsmgame.py): sells 1-4 units at each demand tick (h1,5,9..21) in crashed markets and
  holds a 50-70 item shed buffer through the day, empties it by h23; we dump 10-18 at h0 to $1. DSM drops crashed milk, runs geese.
- market_brain.py: MarketBrain (hold/allocate) = -7.5k/game (holding gifts price to rival). only_more variant = neutral.
  Meter floor mode: shed overflow (workers carry 55-97 items at night). Meter 'spread' mode (daily schedule over ticks,
  all sold by h21): +226/game, +1W on 101 L48 games, +576/game vs top700. Sweeping trigger (rt/sp*.jsonl).
- Public bot authors top out ~2620 (AI Dmitrii #154). Top10 = private bots.
- 2026-09-25 evening RESULTS (real-ladder replay harness, all games valid, 0 errors):
  L8o 127 games: orig 77W (top700 21W). +meter spread 0.4: 88W; 0.3: 92W; 0.3+courier (bots/L8o_mc): 93W (top700 35W), +287/game.
  L48 101 games: orig 80W. meter 0.3: 87W +465; 0.2: 83W; 0.4: 86W; 0.3+courier (bots/L48_mc): 87W +542/game.
  Detour courier (edge_core Courier): ~2.7 trips/game, +3W alone. Inner V9 courier knobs (inner_globals) had zero effect.
  Build: edge/rebuild.py bots/dp_L8o bots/L8o_mc '{"meter": true, "meter_mode": "spread", "meter_trigger": 0.3, "courier": true}'
  Live gauntlet vs 10 opps running -> arena/g_mc.txt

## 2026-09-25 17:20 UTC (resumed after 2nd laptop shutdown)
- SUBMITTED earlier today 16:24 UTC: L8o_mc = ref 56555308 (1647 after ~1h, climbing). Active pair: L8o_mc + r_L48 (2352.8).
- Candidate L48_mc (r_L48 + meter spread 0.3 + courier; edge/sub_L48_mc.tar.gz): replay test L8o games 102/124 (orig 77, L8o_mc 93),
  L48 games 87/101 (orig 80); top700 42 of 60 (L8o_mc 35). Live gauntlet g_mc48: 42-6, beats L8o_mc 6-0.
- L48_mcf = L48_mc + FertHand (ferthand=true: late-game extra hand fertilizes young crops). Replay test running -> rnd/rt/L48_mcf_*.jsonl
- User: do NOT submit until they ask; tell them when something beats the current sub.
- 18:30 UTC: L48_mcf (FertHand) REJECTED: 85W vs L48_mc 102W on same 124 games, -546/game. L48_mc remains the candidate.
- Loss analysis of L48_mc's 36 remaining replay losses (rnd/lossdiag.py -> rnd/ld48, rnd/ldsum.py, rnd/ld48_sum.txt):
  A) 7 games farm differs from day 5 (masayoshi, shiiin9, elmo x2, Crop Dustas, HowardLeeTW, DSM): opp plants strawberry/melon/
     more animals on day 1-5 instead of wheat; -85.9k total, 5 of them top-100 private bots. Production strategy gap.
  B) 7 games farm identical until day 10-25, then opp plants carrots/tomatoes earlier in freed wheat tiles
     (pensukesan, in blue, Howon, Asuka, Jamie Nojek, Satoshi, WilsonPzx): -4.0k total.
  C) 22 games identical farm: lost on sell price/timing race vs clone (median ~-300); 1 of them (Hikaru) = wheat micro-arbitrage
     (buy WHEAT at p, sell next step at p+1, ~2400 units).
- 19:00 UTC: user wants BIG margins (farm plan), not sell tweaks. Facts: DSM ladder avg $110k (max 160k), never >50k margin in 20 games.
  Inner bot = 41 fixed tapes ("routes"), days 0-5 route 0, day 6 route chosen by first 2 shops, day 27 -> route 2.
  Built rnd/inner_fr.py (env FROUTE forces route from day 6) -> bots/L48_fr (identical to L48_mc when unset, verified).
  Route sweep: rnd/routesweep.py, 16 top700 games x 42 routes -> rnd/rt/rs1.jsonl (route -1 = default).
- 19:45 UTC: route sweep (6 games x 42 routes, top700 opps): DEFAULT router best on every game (6/6 wins, +1401 avg margin);
  every forced route worse by 1.4k..18k/game. Farm-plan switching = no gain. FINAL RECOMMENDATION: submit L48_mc (edge/sub_L48_mc.tar.gz).
- 2026-09-25 18:37 UTC: SUBMITTED L48_mc as ref 56557869 (user approved). Active pair: L8o_mc 56555308 + L48_mc 56557869 (retires r_L48).
- 2026-09-26 ~00:30 UTC: DSM TAPE TRANSPLANT. Old tapebot.py had router bug (always route 0). New: rnd/dsm_tapes.json (81 DSM games),
  bots/dsmT0..11 = raw replay of DSM's action stream from its 12 highest-money games (dsmT0 = ep 113227907, $159,854).
  Arena vs L48_mc on ladder seeds: 11 tapes lose badly, dsmT0 wins 3/4 (skip20) + 12/16 (skip30, +6284 mean margin).
  Replay test on 225 real games running -> rnd/rt/dsmT0_*.jsonl. rnd/tapecross.py = tape A on board B vs recorded opp.
- dsmT0 REJECTED on real-ladder replay test: 32/99 wins (L48 orig 69), -23k/game; own money median $77k, range 30k-163k
  (raw tape breaks on other boards: weeds/shops). Arena 15/20 vs L48_mc was misleading (both crash the same market; L48_mc fell to 88k).
  Conclusion: copying top-bot tapes does not work; only a real adaptive planner could. L48_mc stays final.
- 2026-09-26: wheat arbitrage measured exactly (rnd/arbcheck.py): Hikaru's trades worth only +$301/game. Our WheatArb layer
  (edge_core arb=true, bots/L48_arb): 8 real games mean margin ~+$7/game (buying wheat also lifts rival's wheat price). REJECTED, not submitted.
  edge_core backup before arb: edge/edge_core_v3_pre_arb.py. Live: L8o_mc 2447.7, L48_mc 1935.8 (climbing).

## 2026-09-26 session (user: improve until better than current sub, then submit it yourself)
- LB 08:15 UTC: L48_mc 2475.7 rank 343/10035 (104W-28L), L8o_mc 2404.4 (78W-56L). #1 Boey 3110, #10 2902, #100 2654.
- Forum (kaggle competitions topics list/show kaggriculture; saved rnd/forum/): Rust sim, daily top-episodes dataset, lineage-weighted gauntlet tips.
- Community agent pack data/ext/kaggriculture-donor-agents-20260902 (119 agents) + r88-rivals: 14 newest/strongest as bots/x_*.
  Gauntlet arena/g_x.txt: L48_mc 82-2 vs all of them -> no better public base exists.
- New replays: ladder/l48mc (132, all L48_mc games), ladder/l8omc (56 L8o_mc losses). ladder/crawl/cur_eps.json.
- ROOT CAUSE of many same-farm losses (Teraya -4.8k etc): inner sheep crew worker (_v233_worker first version, 3 tiles each)
  does FEED>CARE>HARVEST>COLLECT_FERTILIZER per tile and delivers wool only when all tasks are done -> wool reaches the
  market ~3 steps after faster rivals who deliver before collecting fertilizer. Rival dumps first, we sell into a crashed price.
- FIX "wool first" (rnd/inner_wf.py, bots/L48_wf = L48_mc settings on patched inner): skip COLLECT_FERTILIZER while the worker
  carries WOOL or a sheep still has yield; deliver wool, then collect. 4 losses: 3 flip to wins (+6.4k, +6.6k, +5.8k), 1 halves.
- Full replay test running -> rnd/rt/wf_all.jsonl (summarize vs orig; l8omc 'orig' = L8o_mc results).
- DeferCollect edge layer (edge_core, setting defer) never fires: sheep crews are not tape units. Pre-defer core: edge/edge_core_v4_pre_defer.py.
- RESULT rnd/rt/wf_all.jsonl: L48 games 104->109W (0 wins lost, +336/game); L8o_mc losses 0->31W; top500 opps 37->53W.
  Live gauntlet arena/g_wf.txt vs base g_wf_base.txt: equal vs field; mirror vs L48_mc 2-4-4 (-26/game) = seat noise
  (strawberry same-slot sells; wool crashed in those games).
- 2026-09-26 10:00 UTC: SUBMITTED L48_wf as ref 56576330 (edge/sub_L48_wf.tar.gz, final_check 0 errors, max step 186ms).
  User told me to submit myself when better. Active pair: L48_mc 56557869 + L48_wf 56576330 (retires L8o_mc).
- Next ideas: same "deliver before collecting fertilizer" ordering for cow/goose crews if code-driven; check L48_wf ladder in ~12h.
- 2026-09-26 ~10:30 UTC: DECISION (user): FREEZE the bot. No more changes until L48_wf settles (~Sep 27 10:00 UTC).
  Then compare L48_wf vs L48_mc on the ladder. Reopen bigger changes only if the ML expert provides working scheduler code.
  Findings behind it: DSM also uses only 3 quadrants + 10-12 hands (SE empty) -> SE crew idea dead; farm has 0 free tiles d3-20;
  milk delivery timing = even with rivals (57 vs 58 days); eggs rare; strawberry rivals ~0.5 step earlier but tape-driven (risky).
  L48_wf first 4 ladder games: 4-0. Expert Q&A doc: https://claude.ai/code/artifact/4867a70c-badf-46c2-b3ad-9d37aeb480d6
- 2026-09-26 ~11:30 UTC: DSM vs us opening fingerprint (rnd/ldnew/finger.py): DSM plants 6 melons (we 12) and strawberries on days 3-5
  (we from day 6), 3rd quadrant by day 8 (we ~12), geese 3 by d8 / 7 by d10 (we 3 by d12); final median $106k vs $96k.
- Melon->strawberry swap probe (edge_core MelonSwap, setting mswap=k; bots/L48_ms2): STOP RULE HIT at k=2.
  Swapped strawberries live to d11 (tape waters them as melons) but have 0 yield at the tape's d10 melon HARVEST; tape then stops
  watering, fruit appears d12, plant turns to WEED d13. Net: lose 2 melons, gain ~0. Not tried k=4/6.
- IMPORTANT: real-ladder replay test is NOT valid for farm-plan changes: the world (weeds/shops RNG) diverges, the recorded opponent's
  money changes too (e.g. 17k->32k). Farm changes need live arena tests. Replay test stays exact only for timing/sell changes.
- Back to FREEZE: L48_mc + L48_wf active; compare on ~Sep 27 10:00 UTC.
- 2026-09-26 ~12:30 UTC: user chose the high-risk "scheduler" shot. Go/no-go test = tape (L48_wf) until day D, then own planner
  (beast/main.py Beast.adopt) maintains the farm (rnd/hyb/make.py -> bots/hyb12, hyb20). arena/g_hyb.txt vs L48_wf (4 seeds x2):
  hyb12 0-8 (-31.0k/game), hyb20 0-8 (-17.8k/game). Beast live vs L48_wf: $53k vs $99k.
  Diagnosis (ladder/bst/hyb-1601690949.json): planner lets 5 sheep escape (feed-skipping + sold needed wheat), plants carrots too late
  (22 unharvested at end), weeds spread. STOP RULE HIT: even farm maintenance loses ~$18k over 10 days -> scheduler not viable in time.
  Final plan: keep L48_mc + L48_wf; compare on the ladder ~Sep 27 10:00 UTC.
- 2026-09-26 afternoon: LIVE route sweep (rnd/hyb/lsweep.py, bots/L48_wf_fr + env FROUTE; rnd/hyb/ls1.jsonl, 10 seeds x 42 routes vs L48_wf).
  (Old replay-based route sweep was invalid: world diverges.) Route 103 earns MORE own money than the default on 10/10 boards
  (+2.2k..+6.9k), 104/112 similar. BUT live field test (arena/g_r103.txt vs g_r103_base.txt, 7 opps x 5 seeds x 2 seats):
  route 103 67% wins, margin +1043 vs default 81%, +2516. Leaving the default route relieves the rivals' markets more than it
  helps us (vs dp0924/cha22/moon/L48_mc ~60% instead of ~80%). REJECTED. Default router stays.
- Conditional route gate (expert's idea), rnd/hyb/gate.py -> rnd/hyb/gate1.jsonl: 72 paired live games (12 seeds x 3 opps
  dp0924/moon_q13/statma-ca20 x 2 seats), default route 68 wins vs route 103 16 wins; yarn boards 6-0, non-yarn 62-16; no shop pair
  where 103 wins (Brunch+Pizza 12-12 = 103 is the default there). Opponent gate also dead (103 worse vs every non-L48 bot; helps only
  vs exact L48 copies, i.e. our own subs). REJECTED. Farm-plan search space exhausted for this deadline.
- Loss-pattern mining (expert's last request): rnd/mine/feat.py (132 L48_mc ladder games, labels = L48_wf replay results, 23 losses),
  rnd/mine/scan.py (1266 threshold tests). Top pattern "opponent plants tomato by day 18": 11/22 lose vs 12/110 (p=0.0001) -> but it is
  a board type where BOTH bots run the same SE 10-tomato crew project (21/22 identical layouts, 19 same planting day); tomato sales are
  identical in all 20 such mirror games (8 units, day 27 h1, same revenue) -> races decided elsewhere by <$820. Other patterns
  (opp geese by d11, opp >=7 cows by d7) weak after multiple testing (p~0.01-0.02 of 1266 tests). NO actionable loss pattern.
  22 of 23 L48_wf losses are same-farm mirror races (22/114 mirror games lost); non-mirror games: 1 loss in 18. Farm-change search closed for this deadline.
- MIRROR-RACE ATTACK (expert): resimulated all 22 L48_wf mirror losses (rnd/mine/ml, lossdiag LD_PROCS=2; file lists need CRLF strip).
  Day-by-day cash attribution misleads (e.g. d29 egg dump = cash timing; egg revenue actually equal/higher for us).
  Per-item revenue: we trail in CARROT in 14/22 (-425 units, opp plants carrots on days 20-23 on tiles where our tape replants WHEAT)
  and STRAWBERRY 14/22; ahead in wool/milk/fertilizer.
  CarrotFill layer (edge_core cfill, cfill_days, cfill_max): swap tape's day 20-23 wheat replants to carrots (replay-valid: shops_same 22/22).
  cap 99: 0/22 flips, -5.1k own/game; cap 4/day: 0/22, -2.8k own/game. Cause: on the tape's wheat cycle a carrot tile yields ~1 carrot
  vs ~4 wheat (60 fewer wheat -2460 vs +13 carrots +581). Rival's carrot edge is a better-executed tape, not a swap. KILLED.
- CARROT CYCLE reverse-engineered (rnd/mine/cycle.py): rival's day 20-23 carrot cycle is IDENTICAL to our wheat cycle (same tile, unit,
  steps, waterings, harvest) except PLANT CARROT. Carrots rot to weed at age 4; only tape slots harvested at age<=3 are safe.
  Per-route table of safe slots (rnd/mine/ctable.py -> ctable_safe.json; deterministic: 1351/1351 identical across seeds; ~18/route).
  CarrotFill v2 (cfill_table, bots/L48_ct): swaps work (e.g. +46 carrots, -56 wheat) but value is a wash/negative: 1/22 mirror losses
  flipped, own money -$49..-1529 in 8 of 10 games with swaps. Carrot $51 vs wheat $40 but ~3.3 vs 4 units/tile, 2x seed cost,
  carrot price pushed down. KILLED.
- STRAWBERRY: planting identical in mirror losses (days 5-11: 4,8,4,4,13), harvests differ by <=1-2 units; revenue diffs +-$1k both
  ways, net ~-$112/game (2 atypical non-mirror-plan games excluded). Not a production-cycle difference. KILLED.
- Conclusion: all mirror-race production and timing hypotheses tested; nothing beats L48_wf. Live pair stays L48_mc + L48_wf.
- MICRO-RACE attack (last one): 22 mirror losses need to flip: <100:3, 100-250:4, 250-500:2, 500-1000:8, >1000:5 (and 14 of 92 mirror
  wins are within $250). Endgame timing knobs on 83 close games (|margin|<1500), exact replay test (rnd/mine/score.py, rnd/rt/vA|vB|vC):
  meter_end 718: 0 flips, margin -24; meter_last_hour 23: 0 flips, 0 change; courier_to 22 + courier_min 2: 0 flips, +2.
  Timing layer is saturated. KILLED. FINAL: no micro-race edge; keep L48_mc + L48_wf.
- 2026-09-26 ~16:30 UTC live ladder breakdown (ladder/crawl/live_now.csv): L48_wf 74 games 79.7% wins vs L48_mc 159 games 74.2%.
  By opp rank: 1-50 2 games 50% (med -7.4k), 51-100 4g 50%, 101-200 14g 43% (median margin -$79 = coin flips), 201-400 62%,
  401-700 76%, 701-1500 82%, 1500+ 93%. Rating ceiling = close races vs rank 101-200; top 10 needs beating rank 1-50 (production gap).
- ORDER-POSITION race (engine settles market orders index by index, lockstep): premium_first had a BUG (market[:10] after moving
  edge-appended SELLs to the front cut the tape's last HIRE -> tape desync; explains old -34k and new -37.8k/0-80). Fixed in edge_core
  (trim only sells). Valid retest bots/L48_pf2, 81/83 close games (2 lost to laptop shutdown): +5 flips / -22 wins lost, margin +370 -> -58. REJECTED.
  Live L48_wf is NOT affected (appended sells are at the end, only they get cut).
- Forum 743716 (dzjiann): 3 days RL on 196 cores -> ~top 100 max, weaker vs strong players than their DP/math approach.
- 2026-09-26 ~16:00 UTC FRESH LADDER (ladder/now/pull.py -> eps.json): L48_mc 2475.0 (team rank 302/10046), 162g 119-43 (73.5%);
  L48_wf 2233.7 (still settling), 77g 61-16 (79.2%). WF's higher win% = matchmaking mix (63/77 games vs rank>700); same-band rates
  equal or smaller samples (701-1500: 84.6 vs 82.1; 1-700: wf 6/14 vs mc 63/97). No evidence yet of a broad matchup gain.
  Top-10 cutoff ~2890 (+415 over L48_mc).
- USER: do NOT freeze; objective still top 10. Search high-upside mechanism, no submit.
- YIZHOU (rank 9, sub 56563275 uploaded 09-26) = the top-10 recipe: 96% vs rank 101-1500, 87% vs top-100 (Sep-20 version was 42%).
  Tools: ladder/now/top.py, topeps.py (12k episodes), ladder/yz/ (30 replays) + ledger.py (money-delta ledger, balances exactly),
  shopmix.py, tiles.py, empty.py, prices.py, crash.py, idle.py, ops.py.
  Ledger vs its opponents: +12.3k/game from tomato +4.7k, egg +3.4k, strawberry +4.0k, carrot +2.3k, wool +1.8k; melon -3.2k.
  Opponents earn the same vs Yizhou as vs us -> production edge, NOT suppression. Adaptive, shop-reactive (actions diverge from d4,
  right after the d3 shop): YARN->9-20 sheep, PIZZA->tomatoes 23-35 + 13-15 cows, PET_CAFE->90-170 carrots, BAKERY/BRUNCH->8-11 geese;
  tomatoes on EVERY board (8-35); strawberries 10 by d5; land d6/d9 (+SE d10 in 13/30); 12 units by d9-12; ~0 idle labor.
  Us (L48_mc ledger, 40 games): every item within a few hundred $ of the opponent = pure mirror races.
- PRICE REGIMES (162 replays): crowded goods crash after d14 (median d26: strawberry 25, milk 35, wool 55, melon 113 vs bases
  120/160/200/250); uncontested goods rise (tomato 61->83, p90 177; carrot 36->53; egg 51->55, deep market).
  We order ~410 units/game at <0.3x base (fert 191, milk 82, strawberry 77, wool 61) for ~$5.5k; Yizhou ~120.
  Our day-18 SE tomato project (10 plants) = 74 units, $9-31k revenue -> tomatoes under shop demand are very lucrative.
  Free capacity in our tape: 6-7 empty tiles d12-24 (12/30 games ~15 SE tiles empty >=10 days), 11-19 idle unit-steps/day.
- STRONGEST NEW HYPOTHESIS: "uncontested fill" = add tomato/goose(+CARE) production on free tiles/labor WITHOUT cutting contested
  production (cutting it relieves the mirror rival, cf. route 103). Needs live arena validation (world diverges in replay).
- 2026-09-26 evening: UNCONTESTED-FILL test (user: do not freeze, top 10 only objective).
  Free capacity of the tape (ladder/yz/free.py, 40 L48 games, tiles empty from day D to the end): 0 tiles in 65% of games
  (3-quadrant boards); 14-18 SE tiles only where an inner crew bought SE (YARN v233 from d12, TOMATO v219 from d19).
  Board split (l48mc, 132 games): tomato3+ 14-8 (band 100-700: 6-6), yarn2+ 17-8 (6-6), other 73-12 (35-6) -> 12/18 band
  losses on crew boards. Tomato3+ losses avg -$401 (mirror race); yarn losses = wool PRICE race (same units, rival avg
  $160 vs our $144 in the -5k games; L48_mc data, L48_wf wool-first may already address it).
  RULE A "tomato fill" (rnd/tf_layer.py appended to inner_wf via rnd/swapinner.py -> bots/L48_tf; L48_wf otherwise byte-identical):
  on V219 boards plant 10 tomatoes on SE rows 7-8 (d18-19), one extra hand hired daily AFTER all native/V219 hires
  (piggy-back on V219's request step, else hour>=7), must-water (unwatered yesterday) > harvest (>=2) > optional water.
  Bugs fixed on the way: SE still LOCKED at request step; hand only hired on V219 days -> plants withered; daily-water rule starved.
  Mirror tests vs L48_wf: ungated 22 in-sample tomato seeds 10-26-8 (margin -247); extra hand ~$3.8k + seeds $0.5k vs +$4-10k tomatoes.
  Gate d18 tomato price >=90 (in-sample: >=94 5/5 wins, <=87 0/13). OUT-OF-SAMPLE 117 new tomato3+ seeds: fires 21, W10 L11,
  +$1.8k/fired game (big wins +3..+14k, small losses -70..-3.9k). Adds money, NOT wins -> KILLED per stop rule.
  Rule B (extra sheep on yarn boards) killed on paper: +$540/sheep before labor, extra hand ~$5.4k/18 days.
  Conclusion: the tape is land- and labor-saturated; hire cost fib(n) (12th+ hand $144-610/day) kills any fill layer.
- 2026-09-26 late: WOOL ANALYSIS (ladder/wflive = all 83 L48_wf ladder replays; ladder/yz/yarnw2.py):
  L48_wf yarn boards 16-1 (only loss -120 vs rank 1786); same-sheep mirrors 13-1, wool price +4.6 $/unit, wool rev +2.7k/game.
  L48_mc same boards 17-8, -2.8 $/unit, -655. => wool-first already fixed the wool race. NO wool layer built, nothing submitted.
  L48_wf by board: other 41-11, tomato3+ 11-4, yarn2+ 15-1. Biggest loss (-11.8k vs Sonu Yadav r2560) = adaptive planner
  out-producing us (strawberry +8.7k, egg +5.4k, carrot +4.9k), no bug/escape.
- 2026-09-26 late: FINAL ADAPTIVE DECISION test = sheep veto on no-YARN boards (bots/L48_sv = L48_wf + edge setting
  animal_veto SHEEP from_day 6 unless YARN_STORE open; skips the tape's day-8/9 sheep, ~3.7/game; tape timing unchanged).
  Evidence for it: no-yarn boards wool median price $1 from d14 to end; our wool revenue after d12 ~ $120/game.
  Exact replay test (shops_same 43/44), 44 L48_wf ladder games: baseline 41-3 -> veto 23-21, flips +0 / -18,
  own money -2.2k, OPPONENT +4.9k/game. Our wool supply keeps the rival's wool at $1; removing it relieves the rival
  (same mechanism as route 103). Also loses big where YARN appears after d9. KILLED. Per user: development stops;
  L48_wf + L48_mc stay live. Per-head tool: ladder/yz/perhead.py.
- 2026-09-26 late: FORENSIC branch-point table (ladder/yz/forensic.py; Yizhou 30 vs L48_wf 83 ladder games, shops by d6):
  tomato: Y plants 6.5-11.6 by d12 (first d9) on every board, us 0 (first d18 via V219); Y tomato rev vs opp +4.3..+6.2k,
    opp tomato price vs Y $80 (PIZZA/FARM) / $56 vs ours $148 / $79 -> own gain AND rival suppression.
  goose: Y 6-7.5 by d12 vs us 1.7-3.3; +3.7..+4.9k eggs; opp egg price 50/43 vs 54/50.
  carrot: Y 3-7 seeds by d12 vs us 0.3-0.8; +1.9..+3.8k; opp carrot price 51/38 vs 57/44.
  cow: equal (we do better on milk). sheep: yarn equal; no-yarn we keep 6.6 vs 3.2 (and cutting them helps rival, see veto).
  Existing branch point = inner _router at step 144 (first 2 shops -> route table, 42 routes). Live sweep ls1 (10 seeds vs
  L48_wf): no route beats default on margin (best 103: -209, 7/10). => the only clean 2-way branch is already optimal.
  Tomato-early would need tile surgery on wheat replant cycles (CarrotFill precedent: wash/negative). Recommendation: freeze.
- 2026-09-26 END OF DAY (user: save, resume tomorrow). NOTHING SUBMITTED today after 10:00 UTC: no tested candidate beats L48_wf
  (L48_tf: no W/L gain; L48_sv: 41-3 -> 23-21). Live pair unchanged: L48_mc 56557869 + L48_wf 56576330.
  NEXT (proposed, not built): "tomato-first" for the V219 SE tomato crew = wool-first analogue (deliver/PLACE carried tomatoes
  before the next task so they sell ahead of a same-tape rival). Sale-timing only -> exact replay test valid.
  Targets tomato-board mirror losses (L48_wf 11-4: -161/-235/-844/-3454; L48_mc 8 losses avg -401).
  Test population: tomato3+ replays in ladder/l48mc (22) + ladder/wflive (15). Build via rnd/swapinner.py on bots/L48_wf.
  Fallback next: same delivery-first for egg/milk only if those sales are crew-driven (check first).
- 2026-09-27 (user: FINAL top-10 attempt; overlay on L48_wf, judge by W/L flips only). Tools in rnd/tfirst/ (ab.py = paired table
  by rank band + matchup class; cls.py = day-1 mirror fingerprint + first divergence; fresh replays ladder/fresh27 = 143 games vs rank<=700).
  Fresh ladder 13:30 UTC: team rank 253 (2471.3), top-10 cutoff 2895.7, #1 DSM 3106.7. vs rank 101-300: wf 4/10, mc 28/58.
  TOMATO-FIRST (bots/L48_tfd, rnd/tfirst/tfd_layer.py): 83 wf games 67-16 -> 63-20, 0 flipped / 4 lost; tomato boards -2.2k/game.
    Sells first (635 vs 638) but extra trips cost waterings (63 vs 80 tomatoes). Ceiling small: a 6-lot moves price ~5%. KILLED.
  ENGINE: market orders settle by order index, unit-by-unit lockstep; same item same step same index = exact tie (same prices).
  OPPONENT SIGNAL (causal): rival's whole farm is in our observation every step. 72/84 wf games are same-tape mirrors at day 1.
    Loss classes vs rank<=700 (fresh 143): carrotswap clone (replants CARROT where tape plants WHEAT, d7..d27) 25-24,
    pure mirror 20-13, other divergence 32-18 (wf 14-3), non-mirror 4-7. Carrot-swap = biggest loss pool.
  CarrotFill (L48_ct table) ungated on L48_wf (bots/L48_cf), 226 games: +8/-7; carrotswap +3/-0, pure -2 => it is a COUNTER, not an edge.
  GATED CarrotFill (bots/L48_cg; edge_core cfill_gate: day-1 mirror AND rival CARROT on a tile where ours is WHEAT, sticky;
    backup edge/edge_core_v7_pre_cgate.py): 222 paired games +3 flipped / -1 lost (mraz1006: late gate = partial swap 70->0),
    rank 101-700 +3/-0, margin +23. Control rebuild bots/L48_wf2 == live L48_wf exactly. Package edge/sub_L48_cg.tar.gz validated.
    Held-out 188 older games (rnd/rt/ho_cg.jsonl vs rnd/rt/wf_all.jsonl) running.
  Wheat pump front-run (Shawn404 buys the tape's 84-wheat pump 1 step early): 1/83 games, not a population lever.
  HELD-OUT (188 older L48/L8o_mc games, base = rnd/rt/wf_all.jsonl): +3 flipped / 0 lost, all carrotswap (-71->+46, -134->+9, -59->+155).
  ALL 406 paired games: 283-123 -> 288-118, flipped 6 / lost 1, net +5; carrotswap +5/-1 (+$61/game), pure +1/-0, div 0/0, nonmirror 0/0.
  => L48_cg = only candidate today with a demonstrated W/L gain over L48_wf (~+1.2% win rate, est. +10-20 rating; NOT a top-10 mover).
  Ready: edge/sub_L48_cg.tar.gz. NOT submitted; awaiting user's go (proposed: L48_cg replaces L48_mc, keep L48_wf).
- 2026-09-27 ~13:06 UTC: SUBMITTED L48_cg = ref 56609352 (user approved). Retires L48_mc 56557869. Active pair: L48_cg 56609352 + L48_wf 56576330.
  Pre-submit checks: tar = main.py only (== bots/L48_cg/main.py); final_check 720 steps, 0 edge errors, max step 564ms; deterministic (2 runs identical);
  216/216 gate-never-fired games identical to real L48_wf; 3 gate-fired games with 0 swaps differ by -$24/-41/-434 (table mode buys carrot
  seeds at the window-day start; no W/L change); 8 DeadlineExceeded rows = machine sleep (rerun: all identical to L48_wf).
  REVERT: resubmit edge/sub_L48_wf.tar.gz or edge/sub_L48_mc.tar.gz (checksums edge/releases/SHA256SUMS_20260927.txt).
- 2026-09-27 post-submit research:
  Rank 1-100 (11 games in our replay sets): 10/11 NON-MIRROR adaptive planners (Yizhou, Fourth_Quadrant #10, Densike, tine.sh x2,
    fshindo), losses -5.5k..-18.5k = production gap, not tie-break. Route forcing vs them = repeat of killed route sweeps (default best
    on every game, live sweep confirmed) -> not run.
  "div" mirror class (146 games, 111-35): first divergences of 43 losses spread over 38 patterns (weeds, stray tiles, one-off plantings,
    d0..d29); no dominant class -> no single-branch target. rnd/tfirst/div_all.txt.
  Remaining lever for top-10 = beating rank 1-100 planners on production; no L48_wf-compatible single branch found for it.
- 2026-09-28 (user: last day, top-10 push, research + free disk). D: 2.0 GB free of 51 GB; ladder/ = 32 GB (replays ~30 MB each).
  Ladder now: L48_cg 2170 (settling), L48_wf 2280. Top-10 cutoff ~2896.
  Cleanup proposed (retired-bot replays, re-downloadable): ladder/{l8,l8o,l8o2,reps,mm,top,dsm2} + kaggriculture/{replays_sample,replays} ~19 GB.
    Keep: l48, l48mc, l8omc, wflive, fresh27, yz (used by replay tests). Delete blocked by auto-mode; needs user OK.
  New public notebooks since 09-27 pulled to data/new28 (12). "2965 Master Hybrid" = V79 rollback, self-reported 2456 (title is clickbait).
    Top2 V4 / Harvest Ledger V81 / MarketShock-M1-WR1K (Ice&Fire) = same tape/router family (Hayashi shop router + Seven-Turn Rescue).
    God's Mode (Provorov): shop draw = f(seed, day, total empty tiles); one DIG changes next shop 76.6%, but seed unknown ->
    directed shop control 10-18% of games, player-0 only, score impact unmeasured by the author. Not buildable/validatable in time.
  Arena test of the new bots vs L48_cg blocked (running external notebook code needs user permission).
- 2026-09-28 FORENSIC (expert request, no code). Data: all 110 L48_wf ladder games vs rank<=700 (09-26..09-28) + 60 vs rank>700,
  scratchpad fx/ (fx.py features, an.py/an2.py). Live now: L48_wf 2280 (rank 547). vs 1-100 3-1, 101-300 9-20, 301-700 31-46, 700+ 108-27.
  L48_cg live is worse in every band: 101-300 4-9, 301-700 16-36 (31%), 700+ 57-32 (64% vs wf 80%) -> candidate for retirement.
  Classes (day-1 farm fingerprint): 100/110 strong games are MIRRORS of our tape; losses 60 mirror + 7 planners. Weak opps also 59/60 mirrors.
  Mirror losses: units identical (straw 217/217, milk 177/177); median ~-$840; 36/60 under $1k.
  Sale race (milk/wool/strawberry): rival realizes +$480/game better in our losses, we +$296 in our wins. Matching rival prices flips 21/60
    (each of milk/wool/straw alone 12). Rival sells MILK first on +1.2 days/game and in bigger orders (11.8 vs our 3.9 units; straw 15.7 vs 6.6).
    Strong vs weak clones on same first-2-shop world: identical production, strong get ~+$1.7/unit on milk/wool.
  Carrot boards (PET_CAFE/FARMERS_MARKET in first 4 shops): 77/110 strong games, 26-51 (other boards 17-16). Rival carrot seeds by d12 4.2 vs 0.8,
    carrot net +$650-1000 but costs wheat: carrot+wheat net only -$287/game, flips 4/46 (3 if price shared). Same gap vs weak opps (we win 28-14). NOT the lever.
  Wheat buy/resell loops (Yakouu, BorisV, YASH JAIN...): engine round trip nets 0; wheat net gap in those games -$31. NOT a lever.
  Planners (7 losses, avg -$6.7k): straw 23 vs 12 by d6, geese 5.9 vs 3.3, 2nd land d9 vs d11, carrots 7/tomato 6 by d12-18, +2.4 cows,
    more hands/fert; money EQUAL at d24 (76k), loss made in d24-30. Needs a planner; no single rule.
  Smallest rule candidate: mirror-gated premium sale front-run (milk/strawberry/wool one lot at the step the mirror rival would dump,
    instead of 4-unit metering). Upper bound 21/60 flips; exact replay test required. Not built (user/expert: no code yet).
- 2026-09-28 SALE-RACE TEST (expert GO, one surgical candidate): bots/L48_sr = L48_wf + PremiumRace layer (day-1 mirror gate at step 24,
  <=1 differing tile; then MILK/WOOL/STRAWBERRY sell whole shed stock each step, no metering). Exact replay on the 110 strong games
  (scratchpad fx/sr.jsonl, fx/score.py): base 43-67 -> cand 41-69, flipped 3 / lost 5, net -2, margin -211/game; 0 errors, shops same 110/110,
  nonmirror 10 games unchanged. 101-300: -1, 301-700: -1. KILLED per decision rule (wins_lost >= flipped).
  Lesson: the rival's price edge is not reproducible by dumping earlier/bigger; dumping our own stock lowers our average price.
  Rollback L48_cg -> L48_mc NOT submitted: only the latest 2 submissions are active, so resubmitting mc would retire L48_wf (needs user decision).
- 2026-09-28 FINAL STRUCTURAL SEARCH (expert: 30 min, no revisits). Action/state vocabulary (scratchpad fx/vocab.py): Yizhou 30 games,
  rank<=100 nonmirror planners 10, L48_wf 60. Literal gaps: tomato (13% vs 100%/70%, banned topic) and GEESE: we own geese in 62% of games
  (1.5 bought) vs Yizhou 93% (5.9) and planners 100% (4.8); egg sell orders 14 vs 30/53. Engine: goose $300, 1 egg/day from day 4,
  +1 egg care bonus when fed+cared, +1 fertilizer/day, feed 1 wheat/day -> ~$100/goose/day net on ONE coop tile (wheat tile ~$25/day);
  egg market deep (T=332, glut -20% max). Blockers: needs free tiles (tape fills 100% of tiles in 65% of games) and labor
  (~4-5 unit actions/goose/day; extra hands fib-priced $144-610/day, what killed tomato fill); a production change breaks exact
  replay (empty-tile count changes the shop RNG). Not implementable + validatable today -> not built, nothing submitted. Pair stays L48_wf + L48_cg.
- 2026-09-28 GOOSE FORENSIC (fx/goose.py; Yizhou 30, planners 10, L48_wf 110). First goose: Yizhou step 156 median (d6, 28/30 games, any shop
  pair), planners 152, L48_wf 151 (only 68/110 games, route-gated). Geese on farm d8/d10/d12: Yz 1.6/4.4/6.4, planners 4.2/5.1/5.5, us 0.7/0.7/2.4.
  First egg sale d11 for all. Cum egg revenue d10/15/20/25/29: Yz 0/1673/4594/7242/9298, planners 171/1971/3800/5519/6686, us 0/452/1438/2631/3203.
  Per goose-day: egg $74 (Yz) / $55 (pl) / $68 (us), feed 0.85-0.94 wheat (~$34), 3.6-4.2 coop unit-actions (~0.4 hand-day at ~10 productive
  actions/hand/day). Hire cost fib: 12th/13th hand $144/$233 per day. Corrected net/goose-day for L48_wf's saturated farm ~ 74 - 34 feed - 15 purchase
  - ~60 marginal labor - ~20 displaced tile = about -$50..-$20 (the earlier "$100 vs $25" excluded labor, purchase and tile). Top bots' edge is
  scale made affordable by their whole labor/land plan, not a detachable rule. No small rule; not built; DON'T SUBMIT.
