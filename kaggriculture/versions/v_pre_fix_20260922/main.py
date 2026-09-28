import os
import sys
import traceback

# kaggle_environments loads this file by exec'ing its source text directly
# (see kaggle_environments/agent.py:get_last_callable), so __file__ is not
# defined in that path. It does add this file's directory to sys.path for
# the duration of that exec, which is enough for the imports below to
# resolve; __file__ only works when main.py is imported normally instead.
try:
    _here = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _here = os.getcwd()
for _p in (_here, "/kaggle_simulations/agent"):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from agent_lib_v_pre_fix_20260922.safe_agent import safe_action  # noqa: E402

# Bump this on every candidate that gets packaged/submitted so ladder logs
# (kaggle competitions logs <EPISODE_ID> <idx>) can be matched back to
# exactly which build actually ran, independent of the submission's file
# name or timestamp.
VERSION = "v13-phase0-2026-09-21"

_brain = None
_brain_failed = False
_fallback_count = 0  # total turns spent NOT running the real Brain
_version_logged = False

# kaggle_environments' Agent.act() captures agent() stdout/stderr per turn
# and (per the competition FAQ) these are what `kaggle competitions logs`
# downloads — so writing here is how a caught exception becomes visible on
# the ladder after the fact, instead of silently degrading to safe_action
# with zero trace. Kept terse (one line) since logs are capped per turn
# (maxLogLength, default 10k chars) and this can fire every remaining turn
# once _brain_failed latches.


def _log_fallback(reason):
    global _fallback_count
    _fallback_count += 1
    print(f"[main.py] fallback #{_fallback_count} ({reason})", file=sys.stderr)


def agent(obs, config=None):
    global _brain, _brain_failed, _version_logged
    if not _version_logged:
        _version_logged = True
        step = obs.get("step") if isinstance(obs, dict) else getattr(obs, "step", None)
        print(f"[main.py] VERSION={VERSION} step={step}", file=sys.stderr)
    if not _brain_failed:
        try:
            if _brain is None:
                from agent_lib_v_pre_fix_20260922.strategy import Brain
                _brain = Brain(config)
            return _brain.act(obs)
        except Exception:
            _brain_failed = True
            tb = traceback.format_exc(limit=6)
            _log_fallback(f"Brain.act raised, latching to safe_action for the rest of the game: {tb}")
    else:
        _log_fallback("Brain previously failed this game")
    try:
        return safe_action(obs)
    except Exception:
        _log_fallback("safe_action ALSO raised, returning bare PASS")
        return {"farmer": ["PASS"], "hands": [], "market": []}
