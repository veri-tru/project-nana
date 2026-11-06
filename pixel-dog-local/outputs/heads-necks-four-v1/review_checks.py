"""Independent checks; render in memory and never overwrite submitted PNGs."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj)
    return obj

def neck_weights(m,raw,rig):
    xs=raw[:,0,0]
    p={k:np.asarray(v) for k,v in m.model.pose(rig).items()}
    start=(p['face.jaw_axis']-p['body.head'])[0]+.8
    transition=min(5.,.55*(xs[-1]-start))
    theta=np.linspace(0,2*np.pi,raw.shape[1])
    t=np.clip((theta-np.pi/2)/np.pi,0,1)
    down=np.sin(np.pi*t)
    down[(theta<np.pi/2)|(theta>3*np.pi/2)]=0
    w=m.model.smoothstep((xs-start)/transition)[:,None]*m.model.smoothstep(down/.60)[None,:]
    return w,start

def main():
    m=load('four_candidate_review',HERE/'preview.py')
    old=load('three_before_review',m.SOURCE/'preview.py')
    heads,evidence,rigs,profiles=m.build()
    prior,_=old.build()
    result={'breeds':m.BREEDS,'geometry':{},'tongues':{},'images':{},'hashes':{},'nose_scaling':{}}
    for breed in m.BREEDS:
        rig=rigs[breed]
        profile=m.base.profile_for(rig,profiles[breed],breed)
        if breed=='maltipoo': profile['eye_radius']=(1.4,1.4)
        raw=m.model.head_features(rig,breed,profile)
        scale=m.model.NOSE_SCALE[breed]
        m.model.NOSE_SCALE[breed]=1.
        unscaled=m.model.head_features(rig,breed,profile)
        m.model.NOSE_SCALE[breed]=scale
        u=unscaled[0][0]; depth=u[:,0,0]-u[0,0,0]
        anchor=np.array([u[0,0,0],u[0,0,1],0.])
        full=depth<=4.4; far=depth>=7.2
        expected=anchor+(u[full]-anchor)*scale
        result['nose_scaling'][breed]={'scale':scale,
            'uniform_nose_error':float(np.abs(raw[0][0][full]-expected).max()),
            'outside_blend_error':float(np.abs(raw[0][0][far]-u[far]).max()),
            'ear_geometry_exact':all(np.array_equal(raw[j][0],unscaled[j][0]) for j in (1,2)),
            'materials_exact':all(np.array_equal(a[1],b[1]) for a,b in zip(raw,unscaled)),
            'longitudinal_rows_ordered':bool(np.all(np.diff(raw[0][0][:,0,0])>0))}
        w,start=neck_weights(m,raw[0][0],rig)
        active=w>0
        untouched=(~active)&far[:,None];untouched[-1]=False
        fw=(w[:-1,:-1]+w[1:,1:])/2
        neutral=heads[breed]['neutral'][0][0]
        checks=[]
        for state,_ in m.base.STATES:
            v,c=heads[breed][state][0]
            entry={'state':state,'finite':bool(all(np.isfinite(vv).all() and np.isfinite(cc).all() for vv,cc in heads[breed][state])),
                'angular_seam_error':float(np.abs(v[:,-1]-v[:,0]).max()),
                'rear_cap_pair_error':float(np.abs(v[-1]-v[-1,::-1]).max()),
                'rear_cap_z_error':float(np.abs(v[-1,:,2]).max()),
                'neck_stationary_error':float(np.abs(v[active]-neutral[active]).max()),
                'neck_material_stationary_error':float(np.abs(c[fw>0]-heads[breed]['neutral'][0][1][fw>0]).max())}
            if breed in prior:
                before=prior[breed][state]
                entry['outside_neck_and_nose_geometry_error']=float(np.abs(v[untouched]-before[0][0][untouched]).max())
                material_untouched=(fw==0)&(far[:-1]&far[1:])[:,None]
                entry['outside_neck_and_nose_material_error']=float(np.abs(c[material_untouched]-before[0][1][material_untouched]).max())
                ear_start=2 if state in ('open','tongue','lick') else 1
                entry['ears_exact']=all(
                    np.array_equal(a[0],b[0]) and np.array_equal(a[1],b[1])
                    for a,b in zip(before[ear_start:ear_start+2],heads[breed][state][ear_start:ear_start+2]))
            checks.append(entry)
        result['geometry'][breed]={'neck_start_x':float(start),'neck_vertex_count':int(active.sum()),
            'minimum_head_surface_y':float(neutral[:,:,1].min()/m.base.HEAD_SCALE),
            'reference_head_min_y':float(raw[0][0][:,:,1].min()),'states':checks}
        if breed=='maltipoo':
            curls=m.curly_coat(raw,rig)
            eye_r=profile['eye_radius']
            result['maltipoo']={'eye_radii':list(eye_r),'curly_head_x_error':float(np.abs(curls[0][0][:,:,0]-raw[0][0][:,:,0]).max()),
                'ear_attachment_max_error':float(max(np.abs(curls[j][0][:24]-raw[j][0][:24]).max() for j in (1,2))),
                'ear_attachment_within_1e_12':all(np.allclose(curls[j][0][:24],raw[j][0][:24],rtol=0,atol=1e-12) for j in (1,2))}
        pre_mouth=m.curly_coat(raw,rig) if breed=='maltipoo' else raw
        tc=[]
        for state,nominal in [('tongue',6.),('lick',4.)]:
            degrees=nominal*profile['mouth_style'][1]
            mouth,d=m.base.mouth(pre_mouth,rig,profile,degrees)
            (surface,_),info=m.base.tongue(d,profiles[breed]['half_width'],state=='lick')
            pts=surface[:61].reshape(-1,3)
            floor=np.interp(pts[:,0],d['floor'][:,0],d['floor'][:,1])
            ceiling=np.interp(pts[:,0],d['xs'],d['roof_y'])
            surface_bottom=surface[60,32]
            expected=np.asarray(info['lip_floor_contact'])
            tc.append({'state':state,'floor_clearance':float(np.min(pts[:,1]-floor)),
                'roof_clearance':float(np.min(ceiling-pts[:,1])),
                'lip_contact_error':float(np.linalg.norm(surface_bottom-expected)),
                'tip_contact_error':None if info['contact'] is None else float(np.linalg.norm(np.asarray(info['tip'])-info['contact'])),
                'neck_begins_behind_oral_corner':bool(start>d['back']),
                'oral_corner_to_neck_margin':float(start-d['back'])})
        result['tongues'][breed]=tc
    result['shared_nose']={key:float(getattr(m.model,key)) for key in
        ['NOSE_WIDTH','NOSE_HEIGHT','NOSE_FRONT_ROUND','NOSE_HEIGHT_ROUND','NOSE_TOP_DEPTH']}
    result['shared_nose']['same_as_retained_generator']=all(getattr(m.model,k)==getattr(old.model,k) for k in
        ['NOSE_WIDTH','NOSE_HEIGHT','NOSE_FRONT_ROUND','NOSE_HEIGHT_ROUND','NOSE_TOP_DEPTH'])
    boards={
        'heads-necks.png':('머리와 짧은 목 · 네 품종',[
            ('사선','neutral',38),('측면','neutral',90),('정면','neutral',0)]),
        'mouth-neck-check.png':('턱과 목 · 표정 연결 확인',[
            ('입 벌림','open',38),('혀 내밀기','tongue',38),('코 핥기','lick',38)])}
    for name,(title,rows) in boards.items():
        img,scale=m.render(heads,rows,title)
        buffer=io.BytesIO();img.save(buffer,format='PNG')
        result['images'][name]={'bytes_match':buffer.getvalue()==(HERE/name).read_bytes(),
            'size':list(img.size),'scale':float(scale),'sha256':hashlib.sha256((HERE/name).read_bytes()).hexdigest()}
    recipe=json.loads((HERE/'recipe.json').read_text(encoding='utf-8'))
    result['hashes']['recipe_inputs_match']=all(hashlib.sha256((HERE.parent/f).read_bytes()).hexdigest()==h for f,h in recipe['input_sha256'].items())
    result['hashes']['recipe_images_match']=all(hashlib.sha256((HERE/f).read_bytes()).hexdigest()==h for f,h in recipe['image_sha256'].items())
    expected={m.SOURCE/'preview.py':'bf8644368beaaea677bd82cb5760520951064373c59bdfdc58b1637ce0cabbe6',
        old.model.HERE/'B.json':'f20990163e6763af041308b12bc703b6b12d0430da2d966714da52be15cf2e9c',
        old.model.HERE/'profiles.json':'1a574306a6bf8eb010ed98a8f3711dfcc22decb55d6fdf6d2a754a3e4e3f995a',
        old.model.HERE/'preview.py':'9da720d13f6472359bd2882bbc390a1f70c7b9e4e28206db3d9eb88f489db11e'}
    result['hashes']['source_files_unchanged']=all(hashlib.sha256(p.read_bytes()).hexdigest()==h for p,h in expected.items())
    result['hashes']['preview_sha256']=hashlib.sha256((HERE/'preview.py').read_bytes()).hexdigest()
    (HERE/'review-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
