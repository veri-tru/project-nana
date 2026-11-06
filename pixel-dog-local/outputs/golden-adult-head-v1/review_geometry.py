"""Independent saved-mesh review. No production file writes."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,pickle,sys
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
for path,names in [(ROOT/'skull-based-heads-v1/review_saved_mesh.py',['topo','nearest','prep']),(ROOT/'skull-based-heads-v1/review_ray_containment.py',['parity']),(ROOT/'skull-based-heads-v1/review_final_geometry.py',['exact_minimum']),(ROOT/'skull-based-heads-v2/review_dev10_crossings.py',['hits','coplanar_overlap']),(ROOT/'skull-based-heads-v2/review_final_geometry.py',['crossings'])]:
 for node in ast.parse(path.read_text('utf-8')).body:
  if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(out):
 (HERE/'technical-measurements.json').write_text(json.dumps(out,indent=2,allow_nan=False),'utf-8')
def eq(a,b):
 if isinstance(a,np.ndarray):return isinstance(b,np.ndarray) and a.dtype==b.dtype and np.array_equal(a,b)
 if isinstance(a,dict):return a.keys()==b.keys() and all(eq(a[k],b[k]) for k in a)
 if isinstance(a,(list,tuple)):return len(a)==len(b) and all(eq(x,y) for x,y in zip(a,b))
 return a==b
spec=importlib.util.spec_from_file_location('golden_review_builder',HERE/'build.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
guardpaths=[ROOT/'head-skeleton-volume-v2'/x for x in ['build.py','profiles.json','geometry.pkl']]+[ROOT/'skull-based-heads-v2'/x for x in ['build.py','geometry.pkl','parameters.json']]+[HERE/'build.py',HERE/'exterior_seed.py']
guards={str(p):sha(p) for p in guardpaths}
out={'guards_before':guards,'variants':{},'methods':'AST-loaded individual audit functions; actual saved triangles, no prior full-review execution.'}
for variant in sys.argv[1:] or ['A','B','C']:
 file=HERE/f'model-{variant}.pkl';model=pickle.loads(file.read_bytes());skel=model['skeleton'];face=model['exterior'];skin=face['parts']['skin'];prep(skin)
 row={'model_sha256':sha(file),'topology':{},'finite':{},'containment':{},'jaw_motion':{},'self_crossings':{}}
 for layer,mod in [('skeleton',skel),('exterior',face)]:
  row['topology'][layer]={k:topo(part) for k,part in mod['parts'].items()}
  row['finite'][layer]=all(np.isfinite(v).all() for part in mod['parts'].values() for k,v in part.items() if isinstance(v,np.ndarray))
 for key in ['upper','jaw']:
  part=skel['parts'][key];q=np.concatenate([part['v'],part['v'][part['f']].mean(1)]);inside=parity(q,skin)
  row['containment'][key]={'samples':len(q),'outside':int((~inside).sum()),'first_outside':q[~inside][:5].tolist(),'crossings':crossings(part,skin),**exact_minimum(q,skin)}
  print(variant,key,'outside',row['containment'][key]['outside'],'crossings',row['containment'][key]['crossings']['intersecting_pairs'],flush=True)
 for name,part in [('upper',skel['parts']['upper']),('jaw',skel['parts']['jaw']),('skin',skin)]:
  row['self_crossings'][name]=crossings(part)
 for angle in [0,10,20]:
  jaw=copy.deepcopy(skel['parts']['jaw']);jaw['v']=m.bones.rotate(jaw['v'],skel['parameters']['hinge'],angle)
  q=np.concatenate([jaw['v'],jaw['v'][jaw['f']].mean(1)]);inside=parity(q,skel['parts']['upper'])
  row['jaw_motion'][str(angle)]={'samples':len(q),'inside_upper':int(inside.sum()),'first_inside':q[inside][:6].tolist(),'crossings':crossings(jaw,skel['parts']['upper'])}
  print(variant,'jaw',angle,row['jaw_motion'][str(angle)],flush=True)
 # Eye radius is preserved although placement follows the changed skeleton.
 row['eye_radius']=model['settings']['eye_radius'];row['nose_template_scale']=model['settings']['nose_template_scale']
 row['settings']=model['settings']
 out['variants'][variant]=row;save(out)
 # Rebuild actual geometry in memory, leaving original artifacts untouched.
 t=model['settings']['strength'];m.seed.GOLDEN_MUZZLE_WIDTH=13+3*t;m.seed.GOLDEN_MUZZLE_HEIGHT=10.8+1.2*t
 original=m.bones.params
 def adult_params(p):
  a=original(p);a['body_height']*=1+.12*t;return a
 m.bones.params=adult_params
 try:freshbones=m.bones.build_one(m.profile(t))
 finally:m.bones.params=original
 freshface=m.skin.build_one(freshbones,'golden','B')
 row['reproduction']={'skeleton_exact':eq(freshbones,skel),'exterior_exact':eq(freshface,{**face,'parts':{k:{kk:vv for kk,vv in p.items() if not kk.startswith('_')} for k,p in face['parts'].items()}})}
 out['variants'][variant]=row;out['guards_unchanged']=all(sha(Path(p))==h for p,h in guards.items());save(out)
 print('DONE',variant,'reproduction',row['reproduction'],'self_crossings',row['self_crossings'],flush=True)
