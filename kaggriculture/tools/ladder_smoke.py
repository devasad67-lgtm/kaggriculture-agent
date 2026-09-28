#!/usr/bin/env python
"""Ladder smoke test: extracts submission.tar.gz into a clean temp dir (the
same shape as /kaggle_simulations/agent at grading time), loads main.py the
way the real kaggle_environments loader does (by path, exec'ing its source
text — see kaggle_environments/agent.py:get_last_callable), and plays a full
game against `random`. Fails (non-zero exit) if:
  - any step's stderr contains a "[main.py] fallback" line (Brain.act raised
    and we silently degraded to safe_agent/PASS — the exact failure mode
    that can't be told apart from a real strategic loss on the ladder
    without this instrumentation),
  - the VERSION line never appears,
  - any step exceeds actTimeout,
  - the game doesn't finish DONE.

Run before every submission:
    python tools/ladder_smoke.py
"""
import os
import re
import shutil
import statistics
import sys
import tarfile
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAR_PATH = os.path.join(ROOT, "submission.tar.gz")

FALLBACK_RE = re.compile(r"\[main\.py\] fallback #(\d+)")
VERSION_RE = re.compile(r"\[main\.py\] VERSION=(\S+)")


def main():
    if not os.path.exists(TAR_PATH):
        print(f"ERROR: {TAR_PATH} not found — run `python package.py` first.")
        return 1

    tmp_dir = tempfile.mkdtemp(prefix="ladder_smoke_")
    try:
        with tarfile.open(TAR_PATH, "r:gz") as tar:
            tar.extractall(tmp_dir)
        main_path = os.path.join(tmp_dir, "main.py")
        if not os.path.exists(main_path):
            print("ERROR: main.py missing at tarball root")
            return 1

        sys.path.insert(0, ROOT)
        from kaggle_environments import make

        env = make("kaggriculture", configuration={"episodeSteps": 720}, debug=False)
        env.run([main_path, "random"])

        final = env.steps[-1]
        statuses = [s.status for s in final]
        rewards = [s.reward for s in final]

        fallback_lines = []
        version_seen = None
        durations = []
        act_timeout = env.configuration.actTimeout
        overage_violations = 0

        for step_logs in env.logs:
            if not step_logs:
                continue
            our_log = step_logs[0]  # our agent is player 0 in this smoke test
            if not isinstance(our_log, dict):
                continue
            durations.append(our_log.get("duration", 0.0))
            if our_log.get("duration", 0.0) > act_timeout:
                overage_violations += 1
            err = our_log.get("stderr", "") or ""
            for m in FALLBACK_RE.finditer(err):
                fallback_lines.append(m.group(0))
            vm = VERSION_RE.search(err)
            if vm:
                version_seen = vm.group(1)

        print(f"VERSION seen: {version_seen}")
        print(f"Final statuses: {statuses}")
        print(f"Final rewards: {rewards}")
        if durations:
            p95 = statistics.quantiles(durations, n=100)[94] if len(durations) >= 20 else max(durations)
            print(f"Turn time: mean={statistics.mean(durations)*1000:.3f}ms "
                  f"p95={p95*1000:.3f}ms max={max(durations)*1000:.3f}ms "
                  f"(actTimeout={act_timeout*1000:.0f}ms)")
        print(f"Fallback lines seen: {len(fallback_lines)}")

        ok = True
        if any(s != "DONE" for s in statuses):
            print("FAIL: game did not finish DONE")
            ok = False
        if version_seen is None:
            print("FAIL: VERSION line never appeared in stderr")
            ok = False
        if fallback_lines:
            print(f"FAIL: {len(fallback_lines)} fallback(s) occurred — Brain.act raised at least once. "
                  f"First few: {fallback_lines[:3]}")
            ok = False
        if overage_violations:
            print(f"FAIL: {overage_violations} step(s) exceeded actTimeout ({act_timeout}s)")
            ok = False

        if ok:
            print("PASS: ladder smoke test clean (0 fallbacks, VERSION present, DONE, within actTimeout).")
        return 0 if ok else 1
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
