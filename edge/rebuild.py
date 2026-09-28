"""Rebuild an existing edge bot with the current edge core + setting overrides.
python edge/rebuild.py <src_bot_dir> <out_dir> '<json overrides>'"""
import sys,re,json,base64,zlib,os,ast,subprocess
src,out,ov=sys.argv[1],sys.argv[2],json.loads(sys.argv[3] if len(sys.argv)>3 else '{}')
m=open(os.path.join(src,'main.py'),encoding='utf-8').read()
blob=re.search(r"_b64\.b64decode\('([^']+)'\)",m).group(1)
inner=zlib.decompress(base64.b64decode(blob))
st=ast.literal_eval(re.search(r"_EDGE = Edge\(_INNER_NS\['agent'\], (\{.*\}), _chassis\)",m).group(1))
st.update(ov)
tmp=os.path.join(os.path.dirname(os.path.abspath(__file__)),'_inner_tmp.py'); open(tmp,'wb').write(inner)
subprocess.check_call([sys.executable,os.path.join(os.path.dirname(os.path.abspath(__file__)),'build.py'),tmp,out,json.dumps(st)])
os.remove(tmp); print('settings',st)
