import sys,json
sys.path.insert(0,'rnd'); import replaytest
LOG=open('rnd/ldnew/dbg.log','w')
orig_load=replaytest.load
def load(p):
    fn=orig_load(p); E=fn.__globals__['_EDGE']; g=fn.__globals__
    D=g['DeferCollect']; A=D.apply
    def ap(self,obs,action,tape,courier=None):
        st=obs.get('step',0) if isinstance(obs,dict) else obs.step
        if 443<=st<=452:
            LOG.write(repr((st,'tapelen',len(tape),'act',action.get('hands')[12:14] if action.get('hands') else None,'tape',(tape[st].get('hands') or [])[12:14] if st<len(tape) else None,'inv',[dict(x or {}) for x in obs['private']['inventories']][13:15], 'd',self.d))+chr(10))
        return A(self,obs,action,tape,courier)
    D.apply=ap
    return fn
replaytest.load=load
print(replaytest.run('bots/L48_df/main.py','ladder/l48mc/episode-113462974-replay.json')['tel'])
