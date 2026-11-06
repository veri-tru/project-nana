"""Reviewer-owned lightweight actual-mesh preflight for development models."""
from pathlib import Path
import ast,hashlib,json,pickle,sys
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE=Path(__file__).resolve().parent
for path,names in [(HERE.parent/'skull-based-heads-v1/review_saved_mesh.py',['topo']),(HERE.parent/'skull-based-heads-v1/review_ray_containment.py',['parity'])]:
 for node in ast.parse(path.read_text('utf-8')).body:
  if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'))
file=HERE/sys.argv[1];model=pickle.loads(file.read_bytes());skin=model['exterior']['parts']['skin']
out={'model':str(file.relative_to(HERE)),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'skin_topology':topo(skin),'containment':{}}
for name,part in model['skeleton']['parts'].items():
 q=np.concatenate([part['v'],part['v'][part['f']].mean(1)]);inside=parity(q,skin)
 out['containment'][name]={'samples':len(q),'outside':int((~inside).sum()),'first_outside':q[~inside][:8].tolist()}
 print(name,out['containment'][name],flush=True)
(HERE/('technical-preflight-'+file.stem+'.json')).write_text(json.dumps(out,indent=2),'utf-8')
print(out['skin_topology'],flush=True)
