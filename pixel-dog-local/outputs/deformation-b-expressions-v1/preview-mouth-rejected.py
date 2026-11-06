"""Six authored, static head expressions on the retained round-eyed B heads."""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent/'deformation-b-round-eyes-v1'
spec = importlib.util.spec_from_file_location('round_heads',SOURCE/'preview.py')
round_heads = importlib.util.module_from_spec(spec)
spec.loader.exec_module(round_heads)
model = round_heads.model
HEAD_SCALE = round_heads.base.HEAD_SCALE
STATES = [('neutral','기본'),('half','반쯤 감기'),('closed','눈 감기'),
          ('open','입 벌림'),('tongue','혀 내밀기'),('lick','코 핥기')]
ORAL = np.array([61.,37.,35.])


def profile_for(rig, raw):
    profile = model.local_profile(rig,raw)
    radius = float(np.sqrt(np.prod(profile['eye_radius'])))
    profile.update(eye_radius=(radius,radius),eye_tilt=0.,eye_power=2.)
    return profile


def eyelids(rig,breed,profile,closed=False):
    clean = dict(profile,eye_radius=(1e-7,1e-7))
    mesh = model.head_features(rig,breed,clean)
    shell,colors = mesh[0]
    colors = colors.copy()
    centers = (shell[:-1,:-1]+shell[1:,:-1]+shell[1:,1:]+shell[:-1,1:])/4
    xx,yy,zz = centers.transpose(2,0,1)
    pose = {k:np.asarray(v) for k,v in model.pose(rig).items()}
    radius = profile['eye_radius'][0]
    def stain(mask,color):
        nonlocal colors
        mask = np.clip(mask,0,1)[...,None]
        colors = colors*(1-mask)+np.asarray(color)*mask
    for side,sign in [('L_',1),('R_',-1)]:
        eye = pose['face.'+side+'eye']-pose['body.head']
        u,v = (xx-eye[0])/radius,(yy-eye[1])/radius
        visible = (sign*zz>0)
        if closed:
            # A lid-contact curve replaces the covered eye, including glint.
            line = np.exp(-((v-(-.08+.18*u*u))/.12)**2)
            ends = 1-model.smoothstep((np.abs(u)-.78)/.28)
            stain(line*ends*visible,(53,43,34))
        else:
            lid = np.clip((-.02-v)/.07+.5,0,1)*visible
            stain(np.clip((1.12-u*u-v*v)*4,0,1)*lid,(52,42,32))
            stain(np.exp(-4*(u*u+(v*.8)**2))*.50*lid,(107,77,42))
            stain(np.exp(-12*(u*u+v*v))*.98*lid,(27,26,24))
            stain(np.exp(-((u+.25)**2/.023+(v-.21)**2/.065))*.75*lid,(242,228,204))
    mesh[0] = (shell,colors)
    return mesh


def row_sample(values,coordinates):
    """Periodic linear interpolation along each row of a structured surface."""
    period = values.shape[1]-1
    coordinates = np.mod(coordinates,period)
    left = np.floor(coordinates).astype(int)
    right = (left+1)%period
    fraction = (coordinates-left)[...,None]
    rows = np.arange(len(values))[:,None]
    return values[rows,left]*(1-fraction)+values[rows,right]*fraction


def rotate_jaw(vertices,pivot,angles):
    delta = vertices-pivot
    c,s = np.cos(angles)[:,None],np.sin(angles)[:,None]
    result = vertices.copy()
    result[:,:,0] = pivot[0]+c*delta[:,:,0]-s*delta[:,:,1]
    result[:,:,1] = pivot[1]+s*delta[:,:,0]+c*delta[:,:,1]
    return result


