# crawl episode metadata (no replays): start from our subs, expand to opponents' submissions
import json,sys,os,collections
from kaggle.api.kaggle_api_extended import KaggleApi
a=KaggleApi(); a.authenticate()
out='ladder/crawl/eps.json'
E=json.load(open(out)) if os.path.exists(out) else {}
done=set()
def fetch(sid):
    if sid in done: return []
    done.add(sid)
    try: r=a.competition_list_episodes(sid)
    except Exception as e: print('ERR',sid,e); return []
    res=[]
    for e in r:
        d=json.loads(str(e)) if not isinstance(e,dict) else e
        E[str(d['id'])]=d; res.append(d)
    return res
seeds=[int(x) for x in sys.argv[1].split(',')]
want=set(sys.argv[2].split('|')) if len(sys.argv)>2 else set()
for s in seeds:
    for d in fetch(s):
        for ag in d.get('agents',[]):
            if ag['teamName'] in want: want.discard(ag['teamName']); print('found',ag['teamName'],ag['submissionId']); fetch(ag['submissionId'])
json.dump(E,open(out,'w'))
print('episodes',len(E),'missing',want)
