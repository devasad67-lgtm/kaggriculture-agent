"""Regression test for a real submission gotcha: kaggle_environments loads
main.py by exec'ing its source text and taking the LAST callable defined at
module level (kaggle_environments/agent.py:get_last_callable does
`[v for v in env.values() if callable(v)][-1]`). If anything callable
(a function, class, or `from x import y`) is defined/imported after `agent`,
the loader silently picks THAT instead, and the real agent never runs.

This must keep passing after every edit to main.py.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _resolve_last_callable(path):
    """Mirrors kaggle_environments/agent.py:get_last_callable exactly,
    including its sys.path handling (it appends the file's directory for the
    duration of the exec call so sibling-package imports resolve, then pops
    it back off)."""
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    code_object = compile(raw, path, "exec")
    env = {}
    exec_dir = os.path.dirname(path)
    sys.path.append(exec_dir)
    try:
        exec(code_object, env)
    finally:
        sys.path.pop()
    callables = [v for v in env.values() if callable(v)]
    return callables, callables[-1] if callables else None


def test_last_callable_in_main_py_is_agent():
    callables, resolved = _resolve_last_callable(os.path.join(ROOT, "main.py"))
    assert resolved is not None, "no callables found in main.py at all"
    assert resolved.__name__ == "agent", (
        f"loader would resolve to {resolved.__name__!r}, not 'agent' — "
        f"callables in order: {[getattr(c, '__name__', repr(c)) for c in callables]}"
    )


def test_resolved_agent_is_actually_callable_with_obs_and_config():
    _, resolved = _resolve_last_callable(os.path.join(ROOT, "main.py"))
    # The real loader calls agent(observation, configuration) when the
    # function accepts 2 positional args (checked via co_argcount), or just
    # agent(observation) if it only accepts 1. Confirm both call shapes work
    # without raising, using a minimal well-formed obs.
    obs = {
        "player": 0, "day": 0, "hour": 0, "step": 0,
        "farms": [
            {"money": 3000, "tiles": [[None] * 10 for _ in range(10)], "farmer": [4, 4],
             "hands": [], "unlocked_quadrants": ["NW"], "hires_today": 0},
            {"money": 3000, "tiles": [[None] * 10 for _ in range(10)], "farmer": [4, 4],
             "hands": [], "unlocked_quadrants": ["NW"], "hires_today": 0},
        ],
        "private": {"shed": {}, "seeds": {}, "inventories": [{}]},
        "market": {"inventory": {}, "prices": {}},
        "town": {"unlocked_shops": []},
    }
    argcount = resolved.__code__.co_argcount
    args = [obs, {"episodeSteps": 720}][:argcount]
    result = resolved(*args)
    assert isinstance(result, dict)
    assert "farmer" in result and "hands" in result and "market" in result


def test_every_versioned_snapshot_also_resolves_correctly():
    versions_dir = os.path.join(ROOT, "versions")
    if not os.path.isdir(versions_dir):
        return
    for name in sorted(os.listdir(versions_dir)):
        main_path = os.path.join(versions_dir, name, "main.py")
        if not os.path.exists(main_path):
            continue
        _, resolved = _resolve_last_callable(main_path)
        assert resolved is not None and resolved.__name__ == "agent", (
            f"versions/{name}/main.py would not load correctly: "
            f"resolved to {getattr(resolved, '__name__', resolved)!r}"
        )
