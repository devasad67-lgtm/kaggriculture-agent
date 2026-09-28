"""Round-robin / head-to-head arena for Kaggriculture agents.

Each game runs in a fresh worker process so agent modules never leak between games
(kaggle_environments exec()s main.py and module caches are per process).

Usage:
  python tourney.py A B [--seeds 8]            # head-to-head, both seats per seed
  python tourney.py --rr bot1 bot2 ... --seeds 4
Bot names resolve to D:/kaggle/bots/<name>/main.py, or a direct path to a main.py.
"""
import argparse, itertools, json, multiprocessing as mp, os, sys, time, io, contextlib

BOTS = "D:/kaggle/bots"


def resolve(name):
    if name.endswith(".py"):
        return os.path.abspath(name)
    return os.path.abspath(os.path.join(BOTS, name, "main.py"))


def play(args):
    a, b, seed = args
    devnull = os.open(os.devnull, os.O_WRONLY); saved = os.dup(1); os.dup2(devnull, 1)
    try:
        return _play(a, b, seed)
    finally:
        os.dup2(saved, 1)


def _play(a, b, seed):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        from kaggle_environments import make
        env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720}, debug=False)
        t = time.time()
        # the loader resolves relative data files from cwd for some bots; point cwd at A's dir
        env.run([resolve(a), resolve(b)])
    final = env.steps[-1]
    return {"a": a, "b": b, "seed": seed, "ra": final[0].reward, "rb": final[1].reward,
            "sa": final[0].status, "sb": final[1].status, "sec": round(time.time() - t, 1)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("bots", nargs="*")
    p.add_argument("--rr", action="store_true")
    p.add_argument("--both", action="store_true")
    p.add_argument("--seeds", type=int, default=4)
    p.add_argument("--seed0", type=int, default=1000)
    p.add_argument("--procs", type=int, default=max(1, os.cpu_count() - 1))
    p.add_argument("--out", default=None)
    o = p.parse_args()
    pairs = list(itertools.combinations(o.bots, 2)) if o.rr else [(o.bots[0], o.bots[1])]
    jobs = []
    for a, b in pairs:
        for s in range(o.seeds):
            jobs.append((a, b, o.seed0 + s))
            if o.both:
                jobs.append((b, a, o.seed0 + s))
    results = []
    with mp.Pool(o.procs, maxtasksperchild=1) as pool:
        for r in pool.imap_unordered(play, jobs):
            results.append(r)
            print(f"{r['a'][:28]:28s} {r['ra']!s:>8} vs {r['rb']!s:<8} {r['b'][:28]:28s} seed={r['seed']} {r['sec']}s "
                  f"{'' if r['sa']==r['sb']=='DONE' else (r['sa'], r['sb'])}", flush=True)
    # summary
    stats = {}
    for r in results:
        for me, op, rm, ro in ((r["a"], r["b"], r["ra"], r["rb"]), (r["b"], r["a"], r["rb"], r["ra"])):
            s = stats.setdefault(me, {"w": 0, "l": 0, "t": 0, "money": [], "margin": []})
            rm = rm or 0; ro = ro or 0
            s["w" if rm > ro else "l" if rm < ro else "t"] += 1
            s["money"].append(rm); s["margin"].append(rm - ro)
    print("\n%-45s %5s %5s %5s %9s %9s" % ("bot", "W", "L", "T", "mean$", "margin"))
    for k, s in sorted(stats.items(), key=lambda kv: -(kv[1]["w"] + 0.5 * kv[1]["t"]) / max(1, len(kv[1]["money"]))):
        n = len(s["money"])
        print("%-45s %5d %5d %5d %9.0f %9.0f" % (k[-45:], s["w"], s["l"], s["t"], sum(s["money"]) / n, sum(s["margin"]) / n))
    if o.out:
        json.dump(results, open(o.out, "w"), indent=1)


if __name__ == "__main__":
    main()

