"""Random search over beast configs vs dp_L720a. Appends JSON lines to bsearch.jsonl."""
import sys,io,contextlib,json,os,random,multiprocessing as mp,time
sys.path.insert(0,'.')
from btune import run
def sample(rng):
    def q(lo,hi): return rng.randint(lo,hi)
    nw_cow,nw_sh,nw_mel=q(1,3),q(1,3),q(8,14)
    ne_cow,ne_sh,ne_st=q(3,8),q(2,6),q(8,16)
    sw_sh,sw_st,sw_go=q(0,4),q(6,14),q(0,4)
    se_to,se_go,se_ca=q(0,10),q(0,4),q(0,8)
    lay={"NW":[["COW",nw_cow],["SHEEP",nw_sh],["MELON",nw_mel]],
         "NE":[["COW",ne_cow],["SHEEP",ne_sh],["STRAWBERRY",ne_st]],
         "SW":[["SHEEP",sw_sh],["GOOSE",sw_go],["STRAWBERRY",sw_st]],
         "SE":[["GOOSE",se_go],["TOMATO",se_to],["CARROT",se_ca]]}
    return {"layout":lay,"hands_max":q(10,14),"work_per_hand":rng.choice([10,12,14,16,18]),
            "fert_mult":rng.choice([1.5,2.0,2.5,3.0,4.0]),"feed_margin":rng.choice([0.5,0.8,1.0,1.15,1.5,2.0]),
            "land_days":rng.choice([[3,6,8],[4,7,9],[5,8,10],[6,9,11]]),"drop_value":rng.choice([400,700,1000,1500,2500]),
            "dist_cost":rng.choice([6.0,9.0,12.0]),"seed_buffer":rng.choice([2,6,10])}
if __name__=='__main__':
    rng=random.Random(int(sys.argv[1]) if len(sys.argv)>1 else 7)
    n=int(sys.argv[2]) if len(sys.argv)>2 else 60
    seeds=[3100,3101,3102]
    with mp.Pool(4,maxtasksperchild=1) as pool:
        for i in range(n):
            cfg=sample(rng)
            res=pool.map(run,[(cfg,'dp_L720a',s,0) for s in seeds]+[(cfg,'dp_L720a',seeds[0],1)])
            me=sum(r[1] for r in res)/len(res); mg=sum(r[1]-r[2] for r in res)/len(res)
            with open('bsearch.jsonl','a') as f: f.write(json.dumps({"money":me,"margin":mg,"cfg":cfg})+"\n")
            print(i,int(me),int(mg),flush=True)
