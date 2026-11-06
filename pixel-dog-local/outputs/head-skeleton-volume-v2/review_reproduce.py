"""Independent read-only final reproduction. Run only against a frozen candidate."""
from pathlib import Path
import hashlib,importlib.metadata,importlib.util,io,json,os,pickle,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
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
source=HERE/'build.py';source_start=sha(source)
spec=importlib.util.spec_from_file_location('independent_final_volume',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
guard={str(p):sha(p) for p in [source,HERE/'profiles.json',HERE/'raster.py',HERE/'references.json']}
profiles=json.loads((HERE/'profiles.json').read_text('utf-8'));rebuilt={}
for b in m.BREEDS:
    rebuilt[b]=m.build_one(profiles[b]);print('Independently rebuilt',b,flush=True)
images=m.boards(rebuilt);active=False
saved=pickle.loads((HERE/'geometry.pkl').read_bytes())
def equal(a,b):
    if isinstance(a,np.ndarray):return isinstance(b,np.ndarray) and a.dtype==b.dtype and np.array_equal(a,b)
    if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
    if isinstance(a,(list,tuple)):return isinstance(b,type(a)) and len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    return a==b
out=HERE/'review-reproduction';out.mkdir(exist_ok=True)
report={'images':{},'geometry':{},'region_exports':{},'source_sha256':source_start,'geometry_sha256':sha(HERE/'geometry.pkl')}
for name,im in images.items():
    buf=io.BytesIO();im.save(buf,format='PNG');data=buf.getvalue();record=dict(sha256=hashlib.sha256(data).hexdigest(),candidate_sha256=sha(HERE/name),bytes_equal=data==(HERE/name).read_bytes(),size=list(im.size));report['images'][name]=record
    (out/name).write_bytes(data)
for b,model in rebuilt.items():
    report['geometry'][b]={'exact_all_arrays_parameters_profiles':equal(model,saved[b])}
    export=HERE/(b+'-regions.npz')
    with np.load(export) as z:
        expected={f'{part}_{key}':rec[key] for part,rec in model['parts'].items() for key in ['v','f','n','region']}
        same=set(z.files)==set(expected) and all(equal(z[k],v) for k,v in expected.items())
    report['region_exports'][b]={'arrays_exact':same,'sha256':sha(export),'region_counts':{part:{str(int(k)):int(c) for k,c in zip(*np.unique(rec['region'],return_counts=True))} for part,rec in model['parts'].items()}}
    print('Compared saved data',b,flush=True)
report['regions_json_exact']=json.loads((HERE/'regions.json').read_text('utf-8'))=={str(k):v for k,v in m.REGIONS.items()}
cspec=importlib.util.spec_from_file_location('independent_controls',HERE/'review_controls.py');cm=importlib.util.module_from_spec(cspec);cspec.loader.exec_module(cm)
report['controls']=cm.run(m,rebuilt)
refs=json.loads((HERE/'references.json').read_text('utf-8'));opened.add((HERE/'references.json').resolve())
for ref in refs['images']:
    p=(HERE/ref['path']).resolve();assert sha(p)==ref['sha256'];opened.add(p)
p=(HERE/refs['profile_source']).resolve();assert sha(p)==refs['profile_source_sha256'];opened.add(p)
opened.update([source.resolve(),(HERE/'raster.py').resolve(),(HERE/'profiles.json').resolve(),Path(m.FONT).resolve(),Path(m.BOLD).resolve()])
excluded={HERE/name for name in images}|{Path(__file__).resolve()}
report['inputs']={os.path.relpath(p,HERE).replace('\\','/'):sha(p) for p in sorted(opened) if p.exists() and p not in excluded and not p.name.startswith('review_')}
report['source_unchanged']=source_start==sha(source)
report['all_guarded_inputs_unchanged']=all(sha(Path(p))==h for p,h in guard.items())
report['libraries']={k:importlib.metadata.version(k) for k in ['numpy','scipy','scikit-image','Pillow','numba']};report['python']=sys.version
report['all_exact']=all(r['bytes_equal'] for r in report['images'].values()) and all(r['exact_all_arrays_parameters_profiles'] for r in report['geometry'].values()) and all(r['arrays_exact'] for r in report['region_exports'].values()) and report['source_unchanged'] and report['regions_json_exact'] and report['all_guarded_inputs_unchanged']
(HERE/'review-reproduction.json').write_text(json.dumps(report,indent=2)+'\n','utf-8');print(json.dumps({'all_exact':report['all_exact'],'images':report['images'],'inputs':len(report['inputs']),'controls':report['controls']},indent=2))
