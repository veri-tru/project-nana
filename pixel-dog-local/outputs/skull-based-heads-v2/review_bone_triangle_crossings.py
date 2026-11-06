"""Frozen iteration actual skin/bone triangle intersection audit."""
from pathlib import Path
import ast,sys,numpy as np,pickle,json,hashlib
from scipy.spatial import cKDTree
root=Path(__file__).resolve().parent;iteration=sys.argv[1];cache=root/'iterations'/iteration/'geometry.pkl';digest=hashlib.sha256(cache.read_bytes()).hexdigest()
for node in ast.parse((root/'review_dev10_crossings.py').read_text('utf-8')).body:
 if isinstance(node,ast.FunctionDef):exec(compile(ast.Module(body=[node],type_ignores=[]),'crossing_helpers','exec'))
models=pickle.loads(cache.read_bytes())['B'];bones=pickle.loads((root.parent/'head-skeleton-volume-v2/geometry.pkl').read_bytes());out={'frozen_cache_path':f'iterations/{iteration}/geometry.pkl','cache_sha256':digest,'scope':'Skin/bone triangle pairs using complete centroid-radius and AABB broadphase; edge/triangle and coplanar tests. Floating-tolerance diagnostic.','breeds':{}}
for b,model in models.items():
 skin=model['parts']['skin'];st=skin['v'][skin['f']].astype(float);sc=st.mean(1);sr=np.linalg.norm(st-sc[:,None],axis=2).max(1);tree=cKDTree(sc);sl=st.min(1);su=st.max(1);row={}
 for key in ['upper','jaw']:
  bone=bones[b]['parts'][key];bt=bone['v'][bone['f']].astype(float);bc=bt.mean(1);br=np.linalg.norm(bt-bc[:,None],axis=2).max(1);bl=bt.min(1);bu=bt.max(1);candidate_count=0;hits_all=[]
  for start in range(0,len(bt),800):
   rows=np.arange(start,min(start+800,len(bt)));lists=tree.query_ball_point(bc[rows],br[rows]+sr.max()+1e-8);aa=np.repeat(rows,[len(x) for x in lists]);bb=np.concatenate(lists).astype(int);keep=(np.maximum(bl[aa],sl[bb])<=np.minimum(bu[aa],su[bb])+1e-9).all(1);aa=aa[keep];bb=bb[keep];candidate_count+=len(aa)
   if len(aa):
    collision=hits(bt[aa],st[bb])|hits(st[bb],bt[aa])|coplanar_overlap(bt[aa],st[bb]);hits_all.extend(np.column_stack([aa[collision],bb[collision]]).tolist())
  row[key]={'aabb_candidates':candidate_count,'intersecting_pairs':len(hits_all),'first_pairs':hits_all[:20],'first_pair_centers':[[bc[a].tolist(),sc[z].tolist()] for a,z in hits_all[:5]]}
 out['breeds'][b]=row;print(b,{k:v['intersecting_pairs'] for k,v in row.items()},flush=True)
out['frozen_cache_stable']=digest==hashlib.sha256(cache.read_bytes()).hexdigest();(root/f'review-dev{iteration}-bone-triangle-crossings.json').write_text(json.dumps(out,indent=2),'utf-8')
