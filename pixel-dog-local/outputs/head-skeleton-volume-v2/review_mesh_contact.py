"""Actual triangle closest-surface diagnostics for field-flagged jaw samples."""
import importlib.util,json,pickle,sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('mesh_contact_volume',HERE/'build.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
models=pickle.loads((HERE/'geometry.pkl').read_bytes())
def nearest(points,part):
    tri=part['v'][part['f']];cent=tri.mean(1);radii=np.linalg.norm(tri-cent[:,None],axis=2).max(1);tree=cKDTree(cent)
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
report={}
for b,model in models.items():
    ff,a=m.fields(model['profile']);jaw=model['parts']['jaw'];v=np.concatenate([jaw['v'],jaw['v'][jaw['f']].mean(1)]);h=a['hinge'];hs=np.array([h+[0,0,s*a['W']*.8] for s in [-1,1]])
    allowed=np.min(np.linalg.norm(v[:,None]-hs,axis=2),axis=1)>=a['condyle_radius']+1.4
    rec={}
    for angle in [0,5,10,15,20]:
        posed=m.rotate(v,h,angle);field=ff['upper'](posed);residual=float(np.abs(ff['upper'](model['parts']['upper']['v'])).max());ix=np.flatnonzero(field<residual+.2);samples=posed[ix]
        if len(samples):
            sd,q,cert=nearest(samples,model['parts']['upper']);mask=allowed[ix]
            def summarize(mask):
                if not mask.any():return dict(samples=0)
                ii=np.flatnonzero(mask);i=ii[np.argmin(sd[mask])]
                return dict(samples=int(mask.sum()),minimum_signed_mesh_distance=float(sd[mask].min()),inside_gt_001=int((sd[mask]<-.01).sum()),inside_gt_01=int((sd[mask]<-.1).sum()),inside_gt_035=int((sd[mask]<-.35).sum()),nearest_search_certified=bool(cert[mask].all()),worst_sample=samples[i].tolist(),nearest_upper_point=q[i].tolist())
            rec[str(angle)]=summarize(mask);rec[str(angle)]['tmj_band']=summarize(~mask);rec[str(angle)]['broadphase_field_threshold']=residual+.2
        else:rec[str(angle)]={'samples':0}
    report[b]=rec
(HERE/'review-mesh-contact.json').write_text(json.dumps(report,indent=2)+'\n','utf-8');print(json.dumps(report,indent=2))
