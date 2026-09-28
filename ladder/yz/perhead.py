# revenue per animal / per crop tile by board class, for a given team in a set of replays
import json,glob,sys,collections,statistics as S
sys.path.insert(0,'D:/kaggle/ladder/yz')
import io,contextlib
with contextlib.redirect_stdout(io.StringIO()): import ledger
who=sys.argv[1];R=collections.defaultdict(list)
def sc(sh,names): return sum(x in names for x in sh)
for f in sys.argv[2:]:
    r=json.load(open(f,encoding='utf8'));s=r['steps'];N=r['info']['TeamNames'];ps=[i for i,x in enumerate(N) if who in x]
    if not ps or len(s)<700: continue
    p=ps[0];sh=s[288][0]['observation']['town']['unlocked_shops']  # shops known by day 12
    rev,cost,units=ledger.ledger(r,p)
    nsheep=cost['ANIMAL:SHEEP']/500;ncow=cost['ANIMAL:COW']/400;ngoose=cost['ANIMAL:GOOSE']/300
    y=sh.count('YARN_STORE');milk=sc(sh,('PIZZA_SHOP','ICE_CREAM_SHOP','SMOOTHIE_SHOP'));egg=sc(sh,('BAKERY','BRUNCH_SPOT'))
    if nsheep: R[('wool/sheep','yarn%d'%min(y,2))].append(rev['WOOL']/nsheep)
    if ncow: R[('milk/cow','milkshops%d'%min(milk,2))].append(rev['MILK']/ncow)
    if ngoose: R[('egg/goose','eggshops%d'%min(egg,2))].append(rev['EGG']/ngoose)
    R[('sheep count','yarn%d'%min(y,2))].append(nsheep);R[('cow count','milkshops%d'%min(milk,2))].append(ncow);R[('goose count','eggshops%d'%min(egg,2))].append(ngoose)
for k in sorted(R): print(f"{k[0]:12s} {k[1]:11s} n={len(R[k]):3d} median {S.median(R[k]):7.0f}")
