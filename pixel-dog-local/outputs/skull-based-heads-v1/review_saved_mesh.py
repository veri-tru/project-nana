"""Reviewer-owned saved-mesh preflight; no generation or source mutation."""
from pathlib import Path
import importlib.util,hashlib,json,pickle
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE=Path(__file__).resolve().parent
def nearest(points,part):
    tri,cent,radii,tree=part['_nearest_cache']
    distances,indices=tree.query(points,k=96);t=tri[indices];a,b,c=t[:,:,0],t[:,:,1],t[:,:,2];p=points[:,None]
    ab=b-a;ac=c-a;normal=np.cross(ab,ac);normal/=np.maximum(np.linalg.norm(normal,axis=2,keepdims=True),1e-14)
    proj=p-np.sum((p-a)*normal,axis=2,keepdims=True)*normal
    dot00=np.sum(ab*ab,axis=2);dot01=np.sum(ab*ac,axis=2);dot11=np.sum(ac*ac,axis=2);pv=proj-a;dot20=np.sum(pv*ab,axis=2);dot21=np.sum(pv*ac,axis=2);den=dot00*dot11-dot01**2
    u=(dot11*dot20-dot01*dot21)/np.maximum(den,1e-20);v=(dot00*dot21-dot01*dot20)/np.maximum(den,1e-20);inside=(u>=0)&(v>=0)&(u+v<=1)
    poss=[proj]
    for x,y in [(a,b),(b,c),(c,a)]:
        delta=y-x;u=np.clip(np.sum((p-x)*delta,axis=2)/np.sum(delta*delta,axis=2),0,1);poss.append(x+u[:,:,None]*delta)
    candidates=np.stack(poss,axis=2);dd=np.sum((candidates-p[:,:,None])**2,axis=3);dd[:,:,0]=np.where(inside,dd[:,:,0],np.inf)
    which=dd.argmin(2);best=np.take_along_axis(candidates,which[:,:,None,None],axis=2)[:,:,0];d2=dd.min(2);facechoice=d2.argmin(1);rows=np.arange(len(points));q=best[rows,facechoice];normal=normal[rows,facechoice];ix=indices[rows,facechoice]
    avg=part['n'][part['f'][ix]].mean(1);normal*=np.where(np.sum(normal*avg,axis=1)>=0,1.,-1.)[:,None]
    distance=np.sqrt(d2[rows,facechoice]);signed=distance*np.sign(np.sum((points-q)*normal,axis=1))
    certified=distances[:,-1]-radii.max()>distance
    return signed,q,certified
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def topo(part):
 v,f=part['v'],part['f'];edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);unique,counts=np.unique(edges,axis=0,return_counts=True)
 graph=coo_matrix((np.ones(len(unique)),(unique[:,0],unique[:,1])),shape=(len(v),len(v))).tocsr();nc,labels=connected_components(graph,directed=False)
 return dict(vertices=len(v),faces=len(f),components=int(nc),boundary_edges=int((counts==1).sum()),nonmanifold_edges=int((counts>2).sum()),euler=int(len(v)-len(unique)+len(f)),zero_area_faces=int((np.linalg.norm(np.cross(v[f[:,1]].astype(float)-v[f[:,0]],v[f[:,2]].astype(float)-v[f[:,0]]),axis=1)==0).sum()),near_zero_double_area_lt_1e10=int((np.linalg.norm(np.cross(v[f[:,1]].astype(float)-v[f[:,0]],v[f[:,2]].astype(float)-v[f[:,0]]),axis=1)<1e-10).sum()))
def prep(part):
 tri=part['v'][part['f']];cent=tri.mean(1);radii=np.linalg.norm(tri-cent[:,None],axis=2).max(1);part['_nearest_cache']=(tri,cent,radii,cKDTree(cent))
def scan(q,skin):
 sd=[];cert=[]
 for start in range(0,len(q),512):
  a,_,c=nearest(q[start:start+512],skin);sd.extend(a);cert.extend(c)
 return np.array(sd),np.array(cert)
