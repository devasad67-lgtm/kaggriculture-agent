import json,glob,sys
sys.path.insert(0,'D:/kaggle/ladder/yz')
import io,contextlib
with contextlib.redirect_stdout(io.StringIO()): import ledger
for f in glob.glob('ladder/l48mc/*.json'):
    r=json.load(open(f,encoding='utf8'));s=r['steps'];N=r['info']['TeamNames'];p=[i for i,x in enumerate(N) if 'asad' in x][0]
    sh=s[min(432,len(s)-1)][0]['observation']['town']['unlocked_shops']
    if sh.count('YARN_STORE')<2 or sum(x in('PIZZA_SHOP','FARMERS_MARKET') for x in sh)>=3: continue
    a=ledger.ledger(r,p);b=ledger.ledger(r,1-p)
    q=s[-1][0]['observation']['farms']
    print(f.split('-')[1],'margin',round(r['rewards'][p]-r['rewards'][1-p]),'| wool units',round(a[2]['WOOL']),round(b[2]['WOOL']),'rev',round(a[0]['WOOL']),round(b[0]['WOOL']),'avg $',round(a[0]['WOOL']/max(1,a[2]['WOOL'])),round(b[0]['WOOL']/max(1,b[2]['WOOL'])),'| sheep bought',a[1]['ANIMAL:SHEEP']//500,b[1]['ANIMAL:SHEEP']//500)
