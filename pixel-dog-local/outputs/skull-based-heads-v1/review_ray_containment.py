"""Independent actual closed-mesh containment by +X ray parity, no field assumptions."""
from pathlib import Path
import numpy as np,pickle,json,hashlib
from scipy.spatial import cKDTree
HERE=Path(__file__).resolve().parent

def parity(q,part):
 tri=part['v'][part['f']].astype(float);cent=tri[:,:,1:].mean(1);rad=np.linalg.norm(tri[:,:,1:]-cent[:,None],axis=2).max();tree=cKDTree(cent);a=tri[:,0];ab=tri[:,1]-a;ac=tri[:,2]-a;det=ab[:,1]*ac[:,2]-ac[:,1]*ab[:,2]
 result=[]
 for start in range(0,len(q),1500):
  pts=q[start:start+1500].astype(float).copy();pts[:,1]+=1.123e-5;pts[:,2]+=2.719e-5
  lists=tree.query_ball_point(pts[:,1:],rad+1e-8);counts=np.array([len(x) for x in lists]);ri=np.repeat(np.arange(len(pts)),counts);ix=np.concatenate(lists).astype(int);dy=pts[ri,1]-a[ix,1];dz=pts[ri,2]-a[ix,2];dd=det[ix];good=np.abs(dd)>1e-12;safe=np.where(good,dd,1)
  u=(dy*ac[ix,2]-dz*ac[ix,1])/safe;v=(ab[ix,1]*dz-ab[ix,2]*dy)/safe;xx=a[ix,0]+u*ab[ix,0]+v*ac[ix,0]
  hit=good&(u>=0)&(v>=0)&(u+v<=1)&(xx>pts[ri,0]);number=np.bincount(ri[hit],minlength=len(pts));result.extend(number%2==1)
 return np.array(result)
cache=HERE/'geometry.pkl';digest=hashlib.sha256(cache.read_bytes()).hexdigest();models=pickle.loads(cache.read_bytes())['B'];bones=pickle.loads((HERE.parent/'head-skeleton-volume-v2/geometry.pkl').read_bytes());out={'method':'Complete +X ray candidates via projected-triangle centroid radius bound; 0.00001 coordinate perturbation avoids shared-edge double counts. Not a continuous-triangle containment proof.','cache_sha256':digest,'breeds':{}}
for b,model in models.items():
 row={}
 for k in ['upper','jaw']:
  p=bones[b]['parts'][k];q=np.concatenate([p['v'],p['v'][p['f']].mean(1)]);inside=parity(q,model['parts']['skin']);row[k]={'samples':len(q),'outside':int((~inside).sum()),'first_outside':q[~inside][:5].tolist()}
 out['breeds'][b]=row;print(b,row,flush=True)
out['cache_stable']=digest==hashlib.sha256(cache.read_bytes()).hexdigest();(HERE/'review-pass11-ray-containment.json').write_text(json.dumps(out,indent=2),'utf-8')
