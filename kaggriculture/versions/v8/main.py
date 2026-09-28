import os
import sys

try:
    _here = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _here = os.getcwd()
for _p in (_here, "/kaggle_simulations/agent"):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from agent_lib_v8.safe_agent import safe_action  # noqa: E402

_brain = None


def agent(obs, config=None):
    global _brain
    try:
        if _brain is None:
            from agent_lib_v8.strategy import Brain
            _brain = Brain(config)
        return _brain.act(obs)
    except Exception:
        try:
            return safe_action(obs)
        except Exception:
            return {"farmer": ["PASS"], "hands": [], "market": []}
