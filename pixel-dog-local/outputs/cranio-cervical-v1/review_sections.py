"""Check neck cross-section polygon crossings without rerendering boards."""
import importlib.util,json
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent

def crossings(pts):
    a=pts;b=np.roll(pts,-1,axis=0)
    def cross(x,y):return x[...,0]*y[...,1]-x[...,1]*y[...,0]
    aa=a[:,None];bb=b[:,None];cc=a[None];dd=b[None]
    o1=cross(bb-aa,cc-aa);o2=cross(bb-aa,dd-aa)
    o3=cross(dd-cc,aa-cc);o4=cross(dd-cc,bb-cc)
    return np.argwhere(np.triu((o1*o2 < -1e-10)&(o3*o4 < -1e-10),2))

def main():
    s=importlib.util.spec_from_file_location('cervical_sections_review',HERE/'preview.py')
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    rigs,profiles=m.inputs();results={}
    for breed in m.BREEDS:
        rig=rigs[breed];p=m.base.profile_for(rig,profiles[breed],breed)
        p.update(structured_jaw=True,**{k:v for k,v in m.PARAMS[breed].items() if k.startswith('jaw_')})
        if breed=='maltipoo':p['eye_radius']=(1.4,1.4)
        raw=m.model.head_features(rig,breed,p)
        if breed=='maltipoo':raw=m.previous.curly_coat(raw,rig)
        mouth,_=m.base.mouth(raw,rig,p,0)
        mesh,info=m.cervical_skin(mouth,rig,breed);v=mesh[0][0]
        bad=[]
        for i in range(len(v)-1):
            if v[i,0,0]<info['start_x']:continue
            pairs=crossings(v[i,:-1:2,1:])
            if len(pairs):bad.append({'row':i,'x':float(v[i,0,0]),
                'row_x_range':float(np.ptp(v[i,:,0])),
                'crossing_segment_pairs':pairs[:5].tolist()})
        results[breed]={'self_crossing_sections':len(bad),'examples':bad[:8]}
    (HERE/'review-sections.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))

if __name__=='__main__':main()
