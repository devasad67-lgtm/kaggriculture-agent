import json,glob,collections,sys
sys.path.insert(0,'D:/kaggle/ladder/yz')
import io,contextlib
with contextlib.redirect_stdout(io.StringIO()): import ledger
D=collections.defaultdict(lambda:collections.defaultdict(list))
for f in glob.glob('ladder/l48mc/*.json'):
    r=json.load(open(f,encoding='utf8'));s=r['steps'];N=r['info']['TeamNames'];p=[i for i,x in enumerate(N) if 'asad' in x][0]
    sh=s[min(432,len(s)-1)][0]['observation']['town']['unlocked_shops'];n=sum(x in('PIZZA_SHOP','FARMERS_MARKET') for x in sh)
    cls='tomato3+' if n>=3 else 'yarn2+' if sh.count('YARN_STORE')>=2 else None
    if not cls: continue
    win=r['rewards'][p]>r['rewards'][1-p]
    a=ledger.ledger(r,p);b=ledger.ledger(r,1-p)
    key=(cls,'W' if win else 'L')
    for k in set(a[0])|set(b[0]): D[key][k].append(a[0][k]-b[0][k])
    D[key]['_margin'].append(r['rewards'][p]-r['rewards'][1-p])
    for k in set(a[1])|set(b[1]): D[key]['cost:'+k].append(-(a[1][k]-b[1][k]))
for key in sorted(D):
    n=len(D[key]['_margin'])
    print(key,'n',n,'  '.join(f"{k}:{sum(v)/n:+.0f}" for k,v in sorted(D[key].items(),key=lambda kv:sum(kv[1])) if abs(sum(v)/n)>150 or k=='_margin'))
