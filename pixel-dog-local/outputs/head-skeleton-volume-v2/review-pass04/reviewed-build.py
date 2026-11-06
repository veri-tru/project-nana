"""Authored canine skeletal support volumes. Anatomy-informed, not a CT replica."""
from pathlib import Path
import json,pickle,sys
import numpy as np
from scipy.interpolate import PchipInterpolator,CubicSpline
from scipy.ndimage import gaussian_filter
from skimage.measure import marching_cubes
from PIL import Image,ImageDraw,ImageFont
from raster import paint

HERE=Path(__file__).resolve().parent
BREEDS=['golden','whippet','dachshund','maltipoo'];NAMES=['골든 리트리버','휘핏','닥스훈트','말티푸']
BG=(248,247,242);INK=(38,54,48)
COLORS={'cranium':(160,179,184),'rostrum':(204,182,130),'arch':(149,177,163),'mandible':(192,135,112),'cartilage':(145,154,189)}
FONT='C:/Windows/Fonts/malgun.ttf';BOLD='C:/Windows/Fonts/malgunbd.ttf'
STEP=.65

def smoothmin(a,b,k=.8):
    h=np.clip(.5+.5*(b-a)/k,0,1);return b*(1-h)+a*h-k*h*(1-h)

def ellipsoid(q,c,r):
    v=(q-np.array(c))/np.array(r);a=np.linalg.norm(v,axis=-1);b=np.linalg.norm(v/np.array(r),axis=-1)
    return a*(a-1)/np.maximum(b,1e-7)

def capsule(q,a,b,r):
    a=np.array(a);b=np.array(b);d=b-a;t=np.clip(np.sum((q-a)*d,axis=-1)/np.dot(d,d),0,1)
    return np.linalg.norm(q-a-t[...,None]*d,axis=-1)-r

def sweep(q,points,radii):
    points=np.asarray(points,float);r=np.asarray(radii,float);scaled=q/r;f=np.full(q.shape[:-1],1e4)
    for a,b in zip(points[:-1]/r,points[1:]/r):f=np.minimum(f,capsule(scaled,a,b,1.)*r.min())
    return f

def curved(points,count=18,closed=False):
    pts=np.asarray(points,float)
    if closed:pts=np.vstack([pts,pts[0]])
    t=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))]
    return (CubicSpline(t,pts,bc_type='periodic') if closed else PchipInterpolator(t,pts,axis=0))(np.linspace(0,t[-1],count,endpoint=not closed))

def shaped_sweep(q,points,front,middle,rear):
    f=np.full(q.shape[:-1],1e4)
    for i,(a,b) in enumerate(zip(points[:-1],points[1:])):
        delta=b-a;u=np.clip(np.sum((q-a)*delta,axis=-1)/np.dot(delta,delta),0,1)
        t=((i+u)/(len(points)-1))[...,None]
        r=np.array(middle)+(np.array(front)-middle)*(1-t)**4+(np.array(rear)-middle)*t**4
        distance=(np.linalg.norm((q-a-u[...,None]*delta)/r,axis=-1)-1)*r.min(axis=-1)
        f=np.minimum(f,distance)
    return f

def polygon_sdf(x,y,poly):
    """Signed 2D distance to a closed non-convex polygon."""
    inside=np.zeros(x.shape,bool);dist=np.full(x.shape,1e9)
    for a,b in zip(poly,np.roll(poly,-1,axis=0)):
        v=b-a;t=np.clip(((x-a[0])*v[0]+(y-a[1])*v[1])/np.dot(v,v),0,1)
        dist=np.minimum(dist,np.hypot(x-a[0]-t*v[0],y-a[1]-t*v[1]))
        crosses=(a[1]>y)!=(b[1]>y)
        if abs(b[1]-a[1])>1e-9:inside^=crosses & (x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0])
    return np.where(inside,-dist,dist)

def params(p):
    d=np.array(p['dorsal'],float);w=np.array(p['widths']);W=w[0];H=d[0,1]-3.5
    return dict(d=d,w=w,W=W,H=H,hinge=np.array([p['hinge_x'],10.,0]),
                wall=max(1.3,W*.085),arch_radius=max(1.6,W*.10),arch_offset=W*.27,
                temporal_inset=W*.22,body_height=H*.19,body_thickness=max(1.4,W*.075),
                ramus_thickness=max(1.6,W*.09),condyle_radius=2.1,coronoid_rise=H*.36)

