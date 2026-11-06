"""Development diagnosis of nasal scope, fixed-head controls and oral overlaps."""
import copy
import hashlib
import importlib.util
import json
import pickle
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

HERE=Path(__file__).resolve().parent


def main():
    spec=importlib.util.spec_from_file_location('scope_candidate',HERE/'preview.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    with (HERE/'geometry.pkl').open('rb') as f:data=pickle.load(f)
    rigs,raw=m.inputs();result={}
    for b in m.BREEDS:
        s=m.sections(rigs[b],raw[b],b);world={k:np.array(v) for k,v in m.model.pose(rigs[b]).items()}
        ov,oc=s['features'][0];centers=(ov[:-1,:-1]+ov[1:,:-1]+ov[:-1,1:]+ov[1:,1:])/4
        nose=(centers[:,:,0]<s['xs'][0]+4.4*m.model.NOSE_SCALE[b]) & (oc.max(axis=-1)<100)
        points=centers[nose]
        hf=m.head_field(points,s,rigs[b],b)
        v=data['heads'][b]['neutral']['tri'][0][0]
        dist,_=cKDTree(v).query(points)
        rec={'nose':dict(source_dark_faces=int(nose.sum()),source_dark_x_range=[float(points[:,0].min()),float(points[:,0].max())],source_dark_depth_range=[float(points[:,0].min()-s['xs'][0]),float(points[:,0].max()-s['xs'][0])],current_field_range=[float(hf.min()),float(hf.max())],absolute_field_p95=float(np.quantile(np.abs(hf),.95)),nearest_vertex_distance_p95=float(np.quantile(dist,.95)),source_dark_faces_in_rebuilt_blend=int(np.sum(points[:,0]>s['xs'][0]+2.55)) if b=='maltipoo' else 0),'controls':{},'mouth':{}}
        baseline=m.head_field(v,s,rigs[b],b)
        for key in ['head.occipital_joint','neck.C1','neck.C2','neck.lower']:
            rig=copy.deepcopy(rigs[b]);delta=np.array([0.,.75,0.])
            rig['nodes'][key]['offset']=(np.array(rig['nodes'][key]['offset'])+delta).tolist()
            for name,node in rig['nodes'].items():
                if node['parent']==key:node['offset']=(np.array(node['offset'])-delta).tolist()
            posed=m.model.pose(rig)
            change=m.head_field(v,s,rig,b)-baseline
            rec['controls'][key]=dict(fixed_head_world_error=float(max(np.max(np.abs(posed[k]-world[k])) for k in world if k.startswith('face.') or k=='body.head')),surface_field_max_change=float(np.max(np.abs(change))),surface_vertices_changed_more_than_01=int((np.abs(change)>.01).sum()))
        corner=world['face.L_mouth_corner'][0]-world['body.head'][0]
        hinge=world['face.jaw_axis']-world['body.head']
        for state in ['neutral','mid','open']:
            jv=data['heads'][b][state]['tri'][1][0]
            angle=m.PARAMS[b]['angle']*(.5 if state=='mid' else 1 if state=='open' else 0)
            rest=m.rotate(jv,hinge,-angle)
            oral=rest[:,0]<corner-2.5
            dd=m.head_field(jv[oral],s,rigs[b],b)
            rec['mouth'][state]=dict(exposed_rostral_x_max=float(corner-2.5),min_field=float(dd.min()),vertices_below_minus_01=int((dd<-.1).sum()))
        result[b]=rec
    report=dict(source_sha256=hashlib.sha256((HERE/'preview.py').read_bytes()).hexdigest(),geometry_sha256=hashlib.sha256((HERE/'geometry.pkl').read_bytes()).hexdigest(),breeds=result)
    (HERE/'review-scope-development.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()

