"""Independent full reconstruction; candidate sources and exports are read only."""
from pathlib import Path
import hashlib,importlib.metadata,importlib.util,io,json,os,pickle,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
opened=set();active=True
def observe(event,data):
 if not active or event!='open' or not isinstance(data[0],(str,bytes)):return
 p=Path(os.fsdecode(data[0])).resolve();mode,flags=data[1:3]
 if isinstance(mode,str) and any(c in mode for c in 'wax+'):return
 if mode is None and flags & (os.O_WRONLY|os.O_RDWR):return
 if p.suffix=='.pyc':
  try:p=Path(importlib.util.source_from_cache(str(p)))
  except ValueError:return
 if p.is_relative_to(ROOT) or p.parent==Path('C:/Windows/Fonts'):opened.add(p)
sys.addaudithook(observe)
import numpy as np
from PIL import ImageFont
original_font=ImageFont.truetype
def font(*args,**kwargs):
 f=original_font(*args,**kwargs)
 if isinstance(f.path,(str,bytes)):opened.add(Path(os.fsdecode(f.path)).resolve())
 return f
ImageFont.truetype=font
source=HERE/'build.py';guard={str(p):sha(p) for p in [source,HERE/'references.json',HERE/'geometry.pkl',HERE/'parameters.json',HERE.parent/'head-skeleton-volume-v2/geometry.pkl',HERE.parent/'head-skeleton-volume-v2/profiles.json',HERE.parent/'head-skeleton-volume-v2/review-status.json']}
spec=importlib.util.spec_from_file_location('independent_skin_full',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
skels=m.load_inputs();saved=pickle.loads((HERE/'geometry.pkl').read_bytes());rebuilt={}
def equal(a,b):
 if isinstance(a,np.ndarray):return isinstance(b,np.ndarray) and a.dtype==b.dtype and np.array_equal(a,b)
 if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
 if isinstance(a,(list,tuple)):return isinstance(b,type(a)) and len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
 return a==b
report={'images':{},'geometry':{},'source_sha256':sha(source)};out=HERE/'review-reproduction';out.mkdir(exist_ok=True)
for variant in m.VARIANTS:
 rebuilt[variant]={};report['geometry'][variant]={}
 for b in m.BREEDS:
  rebuilt[variant][b]=m.build_one(skels[b],b,variant);report['geometry'][variant][b]=equal(rebuilt[variant][b],saved[variant][b]);print('Built and exact compared',variant,b,report['geometry'][variant][b],flush=True)
 im=m.board(rebuilt,variant);buf=io.BytesIO();im.save(buf,format='PNG');data=buf.getvalue();name=f'heads-{variant}.png';report['images'][name]={'bytes_equal':data==(HERE/name).read_bytes(),'sha256':hashlib.sha256(data).hexdigest(),'candidate_sha256':sha(HERE/name),'size':list(im.size)};(out/name).write_bytes(data)
 print('Rendered',variant,report['images'][name]['bytes_equal'],flush=True)
 (HERE/'review-reproduction-progress.json').write_text(json.dumps(report,indent=2),'utf-8')
active=False
report['parameters_exact']=json.loads((HERE/'parameters.json').read_text('utf-8'))=={v:{b:model['metadata'] for b,model in row.items()} for v,row in rebuilt.items()}
report['prior_B_exact']=None
prior=HERE/'iterations/11/geometry.pkl'
if prior.exists():report['prior_B_exact']=equal(saved['B'],pickle.loads(prior.read_bytes())['B']);report['prior_cache_sha256']=sha(prior)
refs=json.loads((HERE/'references.json').read_text('utf-8'));opened.add((HERE/'references.json').resolve())
for ref in refs['references']:
 p=(HERE/ref['path']).resolve();assert sha(p)==ref['sha256'],str(p);opened.add(p)
opened.update([source.resolve(),(HERE/'geometry.pkl').resolve(),(HERE/'parameters.json').resolve(),Path(m.bones.FONT).resolve(),Path(m.bones.BOLD).resolve()])
# Include reviewed skeleton provenance; these photographs are design evidence, not parsed render inputs.
priorinputs=json.loads((m.SOURCE/'review-reproduction.json').read_text('utf-8'))['inputs']
for name,h in priorinputs.items():
 p=(m.SOURCE/name).resolve();assert sha(p)==h,str(p);opened.add(p)
excluded={HERE/f'heads-{v}.png' for v in m.VARIANTS}|{Path(__file__).resolve()}
report['inputs']={os.path.relpath(p,HERE).replace(chr(92),'/'):sha(p) for p in sorted(opened) if p.exists() and p not in excluded and not p.name.startswith('review_') and (not p.name.startswith('review-') or p.name=='review-status.json')}
report['guarded_inputs_unchanged']=all(sha(Path(p))==h for p,h in guard.items());report['libraries']={k:importlib.metadata.version(k) for k in ['numpy','scipy','scikit-image','Pillow','numba']};report['python']=sys.version
report['all_exact']=all(all(row.values()) for row in report['geometry'].values()) and all(row['bytes_equal'] for row in report['images'].values()) and report['parameters_exact'] and report['guarded_inputs_unchanged']
(HERE/'inputs.json').write_text(json.dumps(report['inputs'],indent=2),'utf-8');(HERE/'review-reproduction.json').write_text(json.dumps(report,indent=2),'utf-8');print('FINAL',report['all_exact'],'inputs',len(report['inputs']),flush=True)
