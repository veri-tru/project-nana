"""Reviewer-owned measurements over the same rebuilt geometry used for byte checks."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import pickle
import numpy as np
from scipy.spatial import cKDTree

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('review_topology',HERE/'review_geometry.py')
topology_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(topology_module)


def equal_tree(a,b):
    if isinstance(a,np.ndarray):return isinstance(b,np.ndarray) and np.array_equal(a,b)
    if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(equal_tree(a[k],b[k]) for k in a)
    if isinstance(a,(list,tuple)):return isinstance(b,type(a)) and len(a)==len(b) and all(equal_tree(x,y) for x,y in zip(a,b))
    return a==b


def run(m,heads,evidence,rigs):
    with (HERE/'geometry.pkl').open('rb') as f:saved=pickle.load(f)
    with (HERE.parent/'head-neck-volume-v2/geometry.pkl').open('rb') as f:previous=pickle.load(f)
    oldrigs,oldraw=m.old.inputs()
    result={}
    for b in m.BREEDS:
        s=evidence[b]['sections'];jaw=evidence[b]['jaw'];v,f,n=evidence[b]['head']
        world={k:np.array(p) for k,p in m.model.pose(rigs[b]).items()}
        oldworld={k:np.array(p) for k,p in m.model.pose(oldrigs[b]).items()}
        rec={'topology':{},'states':{},'controls':{},'preservation':{}}
        rec['preservation']['previous_v2_all_states_exact']=equal_tree(heads[b],previous['heads'][b])
        rec['preservation']['previous_v2_rig_exact']=equal_tree(rigs[b],previous['rigs'][b])
        rec['preservation']['eye_radius_actual']=list(s['profile']['eye_radius'])
        rec['saved_heads_exactly_rebuilt']=equal_tree(heads[b],saved['heads'][b])
        rec['saved_rig_exactly_rebuilt']=equal_tree(rigs[b],saved['rigs'][b])
        rec['topology']['head']=topology_module.topology(v,f,n)
        rec['topology']['jaw']=topology_module.topology(jaw['v'],jaw['f'],jaw['n'])
        oldprofile=m.old.base.profile_for(oldrigs[b],oldraw[b],b)
        if b=='maltipoo':oldprofile['eye_radius']=(1.5,1.5)
        rec['preservation']['face_world_max_error']=float(max(np.max(np.abs(world[k]-oldworld[k])) for k in world if k in oldworld and (k.startswith('face.') or k=='body.head')))
        rec['preservation']['eye_radius_exact']=s['profile']['eye_radius']==oldprofile['eye_radius']
        if b!='maltipoo':
            oldfeatures=m.model.head_features(oldrigs[b],b,oldprofile)
            rec['preservation']['original_ears_exact']=equal_tree(s['features'][1:],oldfeatures[1:])
            rec['preservation']['original_ear_vertex_max_error']=float(max(np.abs(a[0]-z[0]).max() for a,z in zip(s['features'][1:],oldfeatures[1:])))
        else:rec['preservation']['original_ears_exact']='INTENTIONALLY_REBUILT; not an unchanged-ear claim'
        rec['preservation']['ears_fixed_all_states']=all(equal_tree(heads[b][state]['grids'][:2],s['features'][1:]) for state in m.STATES)
        rec['ear_roots']=[]
        for ev,ec in s['features'][1:]:
            root=ev[:5].reshape(-1,3);field=m.head_field(root,s,rigs[b],b)
            rec['ear_roots'].append(dict(root_field_min=float(field.min()),root_field_max=float(field.max()),embedded_root_samples=int((field<0).sum()),root_samples=len(field),angular_seam_error=float(np.abs(ev[:,0]-ev[:,-1]).max()),finite=bool(np.isfinite(ev).all()),max_x_width=float(np.ptp(ev[:,:,0],axis=1).max()),max_z_depth=float(np.ptp(ev[:,:,2],axis=1).max())))
        ov,oc=s['features'][0]
        centers=(ov[:-1,:-1]+ov[1:,:-1]+ov[:-1,1:]+ov[1:,1:])/4
        mask=(centers[:,:,0]<s['xs'][0]+4.4*m.model.NOSE_SCALE[b]) & (oc.max(axis=-1)<100)
        nasal=centers[mask];res=m.head_field(nasal,s,rigs[b],b);near,_=cKDTree(v).query(nasal)
        rec['nose']=dict(source_dark_faces=int(mask.sum()),source_dark_depth_max=float(nasal[:,0].max()-s['xs'][0]),field_min=float(res.min()),field_max=float(res.max()),absolute_field_p95=float(np.quantile(np.abs(res),.95)),nearest_vertex_p95=float(np.quantile(near,.95)),faces_in_rebuild=int((nasal[:,0]>s['xs'][0]+2.55).sum()) if b=='maltipoo' else 0)
        baseline=m.head_field(v,s,rigs[b],b)
        for key in ['head.occipital_joint','neck.C1','neck.C2','neck.lower']:
            rig=copy.deepcopy(rigs[b]);delta=np.array([0.,.75,0.])
            rig['nodes'][key]['offset']=(np.array(rig['nodes'][key]['offset'])+delta).tolist()
            for node in rig['nodes'].values():
                if node['parent']==key:node['offset']=(np.array(node['offset'])-delta).tolist()
            posed=m.model.pose(rig);change=m.head_field(v,s,rig,b)-baseline
            rec['controls'][key]=dict(fixed_head_error=float(max(np.max(np.abs(posed[k]-world[k])) for k in world if k.startswith('face.') or k=='body.head')),surface_field_max_change=float(np.abs(change).max()),vertices_changed_gt_01=int((np.abs(change)>.01).sum()))
        if b=='maltipoo':
            rec['facial_controls']={}
            for key in ['face.skull','face.maxilla','face.L_ear_root']:
                rig=copy.deepcopy(rigs[b]);delta=np.array([0.,.5,0.])
                rig['nodes'][key]['offset']=(np.array(rig['nodes'][key]['offset'])+delta).tolist()
                for node in rig['nodes'].values():
                    if node['parent']==key:node['offset']=(np.array(node['offset'])-delta).tolist()
                ss=m.sections(rig,oldraw[b],b)
                if key.endswith('ear_root'):
                    rec['facial_controls'][key]=dict(ear_max_change=float(np.abs(ss['features'][1][0]-s['features'][1][0]).max()),other_ear_exact=equal_tree(ss['features'][2],s['features'][2]))
                else:
                    shifted=m.head_field(v,ss,rig,b);deltafield=shifted-baseline
                    vv,ff,nn=m.extract(lambda q:m.head_field(q,ss,rig,b),[(ss['xs'][0]-1,19),(-13,20),(-15,15)])
                    rec['facial_controls'][key]=dict(surface_field_max_change=float(np.abs(deltafield).max()),vertices_changed_gt_01=int((np.abs(deltafield)>.01).sum()),rebuilt_vertices=len(vv),rebuilt_mesh_exact=equal_tree((vv,ff,nn),(v,f,n)))
        hinges=np.array([world['face.'+side+'_jaw_hinge']-world['body.head'] for side in ['L','R']])
        rec['tmj']=dict(head_field=m.head_field(hinges,s,rigs[b],b).tolist(),jaw_field=jaw['field'](hinges).tolist(),axis_xy_error=float(np.abs(hinges[:,:2]-jaw['hinge'][:2]).max()))
        corner=world['face.L_mouth_corner'][0]-world['body.head'][0]
        for state in m.STATES:
            mesh=heads[b][state];jv=mesh['tri'][1][0]
            angle=m.PARAMS[b]['angle']*(.5 if state=='mid' else .70 if state=='lick' else 1 if state in ['open','tongue'] else 0)
            rest=m.rotate(jv,jaw['hinge'],-angle)
            exposed=rest[:,0]<corner-2.5
            rd=m.head_field(jv[exposed],s,rigs[b],b)
            record=dict(head_vertices_fixed=np.array_equal(mesh['tri'][0][0],v),jaw_inverse_rigid_error=float(np.abs(rest-jaw['v']).max()),exposed_rostral_min_head_field=float(rd.min()),exposed_rostral_inside_gt_01=int((rd<-.1).sum()))
            if b=='maltipoo' and angle>0:
                liner=mesh['grids'][2][0]
                upper=liner[:,0];lower=liner[:,-1]
                recupper=m.head_field(upper,s,rigs[b],b)
                reclower=jaw['field'](m.rotate(lower,jaw['hinge'],-angle))
                record['oral_liner']=dict(finite=bool(np.isfinite(liner).all()),shape=list(liner.shape),upper_head_field_range=[float(recupper.min()),float(recupper.max())],lower_jaw_field_range=[float(reclower.min()),float(reclower.max())],lower_rotates_from_upper_error=float(np.abs(m.rotate(lower,jaw['hinge'],-angle)-upper).max()))
            if state in ['tongue','lick']:
                tv=mesh['grids'][-1][0]
                # Test vertices and actual quad centers to catch chord penetration.
                mids=(tv[:-1,:-1]+tv[1:,:-1]+tv[:-1,1:]+tv[1:,1:])/4
                pts=np.concatenate([tv.reshape(-1,3),mids.reshape(-1,3)])
                jd=jaw['field'](m.rotate(pts,jaw['hinge'],-angle));hd=m.head_field(pts,s,rigs[b],b)
                lower=tv[:,24]  # theta=pi, lower side before contact projection
                contact=jaw['field'](m.rotate(lower[7:45],jaw['hinge'],-angle))
                tip=tv[-1].mean(0)
                record.update(tongue_jaw_min=float(jd.min()),tongue_head_min=float(hd.min()),tongue_jaw_penetration_gt_01=int((jd<-.1).sum()),tongue_head_penetration_gt_01=int((hd<-.1).sum()),tongue_support_lower_clearance_range=[float(contact.min()),float(contact.max())],tongue_max_width=float(np.ptp(tv[:,:,2],axis=1).max()),tongue_max_vertical_thickness=float(np.ptp(tv[:,:,1],axis=1).max()),tip_head_field=float(m.head_field(tip[None],s,rigs[b],b)[0]),tongue_support_count_within_005=int((np.abs(contact)<.05).sum()),tongue_support_count_total=len(contact),angular_seam_error=float(np.abs(tv[:,0]-tv[:,-1]).max()),finite=bool(np.isfinite(tv).all()))
            rec['states'][state]=record
        result[b]=rec
    report=dict(source_sha256=hashlib.sha256((HERE/'preview.py').read_bytes()).hexdigest(),geometry_sha256=hashlib.sha256((HERE/'geometry.pkl').read_bytes()).hexdigest(),breeds=result)
    (HERE/'review-final-checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return dict(report='review-final-checks.json',saved_geometry_exact=all(r['saved_heads_exactly_rebuilt'] and r['saved_rig_exactly_rebuilt'] for r in result.values()))
