"""Independent, non-mutating checks of the whippet lip-slope correction."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
from unittest.mock import patch
import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent
def load(name,filename):
    spec=importlib.util.spec_from_file_location(name,HERE/filename)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def exact(a,b):
    return len(a)==len(b) and all(np.array_equal(x,y) for f,g in zip(a,b) for x,y in zip(f,g))

def main():
    old=load('old_neutral','preview-before-whippet-neutral.py')
    m=load('new_neutral','preview.py')
    before,_=old.build(); heads,evidence=m.build()
    r={'unchanged_states':{breed:{s:exact(before[breed][s],heads[breed][s]) for s,_ in m.STATES} for breed in m.model.BREEDS}}
    rigs,profiles=m.model.load('B.json')['breeds'],m.model.load('profiles.json')
    rig=rigs['whippet']; profile=m.profile_for(rig,profiles['whippet'],'whippet')
    base=m.model.head_features(rig,'whippet',profile)
    r['profiles']={}
    for name,mod in [('before',old),('after',m)]:
        p=mod.profile_for(rig,profiles['whippet'],'whippet')
        mesh,d=mod.mouth(mod.model.head_features(rig,'whippet',p),rig,p,0)
        first,last=d['region']; xs=d['xs'][first:last+1]
        exposed=(xs>d['front']+.2)&(xs<d['back']-2.5)
        floor=(d['lower_rest'][:,0]+d['lower_rest'][:,-1])/2
        r['profiles'][name]={'front_x':d['front'],'length':float(d['back']-d['front']),
            'max_depth':float(np.ptp(d['lower_rest'][:,:,1],axis=1)[exposed].max()),
            'max_width':float(np.ptp(d['lower_rest'][:,:,2],axis=1)[exposed].max()),
            'visible_floor_slope':float(np.polyfit(xs[exposed],floor[exposed,1],1)[0])}
    r['jaw']=[]; r['tongue']=[]
    for nominal in (4,6,8):
        angle=nominal*profile['mouth_style'][1]
        mesh,d=m.mouth(base,rig,profile,angle)
        restored=m.rotate_jaw(d['lower_posed'],d['pivot'],np.full(len(d['lower_posed']),-np.deg2rad(angle)))
        hinge=m.rotate_jaw(d['hinge_axis'][None],d['pivot'],np.array([np.deg2rad(angle)]))
        r['jaw'].append({'degrees':angle,'inverse_error':float(np.abs(restored-d['lower_rest']).max()),
            'hinge_error':float(np.abs(hinge[0]-d['hinge_axis']).max()),
            'ears_exact':all(np.array_equal(mesh[-2+i][j],base[1+i][j]) for i in (0,1) for j in (0,1))})
    for state,nominal in [('tongue',6),('lick',4)]:
        mesh,d=m.mouth(base,rig,profile,nominal*profile['mouth_style'][1])
        (surface,_),info=m.tongue(d,profiles['whippet']['half_width'],state=='lick')
        pts=surface[:61].reshape(-1,3)
        fy=np.interp(pts[:,0],d['floor'][:,0],d['floor'][:,1]); cy=np.interp(pts[:,0],d['xs'],d['roof_y'])
        rim=d['lower_posed'][:,0]
        half=np.interp(surface[:61,0,0],rim[:,0],np.abs(rim[:,2]))
        r['tongue'].append({'state':state,'floor_clearance':float((pts[:,1]-fy).min()),
            'roof_clearance':float((cy-pts[:,1]).min()),'lateral_clearance':float((half-np.abs(surface[:61,:,2]).max(axis=1)).min()),
            'lip_support_error':float(np.linalg.norm(surface[60,32]-info['lip_floor_contact'])),
            'contact_error':None if info['contact'] is None else float(np.linalg.norm(np.array(info['tip'])-info['contact']))})
    protected=np.mean(base[0][1],axis=-1)<70
    vertices=np.zeros(base[0][0].shape[:2],dtype=bool)
    for rows,cols in ((slice(None,-1),slice(None,-1)),(slice(1,None),slice(None,-1)),(slice(None,-1),slice(1,None)),(slice(1,None),slice(1,None))): vertices[rows,cols]|=protected
    r['nose_eye_material_error']=float(np.abs(mesh[0][1]-base[0][1])[protected].max())
    r['nose_eye_vertex_error']=float(np.abs(mesh[0][0]-base[0][0])[vertices].max())
    captured={}; original_save=Image.Image.save
    def capture(image,fp,*args,**kwargs):
        out=io.BytesIO(); original_save(image,out,format='PNG'); captured[Path(fp).name]=out.getvalue()
    with patch.object(Image.Image,'save',capture),patch.object(Path,'write_text',lambda *a,**k:0),patch.object(m,'build',lambda:(heads,evidence)): m.main()
    comp=load('neutral_compare','whippet_neutral_comparison.py'); out=io.BytesIO(); comp.render().save(out,format='PNG')
    captured['whippet-neutral-before-after.png']=out.getvalue()
    r['renders']={name:{'byte_identical':data==(HERE/name).read_bytes(),'sha256':hashlib.sha256(data).hexdigest()} for name,data in captured.items()}
    recipe=json.loads((HERE/'recipe.json').read_text(encoding='utf-8'))
    r['recipe_inputs_exact']=all(hashlib.sha256((HERE.parent/f).read_bytes()).hexdigest()==h for f,h in recipe['input_sha256'].items())
    r['recipe_images_exact']=all(hashlib.sha256((HERE/f).read_bytes()).hexdigest()==h for f,h in recipe['image_sha256'].items())
    cr=json.loads((HERE/'whippet-neutral-recipe.json').read_text(encoding='utf-8'))
    r['comparison_recipe_exact']=all(hashlib.sha256((HERE/f).read_bytes()).hexdigest()==h for f,h in cr['sha256'].items())
    r['source_sha256']=hashlib.sha256((HERE/'preview.py').read_bytes()).hexdigest()
    (HERE/'review-whippet-neutral-checks.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(r))
if __name__=='__main__': main()
