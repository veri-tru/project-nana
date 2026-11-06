"""Final actual-surface audit; run only after all variants are saved/frozen."""
from pathlib import Path
import ast,importlib.util,hashlib,pickle,json,numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'skull-based-heads-v1'
for path,names in [(OLD/'review_saved_mesh.py',['topo','nearest','prep']),(OLD/'review_ray_containment.py',['parity']),(OLD/'review_final_geometry.py',['exact_minimum']),(HERE/'review_dev10_crossings.py',['hits','coplanar_overlap'])]:
 for node in ast.parse(path.read_text('utf-8')).body:
  if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sorted_rows(v):return v[np.lexsort((v[:,2],v[:,1],v[:,0]))]
def crossings(first,second=None):
 selftest=second is None
 if selftest:second=first
 f=first['f'];g=second['f'];a=first['v'][f].astype(float);b=second['v'][g].astype(float);ac=a.mean(1);bc=b.mean(1);ar=np.linalg.norm(a-ac[:,None],axis=2).max(1);br=np.linalg.norm(b-bc[:,None],axis=2).max(1);tree=cKDTree(bc);al=a.min(1);au=a.max(1);bl=b.min(1);bu=b.max(1);count=0;found=[]
 for start in range(0,len(f),600):
  rows=np.arange(start,min(start+600,len(f)));lists=tree.query_ball_point(ac[rows],ar[rows]+br.max()+1e-8);ii=np.repeat(rows,[len(v) for v in lists]);jj=np.concatenate(lists).astype(int)
  if selftest:
   use=jj>ii;ii=ii[use];jj=jj[use]
  use=(np.maximum(al[ii],bl[jj])<=np.minimum(au[ii],bu[jj])+1e-9).all(1);ii=ii[use];jj=jj[use]
  if selftest:
   use=~(f[ii,:,None]==g[jj,None,:]).any((1,2));ii=ii[use];jj=jj[use]
  count+=len(ii)
  if len(ii):
   hit=hits(a[ii],b[jj])|hits(b[jj],a[ii])|coplanar_overlap(a[ii],b[jj]);found.extend(np.column_stack([ii[hit],jj[hit]]).tolist())
 return {'aabb_candidate_pairs':count,'intersecting_pairs':len(found),'first_pairs':found[:15]}
files=['build.py','geometry.pkl','parameters.json','heads-A.png','heads-B.png','heads-C.png'];guards={p:sha(HERE/p) for p in files};models=pickle.loads((HERE/'geometry.pkl').read_bytes());oldmodels=pickle.loads((OLD/'geometry.pkl').read_bytes())['B'];spec=importlib.util.spec_from_file_location('review_final_v2_builder',HERE/'build.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);skels=m.load_inputs();out={'hashes':guards,'variants':{},'variation_isolation':{},'scope':'Final saved meshes only. Analytic fields used only to label ear/head semantic partitions, never to certify post-relaxation containment.'}
for variant in ['A','B','C']:
 out['variants'][variant]={}
 for breed,model in models[variant].items():
  skin=model['parts']['skin'];prep(skin);row={'topology':{k:topo(v) for k,v in model['parts'].items()},'finite_arrays':all(np.isfinite(value).all() for part in model['parts'].values() for key,value in part.items() if not key.startswith('_')),'bones':{},'eyes':{},'ears':[]}
  for key in ['upper','jaw']:
   p=skels[breed]['parts'][key];q=np.concatenate([p['v'],p['v'][p['f']].mean(1)]);inside=parity(q,skin);rec={'samples':len(q),'outside_actual_mesh':int((~inside).sum()),'first_outside':q[~inside][:8].tolist()};rec.update(exact_minimum(q,skin));rec['triangle_crossings']=crossings(p,skin);row['bones'][key]=rec
  for key in ['eye_-1','eye_1']:
   p=model['parts'][key];q=np.concatenate([p['v'],p['v'][p['f']].mean(1)]);inside=parity(q,skin);iv=inside[:len(p['v'])];row['eyes'][key]={'inside_samples':int(inside.sum()),'outside_samples':int((~inside).sum()),'crossing_faces':int((iv[p['f']].any(1)&(~iv[p['f']].all(1))).sum()),'arrays_exact_v1B':{k:np.array_equal(v,oldmodels[breed]['parts'][key][k]) for k,v in p.items()}}
  old=oldmodels[breed]['parts']['skin'];black=np.all(skin['c']==[43,40,34],axis=1);v=skin['v'][black];ov=old['v'][np.all(old['c']==[43,40,34],axis=1)];row['black_nose']={'vertices':len(v),'old_vertices':len(ov),'coordinates_byte_exact_v1B':v.dtype==ov.dtype and sorted_rows(v).tobytes()==sorted_rows(ov).tobytes()}
  row['self_crossings']=crossings(skin)
  ff,meta=m.make_fields(skels[breed],breed,variant);f=skin['f'];edges=np.unique(np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1),axis=0);ear=ff['ears'](skin['v'])<ff['head'](skin['v']);boundary=edges[ear[edges[:,0]]!=ear[edges[:,1]]];centers=skin['v'][boundary].mean(1)
  for path in meta['ear_paths']:
   root=np.array(path[0]);local=np.linalg.norm(centers-root,axis=1)<12;row['ears'].append({'root':root.tolist(),'actual_shared_mesh_edges_near_root':int(local.sum()),'partition_basis':'initial head/ear fields evaluated at final saved vertices'})
  out['variants'][variant][breed]=row;print('Checked',variant,breed,'outside',sum(r['outside_actual_mesh'] for r in row['bones'].values()),'bone crossings',sum(r['triangle_crossings']['intersecting_pairs'] for r in row['bones'].values()),'self',row['self_crossings']['intersecting_pairs'],flush=True);(HERE/'review-final-geometry-progress.json').write_text(json.dumps(out,indent=2),'utf-8')
for breed in m.BREEDS:
 base=models['B'][breed];row={}
 for variant in ['A','C']:
  model=models[variant][breed];a=base['metadata'];b=model['metadata'];changed=[k for k in a if a[k]!=b[k]];relax_changed=[k for k in a['surface_relaxation'] if a['surface_relaxation'][k]!=b['surface_relaxation'][k]];row[variant]={'changed_metadata_keys':changed,'surface_relaxation_changed_keys':relax_changed,'only_declared_settings':set(changed)<=set(['variant','front_patch','surface_relaxation']) and set(relax_changed)<=set(['iterations','maximum_displacement']),'skin_faces_exact':np.array_equal(base['parts']['skin']['f'],model['parts']['skin']['f']),'skin_colors_exact':np.array_equal(base['parts']['skin']['c'],model['parts']['skin']['c']),'profile_exact_source':b['profile']==skels[breed]['profile']}
 out['variation_isolation'][breed]=row
out['hashes_stable']=all(sha(HERE/p)==h for p,h in guards.items());(HERE/'review-final-geometry.json').write_text(json.dumps(out,indent=2),'utf-8');print('FINAL actual surface checks complete',out['hashes_stable'],flush=True)
