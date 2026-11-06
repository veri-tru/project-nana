"""Callable fresh-mesh control test; no execution until final audit invokes run()."""
import copy
import numpy as np

def run(m,models):
    b='golden';model=models[b];p=model['profile'];a=m.params(p);d=a['d'];W=a['W']
    bounds=[(d[5,0]-3,8),(-10,d[0,1]+5),(-W*1.55,W*1.55)]
    probes=[('crown_height','dorsal',0,1,'upper'),('forehead_height','dorsal',1,1,'upper'),('derived_maxilla_width','widths',2,None,'upper'),('nasal_base_x','dorsal',4,0,'upper'),('soft_nose_tip_x','dorsal',5,0,'cartilage')]
    result={}
    ff0,_=m.fields(p)
    for label,field,index,axis,part in probes:
        pp=copy.deepcopy(p)
        if axis is None:pp[field][index]+=.75
        else:pp[field][index][axis]+=.75
        ff,aa=m.fields(pp);v=model['parts'][part]['v'];base=ff0[part](v);changed=ff[part](v)-base
        vv,faces,nn=m.extract(ff[part],bounds)
        old=model['parts'][part]
        exact=vv.shape==old['v'].shape and faces.shape==old['f'].shape and np.array_equal(vv,old['v']) and np.array_equal(faces,old['f'])
        result[label]=dict(breed=b,delta=.75,part=part,surface_field_max_change=float(np.abs(changed).max()),surface_samples_changed_gt_001=int((np.abs(changed)>.001).sum()),fresh_mesh_vertices=len(vv),saved_mesh_vertices=len(v),fresh_mesh_exact=bool(exact),fixed_grid_bounds=bounds)
    return result
