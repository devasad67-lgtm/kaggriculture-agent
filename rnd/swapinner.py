import re,sys,base64,zlib,os
src_bot,out_dir,layer=sys.argv[1],sys.argv[2],sys.argv[3]
m=open(src_bot,encoding='utf-8').read()
g=re.search(r"_b64\.b64decode\('([A-Za-z0-9+/=]+)'\)",m)
inner=zlib.decompress(base64.b64decode(g.group(1)))
ref=open('rnd/inner_wf.py','rb').read()
print('embedded == rnd/inner_wf.py:',inner==ref,len(inner),len(ref))
new=inner+open(layer,'rb').read()
blob=base64.b64encode(zlib.compress(new,9)).decode()
os.makedirs(out_dir,exist_ok=True)
open(os.path.join(out_dir,'main.py'),'w',encoding='utf-8',newline='\n').write(m.replace(g.group(1),blob))
print('built',out_dir)
