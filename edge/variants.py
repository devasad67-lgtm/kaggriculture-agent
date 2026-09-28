"""Build all edge variants listed here: python variants.py [inner_bot_name]"""
import subprocess, sys, json
INNER = sys.argv[1] if len(sys.argv) > 1 else "the-2945-farm-96-vs-the-top-10-public-bots"
CRASH = ["MELON", "WOOL", "MILK", "STRAWBERRY"]
ALL = CRASH + ["TOMATO", "CARROT", "EGG"]
V = {
    "edge_L2c": {"premium_items": CRASH, "lead_steps": 2},
    "edge_L4c": {"premium_items": CRASH, "lead_steps": 4},
    "edge_L8c": {"premium_items": CRASH, "lead_steps": 8},
    "edge_L4a": {"premium_items": ALL, "lead_steps": 4},
    "edge_L12c": {"premium_items": CRASH, "lead_steps": 12},
    "edge_L16c": {"premium_items": CRASH, "lead_steps": 16},
    "edge_L24c": {"premium_items": CRASH, "lead_steps": 24},
    "edge_L8a": {"premium_items": ALL, "lead_steps": 8},
}
only = sys.argv[2:] or list(V)
for name in only:
    subprocess.run([sys.executable, "D:/kaggle/edge/build.py", f"D:/kaggle/bots/{INNER}/main.py",
                    f"D:/kaggle/bots/{name}", json.dumps(V[name])], check=True)

