"""Bounded saved-surface audit after mesh relaxation. Does not use analytic exterior fields."""
from pathlib import Path
import ast,pickle,json,hashlib,numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'skull-based-heads-v1'
for file,names in [('review_saved_mesh.py',['topo']),('review_ray_containment.py',['parity'])]:
 for node in ast.parse((OLD/file).read_text('utf-8')).body:
  if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),file,'exec'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sorted_rows(v):return v[np.lexsort((v[:,2],v[:,1],v[:,0]))]
guards={name:sha(HERE/name) for name in ['build.py','geometry.pkl','heads-B.png']};assert guards['heads-B.png']=='7cfa4ab5dce70cf80479a1756f99fd434df2544783f8f4db1f02e838a7a675f1'
models=pickle.loads((HERE/'geometry.pkl').read_bytes())['B'];oldmodels=pickle.loads((OLD/'geometry.pkl').read_bytes())['B'];skels=pickle.loads((HERE.parent/'head-skeleton-volume-v2/geometry.pkl').read_bytes());report={'scope':'B actual saved surface; no analytic containment or full reproduction','hashes':guards,'breeds':{}}
for b,model in models.items():
 skin=model['parts']['skin'];row={'topology':{k:topo(p) for k,p in model['parts'].items()},'bones':{},'eyes':{}}
 for k in ['upper','jaw']:
  p=skels[b]['parts'][k];q=np.concatenate([p['v'],p['v'][p['f']].mean(1)]);inside=parity(q,skin);out=q[~inside];row['bones'][k]={'samples':len(q),'outside_actual_mesh':len(out),'outside_bbox':[out.min(0).tolist(),out.max(0).tolist()] if len(out) else None,'first_outside':out[:10].tolist()}
 for k in ['eye_-1','eye_1']:
  p=model['parts'][k];q=np.concatenate([p['v'],p['v'][p['f']].mean(1)]);inside=parity(q,skin);verts=inside[:len(p['v'])];row['eyes'][k]={'inside_samples':int(inside.sum()),'outside_samples':int((~inside).sum()),'crossing_faces':int((verts[p['f']].any(1)&(~verts[p['f']].all(1))).sum()),'arrays_exact_old_B':{key:np.array_equal(value,oldmodels[b]['parts'][k][key]) for key,value in p.items()}}
 old=oldmodels[b]['parts']['skin'];v=skin['v'][np.all(skin['c']==[43,40,34],axis=1)];ov=old['v'][np.all(old['c']==[43,40,34],axis=1)];row['black_nose']={'count':len(v),'old_count':len(ov),'sorted_coordinates_byte_exact':v.dtype==ov.dtype and sorted_rows(v).tobytes()==sorted_rows(ov).tobytes(),'max_nearest_old_distance':float(cKDTree(ov).query(v)[0].max())}
 row['finite_arrays']=all(np.isfinite(value).all() for part in model['parts'].values() for value in part.values());report['breeds'][b]=row;print(b,'outside bones',sum(x['outside_actual_mesh'] for x in row['bones'].values()),'black exact',row['black_nose']['sorted_coordinates_byte_exact'],flush=True);(HERE/'review-dev10-mesh-progress.json').write_text(json.dumps(report,indent=2),'utf-8')
report['hashes_stable']=all(sha(HERE/k)==v for k,v in guards.items());(HERE/'review-dev10-saved-mesh.json').write_text(json.dumps(report,indent=2),'utf-8');print('DONE',report['hashes_stable'],flush=True)