def fields(p):
    a=params(p);d,w,W,H=a['d'],a['w'],a['W'],a['H'];hx=a['hinge'][0];zhinge=W*.8
    xs=np.array([d[4,0]-1,d[3,0],d[2,0],d[2,0]+9,d[2,0]+19])
    roofs=np.array([d[4,1],d[3,1],d[2,1],d[1,1]-2,d[1,1]-3])
    widths=np.array([w[4]*.70,w[3]*.88,w[2]*.82,w[1]*.60,2.5])
    roof=PchipInterpolator(xs,roofs);width=PchipInterpolator(xs,widths)
    floor=PchipInterpolator(xs,[3.5,3.5,3.5,4.5,9.])
    archpaths=[];ramus_polys=[];bodypaths=[]
    for sign in (-1,1):
        archpaths.append(curved([[d[2,0]+5,11,sign*widths[2]],
          [d[1,0]-3,9,sign*W*.98],[d[1,0]+5,8.5,sign*(W+a['arch_offset'])],
          [hx,11,sign*(W+a['arch_offset']*.85)],[hx+6,15,sign*W*.68]]))
        bodypaths.append(curved([[d[4,0]+2,-2,0],[d[4,0]+5,-2,sign*w[4]*.70],
          [d[3,0],-2.5,sign*w[3]*.82],[d[2,0]+7,-3,sign*w[2]*.83],[hx-5,-1,sign*zhinge]]))
    ramus=curved([[hx-18,-4],[hx-17,2],[hx-15,10],[hx-13,10+a['coronoid_rise']*.95],
                  [hx-10,10+a['coronoid_rise']],[hx-6,10+a['coronoid_rise']*.78],
                  [hx-3,12],[hx-3.5,9],[hx-1.5,5],[hx-1,0],[hx+2,-3],[hx-3,-6],[hx-12,-6]],56,True)
    def rostrum(q):
        x,y,z=np.moveaxis(q,-1,0);xc=np.clip(x,xs[0],xs[-1]);top=roof(xc);ww=width(xc);bottom=floor(xc)
        def section(top,bottom,ww):
            roofline=top-(top-bottom)*.48*(np.abs(z)/ww)**1.65
            return -smoothmin(smoothmin(-(bottom-y),-(y-roofline),.6),-(np.abs(z)-ww),.6)
        outer=section(top,bottom,ww)
        outer=-smoothmin(-outer,-np.maximum(xs[0]-x,x-xs[-1]),.5)
        wall=a['wall']*(.7+.3*np.clip((x-xs[0])/10,0,1))
        inner=section(top-wall,bottom+wall,np.maximum(.5,ww-wall))
        inner=np.maximum(inner,x-(xs[-1]-3))
        shell=np.maximum(outer,-inner)
        # Incisive U below the nasal aperture, continuous with the palate/walls.
        t=np.linspace(0,np.pi,17);inc=np.column_stack([xs[0]+1.8-2.5*np.sin(t),np.full_like(t,4.),widths[0]*.86*np.cos(t)])
        shell=smoothmin(shell,sweep(q,inc,[1.3,1.2,1.25]),.8)
        return shell
    def recess(q):
        f=np.full(q.shape[:-1],1e4)
        for sign in (-1,1):
            orbit=ellipsoid(q,[d[1,0]+2,19,sign*W*.91],[8.0,8.3,W*.43])
            temporal=ellipsoid(q,[hx-1,16,sign*(W+1)],[13,13,W*.58])
            f=smoothmin(f,smoothmin(orbit,temporal,.5),.5)
        return f
    def cranial(q):
        x,y,z=np.moveaxis(q,-1,0)
        cx=np.array([d[2,0]-4,d[2,0],d[1,0],d[0,0],1.,5.])
        ct=np.array([d[2,1]-1,d[2,1],d[1,1],d[0,1],d[0,1]*.75,18.])
        cb=np.array([7.,6.,7.,9.,10.,17.9]);cw=np.array([3.,w[2]*.7,w[1]*.82,W,10.,.1])
        xc=np.clip(x,cx[0],cx[-1]);top=PchipInterpolator(cx,ct)(xc);bottom=PchipInterpolator(cx,cb)(xc);ww=PchipInterpolator(cx,cw)(xc)
        cap=np.sqrt(np.clip(1-((x-1)/4)**2,0,1))
        cap_top=d[0,1]*.75;cap_mid=(cap_top+10)/2;cap_ry=(cap_top-10)/2
        top=np.where(x>1,cap_mid+cap_ry*cap,top);bottom=np.where(x>1,cap_mid-cap_ry*cap,bottom);ww=np.where(x>1,np.maximum(.05,10*cap),ww)
        cy=(top+bottom)/2;hh=np.maximum(.05,(top-bottom)/2)
        f=(np.sqrt(((y-cy)/hh)**2+(z/ww)**2)-1)*np.minimum(hh,ww)
        return np.maximum(f,np.maximum(cx[0]-x,x-cx[-1]))
    def arches(q):
        f=np.full(q.shape[:-1],1e4)
        for path,sign in zip(archpaths,(-1,1)):
            f=smoothmin(f,shaped_sweep(q,path,[2.8,3.6,2.3],[1.9,1.65,1.5],[2.8,3.4,2.4]),.7)
            # Temporal buttress ends above the condyle, not in its moving volume.
            but=sweep(q,[[hx+5,17,sign*W*.5],[hx+4,16,sign*zhinge],[hx,15.0,sign*zhinge]],[2.7,2.4,2.8])
            f=smoothmin(f,but,.6)
        return f
    def upper(q):
        base=np.maximum(smoothmin(cranial(q),rostrum(q),1.0),-recess(q))
        f=smoothmin(base,arches(q),.9)
        for sign in (-1,1):
            f=np.maximum(f,-ellipsoid(q,[hx,10,sign*zhinge],[2.7,2.7,3.5]))
        return f
    def jaw(q):
        x,y,z=np.moveaxis(q,-1,0);f=np.full(x.shape,1e4)
        for path,sign in zip(bodypaths,(-1,1)):
            body=shaped_sweep(q,path,[1.7,a['body_height']*.40,a['body_thickness']],
                             [2.,a['body_height']*.52,a['body_thickness']],
                             [2.5,a['body_height']*.95,a['body_thickness']*1.15])
            # Broad rounded ramus plate, with high coronoid and separate posterior condyle.
            sd=polygon_sdf(x,y,ramus);zz=np.abs(z-sign*zhinge)-a['ramus_thickness']/2
            plate=np.maximum(sd,zz)+np.linalg.norm(np.maximum(np.stack([sd,zz],axis=-1),0),axis=-1)-np.maximum(np.maximum(sd,zz),0)-.6
            condyle=ellipsoid(q,[hx,10,sign*zhinge],[a['condyle_radius'],a['condyle_radius'],3.0])
            neck=capsule(q,[hx-3,9,sign*zhinge],[hx,10,sign*zhinge],1.6)
            f=smoothmin(f,smoothmin(smoothmin(body,plate,1.2),smoothmin(condyle,neck,.5),.5),.7)
        return f
    def cartilage(q):
        # Generic attachment volume; the shared finished nasal leather is not rebuilt here.
        center=[(d[4,0]+d[5,0])/2,d[5,1],0]
        return ellipsoid(q,center,[abs(d[5,0]-d[4,0])/2+.15,3.0,w[4]*.85])
    a.update(rostral_x=xs.tolist(),rostral_widths=widths.tolist(),arch_paths=[v.tolist() for v in archpaths],body_paths=[v.tolist() for v in bodypaths],ramus_polygon=ramus.tolist())
    return dict(cranial=cranial,rostrum=rostrum,arches=arches,upper=upper,jaw=jaw,cartilage=cartilage),a

