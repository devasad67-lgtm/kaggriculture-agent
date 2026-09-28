import json,zipfile,csv,io,sys
from kaggle.api.kaggle_api_extended import KaggleApi
a=KaggleApi();a.authenticate()
z=zipfile.ZipFile('ladder/now/kaggriculture.zip');f=z.namelist()[0]
rows=list(csv.DictReader(io.TextIOWrapper(z.open(f),encoding='utf8')))
rank={r['TeamName']:(i+1,float(r['Score'])) for i,r in enumerate(rows)}
me=rank.get('dev.asad67');print('team rank',me,'of',len(rows))
out=[]
for name,sid in [('L48_wf',56576330),('L48_mc',56557869)]:
    for e in a.competition_list_episodes(sid):
        d=json.loads(str(e))
        if d['state']!='COMPLETED' or len(d['agents'])!=2 or len({g['submissionId'] for g in d['agents']})<2: continue
        m=[g for g in d['agents'] if g['submissionId']==sid][0]; o=[g for g in d['agents'] if g['submissionId']!=sid][0]
        r=rank.get(o['teamName'],(9999,0))
        out.append(dict(sub=name,ep=d['id'],t=d['createTime'],opp=o['teamName'],osid=o['submissionId'],orank=r[0],oscore=r[1],seat=m['index'],me=m.get('reward') or 0,op=o.get('reward') or 0))
json.dump(out,open('ladder/now/eps.json','w'))
print(len(out))
