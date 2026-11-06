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
MOUTH_STYLE = {'golden':(.22,1.),'whippet':(.13,.58),'dachshund':(.20,.85)}


def profile_for(rig, raw, breed=None):
    profile = model.local_profile(rig,raw)
    radius = float(np.sqrt(np.prod(profile['eye_radius'])))
    profile.update(eye_radius=(radius,radius),eye_tilt=0.,eye_power=2.)
    profile['mouth_style'] = MOUTH_STYLE.get(breed,(.22,1.))
    profile['slender_jaw'] = breed=='whippet'
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
    pose = {k:np.asarray(v) for k,v in model.pose(rig).items()}
    pivot = pose['face.jaw_axis']-pose['body.head']
    hinge_axis = np.array([pose['face.'+s+'_jaw_hinge']-pose['body.head'] for s in ('L','R')])
    # One quiet lip plane replaces the observed polycurve and front taper.
    # Its intersection with the rounded muzzle supplies a round front edge.
    rear = pivot[0]+1.6
    middle = (front+back)/2
    low = np.interp(middle,xs,bottom)
    high = np.interp(middle,xs,shell[:,:,1].max(axis=1))
    plane_y = low+profile['mouth_style'][0]*(high-low)
    lip = np.full_like(xs,plane_y)
    if profile.get('slender_jaw',False):
        # Reference-guided long, straight oral margin: the jaw starts near
        # the nose instead of being a short slice from the bottom of a dome.
        a,b = mouth_points[0],mouth_points[-1]
        u = np.clip((xs-a[0])/(b[0]-a[0]),0.,1.)
        # A shallow arc with horizontal tangents at both ends; the final
        # turn eases into the cheek without a descending straight slash.
        lip = (a[1]-2.0)-.50*np.sin(np.pi*u)**2-.50*model.smoothstep(u)
    rear_fade = 1-model.smoothstep((xs-pivot[0])/(rear-pivot[0]))
    lip = bottom+np.maximum(0,lip-bottom)*rear_fade
    # Intersect the registered lip line with the existing, unchanged section.
    mouth_theta = np.array([np.interp(y,row[:count//2+1,1][::-1],theta[:count//2+1][::-1])
                            for y,row in zip(lip,shell)])
    original = np.broadcast_to(theta,shell.shape[:2])
    # The joint remains inside the cheek. Keep the fixed cheek over the rear
    # mandible rather than drawing an exposed loop around the hinge.
    cheek = (model.smoothstep((xs-(back-3.5))/5.0) if profile.get('slender_jaw',False)
             else model.smoothstep((xs-(back-1.5))/2.0))
    upper_limit = mouth_theta+(np.pi-mouth_theta)*cheek
    upper_angles = np.where((original>upper_limit[:,None])&(original<=np.pi),upper_limit[:,None],original)
    upper_angles = np.where((original>np.pi)&(original<2*np.pi-upper_limit[:,None]),
                            2*np.pi-upper_limit[:,None],upper_angles)
    upper = row_sample(shell,upper_angles/(2*np.pi)*count)
    # Preserve every unaffected upper-face vertex exactly, including nose/eyes.
    unchanged = upper_angles==original
    upper[unchanged] = shell[unchanged]
    upper[:,-1] = upper[:,0]
    upper_colors = material.copy()
    # Only the actual transverse palate face is oral material. Boundary
    # skin triangles keep their coat, avoiding a dotted external lip stroke.
    roof_faces = (upper_limit[:-1]<np.pi-1e-5)&(upper_limit[1:]<np.pi-1e-5)
    oral_weight = 1-model.smoothstep((cheek[:-1]+cheek[1:])/2/.4)
    palate_color = material[:,count//2]*(1-oral_weight[:,None])+ORAL*oral_weight[:,None]
    upper_colors[roof_faces,count//2] = palate_color[roof_faces]
    t = np.linspace(0,1,145)
    lower_angles = mouth_theta[:,None]+(2*np.pi-2*mouth_theta[:,None])*t[None,:]
    lower = row_sample(shell,lower_angles/(2*np.pi)*count)
    if profile.get('slender_jaw',False):
        # Keep the lip/floor height; flatten the pendant bowl beneath it.
        # This is a rest-shape edit, before the common rigid hinge motion.
        rim_y = (lower[:,0,1]+lower[:,-1,1])/2
        depth = np.maximum(1e-9,(rim_y[:,None]-lower[:,:,1]).max(axis=1))
        depth_scale = np.minimum(.55,1.10/depth)
        lower[:,:,1] = rim_y[:,None]+depth_scale[:,None]*(lower[:,:,1]-rim_y[:,None])
        lower[:,:,2] *= .76
        half_width = np.maximum(np.abs(lower[:,:,2]).max(axis=1),1e-9)
        lower[:,:,2] *= np.minimum(1.,2.98/half_width)[:,None]
    burial_start = back-2.5
    buried = model.smoothstep((xs-burial_start)/(pivot[0]-burial_start))
    lower[:,:,1] = pivot[1]+(lower[:,:,1]-pivot[1])*(1-.88*buried[:,None])
    lower[:,:,2] *= 1-.88*buried[:,None]
    lower_rest = lower.copy()
    angle = np.full(len(xs),np.deg2rad(degrees))
    lower = rotate_jaw(lower_rest,pivot,angle)
    floor = (lower[:,0]+lower[:,-1])/2
    # The final column closes the lower jaw with its dark oral floor.
    lower_closed = np.concatenate((lower,lower[:,:1]),axis=1)
    # Sample only the original lower-face material; no new exterior lip stroke.
    color_angles = (lower_angles[:-1,:-1]+lower_angles[1:,1:])/2
    color_indices = np.clip((color_angles/(2*np.pi)*count).astype(int),0,count-1)
    lower_colors = material[np.arange(len(xs)-1)[:,None],color_indices]
    lower_colors = np.concatenate((lower_colors,np.broadcast_to(ORAL,(len(xs)-1,1,3))),axis=1)
    # Omit collapsed pre-mouth rows entirely: they are upper muzzle, not a
    # mandible or an oral wall stretching down from the front of the nose.
    active = np.flatnonzero(np.sin(mouth_theta)>1e-5)
    first,last = max(0,int(active[0])-1),min(len(xs)-1,int(active[-1])+1)
    region = slice(first,last+1)
    front = float(xs[first+1])
    # Each jaw has its own roof/floor. No strip joins the two lip rims:
    # a lateral ray can pass through the opened oral aperture.
    result = [(upper,upper_colors),(lower_closed[region],lower_colors[first:last]),*mesh[1:]]
    data = dict(xs=xs,front=front,back=back,floor=floor,pivot=pivot,
                angle=degrees,upper=shell,mouth_theta=mouth_theta,
                lower_rest=lower_rest[region],lower_posed=lower[region],
                hinge_axis=hinge_axis,region=(first,last),roof_y=upper[:,:,1].min(axis=1))
    return result,data


def floor_at(data,x):
    return np.array([np.interp(x,data['xs'],data['floor'][:,i]) for i in range(3)])


def tongue(data,width,lick=False):
    front,back = data['front'],data['back']
    inside_x = np.linspace((front+back)/2,front+.3,61)
    inside_floor = np.array([floor_at(data,x) for x in inside_x])
    gap = np.maximum(.02,np.interp(inside_floor[:,0],data['xs'],data['roof_y'])-inside_floor[:,1])
    root_envelope = np.sqrt(np.clip(np.linspace(0,1,len(inside_x))/.14,0,1))
    full_thickness = (.065 if lick else .085)*width
    inside_thickness = np.minimum(full_thickness,.28*gap)*root_envelope
    inside = inside_floor.copy()
    # The underside rests on the lower oral floor, including the lip exit.
    # Only the section inside the mouth is compressed to fit the aperture.
    inside[:,1] += inside_thickness
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
        p1 = lip+direction*.8
        tip = np.array([data['xs'][0]-1.4,lip[1]-.16*width,0.])
        p2 = tip+[.7,.35,0]
        contact = None
        half_width = .14*width
    outside_t = np.linspace(0,1,81)
    t = outside_t
    outside = ((1-t)**3)[:,None]*lip+(3*(1-t)**2*t)[:,None]*p1+(3*(1-t)*t*t)[:,None]*p2+(t**3)[:,None]*tip
    path = np.concatenate((inside,outside[1:]),axis=0)
    t = np.linspace(0,1,len(path))
    tangent = np.gradient(path,axis=0)
    normal = np.stack((-tangent[:,1],tangent[:,0],np.zeros(len(t))),axis=1)
    normal /= np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-9)
    normal[:len(inside)] = [0.,1.,0.]
    phi = np.linspace(0,2*np.pi,65)
    envelope = np.sqrt(np.clip(t/.10,0,1)*np.clip((1-t)/.14,0,1))
    radii = half_width*envelope
    outside_thickness = (inside_thickness[-1]+(full_thickness-inside_thickness[-1])*
                         model.smoothstep(outside_t/.35))
    outside_thickness *= np.sqrt(np.clip((1-outside_t)/.18,0,1))
    thickness = np.concatenate((inside_thickness,outside_thickness[1:]))
    surface = path[:,None,:]+normal[:,None,:]*thickness[:,None,None]*np.cos(phi)[None,:,None]
    surface[:,:,2] += radii[:,None]*np.sin(phi)[None,:]
    record = dict(root=root.tolist(),tip=tip.tolist(),contact=None if contact is None else contact.tolist(),
                  lip_floor_contact=inside_floor[-1].tolist(),lip_center=lip.tolist(),
                  lip_half_thickness=float(inside_thickness[-1]),
                  outside_max_thickness=float(2*outside_thickness.max()),
                  contact_distance=0.0 if lick else None)
    return (surface,np.array([194.,116.,119.])),record


def build():
    rigs,profiles = model.load('B.json')['breeds'],model.load('profiles.json')
    heads,evidence = {},{}
    for breed in model.BREEDS:
        rig = rigs[breed]
        profile = profile_for(rig,profiles[breed],breed)
        base = model.head_features(rig,breed,profile)
        heads[breed],evidence[breed] = {},{}
        for state,_ in STATES:
            detail = {}
            if state in ('half','closed'):
                mesh = eyelids(rig,breed,profile,closed=state=='closed')
            elif state in ('open','tongue','lick'):
                degrees = (6. if state!='lick' else 4.)*profile['mouth_style'][1]
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


def render(heads,angle=38,states=None,title='B 머리 · 여섯 가지 표정'):
    states = STATES if states is None else states
    cases = []
    for breed in model.BREEDS:
        row = []
        for state,_ in states:
            v,c = model.polys(heads[breed][state],angle,0)
            lo,hi = v[:,:,:2].min((0,1)),v[:,:,:2].max((0,1))
            row.append((v,c,lo,hi))
        cases.append(row)
    scale = min(min(286/(hi[0]-lo[0]),218/(hi[1]-lo[1])) for row in cases for _,_,lo,hi in row)
    image = Image.new('RGB',(30+325*len(states),1030),model.BG)
    pen = ImageDraw.Draw(image)
    model.label(image,30,24,title,32,bold=True)
    view_name = '¾ 보기' if angle==38 else '측면 보기'
    model.label(image,32,78,f'{view_name} · 둥근 눈 기준 · 같은 배율 · 기본형과 눈·입 동작 비교',18,model.MUTED)
    for i,(_,name) in enumerate(states):
        model.label(image,32+i*325,130,name,20,bold=True)
    for row_index,(row,name) in enumerate(zip(cases,model.NAMES)):
        top = 172+row_index*273
        pen.line((25,top,image.width-25,top),fill=model.LINE)
        model.label(image,30,top+12,name,20,bold=True)
        lo = np.min([case[2] for case in row],axis=0)
        hi = np.max([case[3] for case in row],axis=0)
        center = np.array([170,top+151])-(lo+hi)/2*np.array([scale,-scale])
        for col,(v,c,_,_) in enumerate(row):
            model.paint(image,v,c,center+[col*325,0],scale)
    model.label(image,32,1002,'정적 동작 시안 · 턱 각도는 제작값 · 사용자 검토 대기',15,model.MUTED)
    return image,scale


def main():
    heads,evidence = build()
    image,scale = render(heads)
    image.save(HERE/'expressions.png')
    side,side_scale = render(heads,90)
    side.save(HERE/'expressions-side.png')
    rigs,profiles = model.load('B.json')['breeds'],model.load('profiles.json')
    stages = {}
    for breed in model.BREEDS:
        rig = rigs[breed]
        profile = profile_for(rig,profiles[breed],breed)
        base = model.head_features(rig,breed,profile)
        stages[breed] = {}
        for degrees in (4,6,8):
            mesh,_ = mouth(base,rig,profile,degrees*profile['mouth_style'][1])
            if degrees==0:
                mesh = base  # retained closed expression, without a cut-line overlay
            stages[breed][degrees] = [(v*HEAD_SCALE,c) for v,c in mesh]
    jaw,_ = render(stages,38,[(4,'A · 작게'),(6,'B · 중간'),(8,'C · 조금 더')],
                   '입 단순화 · 같은 형태, 벌림만 비교')
    jaw.save(HERE/'mouth-options.png')
    inputs = [HERE/'preview.py',SOURCE/'preview.py',round_heads.BASE/'preview.py',
              model.HERE/'preview.py',model.HERE/'B.json',model.HERE/'profiles.json',round_heads.base.STYLE_PATH]
    recipe = dict(states=STATES,head_scale=HEAD_SCALE,primary_camera=38,side_camera=90,
                  comparison_camera=38,comparison_degrees=[4,6,8],
                  mouth_style=MOUTH_STYLE,
                  pixels_per_unit=scale,side_pixels_per_unit=side_scale,evidence=evidence,
                  input_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                  image_sha256={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in ['expressions.png','expressions-side.png','mouth-options.png']},
                  classification='authored static action examples; not measured anatomy or affect inference',status='USER_REVIEW_PENDING')
    (HERE/'recipe.json').write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
