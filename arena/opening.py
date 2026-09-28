import sys,os,io,contextlib,json
sys.path.insert(0,'.'); from tourney import resolve
def first(b):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        from kaggle_environments import make
        env=make("kaggriculture",configuration={"seed":7,"episodeSteps":4},debug=False)
        env.run([resolve(b),resolve(b)])
    return env.steps[1][0].action
if __name__=='__main__':
    import multiprocessing as mp
    bots=[d for d in os.listdir('D:/kaggle/bots') if os.path.exists(f'D:/kaggle/bots/{d}/main.py') and not d.startswith(('dp_','edge_','h65','me3','pr_'))]
    with mp.Pool(4) as p:
        for b,a in zip(bots,p.map(first,bots)): print(b[:45].ljust(45), json.dumps((a or {}).get('market'))[:90])
