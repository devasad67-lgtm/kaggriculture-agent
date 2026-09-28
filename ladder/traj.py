import json,glob,sys
def load(f):
    r=json.load(open(f,encoding='utf8')); n=r['info']['TeamNames']; me=[i for i,x in enumerate(n) if 'asad' in x.lower()][0]; return r,me,1-me,n
def worth(ob,p):
    f=ob['farms'][p]; return f['money']
out=[]
for f in sorted(glob.glob('reps/*.json')):
    r,me,op,n=load(f)
    if n[0]==n[1]: continue
    s=r['steps']; rw=r['rewards']
    diffs=[]
    for d in range(30):
        ob=s[min(d*24+23,719)][0]['observation']
        diffs.append(round(ob['farms'][me]['money']-ob['farms'][op]['money']))
    tag='L' if rw[me]<rw[op] else 'W'
    out.append((tag,n[op][:14],int(rw[me]-rw[op]),diffs))
for t,nm,fin,d in out:
    if t=='L': print(t,nm.ljust(14),fin,'| d5',d[4],'d10',d[9],'d15',d[14],'d20',d[19],'d25',d[24],'d27',d[26],'d28',d[27],'d29',d[28],'d30',d[29])
