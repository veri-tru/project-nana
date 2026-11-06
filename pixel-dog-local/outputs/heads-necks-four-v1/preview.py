"""Four head-and-short-neck candidates with the shared articulated facial rig."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent/'deformation-b-expressions-simple-v1'

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

base=module('neck_expression_base',SOURCE/'preview.py')
original_model=base.model
model=module('neck_head_surface',HERE/'head_surface.py')
base.model=model
BREEDS=['golden','whippet','dachshund','maltipoo']
NAMES=['골든 리트리버','휘핏','닥스훈트','말티푸']
NECK={'golden':dict(bottom=-8.,lean=1.6,width=.95),
      'whippet':dict(bottom=-2.,lean=1.5,width=.72),
      'dachshund':dict(bottom=-7.,lean=1.3,width=.90),
      'maltipoo':dict(bottom=-5.5,lean=2.,width=.90)}


def inputs():
    rigs=original_model.load('B.json')['breeds']
    profiles=original_model.load('profiles.json')
    world={k:np.array(v) for k,v in model.pose(rigs['golden']).items()}
    origin=world['body.head']
    transformed={k:(v-origin)*[.56,.92,.93] for k,v in world.items() if k.startswith('face.')}
    landmarks={'skull':[-1.5,7,0],'crown':[-1,15,0],'occiput':[5,7,0],
               'stop':[-7,8,0],'nose':[-13.4,5,0],'nose_bottom':[-12.7,3.2,0],
               'upper_lip':[-10.5,2,0],'chin':[-8,.8,0],'jaw_axis':[-.8,3.5,0]}
    for key,value in landmarks.items():
        transformed['face.'+key]=np.array(value,dtype=float)
    for side,sign in [('L',1),('R',-1)]:
        transformed[f'face.{side}_ear_root']=np.array([2.0,9.3,sign*7.7])
        transformed[f'face.{side}_ear_fold']=np.array([3.5,4.5,sign*8.7])
        transformed[f'face.{side}_ear_tip']=np.array([3.5,-1.7,sign*8.5])
        for name,dy,dz in [('eye',0,0),('pupil',0,0),('brow',1.4,0),
                           ('upper_lid',.9,0),('lower_lid',-.7,0),
                           ('eye_inner',0,-1.4),('eye_outer',0,1.4)]:
            transformed[f'face.{side}_{name}']=np.array([-4.7,8.8+dy,sign*(7.5+dz)])
        for name,xyz in {'temple':[3,7,8],'muzzle_side':[-8,4,5],
                         'nose_wing':[-12,4.8,3.5],'jaw_hinge':[-.8,3.5,6],
                         'mouth_corner':[-4,1.3,5],'jaw_side':[-5,1,5]}.items():
            value=np.array(xyz,dtype=float);value[2]*=sign
            transformed[f'face.{side}_{name}']=value
    nodes={'body.head':{'parent':None,'offset':[0.,0.,0.]}}
    for key,value in transformed.items():
        nodes[key]={'parent':'body.head','offset':value.tolist()}
    rigs=copy.deepcopy(rigs)
    rigs['maltipoo']={'name':'말티푸 작화 후보','nodes':nodes}
    raw=copy.deepcopy(profiles['golden'])
    for key in ('top','bottom','mouth','nose','ear','ridge'):
        raw[key]=((np.asarray(raw[key])-origin)*[.56,.92,.93]).tolist()
    raw['half_width']=9.5
    raw['top']=[[x,y,0.] for x,y in [(5,5),(4,11),(1,15),(-3,15),
                                   (-6,12),(-7.5,8),(-10.5,6.3),(-13.4,5.8)]]
    raw['bottom']=[[x,y,0.] for x,y in [(5,5),(3,0),(-1,-1),(-5,0),
                                      (-8,1.8),(-11.5,2.7),(-13.4,4.4)]]
    raw['mouth']=[[x,y,0.] for x,y in [(-12.1,3.5),(-10,2.3),(-7,1.4),(-4,1.3)]]
    raw['ear']=[[x,y,0.] for x,y in [(1.8,10),(5.5,9.2),(7,4.5),(6,-1),
                                   (2.5,-3),(0,-1),(.2,5.5)]]
    raw['ridge']=[[2.,8.,0.],[3.5,4.,0.],[3.,-1.,0.]]
    raw['nose_color']=[47,44,40]
    profiles=copy.deepcopy(profiles)
    profiles['maltipoo']=raw
    return rigs,profiles


def curly_coat(mesh,rig):
    """Low relief on crown/ear hair; nasal skin and eyelids stay untouched."""
    pose={k:np.asarray(v) for k,v in model.pose(rig).items()}
    origin=pose['body.head']
    output=[]
    for index,(vertices,color) in enumerate(mesh):
        v=vertices.copy()
        x,y,z=v.transpose(2,0,1)
        if index==0:
            mask=model.smoothstep((x+7)/3)*model.smoothstep((y-3.5)/3)
            for side in ('L','R'):
                eye=pose[f'face.{side}_eye']-origin
                distance=((x-eye[0])/2.7)**2+((y-eye[1])/2.7)**2
                mask*=model.smoothstep(distance-1)
            direction=v-np.array([-1.,6.,0.])
            direction[:,:,0]=0.  # preserve the longitudinal rows used by the jaw rig
        else:
            row=np.linspace(0,1,len(v))[:,None]
            mask=model.smoothstep((row-.2)/.2)*model.smoothstep((1-row)/.12)
            direction=v-v.mean(axis=1,keepdims=True)
        direction/=np.maximum(np.linalg.norm(direction,axis=-1,keepdims=True),1e-9)
        curls=(.5+.5*np.cos(2.4*x+.65*np.sin(y*1.8))*np.cos(2.8*y+.8*np.sin(z*1.6)))
        v+=direction*(.22*mask*curls)[...,None]
        v[:,-1]=v[:,0]
        output.append((v,color.copy()))
    return output


def add_neck(mesh,reference,rig,breed,fixed_surface=None):
    """Extend the head grid itself: no separate neck shell or surface seam."""
    shell,colors=mesh[0]
    raw=reference[0][0]
    xs=raw[:,0,0]
    pose={k:np.asarray(v) for k,v in model.pose(rig).items()}
    pivot=pose['face.jaw_axis']-pose['body.head']
    start=pivot[0]+.8
    settings=NECK[breed]
    transition=min(5.,.55*(xs[-1]-start))
    along=model.smoothstep((xs-start)/transition)
    theta=np.linspace(0,2*np.pi,shell.shape[1])
    t=np.clip((theta-np.pi/2)/np.pi,0,1)
    down=np.sin(np.pi*t)
    down[(theta<np.pi/2)|(theta>3*np.pi/2)]=0
    angular=model.smoothstep(down/.60)
    weight=along[:,None]*angular[None,:]
    side_y=(raw[:,72,1]+raw[:,216,1])/2
    half_width=np.abs(raw[:,:,2]).max(axis=1)*settings['width']
    target=shell.copy()
    target[:,:,0]=xs[:,None]+settings['lean']*down[None,:]**2
    # Slight overrun clipped to a common base makes a short, closed neck end.
    target[:,:,1]=np.maximum(settings['bottom'],side_y[:,None]-(side_y-settings['bottom']+5.0)[:,None]*down[None,:]**.78)
    target[:,:,2]=half_width[:,None]*np.cos(np.pi*t)[None,:]
    joined=shell+(target-shell)*weight[...,None]
    fair=gaussian_filter(joined[:,:-1],sigma=(5,5,0),mode=('nearest','wrap','nearest'))
    fair=np.concatenate((fair,fair[:,:1]),axis=1)
    joined+=(fair-joined)*np.minimum(1,weight*3)[...,None]
    joined[:,-1]=joined[:,0]
    # Same coat on the new surface; nose, eyes and oral faces are outside it.
    material=colors.copy()
    face_weight=(weight[:-1,:-1]+weight[1:,1:])/2
    coat=np.asarray(model.old.COLORS.get(breed,([239,228,210],None))[0],dtype=float)
    material=np.where((face_weight>.02)[...,None],coat,material)
    if fixed_surface is not None:
        joined[weight>0]=fixed_surface[0][weight>0]
        material[face_weight>0]=fixed_surface[1][face_weight>0]
    # Extending the tiny original rear cap must not turn it into an open slit.
    joined[-1]=(joined[-1]+joined[-1,::-1])/2
    joined[-1,:,2]=0.
    if fixed_surface is not None:
        joined[-1]=fixed_surface[0][-1]
    result=[(joined,material),*mesh[1:]]
    return result,dict(start_x=float(start),bottom_y=settings['bottom'],
                       modified_vertices=int(np.count_nonzero(weight)),
                       shared_surface=True)


def build():
    rigs,profiles=inputs()
    heads,evidence={},{}
    for breed in BREEDS:
        rig=rigs[breed]
        profile=base.profile_for(rig,profiles[breed],breed)
        if breed=='maltipoo':
            profile['eye_radius']=(1.4,1.4)
        neutral=model.head_features(rig,breed,profile)
        reference=neutral
        heads[breed],evidence[breed]={},{}
        fixed_neck=None
        for state,_ in base.STATES:
            detail={}
            if state in ('half','closed'):
                mesh=base.eyelids(rig,breed,profile,state=='closed')
            else:
                mesh=neutral
            if breed=='maltipoo':
                mesh=curly_coat(mesh,rig)
            if state in ('open','tongue','lick'):
                degrees=(6. if state!='lick' else 4.)*profile['mouth_style'][1]
                mesh,data=base.mouth(mesh,rig,profile,degrees)
                detail['jaw_degrees']=degrees
                detail['jaw_axis']=data['pivot'].tolist()
                if state in ('tongue','lick'):
                    part,info=base.tongue(data,profiles[breed]['half_width'],state=='lick')
                    mesh.append(part)
                    detail['tongue']=info
            elif breed=='whippet':
                mesh=base.trim_whippet_neck(mesh,rig,profile)
            mesh,neck=add_neck(mesh,reference,rig,breed,fixed_neck)
            if fixed_neck is None:
                fixed_neck=(mesh[0][0].copy(),mesh[0][1].copy())
            detail['neck']=neck
            heads[breed][state]=[(v*base.HEAD_SCALE,np.asarray(c)) for v,c in mesh]
            evidence[breed][state]=detail
    return heads,evidence,rigs,profiles


def render(heads,rows,title):
    cases=[]
    for label,state,angle in rows:
        row=[]
        for breed in BREEDS:
            v,c=model.polys(heads[breed][state],angle,0)
            lo,hi=v[:,:,:2].min((0,1)),v[:,:,:2].max((0,1))
            row.append((v,c,lo,hi))
        cases.append(row)
    scale=min(min(316/(hi[0]-lo[0]),245/(hi[1]-lo[1])) for row in cases for _,_,lo,hi in row)
    anchors={}
    for row,(_,_,angle) in zip(cases,rows):
        for j,(_,_,lo,hi) in enumerate(row):
            key=(angle,j)
            if key not in anchors:
                anchors[key]=(lo.copy(),hi.copy())
            else:
                a,b=anchors[key]
                anchors[key]=(np.minimum(a,lo),np.maximum(b,hi))
    image=Image.new('RGB',(1510,180+310*len(rows)),model.BG)
    pen=ImageDraw.Draw(image)
    model.label(image,28,23,title,30,bold=True)
    model.label(image,30,72,'같은 배율 · 짧은 목 포함 · 말티푸는 대표 작화 후보',18,model.MUTED)
    for j,name in enumerate(NAMES):
        model.label(image,60+j*370,118,name,21,bold=True)
    for i,(row,(label,state,angle)) in enumerate(zip(cases,rows)):
        top=160+310*i
        pen.line((25,top,1485,top),fill=model.LINE)
        model.label(image,28,top+10,label,17,bold=True)
        for j,(v,c,lo,hi) in enumerate(row):
            a,b=anchors[(angle,j)]
            center=np.array([200+370*j,top+171])-(a+b)/2*np.array([scale,-scale])
            model.paint(image,v,c,center,scale)
    model.label(image,28,image.height-24,'현재 구현의 정적 시안 · 사용자 검토 대기',14,model.MUTED)
    return image,scale


def main():
    heads,evidence,rigs,profiles=build()
    boards={
        'heads-necks.png':('머리와 짧은 목 · 네 품종',[
            ('사선','neutral',38),('측면','neutral',90),('정면','neutral',0)]),
        'mouth-neck-check.png':('턱과 목 · 표정 연결 확인',[
            ('입 벌림','open',38),('혀 내밀기','tongue',38),('코 핥기','lick',38)])}
    scales={}
    for name,(title,rows) in boards.items():
        image,scales[name]=render(heads,rows,title)
        image.save(HERE/name)
    (HERE/'maltipoo-authored.json').write_text(json.dumps(dict(rig=rigs['maltipoo'],profile=profiles['maltipoo'],
        provenance='Authored mixed-breed candidate, not measured anatomy; cream curly-coat interpretation'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    paths=[HERE/'preview.py',HERE/'head_surface.py',SOURCE/'preview.py',original_model.HERE/'B.json',
           original_model.HERE/'profiles.json',HERE/'maltipoo-authored.json']
    recipe=dict(breeds=BREEDS,head_scale=base.HEAD_SCALE,neck=NECK,nose_scale=model.NOSE_SCALE,evidence=evidence,pixels_per_unit=scales,
                input_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                image_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in boards},status='USER_REVIEW_PENDING')
    (HERE/'recipe.json').write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':
    main()
