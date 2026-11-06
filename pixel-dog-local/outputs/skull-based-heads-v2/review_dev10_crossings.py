"""Non-adjacent triangle crossing diagnostic, including coplanar overlap."""
from pathlib import Path
import numpy as np,pickle,json,hashlib
from scipy.spatial import cKDTree
HERE=Path(__file__).resolve().parent

def hits(tri,other):
 a,b,c=np.moveaxis(other,1,0);e1=b-a;e2=c-a;answer=np.zeros(len(tri),bool)
 for j in range(3):
  start=tri[:,j];direction=tri[:,(j+1)%3]-start;hh=np.cross(direction,e2);det=np.sum(e1*hh,axis=1);valid=np.abs(det)>1e-12;inv=np.where(valid,1/np.where(valid,det,1),0);s=start-a;u=inv*np.sum(s*hh,axis=1);qq=np.cross(s,e1);v=inv*np.sum(direction*qq,axis=1);t=inv*np.sum(e2*qq,axis=1);answer|=valid&(u>=-1e-9)&(v>=-1e-9)&(u+v<=1+1e-9)&(t>=-1e-9)&(t<=1+1e-9)
 return answer

def coplanar_overlap(t,u):
 n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);nn=np.linalg.norm(n,axis=1);n/=np.maximum(nn[:,None],1e-30);other=np.cross(u[:,1]-u[:,0],u[:,2]-u[:,0]);other/=np.maximum(np.linalg.norm(other,axis=1)[:,None],1e-30);same=(np.linalg.norm(np.cross(n,other),axis=1)<1e-7)&(np.abs(np.sum((u[:,0]-t[:,0])*n,axis=1))<1e-8);answer=np.zeros(len(t),bool)
 for axis in range(3):
  ids=np.flatnonzero(same&(np.abs(n).argmax(1)==axis))
  if not len(ids):continue
  coords=[k for k in range(3) if k!=axis];a=t[ids][:,:,coords];b=u[ids][:,:,coords];overlap=np.ones(len(ids),bool)
  for p in [a,b]:
   for j in range(3):
    e=p[:,(j+1)%3]-p[:,j];normal=np.stack([-e[:,1],e[:,0]],axis=1);pa=np.sum(a*normal[:,None],axis=2);pb=np.sum(b*normal[:,None],axis=2);overlap&=(np.minimum(pa.max(1),pb.max(1))-np.maximum(pa.min(1),pb.min(1)))>1e-10
  answer[ids]=overlap
 return answer
cache=HERE/'geometry.pkl';digest=hashlib.sha256(cache.read_bytes()).hexdigest();models=pickle.loads(cache.read_bytes())['B'];out={'cache_sha256':digest,'scope':'All skin triangle pairs whose AABBs overlap, excluding pairs sharing any vertex. Noncoplanar segment/triangle hits and coplanar 2D positive-area overlap. Floating tolerances stated in source; not a formal proof of all self-contact.','breeds':{}}
for breed,model in models.items():
 part=model['parts']['skin'];f=part['f'];tri=part['v'][f].astype(float);cent=tri.mean(1);radii=np.linalg.norm(tri-cent[:,None],axis=2).max(1);rmax=radii.max();tree=cKDTree(cent);lower=tri.min(1);upper=tri.max(1);candidate_count=0;collisions=[];coplanar_count=0
 for start in range(0,len(f),600):
  rows=np.arange(start,min(start+600,len(f)));lists=tree.query_ball_point(cent[rows],radii[rows]+rmax+1e-8);aa=np.repeat(rows,[len(v) for v in lists]);bb=np.concatenate(lists).astype(int);keep=bb>aa;aa=aa[keep];bb=bb[keep];keep=(np.maximum(lower[aa],lower[bb])<=np.minimum(upper[aa],upper[bb])+1e-9).all(1);aa=aa[keep];bb=bb[keep];shared=(f[aa,:,None]==f[bb,None,:]).any((1,2));aa=aa[~shared];bb=bb[~shared];candidate_count+=len(aa)
  if len(aa):
   cross=hits(tri[aa],tri[bb])|hits(tri[bb],tri[aa]);cop=coplanar_overlap(tri[aa],tri[bb]);coplanar_count+=int(cop.sum());ids=np.flatnonzero(cross|cop);collisions.extend(np.column_stack([aa[ids],bb[ids]]).tolist())
 out['breeds'][breed]={'skin_faces':len(f),'max_triangle_centroid_radius':float(rmax),'nonadjacent_aabb_candidates':candidate_count,'intersecting_pairs':len(collisions),'coplanar_overlapping_pairs':coplanar_count,'first_pairs':collisions[:20],'first_pair_centers':[(cent[a].tolist(),cent[b].tolist()) for a,b in collisions[:10]]};print(breed,out['breeds'][breed],flush=True);(HERE/'review-dev10-crossings-progress.json').write_text(json.dumps(out,indent=2),'utf-8')
out['cache_stable']=digest==hashlib.sha256(cache.read_bytes()).hexdigest();(HERE/'review-dev10-crossings.json').write_text(json.dumps(out,indent=2),'utf-8')
