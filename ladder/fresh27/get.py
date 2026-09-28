# download replays of our L48_wf/L48_mc games vs rank<=700 not already on disk
import json,glob,os,inspect
from kaggle.api.kaggle_api_extended import KaggleApi
a=KaggleApi();a.authenticate()
have={os.path.basename(p).split('-')[1] for p in glob.glob('ladder/**/episode-*-replay.json',recursive=True)}
E=[e for e in json.load(open('ladder/now/eps.json')) if e['orank']<=700 and str(e['ep']) not in have]
print('to get',len(E))
sig=inspect.signature(a.competition_episode_replay);print(sig)
for e in E:
    try: a.competition_episode_replay(e['ep'],path='ladder/fresh27')
    except TypeError: a.competition_episode_replay(e['ep'],'ladder/fresh27')
    except Exception as x: print('fail',e['ep'],x)
print(len(glob.glob('ladder/fresh27/*.json')))
