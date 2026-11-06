"""Independent A/C saved-geometry checks, reusing hash-matched B evidence."""
from pathlib import Path
import ast,importlib.util,pickle,json,hashlib,copy
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE=Path(__file__).resolve().parent
for filename,names in [('review_saved_mesh.py',['nearest','topo','prep']),('review_ray_containment.py',['parity'])]:
 source=(HERE/filename).read_text('utf-8');tree=ast.parse(source)
 for node in tree.body:
  if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),filename,'exec'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def exact_minimum(q,skin):
 tri,cent,radii,tree=skin['_nearest_cache'];rmax=radii.max();dist,_=tree.query(q,k=1);ix=int(dist.argmin());sd,_,_=nearest(q[ix:ix+1],skin);upper=float(abs(sd[0]));lower=dist-rmax;chosen=np.flatnonzero(lower<=upper+1e-5);best=upper;worst=q[ix];omitted=float(lower[lower>upper+1e-5].min()) if (lower>upper+1e-5).any() else float('inf')
 for start in range(0,len(chosen),512):
  pts=q[chosen[start:start+512]];sd,_,_=nearest(pts,skin);ii=int(np.abs(sd).argmin());new=float(abs(sd[ii]));dd,_=tree.query(pts,k=[96]);omitted=min(omitted,float(dd.min()-rmax))
  if new<best:best=new;worst=pts[ii]
 return dict(minimum_distance=best,worst_point=worst.tolist(),all_sampled_minimum_certified=bool(omitted>best),omitted_triangle_lower_bound=omitted,triangle_distance_samples=len(chosen))
cache=HERE/'geometry.pkl';source=HERE/'build.py';guards={str(p):sha(p) for p in [cache,source]};models=pickle.loads(cache.read_bytes());spec=importlib.util.spec_from_file_location('review_final_skin_geometry',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);skels=m.load_inputs();out={'source_sha256':sha(source),'cache_sha256':sha(cache),'variants':{},'variant_isolation':{},'nose_template':{}}
for variant in ['A','C']:
 out['variants'][variant]={}
 for b in m.BREEDS:
  model=models[variant][b];skin=model['parts']['skin'];prep(skin);ff,meta=m.make_fields(skels[b],b,variant);row={'topology':{k:topo(v) for k,v in model['parts'].items()},'bones':{},'eyes':{},'ears':[]}
  for k in ['upper','jaw']:
   bone=skels[b]['parts'][k];q=np.concatenate([bone['v'],bone['v'][bone['f']].mean(1)]);inside=parity(q,skin);field=ff['exterior'](q);rec={'samples':len(q),'outside_actual_mesh':int((~inside).sum()),'outside_raw_field':int((field>0).sum()),'maximum_raw_field':float(field.max())};rec.update(exact_minimum(q,skin));row['bones'][k]=rec
  for key in ['eye_-1','eye_1']:
   eye=model['parts'][key];q=np.concatenate([eye['v'],eye['v'][eye['f']].mean(1)]);inside=parity(q,skin);verts=inside[:len(eye['v'])];cross=(verts[eye['f']].any(1))&(~verts[eye['f']].all(1));row['eyes'][key]={'inside_samples':int(inside.sum()),'outside_samples':int((~inside).sum()),'crossing_faces':int(cross.sum())}
  for path in meta['ear_paths']:
   root=np.array(path[0]);ax=np.arange(-6,6.01,.6);q=np.stack(np.meshgrid(ax,ax,ax,indexing='ij'),axis=-1).reshape(-1,3)+root;row['ears'].append({'root':root.tolist(),'local_overlap_samples':int(((ff['head'](q)<-.1)&(ff['ears'](q)<-.1)).sum())})
  mask=np.all(skin['c']==[43,40,34],axis=1);f=skin['f'];edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);edges=np.unique(edges,axis=0);inner=edges[mask[edges].all(1)];remap=np.full(len(mask),-1);remap[mask]=np.arange(mask.sum());graph=coo_matrix((np.ones(len(inner)),(remap[inner[:,0]],remap[inner[:,1]])),shape=(mask.sum(),mask.sum())).tocsr();nc,_=connected_components(graph,directed=False);row['nose']={'material_vertices':int(mask.sum()),'material_components':int(nc),'shared_boundary_edges':int((mask[edges[:,0]]!=mask[edges[:,1]]).sum())}
  out['variants'][variant][b]=row;print('Saved mesh checked',variant,b,'outside',sum(x['outside_actual_mesh'] for x in row['bones'].values()),flush=True);(HERE/'review-final-geometry-progress.json').write_text(json.dumps(out,indent=2),'utf-8')
# Exact metadata isolation plus functional common nasal template.
reference=None;ax=np.linspace(-1.5,1.5,17);unit=np.stack(np.meshgrid(ax,ax,ax,indexing='ij'),axis=-1)
for b in m.BREEDS:
 base=models['B'][b]['metadata'];row={}
 for v in ['A','C']:
  data=models[v][b]['metadata'];changed=[k for k in base if base[k]!=data[k]];row[v]={'changed_metadata_keys':changed,'only_declared_dependents':set(changed)<=set(['sections','eyes','variant']),'profile_exact_source':data['profile']==skels[b]['profile']}
 out['variant_isolation'][b]=row
 for v in m.VARIANTS:
  ff,meta=m.make_fields(skels[b],b,v);normalized=ff['nose'](unit*meta['nose_size']+np.array(meta['nose_center']))/meta['nose_size']
  if reference is None:reference=normalized
  out['nose_template'][v+'_'+b]=float(np.max(np.abs(normalized-reference)))
# Perturb actual source bone vertices with all profile labels unchanged.
b='golden';base=skels[b];altered=copy.deepcopy(base);v=altered['parts']['upper']['v'];mask=(v[:,1]>27)&(v[:,0]>-35)&(v[:,0]<-5);v[mask,1]+=2.;ff,meta=m.make_fields(base,b,'B');ff2,meta2=m.make_fields(altered,b,'B');q=models['B'][b]['parts']['skin']['v'];delta=np.abs(ff2['exterior'](q)-ff['exterior'](q));out['bone_dependency']={'mutated_source_vertices':int(mask.sum()),'profile_unchanged':base['profile']==altered['profile'],'max_surface_field_change':float(delta.max()),'changed_surface_samples_gt_001':int((delta>.01).sum()),'section_radii_changed':meta['sections']['radius']!=meta2['sections']['radius']}
# Fresh mesh on the same production grid confirms a field change reaches actual surface geometry.
d=np.array(base['profile']['dorsal']);W=base['profile']['widths'][0];bounds=[(d[5,0]-12,28),(-30,d[0,1]+24),(-W*2.4,W*2.4)];fresh,faces,_=m.extract(ff2['exterior'],bounds);original=models['B'][b]['parts']['skin']['v'];out['bone_dependency']['fresh_mesh_changed']=fresh.shape!=original.shape or not np.array_equal(fresh,original);out['bone_dependency']['fresh_vertex_count']=len(fresh)
out['guards_unchanged']=all(sha(Path(p))==h for p,h in guards.items());(HERE/'review-final-geometry.json').write_text(json.dumps(out,indent=2),'utf-8');print('GEOMETRY COMPLETE',flush=True)