def extract(field,bounds,step=STEP):
    axes=[np.arange(lo,hi+step,step) for lo,hi in bounds]
    q=np.stack(np.meshgrid(*axes,indexing='ij'),axis=-1)
    val=gaussian_filter(field(q).astype(np.float32),.5)
    v,f,n,_=marching_cubes(val,0,spacing=(step,)*3,allow_degenerate=False)
    v+=np.array([b[0] for b in bounds]);return v,f,-n

REGIONS={1:'cranial_vault',2:'frontal_support',3:'nasal_roof',4:'maxillary_sidewall',5:'hard_palate',6:'incisive_region',7:'zygomatic_arch',8:'temporal_articular_support',9:'mandibular_body',10:'ramus',11:'coronoid_process',12:'condylar_process',13:'nasal_cartilage'}

def ambient_occlusion(v,n,field,mask):
    # Actual geometry probes in the outward hemisphere, not a painted opening.
    ao=np.ones(len(v));q=v[mask];nn=n[mask]
    tangent=np.cross(nn,np.array([0.,1.,0.]));bad=np.linalg.norm(tangent,axis=1)<.1
    tangent[bad]=np.cross(nn[bad],np.array([1.,0.,0.]));tangent/=np.maximum(1e-8,np.linalg.norm(tangent,axis=1)[:,None])
    bitangent=np.cross(nn,tangent);occlusion=np.zeros(len(q))
    for dx,dy in [(0,0),(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1)]:
        ray=nn*.60+tangent*dx+bitangent*dy;ray/=np.linalg.norm(ray,axis=1)[:,None]
        hit=np.zeros(len(q),bool)
        for distance in [1.2,4.,9.,16.]:hit|=field(q+ray*distance)<-.2
        occlusion+=hit
    ao[mask]=1-.62*occlusion/7
    return ao

