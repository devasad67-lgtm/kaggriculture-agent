"""Test candidate bots against a set of opponents; print per-(candidate, opponent) results.

python gauntlet.py --cands edge_L2c edge_L4c --opps base1 base2 --seeds 3 [--both]
"""
import argparse, multiprocessing as mp, os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tourney import play


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cands", nargs="+"); p.add_argument("--opps", nargs="+")
    p.add_argument("--seeds", type=int, default=3); p.add_argument("--seed0", type=int, default=2000)
    p.add_argument("--both", action="store_true"); p.add_argument("--procs", type=int, default=4)
    p.add_argument("--out", default=None); p.add_argument("--seedfile", default=None); p.add_argument("--skip", type=int, default=0)
    o = p.parse_args()
    jobs = []
    seedlist = json.load(open(o.seedfile))[o.skip:o.skip + o.seeds] if o.seedfile else [o.seed0 + s for s in range(o.seeds)]
    for c in o.cands:
        for op in o.opps:
            for sd in seedlist:
                jobs.append((c, op, sd))
                if o.both:
                    jobs.append((op, c, sd))
    res = {}
    t0 = time.time()
    with mp.Pool(o.procs, maxtasksperchild=1) as pool:
        for r in pool.imap_unordered(play, jobs):
            c, op, mine, theirs = (r["a"], r["b"], r["ra"], r["rb"]) if r["a"] in o.cands else (r["b"], r["a"], r["rb"], r["ra"])
            res.setdefault((c, op), []).append((mine or 0, theirs or 0, r["seed"]))
    print(f"{'candidate':22s} {'opponent':44s}  W  L  T   mean$   margin  ({time.time()-t0:.0f}s)")
    tot = {}
    for (c, op), v in sorted(res.items()):
        w = sum(a > b for a, b, _ in v); l = sum(a < b for a, b, _ in v); t = len(v) - w - l
        m = sum(a for a, _, _ in v) / len(v); mg = sum(a - b for a, b, _ in v) / len(v)
        tt = tot.setdefault(c, [0, 0, 0, 0.0, 0])
        tt[0] += w; tt[1] += l; tt[2] += t; tt[3] += mg * len(v); tt[4] += len(v)
        print(f"{c[:22]:22s} {op[:44]:44s} {w:2d} {l:2d} {t:2d} {m:8.0f} {mg:8.0f}")
    print("-- totals")
    for c, (w, l, t, mg, n) in tot.items():
        print(f"{c:22s} W{w} L{l} T{t}  winrate={(w + 0.5 * t) / n:.3f}  mean margin={mg / n:.0f}")
    if o.out:
        json.dump({f"{c}|{op}": v for (c, op), v in res.items()}, open(o.out, "w"))


if __name__ == "__main__":
    main()
