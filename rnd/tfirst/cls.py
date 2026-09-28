import json,glob,sys,collections
E={str(e['ep']):e for e in json.load(open('ladder/now/eps.json'))}
def sig(t):
    if t is None: return '.'
    if t=='LOCKED': return 'L'
    return (t.get('kind','')[:2])+(t.get('crop') or t.get('animal') or '')[:2]
def diff(o,me,op):
    a=o['farms'][me]['tiles'];b=o['farms'][op]['tiles']
    return [(sig(a[y][x]),sig(b[y][x])) for y in range(len(a)) for x in range(len(a)) if sig(a[y][x])!=sig(b[y][x])]
for f in (sorted(glob.glob(sys.argv[1]+'/*.json')) if len(sys.argv)==2 else sys.argv[1:]):
    r=json.load(open(f,encoding='utf8'));s=r['steps'];N=r['info']['TeamNames']
    me=[i for i,x in enumerate(N) if 'asad' in x.lower()][0];op=1-me
    ep=f.split('-')[1];e=E.get(ep,{});m=int(r['rewards'][me]-r['rewards'][op])
    d1=len(diff(s[24][0]['observation'],me,op))
    first=None
    if d1<=1:
        for t in range(25,len(s)):
            d=diff(s[t][0]['observation'],me,op)
            if len(d)>=2: first=(t,collections.Counter(d).most_common(2));break
    kind='NONMIRROR' if d1>1 else ('pure' if first is None else ('carrotswap' if first[1][0][0]==('PLWH','PLCA') else 'div'))
    print(ep,e.get('sub'),e.get('orank'),N[op][:14].replace(' ','_'),m,'W' if m>0 else 'L',kind,'d1diff',d1,first[0] if first else '',first[1] if first else '',flush=True)
