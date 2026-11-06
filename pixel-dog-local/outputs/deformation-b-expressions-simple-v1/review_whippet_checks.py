"""Independent isolation and jaw-profile checks for the whippet-only edit."""
import importlib.util
import hashlib
import io
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent

def load(name,filename):
    spec=importlib.util.spec_from_file_location(name,HERE/filename)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def exact(a,b):
    return len(a)==len(b) and all(np.array_equal(x,y) for f,g in zip(a,b) for x,y in zip(f,g))

def main():
    before=load('before_whippet','preview-before-whippet-jaw.py')
    after=load('after_whippet','preview.py')
    old,_=before.build()
    new,_=after.build()
    report={'unchanged_states':{breed:{state:exact(old[breed][state],new[breed][state])
                                  for state,_ in after.STATES} for breed in after.model.BREEDS}}
    rigs,profiles=after.model.load('B.json')['breeds'],after.model.load('profiles.json')
    rig=rigs['whippet']
    old_profile=before.profile_for(rig,profiles['whippet'],'whippet')
    new_profile=after.profile_for(rig,profiles['whippet'],'whippet')
    old_mesh,od=before.mouth(before.model.head_features(rig,'whippet',old_profile),rig,old_profile,0)
    new_mesh,nd=after.mouth(after.model.head_features(rig,'whippet',new_profile),rig,new_profile,0)
    base=after.model.head_features(rig,'whippet',new_profile)
    protected=np.mean(base[0][1],axis=-1)<70
    protected_vertices=np.zeros(base[0][0].shape[:2],dtype=bool)
    for rows,cols in ((slice(None,-1),slice(None,-1)),(slice(1,None),slice(None,-1)),
                      (slice(None,-1),slice(1,None)),(slice(1,None),slice(1,None))):
        protected_vertices[rows,cols]|=protected
    report['nose_eye_material_error']=float(np.abs(new_mesh[0][1]-base[0][1])[protected].max())
    report['nose_eye_vertex_error']=float(np.abs(new_mesh[0][0]-base[0][0])[protected_vertices].max())
    report['jaw_profiles']={}
    for name,d in (('before',od),('after',nd)):
        first,last=d['region']; xs=d['xs'][first:last+1]
        exposed=(xs<d['back']-2.5)&(xs>d['front']+.1)
        report['jaw_profiles'][name]={
            'front_x':d['front'],
            'exposed_length':float(d['back']-d['front']),
            'max_depth':float(np.ptp(d['lower_rest'][:,:,1],axis=1)[exposed].max()),
            'max_width':float(np.ptp(d['lower_rest'][:,:,2],axis=1)[exposed].max())}
    report['tongue_lateral_clearance']={}
    for state,nominal in (('tongue',6),('lick',4)):
        _,d=after.mouth(base,rig,new_profile,nominal*new_profile['mouth_style'][1])
        (surface,_),_=after.tongue(d,profiles['whippet']['half_width'],state=='lick')
        rim=d['lower_posed'][:,0]
        half=np.interp(surface[:61,0,0],rim[:,0],np.abs(rim[:,2]))
        report['tongue_lateral_clearance'][state]=float((half-np.max(np.abs(surface[:61,:,2]),axis=1)).min())
    comparison=load('comparison_review','whippet_comparison.py')
    stream=io.BytesIO()
    comparison.render().save(stream,format='PNG')
    image_bytes=stream.getvalue()
    report['comparison_byte_identical']=image_bytes==(HERE/'whippet-jaw-before-after.png').read_bytes()
    report['comparison_sha256']=hashlib.sha256(image_bytes).hexdigest()
    recipe=json.loads((HERE/'whippet-comparison-recipe.json').read_text(encoding='utf-8'))
    report['comparison_recipe_exact']=all(hashlib.sha256((HERE/f).read_bytes()).hexdigest()==digest for f,digest in recipe['sha256'].items())
    (HERE/'review-whippet-checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__': main()
