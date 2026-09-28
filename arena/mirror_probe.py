import sys, os, json, io, contextlib, collections
bot = sys.argv[1]; seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
other = sys.argv[3] if len(sys.argv) > 3 else bot
sys.path.insert(0, os.path.dirname(__file__))
from tourney import resolve
with contextlib.redirect_stdout(io.StringIO()):
    from kaggle_environments import make
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.run([resolve(bot), resolve(other)])
steps = env.steps
print("final", [s.reward for s in steps[-1]])
PREM = ("MELON", "WOOL", "MILK", "STRAWBERRY", "TOMATO", "CARROT", "EGG")
pos = collections.Counter(); sold = collections.Counter(); first_sell = {}
for t in range(1, len(steps)):
    for p in (0, 1):
        m = (steps[t][p].action or {}).get("market", []) or []
        for i, o in enumerate(m):
            if o and o[0] == "SELL" and o[1] in PREM and int(o[2]) > 0:
                pos[(p, i)] += 1
                sold[(p, o[1])] += int(o[2])
print("premium SELL slot index counts:", sorted(pos.items()))
print("premium qty ordered:", sorted(sold.items()))
# money over time
for d in range(0, 30, 3):
    t = min(len(steps) - 1, d * 24 + 23)
    ob = steps[t][0].observation
    print(d, [round(f["money"]) for f in ob["farms"]], ob["market"]["prices"])
json.dump([[s.action for s in st] for st in steps], open(f"probe_{seed}.json", "w"))