def build_one(p):
    ff,a=fields(p);d=a['d'];W=a['W'];bounds=[(d[5,0]-3,8),(-10,d[0,1]+5),(-W*1.55,W*1.55)]
    v,f,n=extract(ff['upper'],bounds)
    dist=np.stack([ff[k](v) for k in ['cranial','rostrum','arches']],axis=-1)
    owner=np.argmin(dist,axis=1);x,y,z=v.T;region=np.where(x>d[1,0]+4,1,2)
    region=np.where(owner==1,4,region)
    region=np.where((owner==1)&(x<d[2,0]+2)&(y>3.5+(np.interp(x,d[4:1:-1,0],d[4:1:-1,1])-3.5)*.65),3,region)
    region=np.where((owner==1)&(y<6.0),5,region)
    region=np.where((owner==1)&(x<d[4,0]+5),6,region)
    region=np.where((owner==1)&(x>d[2,0]+2)&(y>18),2,region)
    region=np.where(owner==2,np.where(x>a['hinge'][0]+1,8,7),region)
    colors=np.array([COLORS['cranium'] if r in (1,2) else COLORS['arch'] if r in (7,8) else COLORS['rostrum'] for r in region])
    ao=ambient_occlusion(v,n,ff['upper'],x<d[2,0]+10)
    upper=dict(v=v,f=f,n=n,c=colors,ao=ao,region=region.astype(np.uint8))
    parts={'upper':upper}
    for key,material in [('jaw','mandible'),('cartilage','cartilage')]:
        v,f,n=extract(ff[key],bounds)
        region=np.full(len(v),13,dtype=np.uint8)
        if key=='jaw':
            x,y,z=v.T;hx=a['hinge'][0];region[:]=9
            region[(x>hx-12)&(y>2)]=10;region[(x<hx-2)&(y>14)]=11
            for sign in (-1,1):region[np.linalg.norm((v-[hx,10,sign*W*.8])/[2.6,2.6,3.6],axis=1)<1.1]=12
        parts[key]=dict(v=v,f=f,n=n,c=np.tile(COLORS[material],(len(v),1)),ao=np.ones(len(v)),region=region)
    return dict(parts=parts,parameters=a,profile=p)

def rotate(v,hinge,degrees):
    t=np.radians(degrees);r=np.array([[np.cos(t),-np.sin(t),0],[np.sin(t),np.cos(t),0],[0,0,1]])
    return (v-hinge)@r.T+hinge

def projected(model,az=90,el=0,angle=0,nose=False,mono=False,jaw_only=False,joint_cut=False):
    t,e=np.radians([az,el]);right=np.array([np.sin(t),0,np.cos(t)])
    front=np.array([-np.cos(t)*np.cos(e),np.sin(e),np.sin(t)*np.cos(e)])
    up=np.cross(front,right);view=np.column_stack([right,up,front]);qq=[];cc=[]
    for key,part in model['parts'].items():
        if jaw_only and key!='jaw':continue
        if key=='cartilage' and not nose:continue
        v,n=part['v'],part['n']
        if key=='jaw':v=rotate(v,model['parameters']['hinge'],angle);n=rotate(n,np.zeros(3),angle)
        verts=v@view;norm=n@view;light=np.array([-.35,.72,.6]);shade=.70+.28*np.maximum(0,norm@light)+.05*np.maximum(0,norm[:,1])
        c=np.tile([203,199,185],(len(v),1)) if mono else part['c'];rgba=np.clip(c*(shade*part['ao'])[:,None],0,255)
        faces=part['f']
        if joint_cut:
            centers=v[faces].mean(1);hx=model['parameters']['hinge'][0];zz=model['parameters']['W']*.8
            mask=(np.abs(centers[:,0]-hx)<8)&(centers[:,1]>3)&(centers[:,1]<21)&(np.abs(centers[:,2]-zz)<5)
            faces=faces[mask]
        ix=faces[:,[0,1,2,2]];qq.append(verts[ix]);cc.append(rgba[ix])
    return np.concatenate(qq),np.concatenate(cc)

