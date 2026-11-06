"""Authored cranio-cervical control chain and articulated mandible, four dogs."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter
from scipy.spatial import ConvexHull

HERE=Path(__file__).resolve().parent
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
previous=module('previous_heads',HERE.parent/'heads-necks-four-v1/preview.py')
model=module('cervical_surface',HERE/'head_surface.py')
base=module('cervical_expression',HERE/'expressions.py');base.model=model
BREEDS=previous.BREEDS;NAMES=previous.NAMES
HEAD_SCALE=base.HEAD_SCALE
PARAMS={
 'golden':dict(neck_width=5.3,neck_depth=3.6,neck_drop=10.,neck_lean=4.6,jaw_depth=1.6,jaw_width=.88,jaw_half_width=6.2),
 'whippet':dict(neck_width=3.1,neck_depth=2.7,neck_drop=9.,neck_lean=4.2,jaw_depth=1.1,jaw_width=.76,jaw_half_width=2.98),
 'dachshund':dict(neck_width=4.2,neck_depth=3.1,neck_drop=8.,neck_lean=3.8,jaw_depth=1.3,jaw_width=.86,jaw_half_width=5.1),
 'maltipoo':dict(neck_width=4.6,neck_depth=3.2,neck_drop=8.5,neck_lean=3.8,jaw_depth=1.3,jaw_width=.88,jaw_half_width=5.2)}

def inputs():
    old,profiles=previous.inputs();rigs={}
    for breed in BREEDS:
        world={k:np.asarray(v,float) for k,v in model.pose(old[breed]).items()}
        origin=world['body.head'];p={k:v-origin for k,v in world.items() if k.startswith('face.')}
        profiles[breed]=copy.deepcopy(profiles[breed])
        for key in ('top','bottom','mouth','nose','ear','ridge'):
            profiles[breed][key]=(np.asarray(profiles[breed][key])-origin).tolist()
        settings=PARAMS[breed]
        hinge=p['face.jaw_axis'].copy()
        hinge[1]=p['face.L_temple'][1]-1.2
        p['face.jaw_axis']=hinge
        for side,sign in [('L',1),('R',-1)]:
            p[f'face.{side}_jaw_hinge']=hinge+[0,0,sign*abs(p[f'face.{side}_jaw_hinge'][2])]
        # The head support is a separate posterior skull-base attachment,
        # independent of either the mandible axis or its opening angle.
        ao=p['face.occiput']+[-1.7,-3.8,0]
        c1=ao+[.6,-1.1,0]
        c2=ao+[settings['neck_lean']*.46,-settings['neck_drop']*.43,0]
        lower=ao+[settings['neck_lean'],-settings['neck_drop'],0]
        nodes={}
        def node(name,parent,position,parent_position):
            nodes[name]=dict(parent=parent,offset=(np.asarray(position)-parent_position).tolist())
        node('neck.lower',None,lower,np.zeros(3))
        node('neck.C2','neck.lower',c2,lower)
        node('neck.C1','neck.C2',c1,c2)
        node('head.occipital_joint','neck.C1',ao,c1)
        node('body.head','head.occipital_joint',np.zeros(3),ao)
        for name,value in p.items():
            if name=='face.jaw_axis':parent='face.skull'
            elif name.endswith('_jaw_hinge') or name=='face.chin':parent='face.jaw_axis'
            elif name.endswith('_mouth_corner') or name.endswith('_jaw_side'):
                parent='face.'+name.split('.')[1][0]+'_jaw_hinge'
            else:parent='body.head'
            node(name,parent,value,p.get(parent,np.zeros(3)))
        rigs[breed]=dict(name=breed,nodes=nodes,
            provenance='Authored simplified occipital-C1-C2-lower cervical chain; not measured anatomy',
            neck_skin=dict(width=settings['neck_width'],depth=settings['neck_depth']))
    return rigs,profiles

def ellipse_exit(x,cy,dy,dz,center,radii):
    """Positive ray exit through an ellipsoid section at a longitudinal row."""
    px,py,pz=center;rx,ry,rz=radii
    aa=(dy/ry)**2+(dz/rz)**2
    bb=2*((cy-py)*dy/ry**2-pz*dz/rz**2)
    cc=((x-px)/rx)**2+((cy-py)/ry)**2+(pz/rz)**2-1
    disc=bb*bb-4*aa*cc
    return np.where(disc>=0,np.maximum(0,(-bb+np.sqrt(np.maximum(0,disc)))/(2*aa)),0)

def cervical_skin(mesh,rig,breed):
    """Continuous head/neck envelope sampled from the cervical control chain.

    No jaw coordinate determines the neck. The posterior head cross sections
    and the swept cervical ellipsoids share one closed structured surface.
    """
    vertices,colors=mesh[0];p={k:np.asarray(v) for k,v in model.pose(rig).items()}
    keep=np.r_[True,np.diff(vertices[:,0,0])>1e-8]
    indices=np.flatnonzero(keep)
    vertices=vertices[indices]
    colors=colors[np.minimum(indices[:-1],len(colors)-1)]
    o=p['body.head'];ao=p['head.occipital_joint']-o
    controls=np.array([p[k]-o for k in ('head.occipital_joint','neck.C1','neck.C2','neck.lower')])
    width,depth=rig['neck_skin']['width'],rig['neck_skin']['depth']
    xs=vertices[:,0,0];last_x=max(xs[-1],controls[-1,0]+depth+.01)
    extra=np.linspace(xs[-1],last_x,65)[1:]
    allx=np.r_[xs,extra];n=len(xs);theta=np.linspace(0,2*np.pi,vertices.shape[1])
    dy,dz=np.cos(theta)[None,:],np.sin(theta)[None,:]
    top=vertices[:,:,1].max(axis=1);bottom=vertices[:,:,1].min(axis=1)
    centers=(top+bottom)/2;halfy=np.maximum((top-bottom)/2,.015)
    halfz=np.maximum(np.abs(vertices[:,:,2]).max(axis=1),.015)
    center=np.r_[centers,np.full(len(extra),centers[-1])]
    # At the posterior cap the sampling axis follows the neck, avoiding a
    # hanging strip from an empty skull-centred slice.
    neck_y=np.interp(allx,controls[:,0],controls[:,1])
    recenter=model.smoothstep((allx-ao[0])/max(1,xs[-1]-ao[0]))
    center=center*(1-recenter)+neck_y*recenter
    cy=center[:,None];xx=allx[:,None]
    hr=np.zeros((len(allx),len(theta)))
    # Exact front is restored below; ellipses are used only in the skull base.
    aa=(dy/halfy[:,None])**2+(dz/halfz[:,None])**2
    bb=2*(cy[:n]-centers[:,None])*dy/halfy[:,None]**2
    cc=((cy[:n]-centers[:,None])/halfy[:,None])**2-1
    disc=bb*bb-4*aa*cc
    hr[:n]=np.where(disc>=0,np.maximum(0,(-bb+np.sqrt(np.maximum(0,disc)))/(2*aa)),0)
    nr=np.zeros_like(hr)
    for i in range(len(controls)-1):
        for t in np.linspace(0,1,13):
            c=controls[i]*(1-t)+controls[i+1]*t
            radius=width*(.83+.17*(i+t)/(len(controls)-1))
            nr=np.maximum(nr,ellipse_exit(xx,cy,dy,dz,c,[depth,depth*1.2,radius]))
    # A compact smooth maximum rounds the actual union at its intersection.
    k=.65;h=np.maximum(0,k-np.abs(hr-nr))/k
    radius=np.maximum(hr,nr)+h*h*k*.25*((hr>0)&(nr>0))
    out=np.stack(np.broadcast_arrays(xx,cy+radius*dy,radius*dz),axis=-1)
    start=ao[0]-depth
    blend=model.smoothstep((allx-start)/2.5)
    # Fade around the side of the skull as well as along it: a hard upper/lower
    # split would leave an abrupt step where the sampling axis descends.
    ventral=model.smoothstep(-dy/.65)
    posterior=model.smoothstep((allx-ao[0])/2.5)[:,None]
    skin_weight=blend[:,None]*(ventral+(1-ventral)*posterior)
    out[:n]=vertices*(1-skin_weight[:n,:,None])+out[:n]*skin_weight[:n,:,None]
    smooth=gaussian_filter(out,sigma=(1.5,1.5,0),mode=('nearest','wrap','nearest'))
    out+=(smooth-out)*skin_weight[:,:,None]
    # Mouth-clipped skull rows and circular neck rows do not have matching
    # angular parameterizations. Re-sample the posterior envelope around one
    # interior centre; mixing their vertex indices directly can fold a side.
    rays=np.column_stack((np.cos(theta),np.sin(theta)))
    for row in np.flatnonzero(blend>0):
        yz=out[row,:,1:]
        if np.ptp(yz[:,0])<1e-8 or np.ptp(yz[:,1])<1e-8:continue
        hull=yz[ConvexHull(yz).vertices]
        origin=hull.mean(axis=0);origin[1]=0.
        a=hull-origin;b=np.roll(a,-1,axis=0);edge=b-a
        den=rays[:,0,None]*edge[None,:,1]-rays[:,1,None]*edge[None,:,0]
        safe=np.where(np.abs(den)>1e-12,den,np.nan)
        distance=(a[:,0]*edge[:,1]-a[:,1]*edge[:,0])[None,:]/safe
        segment=(a[None,:,0]*rays[:,1,None]-a[None,:,1]*rays[:,0,None])/safe
        hit=np.where((segment>=-1e-8)&(segment<=1+1e-8)&(distance>=0),distance,np.inf)
        radial=hit.min(axis=1)
        if not np.isfinite(radial).all():raise ValueError('Invalid posterior radial envelope')
        out[row,:,1:]=origin+radial[:,None]*rays
    out[:,:,1]=np.maximum(out[:,:,1],controls[-1,1])
    out[:,-1]=out[:,0]
    # Close the cropped cervical base and distal end geometrically.
    out[-1]=np.array([last_x,controls[-1,1],0.])
    coat=np.array(model.old.COLORS.get(breed,([239,228,210],None))[0],float)
    material=np.broadcast_to(coat,(len(allx)-1,len(theta)-1,3)).copy()
    material[:len(colors)]=colors
    face_blend=(blend[:-1]+blend[1:])/2
    material=material*(1-face_blend[:,None,None])+coat*face_blend[:,None,None]
    return [(out,material),*mesh[1:]],dict(controls=controls.tolist(),start_x=float(start),crop_y=float(controls[-1,1]))

def build():
    rigs,profiles=inputs();heads={};evidence={}
    for breed in BREEDS:
        rig=rigs[breed];profile=base.profile_for(rig,profiles[breed],breed)
        profile.update(structured_jaw=True,**{k:v for k,v in PARAMS[breed].items() if k.startswith('jaw_')})
        if breed=='maltipoo':profile['eye_radius']=(1.4,1.4)
        neutral=model.head_features(rig,breed,profile)
        heads[breed]={};evidence[breed]={}
        for state,_ in base.STATES:
            mesh=base.eyelids(rig,breed,profile,state=='closed') if state in ('half','closed') else neutral
            if breed=='maltipoo':mesh=previous.curly_coat(mesh,rig)
            angle=(4 if state=='lick' else 6)*profile['mouth_style'][1] if state in ('open','tongue','lick') else 0.
            mesh,data=base.mouth(mesh,rig,profile,angle)
            detail=dict(angle=angle,hinge=data['hinge_axis'].tolist(),pivot=data['pivot'].tolist(),
                        ramus_front=data['back'],neck=None)
            jaw_center=data['lower_posed'].mean(axis=1)
            detail['jaw_center_path']=jaw_center[::max(1,len(jaw_center)//30)].tolist()+[data['pivot'].tolist()]
            if state in ('tongue','lick'):
                part,info=base.tongue(data,profiles[breed]['half_width'],state=='lick');mesh.append(part);detail['tongue']=info
            mesh,detail['neck']=cervical_skin(mesh,rig,breed)
            heads[breed][state]=[(v*HEAD_SCALE,np.asarray(c)) for v,c in mesh]
            evidence[breed][state]=detail
    return heads,evidence,rigs,profiles

def render(heads,rigs,rows,title,evidence=None):
    # Use the existing camera and rasterizer; all breeds share one scale.
    cases=[]
    for label,state,angle,overlay in rows:
        row=[]
        for breed in BREEDS:
            v,c=model.polys(heads[breed][state],angle,0)
            row.append((v,c,v[:,:,:2].min((0,1)),v[:,:,:2].max((0,1))))
        cases.append(row)
    scale=min(min(316/(hi[0]-lo[0]),235/(hi[1]-lo[1])) for row in cases for _,_,lo,hi in row)
    anchors={}
    for row,(_,_,angle,_) in zip(cases,rows):
        for j,(_,_,lo,hi) in enumerate(row):
            key=(angle,j)
            if key in anchors:a,b=anchors[key];anchors[key]=(np.minimum(a,lo),np.maximum(b,hi))
            else:anchors[key]=(lo,hi)
    im=Image.new('RGB',(1510,180+310*len(rows)),model.BG);d=ImageDraw.Draw(im)
    model.label(im,28,22,title,29,bold=True)
    model.label(im,30,69,'공통 연결 구조 · 위치와 비율은 제작값 · 사용자 검토 대기',17,model.MUTED)
    for j,name in enumerate(NAMES):model.label(im,60+j*370,117,name,21,bold=True)
    for i,(row,(label,state,angle,overlay)) in enumerate(zip(cases,rows)):
        top=160+310*i;d.line((25,top,1485,top),fill=model.LINE);model.label(im,28,top+9,label,16,bold=True)
        for j,(v,c,lo,hi) in enumerate(row):
            a,b=anchors[(angle,j)];center=np.array([200+370*j,top+171])-(a+b)/2*[scale,-scale]
            model.paint(im,v,c,center,scale)
            if overlay:
                breed=BREEDS[j];p={k:np.array(v) for k,v in model.pose(rigs[breed]).items()}
                o=p['body.head']
                def xy(point):return tuple(center+(np.array(point)-o)[:2]*HEAD_SCALE*[scale,-scale])
                chain=['face.occiput','head.occipital_joint','neck.C1','neck.C2','neck.lower']
                d.line([xy(p[k]) for k in chain],fill='#237e86',width=4)
                for k in chain:
                    x,y=xy(p[k]);d.ellipse((x-4,y-4,x+4,y+4),fill='#237e86')
                if evidence is not None:
                    posed=np.asarray(evidence[breed][state]['jaw_center_path'])+o
                else:
                    # The same generated jaw, not the old photograph guide.
                    jaw=heads[breed][state][1][0]/HEAD_SCALE
                    posed=jaw[:,:-1].mean(axis=1)+o
                d.line([xy(q) for q in posed],fill='#a45335',width=4)
                x,y=xy(p['face.L_jaw_hinge']);d.ellipse((x-5,y-5,x+5,y+5),fill='#a45335')
    model.label(im,28,im.height-25,'청록: 후두부–경추 제어점 / 갈색: 실제 아래턱 단면 중심–턱관절 · 표면 위에 투영',13,model.MUTED)
    return im,scale

BOARDS={
 'structure.png':('머리·턱·목 연결 재구성',[
    ('측면 · 기본','neutral',90,False),('측면 · 골격과 턱 벌림','open',90,True),('사선 · 기본','neutral',38,False)]),
 'expressions.png':('새 턱관절과 목 · 표정 확인',[
    ('입 벌림','open',38,False),('혀 내밀기','tongue',38,False),('코 핥기','lick',38,False)])}

def main():
    heads,evidence,rigs,profiles=build();scales={}
    for name,(title,rows) in BOARDS.items():
        im,scales[name]=render(heads,rigs,rows,title,evidence);im.save(HERE/name)
    (HERE/'rigs.json').write_text(json.dumps(rigs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    paths=[HERE/'preview.py',HERE/'head_surface.py',HERE/'expressions.py',previous.HERE/'preview.py',previous.original_model.HERE/'B.json',previous.original_model.HERE/'profiles.json']
    recipe=dict(status='USER_REVIEW_PENDING',parameters=PARAMS,nose_scale=model.NOSE_SCALE,evidence=evidence,scales=scales,
      input_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
      image_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in BOARDS})
    (HERE/'recipe.json').write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
