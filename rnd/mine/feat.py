# per-game features for us and the opponent from real ladder replays
import json,glob,os,collections,sys
from concurrent.futures import ProcessPoolExecutor
def feats(f):
    r=json.load(open(f,encoding='utf8')); s=r['steps']; n=r['info']['TeamNames']
    me=[i for i,x in enumerate(n) if 'asad' in x.lower()][0]; op=1-me
    out=dict(f=os.path.basename(f),opp=n[op])
    first={}
    for d in range(0,20):
        for p,lab in ((me,'me'),(op,'op')):
            F=s[d*24+12][0]['observation']['farms'][p]
            c=collections.Counter((t.get('crop') or t.get('animal') or t['kind']) for row in F['tiles'] for t in row if isinstance(t,dict))
            for k in ('STRAWBERRY','CARROT','TOMATO','GOOSE','COW','SHEEP','MELON'):
                if c[k]>0 and (lab,k) not in first: first[(lab,k)]=d
            if d in (5,7,10,14):
                out[f'{lab}_q{d}']=len(F['unlocked_quadrants']); out[f'{lab}_cash{d}']=F['money']
                for k in ('WHEAT','STRAWBERRY','CARROT','TOMATO','MELON','GOOSE','COW','SHEEP'): out[f'{lab}_{k}{d}']=c[k]
                out[f'{lab}_h{d}']=len(F.get('hands') or [])
    for (lab,k),d in first.items(): out[f'{lab}_first_{k}']=d
    out['shops']=list(s[150][0]['observation']['town']['unlocked_shops'][:3])
    # mirror = identical tile layout on day 10
    L=[s[10*24+12][0]['observation']['farms'][p]['tiles'] for p in (me,op)]
    kind=lambda t:(t.get('crop') or t.get('animal') or t.get('kind')) if isinstance(t,dict) else t
    out['same_layout10']=sum(kind(a)==kind(b) for ra,rb in zip(*L) for a,b in zip(ra,rb))
    return out
if __name__=='__main__':
    fs=sorted(glob.glob('ladder/l48mc/*.json'))
    with ProcessPoolExecutor(4) as ex, open('rnd/mine/feat.jsonl','w') as o:
        for x in ex.map(feats,fs): o.write(json.dumps(x)+'\n')
