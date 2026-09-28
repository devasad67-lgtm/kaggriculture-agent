"""Build one edge config on several inner bases: python multi.py <lead> <items:crash|all> short=bot ..."""
import subprocess, sys, json
CRASH = ["MELON", "WOOL", "MILK", "STRAWBERRY"]
ALL = CRASH + ["TOMATO", "CARROT", "EGG"]
lead, items = int(sys.argv[1]), sys.argv[2]
pf = items.endswith("P"); items = items.rstrip("P")
tag = f"L{lead}{items[0]}" + ("P" if pf else "")
for pair in sys.argv[3:]:
    short, bot = pair.split("=")
    cfg = {"premium_items": CRASH if items == "crash" else ALL, "lead_steps": lead, "premium_first": pf}
    subprocess.run([sys.executable, "D:/kaggle/edge/build.py", f"D:/kaggle/bots/{bot}/main.py",
                    f"D:/kaggle/bots/{short}_{tag}", json.dumps(cfg)], check=True)

