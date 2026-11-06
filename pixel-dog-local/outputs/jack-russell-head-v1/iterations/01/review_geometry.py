"""Independent reviewer-owned audit. Writes only this review's measurements."""
from pathlib import Path
import ast, copy, hashlib, importlib.util, json, pickle, sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
for path,names in [(ROOT/'skull-based-heads-v1/review_saved_mesh.py',['topo','nearest','prep']),(ROOT/'skull-based-heads-v1/review_ray_containment.py',['parity']),(ROOT/'skull-based-heads-v1/review_final_geometry.py',['exact_minimum']),(ROOT/'skull-based-heads-v2/review_dev10_crossings.py',['hits','coplanar_overlap']),(ROOT/'skull-based-heads-v2/review_final_geometry.py',['crossings'])]:
 for node in ast.parse(path.read_text('utf-8')).body:
  if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def eq(a,b):
 if isinstance(a,np.ndarray):return isinstance(b,np.ndarray) and a.dtype==b.dtype and np.array_equal(a,b)
 if isinstance(a,dict):return a.keys()==b.keys() and all(eq(a[k],b[k]) for k in a)
 if isinstance(a,(list,tuple)):return len(a)==len(b) and all(eq(x,y) for x,y in zip(a,b))
 return a==b
def save(out): (HERE/'technical-measurements.json').write_text(json.dumps(out,indent=2,allow_nan=False),'utf-8')
spec=importlib.util.spec_from_file_location('jack_review_builder',HERE/'build.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
guardpaths=[ROOT/'head-skeleton-volume-v2'/x for x in ['build.py','profiles.json','geometry.pkl','raster.py']]+[ROOT/'skull-based-heads-v2'/x for x in ['build.py','geometry.pkl','parameters.json']]+[HERE/x for x in ['build.py','exterior_seed.py','references.json','source-guards.json']]
guardpaths += [HERE/f'model-{v}.pkl' for v in 'ABC']+[HERE/n for n in ['exterior-comparison.png','skeleton-comparison.png','jaw-check.png']]
guards={str(p):sha(p) for p in guardpaths if p.exists()}
out={'guards_before':guards,'variants':{},'method':'AST-loaded individual audit functions; actual saved triangles; no prior full-review execution. Ray-parity vertices/centroids plus triangle intersections. Minimum is certified over samples, not all continuous surface points.'}
if (HERE/'technical-measurements.json').exists():
 out=json.loads((HERE/'technical-measurements.json').read_text('utf-8'))
 out['guards_before'].update(guards)
selected=[v for v in sys.argv[1:] if v in 'ABC']
models={v:pickle.loads((HERE/f'model-{v}.pkl').read_bytes()) for v in 'ABC' if (HERE/f'model-{v}.pkl').exists()}
for variant in selected:
 model=models[variant];skel=model['skeleton'];face=model['exterior'];skin=face['parts']['skin'];prep(skin)
 row={'model_sha256':sha(HERE/f'model-{variant}.pkl'),'topology':{},'finite':{},'containment':{},'jaw_motion':{},'self_crossings':{},'eyes':{},'ears':[]}
 for layer,mod in [('skeleton',skel),('exterior',face)]:
  row['topology'][layer]={k:topo(part) for k,part in mod['parts'].items()}
  row['finite'][layer]=all(np.isfinite(v).all() for part in mod['parts'].values() for k,v in part.items() if isinstance(v,np.ndarray))
 for key in ['upper','jaw','cartilage']:
  part=skel['parts'][key];q=np.concatenate([part['v'],part['v'][part['f']].mean(1)]);inside=parity(q,skin)
  row['containment'][key]={'samples':len(q),'outside':int((~inside).sum()),'first_outside':q[~inside][:5].tolist(),'crossings':crossings(part,skin),**exact_minimum(q,skin)}
  print(variant,key,'outside',row['containment'][key]['outside'],'crossings',row['containment'][key]['crossings']['intersecting_pairs'],flush=True)
 for name,part in [('upper',skel['parts']['upper']),('jaw',skel['parts']['jaw']),('cartilage',skel['parts']['cartilage']),('skin',skin)]:row['self_crossings'][name]=crossings(part)
 for angle in [0,10,20]:
  jaw=copy.deepcopy(skel['parts']['jaw']);jaw['v']=m.bones.rotate(jaw['v'],skel['parameters']['hinge'],angle)
  q=np.concatenate([jaw['v'],jaw['v'][jaw['f']].mean(1)]);inside=parity(q,skel['parts']['upper'])
  row['jaw_motion'][str(angle)]={'samples':len(q),'inside_upper':int(inside.sum()),'crossings':crossings(jaw,skel['parts']['upper'])}
  print(variant,'jaw',angle,row['jaw_motion'][str(angle)],flush=True)
 for key in ['eye_-1','eye_1']:
  eye=face['parts'][key];q=np.concatenate([eye['v'],eye['v'][eye['f']].mean(1)]);inside=parity(q,skin);iv=inside[:len(eye['v'])]
  row['eyes'][key]={'inside_samples':int(inside.sum()),'outside_samples':int((~inside).sum()),'surface_crossing_faces':int((iv[eye['f']].any(1)&~iv[eye['f']].all(1)).sum())}
 ff,meta=m.skin.make_fields(skel,'jack_russell','B');f=skin['f'];edges=np.unique(np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1),axis=0)
 ear=ff['ears'](skin['v'])<ff['head'](skin['v']);boundary=edges[ear[edges[:,0]]!=ear[edges[:,1]]];centers=skin['v'][boundary].mean(1)
 for sign in [-1,1]:
  root=np.array(meta['ear_root'])*[1,1,sign];ax=np.arange(-6,6.01,.6);q=np.stack(np.meshgrid(ax,ax,ax,indexing='ij'),axis=-1).reshape(-1,3)+root
  row['ears'].append({'root':root.tolist(),'actual_shared_mesh_edges_near_root':int((np.linalg.norm(centers-root,axis=1)<12).sum()),'initial_field_overlap_samples':int(((ff['head'](q)<-.1)&(ff['ears'](q)<-.1)).sum())})
 black=np.all(skin['c']==[43,40,34],axis=1);inner=edges[black[edges].all(1)];remap=np.full(len(black),-1);remap[black]=np.arange(black.sum());graph=coo_matrix((np.ones(len(inner)),(remap[inner[:,0]],remap[inner[:,1]])),shape=(black.sum(),black.sum())).tocsr();nc,_=connected_components(graph,directed=False)
 row['nose']={'material_vertices':int(black.sum()),'material_components':int(nc),'shared_boundary_edges':int((black[edges[:,0]]!=black[edges[:,1]]).sum())}
 row['settings']=model['settings'];out['variants'][variant]=row;save(out)
 if '--reproduce' not in sys.argv:
  print('AUDIT DONE',variant,flush=True)
  continue
 fresh=m.create(variant)
 cleanface={**face,'parts':{k:{kk:vv for kk,vv in p.items() if not kk.startswith('_')} for k,p in face['parts'].items()}}
 row['reproduction']={'skeleton_exact':eq(fresh['skeleton'],skel),'exterior_exact':eq(fresh['exterior'],cleanface),'settings_exact':eq(fresh['settings'],model['settings'])}
 out['variants'][variant]=row;out['guards_unchanged']=all(sha(Path(p))==h for p,h in guards.items());save(out)
 print('DONE',variant,'reproduction',row['reproduction'],'self_crossings',row['self_crossings'],flush=True)
