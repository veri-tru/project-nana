"""Independent checks; saved candidate PNGs are never overwritten."""
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent

def main():
    spec=importlib.util.spec_from_file_location('cervical_independent_review',HERE/'preview.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    heads,evidence,rigs,profiles=m.build()
    results={'breeds':{},'images':{},'hashes':{}}
    for breed in m.BREEDS:
        rig=rigs[breed]
        profile=m.base.profile_for(rig,profiles[breed],breed)
        profile.update(structured_jaw=True,**{k:v for k,v in m.PARAMS[breed].items() if k.startswith('jaw_')})
        if breed=='maltipoo':profile['eye_radius']=(1.4,1.4)
        raw=m.model.head_features(rig,breed,profile)
        if breed=='maltipoo':raw=m.previous.curly_coat(raw,rig)
        mouth,d=m.base.mouth(raw,rig,profile,6*profile['mouth_style'][1])
        neck,info=m.cervical_skin(mouth,rig,breed)
        perturbed=copy.deepcopy(rig)
        perturbed['nodes']['neck.C2']['offset'][1]+=1
        # Hold C1, the head, and all facial nodes in their original world pose.
        perturbed['nodes']['neck.C1']['offset'][1]-=1
        shifted,_=m.cervical_skin(mouth,perturbed,breed)
        jaw_only=copy.deepcopy(rig)
        jaw_only['nodes']['face.jaw_axis']['offset'][0]+=1
        no_neck_change,_=m.cervical_skin(mouth,jaw_only,breed)
        v=neck[0][0]
        state_results={}
        for state,_ in m.base.STATES:
            parts=heads[breed][state]
            current=parts[0][0]
            neutral=heads[breed]['neutral'][0][0]
            # Upper head including neck is independent of jaw rotation.
            state_results[state]={
                'finite':all(np.isfinite(a).all() and np.isfinite(b).all() for a,b in parts),
                'neck_and_upper_head_error':float(np.abs(current-neutral).max()),
                'angular_seam_error':float(np.abs(current[:,0]-current[:,-1]).max()),
                'ears_equal_source':all(np.array_equal(parts[j+2][0],raw[j+1][0]*m.HEAD_SCALE) and np.array_equal(parts[j+2][1],raw[j+1][1]) for j in range(2))}
        hinges=np.asarray(d['hinge_axis'])
        endpoint=d['lower_rest'][-1,[0,-1]]
        hinge_error=min(np.abs(endpoint-hinges).max(),np.abs(endpoint-hinges[::-1]).max())
        pivot=np.asarray(d['pivot'])
        rest_dist=np.linalg.norm(d['lower_rest']-pivot,axis=-1)
        posed_dist=np.linalg.norm(d['lower_posed']-pivot,axis=-1)
        tongue=[]
        for lick in (False,True):
            a=(4 if lick else 6)*profile['mouth_style'][1]
            _,data=m.base.mouth(raw,rig,profile,a)
            (surface,_),ti=m.base.tongue(data,profiles[breed]['half_width'],lick)
            pts=surface[:61].reshape(-1,3)
            floor=np.interp(pts[:,0],data['floor'][:,0],data['floor'][:,1])
            roof=np.interp(pts[:,0],data['xs'],data['roof_y'])
            tongue.append({'lick':lick,'floor_clearance':float((pts[:,1]-floor).min()),
                'roof_clearance':float((roof-pts[:,1]).min()),
                'lip_contact_error':float(np.linalg.norm(surface[60,32]-np.asarray(ti['lip_floor_contact']))),
                'nose_contact_error':None if ti['contact'] is None else float(np.linalg.norm(np.asarray(ti['tip'])-ti['contact']))})
        p={k:np.asarray(q) for k,q in m.model.pose(rig).items()}
        perturbed_pose={k:np.asarray(q) for k,q in m.model.pose(perturbed).items()}
        results['breeds'][breed]={
            'states':state_results,'neck_start_x':info['start_x'],
            'neck_starts_behind_mouth':bool(info['start_x']>d['back']),
            'C2_perturbation_surface_change':float(np.abs(shifted[0][0]-v).max()),
            'C2_perturbation_head_pose_error':float(max(np.abs(p[k]-perturbed_pose[k]).max() for k in p if k.startswith('face.') or k=='body.head')),
            'jaw_perturbation_neck_error':float(np.abs(no_neck_change[0][0]-v).max()),
            'ramus_hinge_endpoint_error':float(hinge_error),
            'jaw_rigid_rotation_distance_error':float(np.abs(rest_dist-posed_dist).max()),
            'raw_x_min_step':float(np.diff(raw[0][0][:,0,0]).min()),
            'skin_x_min_step':float(np.diff(v[:,0,0]).min()),
            'tongue':tongue}
    for name,(title,rows) in m.BOARDS.items():
        im,scale=m.render(heads,rigs,rows,title,evidence)
        buf=io.BytesIO();im.save(buf,format='PNG')
        results['images'][name]={'bytes_match':buf.getvalue()==(HERE/name).read_bytes(),
            'size':list(im.size),'scale':float(scale),'sha256':hashlib.sha256((HERE/name).read_bytes()).hexdigest()}
    recipe=json.loads((HERE/'recipe.json').read_text(encoding='utf-8'))
    results['hashes']['inputs_match']=all(hashlib.sha256((HERE.parent/p).read_bytes()).hexdigest()==h for p,h in recipe['input_sha256'].items())
    results['hashes']['images_match']=all(hashlib.sha256((HERE/p).read_bytes()).hexdigest()==h for p,h in recipe['image_sha256'].items())
    (HERE/'review-checks.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(results,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
