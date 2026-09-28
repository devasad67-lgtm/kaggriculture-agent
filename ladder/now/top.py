# find top-N teams' current submissions by BFS over episode graph, then pull their episodes
import json,zipfile,csv,io,collections
from kaggle.api.kaggle_api_extended import KaggleApi
a=KaggleApi();a.authenticate()
z=zipfile.ZipFile('ladder/now/kaggriculture.zip')
rows=list(csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]),encoding='utf8')))
rank={r['TeamName']:i+1 for i,r in enumerate(rows)}
want={r['TeamName'] for r in rows[:20]}
E=json.load(open('ladder/now/eps.json'))
q=collections.deque(sorted({(e['orank'],e['osid']) for e in E}))
seen=set();found={};eps={}
calls=0
while q and want-set(found) and calls<120:
    rk,sid=q.popleft()
    if sid in seen: continue
    seen.add(sid);calls+=1
    try: r=a.competition_list_episodes(sid)
    except Exception as ex: print('ERR',sid,ex);continue
    for e in r:
        d=json.loads(str(e)); eps[d['id']]=d
        for g in d['agents']:
            t=g['teamName']
            if t in want and t not in found: found[t]=g['submissionId']; print('found',rank[t],t,g['submissionId'],flush=True); q.appendleft((0,g['submissionId']))
            elif g['submissionId'] not in seen and rank.get(t,9999)<=300: q.appendleft((rank.get(t,9999),g['submissionId']))
json.dump({'found':found,'eps':eps},open('ladder/now/top.json','w'))
print('calls',calls,'found',len(found),'missing',want-set(found))