if '--final' not in sys.argv:
 out['guards_unchanged']=all(sha(Path(p))==h for p,h in out['guards_before'].items());save(out)
 raise SystemExit(0)
out['variation_isolation']={}
for v in 'AC':
 a=models['B']['settings'];b=models[v]['settings'];d0=np.array(a['profile']['dorsal']);d1=np.array(b['profile']['dorsal'])
 changed=np.argwhere(d0!=d1).tolist()
 out['variation_isolation'][v]={'changed_settings':[k for k in a if a[k]!=b[k]],'changed_dorsal_indices':changed,'only_anterior_x':changed==[[3,0],[4,0],[5,0]],'widths_hinge_fixed':a['profile']['widths']==b['profile']['widths'] and a['profile']['hinge_x']==b['profile']['hinge_x'],'rostral_delta_exact':bool(np.allclose((d1[3:,0]-d1[2,0])/(d0[3:,0]-d0[2,0]),m.VARIANTS[v],atol=1e-14))}
out['render_reproduction']={}
for name,im in m.boards(m.load_models()).items():
 saved=Image.open(HERE/name)
 out['render_reproduction'][name]={'dimensions':list(saved.size),'mode':saved.mode,'pixels_exact':saved.size==im.size and saved.mode==im.mode and saved.tobytes()==im.tobytes()}
out['guards_unchanged']=all(sha(Path(p))==h for p,h in guards.items());save(out)
print('COMPLETE',out['guards_unchanged'],out['variation_isolation'],out['render_reproduction'],flush=True)
