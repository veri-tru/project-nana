"""Independent structural measurements on saved actual geometry; no render writes."""
import hashlib
import importlib.util
import json
import pickle
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

HERE = Path(__file__).resolve().parent


def topology(v, f, n):
    edges = np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), axis=1)
    edges, count = np.unique(edges, axis=0, return_counts=True)
    cross = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    area = np.linalg.norm(cross, axis=1) / 2
    adjacency = coo_matrix((np.ones(len(edges)), (edges[:, 0], edges[:, 1])), shape=(len(v), len(v)))
    comps, _ = connected_components(adjacency, directed=False)
    return dict(vertices=len(v), faces=len(f), components=int(comps), boundary_edges=int((count == 1).sum()), nonmanifold_edges=int((count > 2).sum()), euler=int(len(v)-len(edges)+len(f)), min_area=float(area.min()), zero_area=int((area <= 0).sum()), area_below_1e10=int((area < 1e-10).sum()), finite=bool(np.isfinite(v).all() and np.isfinite(n).all()), normal_length_range=[float(np.linalg.norm(n,axis=1).min()),float(np.linalg.norm(n,axis=1).max())], normal_winding_agreement=float(np.mean(np.sum(cross*n[f].mean(1),axis=1)>0)))


def main():
    source = HERE/'preview.py'
    spec = importlib.util.spec_from_file_location('geometry_review_candidate',source)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    with (HERE/'geometry.pkl').open('rb') as f:data=pickle.load(f)
    rigs,raw=m.inputs();result={}
    for b in m.BREEDS:
        s=m.sections(rigs[b],raw[b],b);jaw=m.jaw_mesh(s,rigs[b],b)
        rec={'topology':{},'states':{}}
        for i,name in enumerate(['head','jaw']):
            v,f,n,c=data['heads'][b]['neutral']['tri'][i]
            rec['topology'][name]=topology(v,f,n)
        for state in ['neutral','mid','open','tongue','lick']:
            mesh=data['heads'][b][state];jv=mesh['tri'][1][0]
            angle=m.PARAMS[b]['angle']*(.5 if state=='mid' else .70 if state=='lick' else 1 if state in ['open','tongue'] else 0)
            expected=m.rotate(jaw['v'],jaw['hinge'],angle)
            sr={'jaw_pose_max_error':float(np.max(np.abs(jv-expected))) if jv.shape==expected.shape else 'geometry/source shape mismatch'}
            rest=m.rotate(jv,jaw['hinge'],-angle)
            anterior=rest[:,0] < jaw['hinge'][0]-4.5
            hd=m.head_field(jv[anterior],s,rigs[b],b)
            sr['anterior_jaw_head_field_min']=float(hd.min())
            sr['anterior_jaw_inside_head_vertices']=int((hd<-.15).sum())
            if state in ['tongue','lick']:
                tongue=mesh['grids'][-1][0]
                pts=tongue.reshape(-1,3)
                tj=jaw['field'](m.rotate(pts,jaw['hinge'],-angle))
                th=m.head_field(pts,s,rigs[b],b)
                tip=tongue[-1].mean(0)
                sr.update(tongue_jaw_field_min=float(tj.min()),tongue_head_field_min=float(th.min()),tongue_vertices_inside_jaw=int((tj<-.10).sum()),tongue_vertices_inside_head=int((th<-.10).sum()),tip_head_field=float(m.head_field(tip[None],s,rigs[b],b)[0]))
            rec['states'][state]=sr
        result[b]=rec
    report=dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), geometry_sha256=hashlib.sha256((HERE/'geometry.pkl').read_bytes()).hexdigest(),development_diagnostic=True,breeds=result)
    (HERE/'review-geometry-development.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
