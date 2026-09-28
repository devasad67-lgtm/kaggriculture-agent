import json, collections
r = json.load(open("D:/kaggle/ladder/episode-112577487-replay.json"))
steps = r["steps"]
names = r.get("info", {}).get("TeamNames")
print("teams:", names, "rewards:", r.get("rewards"))
me = [i for i, n in enumerate(names) if "asad" in n.lower()][0]
op = 1 - me
# errors / timeouts
print("final status:", [s["status"] for s in steps[-1]])
# money by day
for d in range(0, 30, 3):
    ob = steps[d * 24 + 23][0]["observation"]
    print("day", d, "me", round(ob["farms"][me]["money"]), "opp", round(ob["farms"][op]["money"]))
# identical-action check: first step where the two action streams differ
def norm(a):
    return json.dumps({k: a.get(k) for k in ("farmer", "hands")} if a else None, sort_keys=True)
diff = next((t for t in range(1, len(steps)) if norm(steps[t][me]["action"]) != norm(steps[t][op]["action"])), None)
print("first step with different farm actions:", diff)
# sales volume per item (ordered SELL qty, capped later by stock) and HIRE counts
for p, lab in ((me, "me"), (op, "opp")):
    sells = collections.Counter(); hires = 0
    for t in range(1, len(steps)):
        for o in (steps[t][p]["action"] or {}).get("market", []) or []:
            if o[0] == "SELL" and int(o[2]) > 0: sells[o[1]] += 1
            if o[0] == "HIRE": hires += 1
    print(lab, "sell-order steps:", dict(sells), "hires:", hires)
