"""Build a single-file edge agent: inner bot source embedded (zlib+b64) + edge_core + settings.

python build.py <inner_main.py> <out_dir> '<json settings>'
"""
import base64, json, os, sys, zlib

inner_path, out_dir, settings = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
src = open(inner_path, "rb").read()
blob = base64.b64encode(zlib.compress(src, 9)).decode()
here = os.path.dirname(os.path.abspath(__file__))
core = open(os.path.join(here, "market_brain.py"), encoding="utf-8").read() + chr(10) * 2 + open(os.path.join(here, "edge_core.py"), encoding="utf-8").read()
os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, "main.py"), "w", encoding="utf-8", newline="\n") as f:
    f.write("# Edge wrapper around an Apache-2.0 public Kaggriculture agent (notices in embedded source).\n")
    f.write("import base64 as _b64, zlib as _zlib\n")
    f.write(core)
    f.write("\n_INNER_NS = {'__name__': '_edge_inner'}\n")
    f.write(f"exec(compile(_zlib.decompress(_b64.b64decode({blob!r})), 'inner_main.py', 'exec'), _INNER_NS)\n")
    f.write(f"for _k, _v in {settings.get('inner_globals', {})!r}.items():\n"
            "    _INNER_NS[_k] = tuple(_v) if isinstance(_v, list) else _v\n")
    f.write("def _chassis():\n    impl = _INNER_NS.get('_IMPL')\n"
            "    for hk in ('_pk_host', '_PK3_HOST'):\n"
            "        h = _INNER_NS.get(hk)\n"
            "        if impl is None and isinstance(h, dict):\n"
            "            impl = h.get('_IMPL')\n"
            "    return getattr(impl, 'chassis', None)\n")
    f.write(f"_EDGE = Edge(_INNER_NS['agent'], {settings!r}, _chassis)\n\n")
    f.write("def agent(observation, configuration=None):\n    return _EDGE(observation, configuration)\n")
print("built", out_dir, os.path.getsize(os.path.join(out_dir, "main.py")))