def summary(sd,cert,q):
 i=int(sd.argmax());return dict(samples=len(sd),max_signed_mesh_distance=float(sd[i]),outside_gt_001=int((sd>.01).sum()),outside_gt_01=int((sd>.1).sum()),all_nearest_certified=bool(cert.all()),uncertified=int((~cert).sum()),worst_point=q[i].tolist(),minimum_signed_mesh_distance=float(sd.min()))
source=HERE/'build.py';cache=HERE/'geometry.pkl';image=HERE/'heads-B.png'
report=dict(scope='B saved mesh preflight only; no reproduction',source_sha256=sha(source),cache_sha256=sha(cache),image_sha256=sha(image),breeds={})
spec=importlib.util.spec_from_file_location('review_skin11',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
models=pickle.loads(cache.read_bytes())['B'];skels=m.load_inputs()
for b in m.BREEDS:
 model=models[b];skin=model['parts']['skin'];prep(skin);ff,meta=m.make_fields(skels[b],b,'B');row=dict(topology={k:topo(part) for k,part in model['parts'].items()},bones={},eyes={},ears=[])
 for key in ['upper','jaw']:
  part=skels[b]['parts'][key];q=np.concatenate([part['v'],part['v'][part['f']].mean(1)]);sd,cert=scan(q,skin);row['bones'][key]=summary(sd,cert,q)
 for key in ['eye_-1','eye_1']:
  eye=model['parts'][key];q=np.concatenate([eye['v'],eye['v'][eye['f']].mean(1)]);sd,cert=scan(q,skin);row['eyes'][key]=summary(sd,cert,q);row['eyes'][key]['inside_vertices_and_centroids']=int((sd<-.01).sum());row['eyes'][key]['surface_crossing_faces']=int(((sd[:len(eye['v'])][eye['f']].min(1)<0)&(sd[:len(eye['v'])][eye['f']].max(1)>0)).sum())
 # Local root overlap establishes an actual volumetric seam, beyond global component count.
 for path in meta['ear_paths']:
  root=np.array(path[0]);axis=np.arange(-6,6.01,.6);q=np.stack(np.meshgrid(axis,axis,axis,indexing='ij'),axis=-1).reshape(-1,3)+root
  overlap=(ff['head'](q)<-.1)&(ff['ears'](q)<-.1);ids=np.flatnonzero((np.linalg.norm(skin['v']-root,axis=1)<8))
  row['ears'].append(dict(root=root.tolist(),local_overlap_samples=int(overlap.sum()),overlap_sample_volume=float(overlap.sum()*.6**3),saved_surface_vertices_near_root=len(ids)))
 mask=np.all(skin['c']==[43,40,34],axis=1);f=skin['f'];edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);edges=np.unique(edges,axis=0);inner=edges[mask[edges].all(1)];remap=np.full(len(mask),-1);remap[mask]=np.arange(mask.sum());graph=coo_matrix((np.ones(len(inner)),(remap[inner[:,0]],remap[inner[:,1]])),shape=(mask.sum(),mask.sum())).tocsr();nc,_=connected_components(graph,directed=False)
 row['nose']=dict(material_vertices=int(mask.sum()),material_components=int(nc),boundary_shared_edges=int((mask[edges[:,0]]!=mask[edges[:,1]]).sum()),part='same closed skin mesh')
 report['breeds'][b]=row;print(b,json.dumps(row),flush=True)
report['source_stable']=report['source_sha256']==sha(source);report['cache_stable']=report['cache_sha256']==sha(cache);report['image_stable']=report['image_sha256']==sha(image)
(HERE/'review-pass11-saved-mesh.json').write_text(json.dumps(report,indent=2),'utf-8')
print('COMPLETE',report['source_stable'],report['cache_stable'],report['image_stable'],flush=True)
