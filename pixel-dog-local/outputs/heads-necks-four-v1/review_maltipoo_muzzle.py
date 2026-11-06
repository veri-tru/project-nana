"""Independent scoped review; never overwrites the submitted render files."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

def same_mesh(a,b):
    return len(a)==len(b) and all(np.array_equal(v,w) and np.array_equal(c,d) for (v,c),(w,d) in zip(a,b))

def main():
    m=load('maltipoo_review_candidate',HERE/'preview.py')
    helper=load('maltipoo_review_helpers',HERE/'review_checks.py')
    final=m.model
    previous=load('maltipoo_review_previous',HERE/'head_surface-before-maltipoo-muzzle.py')
    m.model=previous;m.base.model=previous
    old,_,_,_=m.build()
    m.model=final;m.base.model=final
    heads,evidence,rigs,profiles=m.build()
    out={'isolation':{},'maltipoo':{},'images':{},'hashes':{}}
    for breed in m.BREEDS:
        out['isolation'][breed]={state:same_mesh(old[breed][state],heads[breed][state]) for state,_ in m.base.STATES}
    rig=rigs['maltipoo'];profile=m.base.profile_for(rig,profiles['maltipoo'],'maltipoo');profile['eye_radius']=(1.4,1.4)
    before=previous.head_features(rig,'maltipoo',profile)
    after=final.head_features(rig,'maltipoo',profile)
    a,b=before[0][0],after[0][0]
    delta=b-a
    changed=np.max(np.abs(delta),axis=(1,2))>1e-10
    out['maltipoo']['changed_original_x_range']=[float(a[changed,0,0].min()),float(a[changed,0,0].max())]
    out['maltipoo']['minimum_x_row_step']=float(np.diff(b[:,0,0]).min())
    out['maltipoo']['raw_ears_exact']=same_mesh(before[1:],after[1:])
    out['maltipoo']['head_colors_exact']=bool(np.array_equal(before[0][1],after[0][1]))
    # Leather is dark pigment before the eye; restrict to the front to exclude eyes.
    c=before[0][1]
    black=(c.max(axis=-1)<65)&(a[:-1,:-1,0]<a[0,0,0]+3.)
    vertexmask=np.zeros(a.shape[:2],bool)
    for i,j in ((0,0),(0,1),(1,0),(1,1)):
        vertexmask[i:i+black.shape[0],j:j+black.shape[1]]|=black
    shifts=delta[vertexmask]
    out['maltipoo']['nose_translation']=shifts.mean(axis=0).tolist()
    out['maltipoo']['nose_congruence_error']=float(np.abs(shifts-shifts.mean(axis=0)).max())
    w,_=helper.neck_weights(m,b,rig);active=w>0
    neck=[]
    for state,_ in m.base.STATES:
        v,c=heads['maltipoo'][state][0]
        ear_start=2 if state in ('open','tongue','lick') else 1
        neck.append({'state':state,'finite':bool(all(np.isfinite(vv).all() and np.isfinite(cc).all() for vv,cc in heads['maltipoo'][state])),
            'neck_fixed_error':float(np.abs(v[active]-heads['maltipoo']['neutral'][0][0][active]).max()),
            'neck_before_error':float(np.abs(v[active]-old['maltipoo'][state][0][0][active]).max()),
            'seam_error':float(np.abs(v[:,0]-v[:,-1]).max()),
            'cap_error':float(np.abs(v[-1]-v[-1,::-1]).max()),
            'ears_exact':same_mesh(heads['maltipoo'][state][ear_start:ear_start+2],old['maltipoo'][state][ear_start:ear_start+2])})
    out['maltipoo']['states']=neck
    oral=[]
    for state,nominal in [('tongue',6.),('lick',4.)]:
        mesh=m.curly_coat(after,rig)
        _,data=m.base.mouth(mesh,rig,profile,nominal*profile['mouth_style'][1])
        (surface,_),info=m.base.tongue(data,profiles['maltipoo']['half_width'],state=='lick')
        p=surface[:61].reshape(-1,3)
        floor=np.interp(p[:,0],data['floor'][:,0],data['floor'][:,1]);roof=np.interp(p[:,0],data['xs'],data['roof_y'])
        oral.append({'state':state,'floor_clearance':float((p[:,1]-floor).min()),'roof_clearance':float((roof-p[:,1]).min()),
            'lip_contact_error':float(np.linalg.norm(surface[60,32]-info['lip_floor_contact'])),
            'tip_contact_error':None if info['contact'] is None else float(np.linalg.norm(np.asarray(info['tip'])-info['contact']))})
    out['maltipoo']['oral']=oral
    boards={'heads-necks.png':('머리와 짧은 목 · 네 품종',[('사선','neutral',38),('측면','neutral',90),('정면','neutral',0)]),
            'mouth-neck-check.png':('턱과 목 · 표정 연결 확인',[('입 벌림','open',38),('혀 내밀기','tongue',38),('코 핥기','lick',38)])}
    for name,(title,rows) in boards.items():
        img,scale=m.render(heads,rows,title);buf=io.BytesIO();img.save(buf,format='PNG')
        out['images'][name]={'bytes_match':buf.getvalue()==(HERE/name).read_bytes(),'size':list(img.size),'scale':scale,
            'sha256':hashlib.sha256((HERE/name).read_bytes()).hexdigest()}
    recipe=json.loads((HERE/'recipe.json').read_text(encoding='utf-8'))
    out['hashes']['recipe_inputs_match']=all(hashlib.sha256((HERE.parent/f).read_bytes()).hexdigest()==h for f,h in recipe['input_sha256'].items())
    out['hashes']['recipe_images_match']=all(hashlib.sha256((HERE/f).read_bytes()).hexdigest()==h for f,h in recipe['image_sha256'].items())
    (HERE/'review-maltipoo-muzzle-checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
