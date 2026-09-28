import json,sys,glob,collections
def prof(f):
    r=json.load(open(f,encoding='utf8')); s=r['steps']; names=r['info']['TeamNames']
    out=[]
    for p in (0,1):
        sold=collections.Counter(); rev=collections.Counter(); hires=collections.Counter()
        for t in range(1,len(s)):
            ob=s[t-1][0]['observation']; mk=ob['market']
            shed=dict(s[t-1][p]['observation']['private']['shed'])
            for o in (s[t][p]['action'] or {}).get('market') or []:
                if o and o[0]=='SELL':
                    n=min(int(o[2]) if len(o)>2 else 1,shed.get(o[1],0)); shed[o[1]]=shed.get(o[1],0)-n
                    sold[o[1]]+=n; rev[o[1]]+=n*mk['prices'][o[1]]
            f1=s[t][0]['observation']['farms'][p]
            hires[(t)//24]=max(hires[t//24],f1['hires_today'])
        lay={}
        for d in (5,10,15,20,25):
            tl=s[d*24+12][0]['observation']['farms'][p]['tiles']; c=collections.Counter()
            for row in tl:
                for x in row:
                    if isinstance(x,dict): c[x.get('crop') or x.get('animal') or x['kind']]+=1
            lay[d]=dict(c)
        q=[len(s[d*24+1][0]['observation']['farms'][p]['unlocked_quadrants']) for d in range(30)]
        out.append(dict(name=names[p],reward=r['rewards'][p],sold=dict(sold),avgp={k:round(rev[k]/sold[k]) for k in sold if sold[k]},
            hires=[hires[d] for d in range(30)],quads=q,lay=lay))
    return out
if __name__=='__main__':
    for f in sys.argv[1:]:
        for x in prof(f):
            print(x['name'],x['reward']); print('  sold',x['sold']); print('  avgp',x['avgp']); print('  hires',x['hires']); print('  quads',x['quads'])
            for d,l in x['lay'].items(): print('  d%d'%d,l)
        print()
