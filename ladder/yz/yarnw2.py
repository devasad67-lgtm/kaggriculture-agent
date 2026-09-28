import json,glob,sys,statistics as S
sys.path.insert(0,'D:/kaggle/ladder/yz')
import io,contextlib
with contextlib.redirect_stdout(io.StringIO()): import ledger
E={e['ep']:e for e in json.load(open('ladder/now/eps.json'))}
rows=[]
for f in glob.glob(sys.argv[1]+'/*.json'):
    r=json.load(open(f,encoding='utf8'));s=r['steps'];N=r['info']['TeamNames'];p=[i for i,x in enumerate(N) if 'asad' in x][0]
    sh=s[min(432,len(s)-1)][0]['observation']['town']['unlocked_shops']
    if sh.count('YARN_STORE')<2: continue
    a=ledger.ledger(r,p);b=ledger.ledger(r,1-p);ep=int(f.split('-')[1])
    m=r['rewards'][p]-r['rewards'][1-p]
    ua,ub=a[2]['WOOL'],b[2]['WOOL']
    rows.append((ep,E.get(ep,{}).get('orank',0),m,ua,ub,a[0]['WOOL'],b[0]['WOOL'],N[1-p][:16],a[1]['ANIMAL:SHEEP']//500,b[1]['ANIMAL:SHEEP']//500))
rows.sort(key=lambda x:x[2])
for ep,rk,m,ua,ub,ra,rb,o,sa,sb in rows:
    print(f"{ep} r{rk:5d} {o:16s} margin {m:+7.0f} | wool units {ua:4.0f} {ub:4.0f} | avg $ {ra/max(1,ua):4.0f} {rb/max(1,ub):4.0f} | wool rev diff {ra-rb:+6.0f} | sheep {sa} {sb}")
w=sum(x[2]>0 for x in rows);print('yarn games',len(rows),'W',w,'L',len(rows)-w)
band=[x for x in rows if 100<=x[1]<=700];print('band 100-700: W',sum(x[2]>0 for x in band),'L',sum(x[2]<=0 for x in band))
mir=[x for x in rows if x[8]==x[9] and x[8]>0]
print('same-sheep mirror games',len(mir),'W',sum(x[2]>0 for x in mir),'mean wool price gap (ours-theirs)',round(S.mean(x[5]/max(1,x[3])-x[6]/max(1,x[4]) for x in mir),1) if mir else '-', 'mean wool rev diff',round(S.mean(x[5]-x[6] for x in mir)) if mir else '-')
