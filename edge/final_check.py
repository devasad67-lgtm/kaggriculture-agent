"""Package a bot dir into submission.tar.gz and validate it the way Kaggle loads it.

python final_check.py <bot_dir> <out_tar>
- tar contains only main.py at root
- extract into a clean temp dir, run a full 720-turn game vs a public bot from there
- report per-step max time, edge error count, statuses
"""
import io, contextlib, os, sys, tarfile, tempfile, time, shutil

bot_dir, out_tar = sys.argv[1], sys.argv[2]
with tarfile.open(out_tar, "w:gz") as tf:
    tf.add(os.path.join(bot_dir, "main.py"), arcname="main.py")
with tarfile.open(out_tar) as tf:
    names = tf.getnames()
print("tar members:", names, "size:", os.path.getsize(out_tar))
assert names == ["main.py"]

tmp = tempfile.mkdtemp()
with tarfile.open(out_tar) as tf:
    tf.extractall(tmp)
main = os.path.join(tmp, "main.py")

with contextlib.redirect_stdout(io.StringIO()):
    from kaggle_environments import make
    from kaggle_environments.agent import get_last_callable
src = open(main, encoding="utf-8").read()
t = time.time()
fn = get_last_callable(src, path=main)
print("load time: %.2fs  callable: %s" % (time.time() - t, fn.__name__))

times = []
def timed(obs, cfg=None):
    t0 = time.perf_counter()
    a = fn(obs, cfg)
    times.append(time.perf_counter() - t0)
    return a

opp = "D:/kaggle/bots/the-2945-farm-96-vs-the-top-10-public-bots/main.py"
with contextlib.redirect_stdout(io.StringIO()):
    env = make("kaggriculture", configuration={"seed": 424242, "episodeSteps": 720})
    env.run([timed, opp])
final = env.steps[-1]
print("result:", [(s.reward, s.status) for s in final])
print("steps acted: %d  step time avg=%.1fms max=%.1fms" % (len(times), 1000 * sum(times) / len(times), 1000 * max(times)))
edge = fn.__globals__.get("_EDGE")
print("edge errors:", getattr(edge, "errors", "n/a"))
shutil.rmtree(tmp, ignore_errors=True)
