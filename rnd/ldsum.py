# categorize losses from rnd/lossdiag.py output
import json,glob,sys
d=sys.argv[1]
for p in sorted(glob.glob(d+'/*.prof.json'),key=lambda p:0):
    x=json.load(open(p)); me=x['me']; A=x['prof'][me]; B=x['prof'][1-me]
    mg=A['reward']-B['reward']
    same=A['lay']==B['lay']; qs=A['quads']==B['quads']
    rev=lambda P,k:P['sold'].get(k,0)*P['avgp'].get(k,0)
    ks=set(A['sold'])|set(B['sold'])
    dif=sorted(((rev(A,k)-rev(B,k),k,A['sold'].get(k,0),A['avgp'].get(k,0),B['sold'].get(k,0),B['avgp'].get(k,0)) for k in ks))
    cat='MIRROR' if same else ('SAMEQ' if qs else 'DIFF')
    print(f"{x['f'][8:17]} {B['name'][:18]:18s} margin={mg:+7.0f} {cat:6s} quads me/op d8={A['quads'][8]}/{B['quads'][8]} d14={A['quads'][14]}/{B['quads'][14]}")
    print('    worst: '+' | '.join(f"{k} {v:+.0f} ({a}@{ap} vs {b}@{bp})" for v,k,a,ap,b,bp in dif[:3]))
    if not same:
        for dd in ('10','20'):
            la=A['lay'].get(dd) or A['lay'].get(int(dd)); lb=B['lay'].get(dd) or B['lay'].get(int(dd))
            dd_={k:(la.get(k,0),lb.get(k,0)) for k in set(la)|set(lb) if la.get(k,0)!=lb.get(k,0)}
            print(f'    d{dd} diff me/op:',dd_)