def label(im,x,y,s,size=20,bold=False,color=INK):
    ImageDraw.Draw(im).text((x,y),s,font=ImageFont.truetype(BOLD if bold else FONT,size),fill=color)

def render_cell(im,model,box,az,el=0,angle=0,nose=False,mono=False,scale=3.5,jaw_only=False,joint_cut=False):
    q,c=projected(model,az,el,angle,nose,mono,jaw_only,joint_cut);lo=q[:,:,:2].min((0,1));hi=q[:,:,:2].max((0,1));l,t,r,b=box
    if joint_cut:
        aa,ee=np.radians([az,el]);rr=np.array([np.sin(aa),0,np.cos(aa)]);ff=np.array([-np.cos(aa)*np.cos(ee),np.sin(ee),np.sin(aa)*np.cos(ee)]);uu=np.cross(ff,rr)
        center3=model['parameters']['hinge']+np.array([0,3,model['parameters']['W']*.8]);center2=np.array([center3@rr,center3@uu]);lo=hi=center2
    center=np.array([(l+r)/2,(t+b)/2])-(lo+hi)/2*np.array([scale,-scale]);paint(im,q,c,center,scale)

def overview(models):
    im=Image.new('RGB',(1840,1550),BG);d=ImageDraw.Draw(im)
    label(im,30,23,'머리 골격 · 입체 지지 구조',32,True)
    label(im,30,76,'짧아진 주둥이 길이 유지 · 같은 3D 형상의 측면 / 사선 / 정면 / 윗면',20)
    label(im,30,110,'해부 자료를 참고한 단순화 구조입니다. 품종별 CT 복제·치열·털 외피는 포함하지 않습니다.',17)
    for j,title in enumerate(['측면','사선','정면','윗면']):label(im,35+460*j,160,title,21,True)
    for i,(b,name) in enumerate(zip(BREEDS,NAMES)):
        y=204+i*315;d.line((25,y,1815,y),fill='#d5dcd6');label(im,30,y+8,name,21,True)
        for j,(az,el) in enumerate([(90,0),(48,10),(0,0),(90,90)]):render_cell(im,models[b],(25+j*460,y+45,450+j*460,y+290),az,el,scale=3.6)
    label(im,30,1482,'청회색 두개부   황토색 비골·위턱   녹회색 광대활·관절 받침   갈색 아래턱',19)
    label(im,30,1517,'코연골은 골성 구조와 분리해 상세판에서 확인합니다. 색 경계는 설명용이며 실제 봉합선 복제가 아닙니다.',16)
    return im

def motion(models):
    im=Image.new('RGB',(1840,1130),BG);d=ImageDraw.Draw(im)
    label(im,30,22,'턱 몸통에서 턱관절까지',31,True);label(im,30,75,'같은 아래턱 전체를 0° / 10° / 20° 회전 · 위턱과 두개부 고정 · 치열·교합은 미모델링',19)
    for j,name in enumerate(NAMES):label(im,30+j*460,120,name,21,True)
    for i,angle in enumerate([0,10,20]):
        y=164+i*300;d.line((25,y,1815,y),fill='#d5dcd6');label(im,30,y+9,f'{angle}°',19,True)
        for j,b in enumerate(BREEDS):render_cell(im,models[b],(20+j*460,y+32,450+j*460,y+275),70,4,angle,scale=3.6)
    label(im,30,1080,'하악체·상행지·근돌기·관절돌기는 한 강체입니다. 코끝이나 입꼬리를 회전축으로 쓰지 않습니다.',18)
    return im