def mouth(mesh,rig,profile,degrees):
    shell,material = mesh[0]
    xs = shell[:,0,0]
    count = shell.shape[1]-1
    theta = np.linspace(0,2*np.pi,count+1)
    bottom = shell[:,:,1].min(axis=1)
    mouth_points = np.asarray(sorted(profile['mouth'],key=lambda p:p[0]))
    front,back = mouth_points[0,0],mouth_points[-1,0]
    lip = model.curve_at(mouth_points,xs)
    presence = model.smoothstep((xs-(front-1.0))/1.3)*(1-model.smoothstep((xs-(back-1.6))/1.6))
    lip = bottom+np.maximum(0,lip-bottom)*presence
    # Intersect the registered lip line with the existing, unchanged section.
    mouth_theta = np.array([np.interp(y,row[:count//2+1,1][::-1],theta[:count//2+1][::-1])
                            for y,row in zip(lip,shell)])
    original = np.broadcast_to(theta,shell.shape[:2])
    upper_angles = np.where((original>mouth_theta[:,None])&(original<=np.pi),mouth_theta[:,None],original)
    upper_angles = np.where((original>np.pi)&(original<2*np.pi-mouth_theta[:,None]),
                            2*np.pi-mouth_theta[:,None],upper_angles)
    upper = row_sample(shell,upper_angles/(2*np.pi)*count)
    # Preserve every unaffected upper-face vertex exactly, including nose/eyes.
    unchanged = upper_angles==original
    upper[unchanged] = shell[unchanged]
    upper[:,-1] = upper[:,0]
    upper_colors = material.copy()
    face_theta = (theta[:-1]+theta[1:])/2
    face_limit = (mouth_theta[:-1]+mouth_theta[1:])/2
    ceiling = (face_theta[None,:]>face_limit[:,None])&(face_theta[None,:]<2*np.pi-face_limit[:,None])
    upper_colors[ceiling] = ORAL
    t = np.linspace(0,1,145)
    lower_angles = mouth_theta[:,None]+(2*np.pi-2*mouth_theta[:,None])*t[None,:]
    lower = row_sample(shell,lower_angles/(2*np.pi)*count)
    pose = {k:np.asarray(v) for k,v in model.pose(rig).items()}
    pivot = pose['face.jaw_axis']-pose['body.head']
    weight = 1-model.smoothstep((xs-(back-2.4))/2.4)
    angle = np.deg2rad(degrees)*weight
    lower = rotate_jaw(lower,pivot,angle)
    floor = (lower[:,0]+lower[:,-1])/2
    # The final column closes the lower jaw with its dark oral floor.
    lower_closed = np.concatenate((lower,lower[:,:1]),axis=1)
    # Sample only the original lower-face material; no new exterior lip stroke.
    color_angles = (lower_angles[:-1,:-1]+lower_angles[1:,1:])/2
    color_indices = np.clip((color_angles/(2*np.pi)*count).astype(int),0,count-1)
    lower_colors = material[np.arange(len(xs)-1)[:,None],color_indices]
    lower_colors = np.concatenate((lower_colors,np.broadcast_to(ORAL,(len(xs)-1,1,3))),axis=1)
    upper_left = row_sample(shell,mouth_theta[:,None]/(2*np.pi)*count)[:,0]
    upper_right = row_sample(shell,(2*np.pi-mouth_theta[:,None])/(2*np.pi)*count)[:,0]
    left_wall = np.stack((upper_left,lower[:,0]),axis=1)
    right_wall = np.stack((lower[:,-1],upper_right),axis=1)
    # Omit collapsed pre-mouth rows entirely: they are upper muzzle, not a
    # mandible or an oral wall stretching down from the front of the nose.
    active = np.flatnonzero(np.sin(mouth_theta)>1e-5)
    first,last = max(0,int(active[0])-1),min(len(xs)-1,int(active[-1])+1)
    region = slice(first,last+1)
    result = [(upper,upper_colors),(lower_closed[region],lower_colors[first:last]),
              (left_wall[region],ORAL),(right_wall[region],ORAL),*mesh[1:]]
    data = dict(xs=xs,front=front,back=back,floor=floor,pivot=pivot,
                angle=degrees,upper=shell,mouth_theta=mouth_theta,weight=weight)
    return result,data


def floor_at(data,x):
    return np.array([np.interp(x,data['xs'],data['floor'][:,i]) for i in range(3)])


def tongue(data,width,lick=False):
    front,back = data['front'],data['back']
    inside_x = np.linspace((front+back)/2,front+.3,61)
    inside = np.array([floor_at(data,x)+[0,.70,0] for x in inside_x])
    root,lip = inside[0],inside[-1]
    shell = data['upper']
    if lick:
        index = int(np.argmin(np.abs(data['xs']-(data['xs'][0]+1.3))))
        contact = shell[index,0].copy()
        # Route outside the rostral silhouette before returning to nose skin.
        p1 = np.array([data['xs'][0]-2.6,lip[1]+.3,0.])
        p2 = np.array([data['xs'][0]-2.4,contact[1]+.8,0.])
        tip = contact
        half_width = .12*width
    else:
        direction = inside[-1]-inside[-2]
        direction /= np.linalg.norm(direction)
        p1 = lip+direction*1.7
        tip = np.array([data['xs'][0]-2.6,lip[1]-1.5,0.])
        p2 = tip+[1.3,.9,0]
        contact = None
        half_width = .17*width
    outside_t = np.linspace(0,1,81)
    t = outside_t
    outside = ((1-t)**3)[:,None]*lip+(3*(1-t)**2*t)[:,None]*p1+(3*(1-t)*t*t)[:,None]*p2+(t**3)[:,None]*tip
    path = np.concatenate((inside,outside[1:]),axis=0)
    t = np.linspace(0,1,len(path))
    tangent = np.gradient(path,axis=0)
    normal = np.stack((-tangent[:,1],tangent[:,0],np.zeros(len(t))),axis=1)
    normal /= np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-9)
    phi = np.linspace(0,2*np.pi,65)
    envelope = np.sqrt(np.clip(t/.10,0,1)*np.clip((1-t)/.14,0,1))
    radii = half_width*envelope
    thickness = .038*width*envelope
    surface = path[:,None,:]+normal[:,None,:]*thickness[:,None,None]*np.cos(phi)[None,:,None]
    surface[:,:,2] += radii[:,None]*np.sin(phi)[None,:]
    record = dict(root=root.tolist(),tip=tip.tolist(),contact=None if contact is None else contact.tolist(),
                  contact_distance=0.0 if lick else None)
    return (surface,np.array([194.,116.,119.])),record


def build():
    rigs,profiles = model.load('B.json')['breeds'],model.load('profiles.json')
    heads,evidence = {},{}
    for breed in model.BREEDS:
        rig = rigs[breed]
        profile = profile_for(rig,profiles[breed])
        base = model.head_features(rig,breed,profile)
        heads[breed],evidence[breed] = {},{}
        for state,_ in STATES:
            detail = {}
            if state in ('half','closed'):
                mesh = eyelids(rig,breed,profile,closed=state=='closed')
            elif state in ('open','tongue','lick'):
                degrees = 9. if state!='lick' else 5.
                mesh,data = mouth(base,rig,profile,degrees)
                detail['jaw_degrees'] = degrees
                if state in ('tongue','lick'):
                    feature,info = tongue(data,profiles[breed]['half_width'],lick=state=='lick')
                    mesh.append(feature)
                    detail['tongue'] = info
            else:
                mesh = base
            heads[breed][state] = [(v*HEAD_SCALE,np.asarray(c)) for v,c in mesh]
            evidence[breed][state] = detail
    return heads,evidence


def render(heads,angle=38):
    cases = []
    for breed in model.BREEDS:
        row = []
        for state,_ in STATES:
            v,c = model.polys(heads[breed][state],angle,0)
            lo,hi = v[:,:,:2].min((0,1)),v[:,:,:2].max((0,1))
            row.append((v,c,lo,hi))
        cases.append(row)
    scale = min(min(286/(hi[0]-lo[0]),218/(hi[1]-lo[1])) for row in cases for _,_,lo,hi in row)
    image = Image.new('RGB',(1980,1030),model.BG)
    pen = ImageDraw.Draw(image)
    model.label(image,30,24,'B 머리 · 여섯 가지 표정',32,bold=True)
    view_name = '¾ 보기' if angle==38 else '측면 보기'
    model.label(image,32,78,f'{view_name} · 둥근 눈 기준 · 같은 배율 · 기본형과 눈·입 동작 비교',18,model.MUTED)
    for i,(_,name) in enumerate(STATES):
        model.label(image,32+i*325,130,name,20,bold=True)
    for row_index,(row,name) in enumerate(zip(cases,model.NAMES)):
        top = 172+row_index*273
        pen.line((25,top,1955,top),fill=model.LINE)
        model.label(image,30,top+12,name,20,bold=True)
        lo = np.min([case[2] for case in row],axis=0)
        hi = np.max([case[3] for case in row],axis=0)
        center = np.array([170,top+151])-(lo+hi)/2*np.array([scale,-scale])
        for col,(v,c,_,_) in enumerate(row):
            model.paint(image,v,c,center+[col*325,0],scale)
    model.label(image,32,1002,'정적인 표정 적용 시안입니다. 입 벌림·혀 노출은 호흡 동작이나 실제 개체의 감정을 뜻하지 않습니다.',15,model.MUTED)
    return image,scale


def main():
    heads,evidence = build()
    image,scale = render(heads)
    image.save(HERE/'expressions.png')
    side,side_scale = render(heads,90)
    side.save(HERE/'expressions-side.png')
    inputs = [HERE/'preview.py',SOURCE/'preview.py',round_heads.BASE/'preview.py',
              model.HERE/'preview.py',model.HERE/'B.json',model.HERE/'profiles.json',round_heads.base.STYLE_PATH]
    recipe = dict(states=STATES,head_scale=HEAD_SCALE,primary_camera=38,side_camera=90,
                  pixels_per_unit=scale,side_pixels_per_unit=side_scale,evidence=evidence,
                  input_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                  image_sha256={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in ['expressions.png','expressions-side.png']},
                  classification='authored static action examples; not measured anatomy or affect inference',status='USER_REVIEW_PENDING')
    (HERE/'recipe.json').write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
