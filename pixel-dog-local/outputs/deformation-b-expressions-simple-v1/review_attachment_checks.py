"""Independent, non-mutating verification of the jaw attachment candidate."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def same(a,b):
    return len(a)==len(b) and all(np.array_equal(av,bv) and np.array_equal(ac,bc) for (av,ac),(bv,bc) in zip(a,b))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def verify_image(im,name):
    b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()==(HERE/name).read_bytes()

def main():
    m=load('attachment_final','preview.py');old=load('attachment_before','preview-before-jaw-attachment.py')
    heads,evidence=m.build();before,_=old.build()
    result={'other_breeds':{b:{s:same(heads[b][s],before[b][s]) for s,_ in m.STATES} for b in ('golden','dachshund')}}
    rigs,profiles=m.model.load('B.json')['breeds'],m.model.load('profiles.json')
    rig=rigs['whippet'];profile=m.profile_for(rig,profiles['whippet'],'whippet');base=m.model.head_features(rig,'whippet',profile)
    pose={k:np.asarray(v)-np.asarray(m.model.pose(rig)['body.head']) for k,v in m.model.pose(rig).items()}
    shell=base[0][0];protected=np.zeros(shell.shape[:2],dtype=bool)
    for key in ('face.L_eye','face.R_eye'):
        e=pose[key];protected|=(abs(shell[:,:,0]-e[0])<1.9)&(abs(shell[:,:,1]-e[1])<1.9)&(shell[:,:,2]*e[2]>0)
    nose_mask=(base[0][1][:,:,0]<70)&(np.arange(base[0][1].shape[0])[:,None]<150)
    for di,dj in ((0,0),(1,0),(0,1),(1,1)):
        protected[di:di+nose_mask.shape[0],dj:dj+nose_mask.shape[1]]|=nose_mask
    state_checks={}
    for state,_ in m.STATES:
        new,prev=heads['whippet'][state],before['whippet'][state]
        ei=2 if state in ('open','tongue','lick') else 1
        state_checks[state]={
            'ears_exact':all(np.array_equal(new[ei+i][j],prev[ei+i][j]) for i in (0,1) for j in (0,1)),
            'protected_vertex_error':float(abs(new[0][0][protected]-prev[0][0][protected]).max()),
            'protected_material_note':'closed state colors are exact; open palate may change outside protected exterior',
            'closed_material_exact': bool(np.array_equal(new[0][1],prev[0][1])) if ei==1 else None}
    result['whippet_states']=state_checks
    zero,d0=m.mouth(base,rig,profile,0.)
    result['source_pivot']=d0['source_pivot'].tolist();result['runtime_pivot']=d0['pivot'].tolist()
    result['hinge_endpoint_error']=float(abs(d0['lower_rest'][-1,[0,-1]]-d0['hinge_axis']).max())
    result['ramus_after_hinge_max_x']=float(d0['lower_rest'][:,:,0].max()-d0['pivot'][0])
    result['skull_floor']={}
    closed=m.trim_whippet_neck(base,rig,profile)
    for x in (-12,-10,-8,-6,-4,0,3):
        i=int(np.argmin(abs(d0['xs']-x)))
        result['skull_floor'][str(x)]={'old':float(base[0][0][i,:,1].min()),'new_open_upper':float(zero[0][0][i,:,1].min()),'new_closed':float(closed[0][0][i,:,1].min())}
    result['rigid']=[]
    for deg in (2.32,3.48,4.64):
        mesh,d=m.mouth(base,rig,profile,deg)
        inverse=m.rotate_jaw(d['lower_posed'],d['pivot'],np.full(len(d['lower_posed']),-np.deg2rad(deg)))
        hinge=m.rotate_jaw(d['hinge_axis'][None],d['pivot'],np.array([np.deg2rad(deg)]))
        result['rigid'].append({'angle':deg,'inverse_error':float(abs(inverse-d['lower_rest']).max()),
             'axis_motion':float(abs(hinge[0]-d['hinge_axis']).max()),'rest_exact':np.array_equal(d0['lower_rest'],d['lower_rest']),
             'upper_exact':np.array_equal(zero[0][0],mesh[0][0])})
    result['tongue']=[]
    for lick,angle in ((False,3.48),(True,2.32)):
        _,d=m.mouth(base,rig,profile,angle);(v,_),info=m.tongue(d,profiles['whippet']['half_width'],lick)
        pts=v[:61].reshape(-1,3);floor=np.interp(pts[:,0],d['floor'][:,0],d['floor'][:,1]);roof=np.interp(pts[:,0],d['xs'],d['roof_y'])
        width=np.interp(pts[:,0],d['lower_posed'][:,0,0],abs(d['lower_posed'][:,:,2]).max(axis=1))
        lip=np.asarray(info['lip_center'])-[0,info['lip_half_thickness'],0]
        result['tongue'].append({'lick':lick,'floor_clearance':float((pts[:,1]-floor).min()),'roof_clearance':float((roof-pts[:,1]).min()),
            'side_clearance':float((width-abs(pts[:,2])).min()),'lip_contact_error':float(np.linalg.norm(lip-info['lip_floor_contact'])),
            'nose_contact_error':None if not lick else float(np.linalg.norm(np.asarray(info['tip'])-info['contact']))})
    result['renders']={}
    for name,angle in (('expressions.png',38),('expressions-side.png',90)):
        result['renders'][name]=verify_image(m.render(heads,angle)[0],name)
    stages={}
    for breed in m.model.BREEDS:
        rr=rigs[breed];pp=m.profile_for(rr,profiles[breed],breed);bb=m.model.head_features(rr,breed,pp);stages[breed]={}
        for degrees in (4,6,8):
            features,_=m.mouth(bb,rr,pp,degrees*pp['mouth_style'][1]);stages[breed][degrees]=[(v*m.HEAD_SCALE,c) for v,c in features]
    options=m.render(stages,38,[(4,'A · 작게'),(6,'B · 중간'),(8,'C · 조금 더')],'입 단순화 · 같은 형태, 벌림만 비교')[0]
    result['renders']['mouth-options.png']=verify_image(options,'mouth-options.png')
    comparison=load('attachment_comparison','whippet_attachment_comparison.py')
    result['renders']['whippet-attachment-before-after.png']=verify_image(comparison.render(),'whippet-attachment-before-after.png')
    recipe=json.loads((HERE/'recipe.json').read_text(encoding='utf-8'))
    check={k:digest(HERE.parent/k)==v for k,v in recipe['input_sha256'].items()}
    check.update({k:digest(HERE/k)==v for k,v in recipe['image_sha256'].items()})
    recipe2=json.loads((HERE/'whippet-attachment-recipe.json').read_text(encoding='utf-8'))
    check.update({k:digest(HERE/k)==v for k,v in recipe2['sha256'].items()})
    result['hash_checks']=check
    result['final_hashes']={k:digest(HERE/k) for k in ['preview.py',*result['renders']]}
    (HERE/'review-attachment-checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
