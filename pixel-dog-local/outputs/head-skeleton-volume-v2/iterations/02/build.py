"""Authored canine skeletal support volumes. Anatomy-informed, not a CT replica."""
from pathlib import Path
import json,pickle,sys
import numpy as np
from scipy.interpolate import PchipInterpolator,CubicSpline
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
        t=(i+.5)/(len(points)-1)
        r=np.array(middle)+(np.array(front)-middle)*(1-t)**4+(np.array(rear)-middle)*t**4
        f=smoothmin(f,sweep(q,[a,b],r),.6)
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
    ramus=curved([[hx-10,-3],[hx-9,7],[hx-7,10+a['coronoid_rise']],
                  [hx-4,10+a['coronoid_rise']*.86],[hx-3,12],[hx-3.5,9],
                  [hx-1.5,5],[hx-1,0],[hx+2,-3],[hx-3,-5],[hx-7,-4]],48,True)
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
            temporal=ellipsoid(q,[hx-1,16,sign*(W+1)],[12,13,W*.48])
            f=smoothmin(f,smoothmin(orbit,temporal,.5),.5)
        return f
    def cranial(q):
        x,y,z=np.moveaxis(q,-1,0)
        cx=np.array([d[2,0]-4,d[2,0],d[1,0],d[0,0],1.,5.])
        ct=np.array([d[2,1]-1,d[2,1],d[1,1],d[0,1],d[0,1]*.75,18.])
        cb=np.array([7.,6.,7.,9.,10.,17.9]);cw=np.array([3.,w[2]*.7,w[1]*.82,W,10.,.1])
        xc=np.clip(x,cx[0],cx[-1]);top=PchipInterpolator(cx,ct)(xc);bottom=PchipInterpolator(cx,cb)(xc);ww=PchipInterpolator(cx,cw)(xc)
        cy=(top+bottom)/2;hh=np.maximum(.05,(top-bottom)/2)
        f=(np.sqrt(((y-cy)/hh)**2+(z/ww)**2)-1)*np.minimum(hh,ww)
        return np.maximum(f,np.maximum(cx[0]-x,x-cx[-1]))
    def arches(q):
        f=np.full(q.shape[:-1],1e4)
        for path,sign in zip(archpaths,(-1,1)):
            f=smoothmin(f,shaped_sweep(q,path,[2.8,3.6,2.3],[1.9,1.65,1.5],[2.8,3.4,2.4]),.7)
            # Temporal buttress ends above the condyle, not in its moving volume.
            but=sweep(q,[[hx+5,17,sign*W*.5],[hx+4,14,sign*zhinge],[hx,13.2,sign*zhinge]],[2.7,2.4,2.8])
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
                             [2.5,a['body_height']*.72,a['body_thickness']*1.15])
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
    val=field(q).astype(np.float32)
    v,f,n,_=marching_cubes(val,0,spacing=(step,)*3,allow_degenerate=False)
    v+=np.array([b[0] for b in bounds]);return v,f,-n

def build_one(p):
    ff,a=fields(p);d=a['d'];W=a['W'];bounds=[(d[5,0]-3,8),(-10,d[0,1]+5),(-W*1.55,W*1.55)]
    v,f,n=extract(ff['upper'],bounds)
    dist=np.stack([ff[k](v) for k in ['cranial','rostrum','arches']],axis=-1)
    palette=np.array([COLORS[k] for k in ['cranium','rostrum','arch']]);colors=palette[np.argmin(dist,axis=1)]
    upper=dict(v=v,f=f,n=n,c=colors)
    parts={'upper':upper}
    for key,material in [('jaw','mandible'),('cartilage','cartilage')]:
        v,f,n=extract(ff[key],bounds);parts[key]=dict(v=v,f=f,n=n,c=np.tile(COLORS[material],(len(v),1)))
    return dict(parts=parts,parameters=a,profile=p)

def rotate(v,hinge,degrees):
    t=np.radians(degrees);r=np.array([[np.cos(t),-np.sin(t),0],[np.sin(t),np.cos(t),0],[0,0,1]])
    return (v-hinge)@r.T+hinge

def projected(model,az=90,el=0,angle=0,nose=False,mono=False):
    t,e=np.radians([az,el]);right=np.array([np.sin(t),0,np.cos(t)])
    front=np.array([-np.cos(t)*np.cos(e),np.sin(e),np.sin(t)*np.cos(e)])
    up=np.cross(front,right);view=np.column_stack([right,up,front]);qq=[];cc=[]
    for key,part in model['parts'].items():
        if key=='cartilage' and not nose:continue
        v,n=part['v'],part['n']
        if key=='jaw':v=rotate(v,model['parameters']['hinge'],angle);n=rotate(n,np.zeros(3),angle)
        verts=v@view;norm=n@view;light=np.array([-.35,.72,.6]);shade=.70+.28*np.maximum(0,norm@light)+.05*np.maximum(0,norm[:,1])
        c=np.tile([203,199,185],(len(v),1)) if mono else part['c'];rgba=np.clip(c*shade[:,None],0,255)
        ix=part['f'][:,[0,1,2,2]];qq.append(verts[ix]);cc.append(rgba[ix])
    return np.concatenate(qq),np.concatenate(cc)

def label(im,x,y,s,size=20,bold=False,color=INK):
    ImageDraw.Draw(im).text((x,y),s,font=ImageFont.truetype(BOLD if bold else FONT,size),fill=color)

def render_cell(im,model,box,az,el=0,angle=0,nose=False,mono=False,scale=3.5):
    q,c=projected(model,az,el,angle,nose,mono);lo=q[:,:,:2].min((0,1));hi=q[:,:,:2].max((0,1));l,t,r,b=box
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

def boards(models):return {'structure.png':overview(models),'jaw-motion.png':motion(models),'structure-detail.png':detail(models)}

def main():
    profiles=json.loads((HERE/'profiles.json').read_text(encoding='utf-8'))
    models={}
    for b in BREEDS:models[b]=build_one(profiles[b]);print('Built',b,flush=True)
    with (HERE/'geometry.pkl').open('wb') as f:pickle.dump(models,f)
    (HERE/'parameters.json').write_text(json.dumps({b:{k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in m['parameters'].items()} for b,m in models.items()},ensure_ascii=False,indent=2),encoding='utf-8')
    for name,im in boards(models).items():im.save(HERE/name);print('Saved',name,flush=True)

if __name__=='__main__':main()
