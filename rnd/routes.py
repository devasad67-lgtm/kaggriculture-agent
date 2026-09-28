import sys,io,contextlib,collections
sys.argv=['x']
ns={'__name__':'inner'}
with contextlib.redirect_stdout(io.StringIO()): exec(open('rnd/inner_dp.py',encoding='utf-8').read(),ns)
R=ns['_ROUTES']; print('routes',len(R),sorted(R)[:50])
print('shop routes',collections.Counter(ns['_R108_SHOP_ROUTES'].values()))
print('old',collections.Counter(ns['_R110_OLD_SHOPS'].values()),'v92',collections.Counter(ns['_V92_TABLE'].values()))
