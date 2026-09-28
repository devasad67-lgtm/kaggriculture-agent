import sys,json
sys.path.insert(0,'rnd'); import replaytest
LOG=open('rnd/ldnew/dbg3.log','w')
orig_load=replaytest.load
def load(p):
    fn=orig_load(p); g=fn.__globals__; D=g['DeferCollect']; A=D.apply
    def ap(self,obs,action,tape,courier=None):
        st=obs['step']
        if st in (445,450):
            ch=g['_chassis'](); pl=ch.players.get(obs['player'])
            LOG.write(f"{st} tape {json.dumps(tape[st])}\n act {json.dumps(action)}\n player-state keys {list(pl.keys()) if isinstance(pl,dict) else type(pl)}\n")
            LOG.write(' '+repr({k:(v if not isinstance(v,(list,dict)) or len(str(v))<300 else str(v)[:300]) for k,v in pl.items()})+'\n')
        return A(self,obs,action,tape,courier)
    D.apply=ap; return fn
replaytest.load=load
replaytest.run('bots/L48_df/main.py','ladder/l48mc/episode-113462974-replay.json')
