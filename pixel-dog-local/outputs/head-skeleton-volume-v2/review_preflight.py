"""Reviewer-owned saved-mesh topology and actual upper-field jaw-clearance diagnostics."""
import hashlib,importlib.util,json,pickle,sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('independent_volume',HERE/'build.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
source=sha(HERE/'build.py');data=pickle.loads((HERE/'geometry.pkl').read_bytes())
def topo(part):
    v,f,n=part['v'],part['f'],part['n'];edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1);edges,counts=np.unique(edges,axis=0,return_counts=True)
    graph=coo_matrix((np.ones(len(edges)),(edges[:,0],edges[:,1])),shape=(len(v),len(v)))
    count,labels=connected_components(graph,directed=False)
    cross=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]])
    return dict(vertices=len(v),faces=len(f),components=count,component_vertex_sizes=np.bincount(labels).tolist(),boundary_edges=int((counts==1).sum()),nonmanifold_edges=int((counts>2).sum()),euler=int(len(v)-len(edges)+len(f)),zero_area=int((np.linalg.norm(cross,axis=1)<=0).sum()),finite=bool(np.isfinite(v).all() and np.isfinite(n).all()))
results={}
for b,model in data.items():
    p=model['profile'];ff,a=m.fields(p);hinge=a['hinge'];W=a['W'];v=model['parts']['jaw']['v'];f=model['parts']['jaw']['f']
    # Sample both vertices and actual triangle centers.
    samples=np.concatenate([v,v[f].mean(1)])
    hinges=np.array([hinge+[0,0,s*W*.8] for s in [-1,1]])
    exclusion_radius=a.get('condyle_radius',2.1)+1.4
    legitimate_tmj=np.min(np.linalg.norm(samples[:,None]-hinges[None],axis=-1),axis=1)<exclusion_radius
    rec={'topology':{k:topo(part) for k,part in model['parts'].items()},'clearance':{},'voids':{},'own_surface_field_residual':{}}
    for partname,part in model['parts'].items():
        own=ff[partname](part['v']);rec['own_surface_field_residual'][partname]=dict(min=float(own.min()),max=float(own.max()),absolute_p95=float(np.quantile(np.abs(own),.95)),absolute_max=float(np.abs(own).max()))
    cv=model['parts']['cartilage']['v'];cc=ff['upper'](cv)
    rec['cartilage_upper_attachment']=dict(min_upper_field=float(cc.min()),samples_inside_upper=int((cc<-.05).sum()),samples_near_upper=int((np.abs(cc)<.2).sum()))
    for angle in [0,5,10,15,20]:
        posed=m.rotate(samples,hinge,angle);d=ff['upper'](posed);mask=~legitimate_tmj;bad=(d<-.35)&mask
        worst=np.flatnonzero(mask)[np.argsort(d[mask])[:8]]
        rec['clearance'][str(angle)]=dict(excluded_tmj_samples=int(legitimate_tmj.sum()),exclusion_radius=exclusion_radius,min_outside_tmj=float(d[mask].min()),min_in_tmj_band=float(d[legitimate_tmj].min()),tmj_band_inside_gt_01=int((d[legitimate_tmj]<-.1).sum()),penetrating_gt_035=int(bad.sum()),penetrating_gt_01=int(((d<-.1)&mask).sum()),collision_bbox=[posed[bad].min(0).tolist(),posed[bad].max(0).tolist()] if bad.any() else None,worst=[{'point':posed[i].tolist(),'upper_field':float(d[i])} for i in worst])
    dd=a['d'];xm=(dd[4,0]+dd[3,0])/2;roof=(dd[4,1]+dd[3,1])/2
    probes={'nasal_lumen':[xm,(roof+3.5)/2,0.],'oral_midline':[xm,1.,0.],'left_temporal':[hinge[0]-6,14.,W*.95],'right_temporal':[hinge[0]-6,14.,-W*.95]}
    for name,q in probes.items():rec['voids'][name]=dict(point=q,upper_field=float(ff['upper'](np.array(q)[None])[0]),jaw_field=float(ff['jaw'](np.array(q)[None])[0]))
    results[b]=rec
baseline=json.loads((HERE.parent/'head-skeleton-v1/profiles.json').read_text('utf-8'));profiles=json.loads((HERE/'profiles.json').read_text('utf-8'))
report=dict(development_diagnostic=True,source_sha256=source,source_unchanged_during_run=source==sha(HERE/'build.py'),geometry_sha256=sha(HERE/'geometry.pkl'),shortened_profiles_exact=profiles==baseline,saved_profiles_exact=all(data[b]['profile']==profiles[b] for b in profiles),breeds=results)
(HERE/'review-preflight.json').write_text(json.dumps(report,indent=2)+'\n','utf-8')
print(json.dumps({'profiles_exact':report['shortened_profiles_exact'],'source_stable':report['source_unchanged_during_run'],'breeds':{b:{'components':{k:v['components'] for k,v in r['topology'].items()},'collision_counts':{k:v['penetrating_gt_035'] for k,v in r['clearance'].items()},'worst_depth':{k:v['min_outside_tmj'] for k,v in r['clearance'].items()}} for b,r in results.items()}},indent=2))
