import json,glob,sys,collections
# per game, per player: animals escaped (by day), plants turned weed (by day)
def scan(f):
    r=json.load(open(f,encoding='utf8')); n=r['info']['TeamNames']; s=r['steps']; out=[]
    for p in (0,1):
        esc=[];wd=[]
        for d in range(1,30):
            a=s[d*24-1][0]['observation']['farms'][p]['tiles']; b=s[d*24][0]['observation']['farms'][p]['tiles']
            for y in range(10):
                for x in range(10):
                    u,v=a[y][x],b[y][x]
                    if isinstance(u,dict) and u.get('animal') and not (isinstance(v,dict) and v.get('animal')): esc.append((d-1,u['animal']))
                    if isinstance(u,dict) and u['kind']=='PLANT' and u['consecutive_unwatered']>=1 and not u['watered_today'] and isinstance(v,dict) and v['kind']=='WEED': wd.append((d-1,u['crop']))
        out.append((n[p],r['rewards'][p],esc,wd))
    return out
tot=collections.Counter()
for pat in sys.argv[1:]:
    for f in sorted(glob.glob(pat)):
        try: res=scan(f)
        except Exception as e: continue
        for nm,rw,esc,wd in res:
            me='asad' in nm.lower()
            tot[(me,'games')]+=1; tot[(me,'esc')]+=len(esc); tot[(me,'weed')]+=len(wd)
            tot[(me,'gesc')]+=bool(esc); tot[(me,'gweed')]+=bool(wd)
            if me and (esc or wd): print(f.split('-')[1],rw,'ESC',esc,'WEED',wd)
print(dict(tot))