def detail(models):
    im=Image.new('RGB',(1600,1150),BG);d=ImageDraw.Draw(im);g=models['golden']
    label(im,30,22,'연결부와 빈 공간 · 골든 기준 구조',31,True)
    label(im,30,77,'좌: 골성 구조 / 우: 코연골 부착 영역 포함 · 실물 치수 대신 제작용 비율을 사용했습니다.',18)
    for j,(title,az,el,nose) in enumerate([('측면 · 위턱과 하악 상행지',90,0,False),('사선 · 코연골 부착',48,8,True),('윗면 · 광대활 안쪽 공간',90,90,False),('정면 · 비강 입구와 구강 공간',0,0,False)]):
        col=j%2;row=j//2;y=135+row*455;label(im,30+800*col,y,title,21,True)
        render_cell(im,g,(20+800*col,y+45,780+800*col,y+420),az,el,angle=14 if j==3 else 0,nose=nose,scale=6.5)
    label(im,30,1070,'코연골 영역(보라)은 위턱 앞에 붙습니다. 눈구멍의 바깥 위쪽을 닫힌 뼈 고리로 만들지 않았습니다.',18)
    label(im,30,1110,'정수리·이마·콧등의 기준점은 이전 단축안에서 유지했으며, 뼈 두께와 돌출은 새 제작 변수입니다.',17)
    return im

def jaw_detail(models):
    im=Image.new('RGB',(1600,1440),BG);d=ImageDraw.Draw(im)
    label(im,30,22,'아래턱 단독 · 몸통 / 상행지 / 근돌기 / 관절돌기',29,True)
    label(im,30,78,'진단을 위해 위턱을 숨겼습니다. 원래 아래턱 형상을 그대로 세 방향에서 봅니다.',18)
    for j,title in enumerate(['측면','뒤쪽 사선','윗면']):label(im,35+530*j,125,title,21,True)
    for i,(b,name) in enumerate(zip(BREEDS,NAMES)):
        y=175+i*300;d.line((25,y,1575,y),fill='#d5dcd6');label(im,30,y+9,name,21,True)
        for j,(az,el) in enumerate([(90,0),(135,18),(90,90)]):render_cell(im,models[b],(20+j*530,y+40,510+j*530,y+280),az,el,scale=4.4,jaw_only=True)
    label(im,30,1395,'높은 근돌기와 뒤쪽 관절돌기를 분리하고, 좌우 하악체 사이 구강 공간을 유지합니다.',18)
    return im

def joint_detail(models):
    im=Image.new('RGB',(1840,1120),BG);dr=ImageDraw.Draw(im)
    label(im,30,22,'왼쪽 턱관절 · 같은 위치에서 개폐 확인',30,True)
    label(im,30,75,'관절 주변만 남긴 절개 보기 · 원본 표면 유지 / 절개면 미봉합 · 위턱 받침과 아래턱 관절돌기',18)
    for j,name in enumerate(NAMES):label(im,30+j*460,120,name,21,True)
    for i,angle in enumerate([0,10,20]):
        y=165+i*290;dr.line((25,y,1815,y),fill='#d5dcd6');label(im,30,y+10,f'{angle}°',19,True)
        for j,b in enumerate(BREEDS):render_cell(im,models[b],(20+j*460,y+30,450+j*460,y+270),145,-12,angle,scale=10,joint_cut=True)
    label(im,30,1060,'세 행은 동일 관절 중심·배율입니다. 절개 경계의 열린 면은 진단용 표시이며 원본 뼈 표면의 구멍이 아닙니다.',17)
    return im

def boards(models):return {'structure.png':overview(models),'jaw-motion.png':motion(models),'structure-detail.png':detail(models),'jaw-detail.png':jaw_detail(models),'joint-detail.png':joint_detail(models)}

def main():
    profiles=json.loads((HERE/'profiles.json').read_text(encoding='utf-8'))
    models={}
    for b in BREEDS:models[b]=build_one(profiles[b]);print('Built',b,flush=True)
    with (HERE/'geometry.pkl').open('wb') as f:pickle.dump(models,f)
    for b,m in models.items():
        arrays={f'{key}_{name}':part[name] for key,part in m['parts'].items() for name in ['v','f','n','region']}
        np.savez_compressed(HERE/(b+'-regions.npz'),**arrays)
    (HERE/'regions.json').write_text(json.dumps(REGIONS,indent=2),encoding='utf-8')
    (HERE/'parameters.json').write_text(json.dumps({b:{k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in m['parameters'].items()} for b,m in models.items()},ensure_ascii=False,indent=2),encoding='utf-8')
    for name,im in boards(models).items():im.save(HERE/name);print('Saved',name,flush=True)

if __name__=='__main__':main()
