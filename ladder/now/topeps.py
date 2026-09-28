import json,zipfile,csv,io,collections,statistics as S
from kaggle.api.kaggle_api_extended import KaggleApi
a=KaggleApi();a.authenticate()
z=zipfile.ZipFile('ladder/now/kaggriculture.zip')
rows=list(csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]),encoding='utf8')))
rank={r['TeamName']:i+1 for i,r in enumerate(rows)}
T=json.load(open('ladder/now/top.json'));eps={int(k):v for k,v in T['eps'].items()}
subs=collections.defaultdict(set)
for d in eps.values():
    for g in d['agents']:
        if rank.get(g['teamName'],9999)<=20: subs[g['teamName']].add(g['submissionId'])
for t,ss in subs.items():
    for s in ss:
        for e in a.competition_list_episodes(s):
            d=json.loads(str(e)); eps[d['id']]=d
json.dump({str(k):v for k,v in eps.items()},open('ladder/now/topeps.json','w'))
print(len(eps),{t:len(s) for t,s in subs.items()})
