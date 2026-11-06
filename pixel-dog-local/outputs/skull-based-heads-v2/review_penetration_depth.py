"""Actual penetration depths on parity-outside bone samples in frozen cache."""
from pathlib import Path
import sys,ast,json,pickle,hashlib,numpy as np
from scipy.spatial import cKDTree
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'skull-based-heads-v1';iteration=sys.argv[1]
for file,names in [('review_saved_mesh.py',['nearest','prep']),('review_ray_containment.py',['parity'])]:
 text=(OLD/file).read_text('utf-8')
 for node in ast.parse(text).body:
  if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),file,'exec'))
cache=HERE/'iterations'/iteration/'geometry.pkl';digest=hashlib.sha256(cache.read_bytes()).hexdigest();models=pickle.loads(cache.read_bytes())['B'];bones=pickle.loads((HERE.parent/'head-skeleton-volume-v2/geometry.pkl').read_bytes());out={'cache_sha256':digest,'iteration':iteration,'breeds':{}}
for b,model in models.items():
 skin=model['parts']['skin'];prep(skin);row={}
 for key in ['upper','jaw']:
  part=bones[b]['parts'][key];q=np.concatenate([part['v'],part['v'][part['f']].mean(1)]);inside=parity(q,skin);q=q[~inside]
  if not len(q):row[key]={'outside_samples':0,'maximum_penetration':0.};continue
  dd=[];closest=[];cert=[]
  for start in range(0,len(q),256):
   d,c,k=nearest(q[start:start+256],skin);dd.extend(np.abs(d));closest.extend(c);cert.extend(k)
  dd=np.array(dd);closest=np.array(closest);cert=np.array(cert);i=int(dd.argmax());row[key]={'outside_samples':len(q),'maximum_penetration':float(dd[i]),'p95_penetration':float(np.quantile(dd,.95)),'median_penetration':float(np.median(dd)),'all_nearest_certified':bool(cert.all()),'uncertified_samples':int((~cert).sum()),'worst_bone_point':q[i].tolist(),'nearest_skin_point':closest[i].tolist(),'outside_bbox':[q.min(0).tolist(),q.max(0).tolist()],'nearest_skin_bbox':[closest.min(0).tolist(),closest.max(0).tolist()]}
 out['breeds'][b]=row;print(b,{k:x['maximum_penetration'] for k,x in row.items()},flush=True)
out['cache_stable']=digest==hashlib.sha256(cache.read_bytes()).hexdigest();(HERE/f'review-dev{iteration}-penetration-depth.json').write_text(json.dumps(out,indent=2),'utf-8');print(json.dumps(out,indent=2),flush=True)
