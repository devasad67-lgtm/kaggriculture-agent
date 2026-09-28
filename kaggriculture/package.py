#!/usr/bin/env python
"""Build submission.tar.gz (main.py at root + agent_lib/), then validate it by
extracting to a clean temp dir and running a full self-play game from there,
simulating how /kaggle_simulations/agent/ works at submission time. Also
hashes the source tree and the tarball's extracted contents and asserts they
match byte-for-byte, so "the tarball I'm about to submit" and "the code
bench.py actually measured" are provably the same thing — not just assumed."""
import hashlib
import os
import shutil
import sys
import tarfile
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(ROOT, "submission.tar.gz")
MAX_SIZE_MIB = 100


def _iter_source_files(base_dir):
    """(relative_posix_path, absolute_path) for main.py + every .py under
    agent_lib/, deterministically sorted, __pycache__ excluded."""
    files = [("main.py", os.path.join(base_dir, "main.py"))]
    agent_lib_dir = os.path.join(base_dir, "agent_lib")
    for root, dirs, names in os.walk(agent_lib_dir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in names:
            if not name.endswith(".py"):
                continue
            abs_path = os.path.join(root, name)
            rel_path = os.path.relpath(abs_path, base_dir).replace(os.sep, "/")
            files.append((rel_path, abs_path))
    return sorted(files, key=lambda t: t[0])


def source_hash(base_dir):
    """sha256 over (relative path, content) pairs for every shipped .py file —
    changes if any file's content OR the file set itself changes."""
    h = hashlib.sha256()
    for rel_path, abs_path in _iter_source_files(base_dir):
        h.update(rel_path.encode("utf-8"))
        with open(abs_path, "rb") as f:
            h.update(f.read())
    return h.hexdigest()


def build_tarball():
    if os.path.exists(OUT_PATH):
        os.remove(OUT_PATH)
    with tarfile.open(OUT_PATH, "w:gz") as tar:
        tar.add(os.path.join(ROOT, "main.py"), arcname="main.py")
        tar.add(os.path.join(ROOT, "agent_lib"), arcname="agent_lib", filter=_exclude_pycache)
    size_mib = os.path.getsize(OUT_PATH) / (1024 * 1024)
    print(f"Built {OUT_PATH} ({size_mib:.2f} MiB)")
    if size_mib > MAX_SIZE_MIB:
        raise SystemExit(f"submission.tar.gz exceeds {MAX_SIZE_MIB} MiB limit!")
    return OUT_PATH


def _exclude_pycache(tarinfo):
    if "__pycache__" in tarinfo.name or tarinfo.name.endswith(".pyc"):
        return None
    return tarinfo


def validate_extracted(tar_path, steps=100):
    tmp_dir = tempfile.mkdtemp(prefix="kaggriculture_pkg_")
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(tmp_dir)
        main_path = os.path.join(tmp_dir, "main.py")
        assert os.path.exists(main_path), "main.py missing at tarball root"

        live_hash = source_hash(ROOT)
        packaged_hash = source_hash(tmp_dir)
        print(f"Source hash (live agent_lib/):        {live_hash}")
        print(f"Source hash (extracted tarball):       {packaged_hash}")
        assert live_hash == packaged_hash, (
            "submission.tar.gz does NOT match the current agent_lib/main.py source — "
            "rebuild before trusting any benchmark number against it."
        )
        print("Tarball content hash matches live source exactly.")

        # sys.path is manipulated the same way the real grader's exec_dir
        # mechanism (and our own main.py fallback) does: the extracted dir
        # must be importable from a totally clean environment.
        sys.path.insert(0, tmp_dir)
        for mod in list(sys.modules):
            if mod == "agent_lib" or mod.startswith("agent_lib."):
                del sys.modules[mod]
        try:
            from kaggle_environments import make

            env = make("kaggriculture", configuration={"episodeSteps": steps}, debug=True)
            env.run([main_path, main_path])
            final = env.steps[-1]
            statuses = [s.status for s in final]
            print(f"Self-play from extracted tarball: statuses={statuses} rewards={[s.reward for s in final]}")
            assert all(s == "DONE" for s in statuses), f"non-DONE status: {statuses}"
        finally:
            sys.path.remove(tmp_dir)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    print("Package validation passed.")


def main():
    tar_path = build_tarball()
    validate_extracted(tar_path)


if __name__ == "__main__":
    main()
