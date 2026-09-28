import sys,glob,json,collections
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0,'rnd'); from prof import prof
def one(f):
    try: return prof(f)
    except Exception as e: return None
WHO=(sys.argv[-1][4:] if sys.argv[-1].startswith('who=') else 'asad').lower()
if __name__=='__main__':
    for d in [a for a in sys.argv[1:] if not a.startswith('who=')]:
        fs=sorted(glob.glob(d+'/*.json'))
        S={True:collections.Counter(),False:collections.Counter()}; R={True:collections.Counter(),False:collections.Counter()}; rw={True:[],False:[]}
        with ProcessPoolExecutor(6) as ex:
            for res in ex.map(one,fs):
                if not res: continue
                for x in res:
                    me=WHO in x['name'].lower(); rw[me].append(x['reward'])
                    for k,n in x['sold'].items(): S[me][k]+=n; R[me][k]+=n*x['avgp'].get(k,0)
        g=len(rw[True]); print(f"== {d} games {g}  my avg ${sum(rw[True])/g:.0f}  opp avg ${sum(rw[False])/g:.0f}")
        for k in sorted(S[True],key=lambda k:-R[True][k]):
            print(f"  {k:11s} me {S[True][k]/g:6.1f}/g @{R[True][k]/max(1,S[True][k]):5.1f} = ${R[True][k]/g:7.0f}/g | opp {S[False][k]/g:6.1f}/g @{R[False][k]/max(1,S[False][k]):5.1f} = ${R[False][k]/g:7.0f}/g")
