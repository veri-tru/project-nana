"""Neutral exterior candidates fitted to reviewed skeletal surfaces.

Bone meshes are actual inputs; authored tissue/coat offsets are not measurements.
No pose training, pixel conversion, or mouth animation is performed here.
"""
from pathlib import Path
import importlib.util,json,pickle,sys,hashlib
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter1d,gaussian_filter
from skimage.measure import marching_cubes
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'head-skeleton-volume-v2'
sys.path.insert(0,str(SOURCE))
spec=importlib.util.spec_from_file_location('reviewed_bone_builder',SOURCE/'build.py')
bones=importlib.util.module_from_spec(spec);spec.loader.exec_module(bones)
from raster import paint
BREEDS=bones.BREEDS;NAMES=bones.NAMES
VARIANTS={'A':3.2,'B':4.6,'C':6.0}
STEP=.65
BG=(248,247,242);INK=(38,54,48)
PALETTE={'golden':([220,174,109],[175,127,75]),'whippet':([178,156,134],[131,108,90]),'dachshund':([173,105,65],[126,69,43]),'maltipoo':([237,225,203],[216,198,167])}
TISSUE={'golden':1.,'whippet':.55,'dachshund':.72,'maltipoo':1.5}
NOSE_SIZE={'golden':5.4,'whippet':3.8,'dachshund':4.6,'maltipoo':4.1}
EYE_SIZE={'golden':3.7,'whippet':3.1,'dachshund':3.35,'maltipoo':4.8}

def load_inputs():
    status=json.loads((SOURCE/'review-status.json').read_text('utf-8'))
    if status['delivery']!='READY':raise ValueError('Reviewed skeletal candidate required')
    return pickle.loads((SOURCE/'geometry.pkl').read_bytes())

def ellipsoid(q,c,r):return bones.ellipsoid(q,c,r)
def union(a,b,k=2.):return bones.smoothmin(a,b,k)

def sections(skel,b,fullness):
    """Enclosing longitudinal ellipses from actual upper + lower bone vertices."""
    p=skel['profile'];d=np.array(p['dorsal']);W=p['widths'][0]
    points=np.concatenate([skel['parts'][k]['v'] for k in ['upper','jaw']])
    pad=fullness*TISSUE[b]
    xs=np.linspace(points[:,0].min()-.35,points[:,0].max()+.35,47)
    records=[]
    for x in xs:
        local=points[np.abs(points[:,0]-x)<2.2]
        if not len(local):local=points[np.argsort(np.abs(points[:,0]-x))[:80]]
        crown=(.5+.5*np.clip((x-d[2,0])/(d[0,0]-d[2,0]),0,1))
        top=local[:,1].max()+2+pad*crown
        bottom=local[:,1].min()-1.6-pad*.22
        cy=(top+bottom)/2;ry=(top-bottom)/2
        ratio=np.sqrt(np.clip(1-((local[:,1]-cy)/ry)**2,.02,1))
        width=np.max(np.abs(local[:,2])/ratio)+1.5+pad*.35
        records.append([cy,ry,width])
    a=gaussian_filter1d(np.array(records),1.1,axis=0)
    # Sampling/smoothing reserve keeps real support surfaces beneath the coat.
    a[:,1]+=.7;a[:,2]+=.7
    return dict(xs=xs,cy=a[:,0],ry=a[:,1],width=a[:,2],pad=pad,points=points)

def make_fields(skel,b,variant):
    p=skel['profile'];d=np.array(p['dorsal']);W=p['widths'][0];s=sections(skel,b,VARIANTS[variant])
    interpolation={k:PchipInterpolator(s['xs'],s[k]) for k in ['cy','ry','width']}
    front=s['xs'][0];rear=s['xs'][-1]
    # Same nasal template, isotropic individual scale. It is united with the skin.
    size=NOSE_SIZE[b];nc=np.array([d[5,0]+size*.75,d[5,1]+.5,0.])
    def nose(q):
        v=(q-nc)/size
        w=1.18*(1+.12*np.clip(v[...,1],-1,1))
        return (np.sqrt(v[...,0]**2+(v[...,1]/.70)**2+(v[...,2]/w)**2)-1)*size
    def core(q):
        x,y,z=np.moveaxis(q,-1,0);xc=np.clip(x,front,rear)
        cy=interpolation['cy'](xc);ry=interpolation['ry'](xc);width=interpolation['width'](xc)
        # Rounded end caps, not planar muzzle termination.
        rr=np.where(x<front,np.sqrt(np.clip(1-((x-front)/3.6)**2,0,1)),1.)
        rr=np.where(x>rear,np.sqrt(np.clip(1-((x-rear)/5.)**2,0,1)),rr)
        radial=np.sqrt(((y-cy)/np.maximum(.04,ry*rr))**2+(z/np.maximum(.04,width*rr))**2)
        value=(radial-1)*np.minimum(ry*rr+.04,width*rr+.04)
        value=np.maximum(value,np.maximum(front-3.6-x,x-rear-5.))
        if b=='maltipoo':
            # Low-amplitude coat relief; no polygonal hair spikes.
            coat=.25*np.sin(x*.72+y*.39)*np.sin(z*.77-y*.31)+.15*np.cos(x*.43-z*.61)
            value-=coat
        return union(value,nose(q),2.)
    neck_top=np.array([d[0,0]+10,7.,0.]);neck_bottom=np.array([d[0,0]+18,-21.,0.])
    def neck(q):
        r=W*.64+1.5
        # A thick short cervical volume is embedded beneath the occipital end.
        scaled=q/np.array([1.,1.,1.05])
        value=bones.capsule(scaled,neck_top/np.array([1.,1.,1.05]),neck_bottom/np.array([1.,1.,1.05]),r)
        return np.maximum(value,-21.-q[...,1])
    earpaths=[];earwidths=[]
    if b=='golden':
        pts=[[d[0,0]+2,25,W*.85],[d[0,0]+6,21,W*1.42],[d[0,0]+13,4,W*1.48],[d[0,0]+12,-8,W*1.35]]
        widths=[3.8,8.5,11.,3.8];thick=3.2
    elif b=='whippet':
        pts=[[d[0,0]+3,23,W*.85],[d[0,0]+12,25,W*1.48],[d[0,0]+20,18,W*1.50],[d[0,0]+23,10,W*1.43]]
        widths=[3.,5.3,4.,1.5];thick=2.1
    elif b=='dachshund':
        pts=[[d[0,0]+3,25,W*.90],[d[0,0]+7,17,W*1.52],[d[0,0]+10,-6,W*1.65],[d[0,0]+6,-20,W*1.50]]
        widths=[4.,9.2,11.3,4.];thick=3.3
    else:
        pts=[[d[0,0]+4,26,W*.90],[d[0,0]+12,18,W*1.65],[d[0,0]+13,2,W*1.70],[d[0,0]+7,-5,W*1.52]]
        widths=[4.6,11.4,12.8,4.8];thick=4.6
    for sign in [-1,1]:
        path=np.array(pts,float);path[:,2]*=sign;earpaths.append(path)
    def ears(q):
        result=np.full(q.shape[:-1],1e4)
        for path in earpaths:
            ctr=bones.curved(path,11)
            w=PchipInterpolator(np.linspace(0,1,4),widths)(np.linspace(0,1,11))
            # Overlapping volumetric lobes form an uncreased, thick pinna.
            for c,ww in zip(ctr,w):
                result=union(result,ellipsoid(q,c,[ww,4.7,thick]),1.3)
        return result
    def head(q):return union(core(q),neck(q),5.5)
    def exterior(q):return union(head(q),ears(q),2.0)
    metadata=dict(sections={k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in s.items() if k!='points'},nose_center=nc.tolist(),nose_size=size,ear_paths=[v.tolist() for v in earpaths],ear_widths=widths,ear_thickness=thick,neck_top=neck_top.tolist(),neck_bottom=neck_bottom.tolist(),variant=variant,profile=p)
    return dict(core=core,head=head,neck=neck,ears=ears,nose=nose,exterior=exterior),metadata

def extract(fn,bounds,step=STEP):
    axes=[np.arange(lo,hi+step,step) for lo,hi in bounds]
    q=np.stack(np.meshgrid(*axes,indexing='ij'),axis=-1)
    value=gaussian_filter(fn(q).astype(np.float32),.65)
    v,f,n,_=marching_cubes(value,0,spacing=(step,)*3,allow_degenerate=False)
    v+=np.array([v[0] for v in bounds]);return v,f,-n

def colors(v,ff,b,p):
    body,ear=np.array(PALETTE[b][0],float),np.array(PALETTE[b][1],float)
    c=np.tile(body,(len(v),1));x,y,z=v.T
    earweight=np.clip((ff['head'](v)-ff['ears'](v)+.6)/3,0,1)
    c=c*(1-earweight[:,None])+ear*earweight[:,None]
    if b=='maltipoo':
        variation=.9*np.sin(x*.60+y*.30)*np.sin(z*.65)
        c+=variation[:,None]
    nc=np.array(p['nose_center']);size=p['nose_size']
    # A single continuous skin mesh carries an embedded common nasal material patch.
    nose=(ff['nose'](v)<.55)&(x<nc[0]+size*.05)&(y>nc[1]-size*.70)
    c[nose]=[43,40,34]
    # Shallow curved closed-mouth lip on the surface, ending well before the joint.
    d=np.array(p['profile']['dorsal']);start=d[4,0]+2;end=d[1,0]-1
    t=np.clip((x-start)/(end-start),0,1)
    lip=1.0+1.4*t+.3*np.sin(t*np.pi)
    side=(x>start)&(x<end)&(np.abs(y-lip)<.35)&(np.abs(z)>3)
    c[side]=body*.58
    return c

def eye_mesh(center,normal,r):
    normal=np.array(normal,float);normal/=np.linalg.norm(normal)
    up=np.array([0.,1.,0.]);up-=normal*np.dot(up,normal);up/=np.linalg.norm(up)
    right=np.cross(up,normal)
    def fn(q):
        v=q-center
        return (np.sqrt((v@right/r)**2+(v@up/r)**2+(v@normal/(r*.38))**2)-1)*r*.38
    v,f,n=extract(fn,[(a-r*1.5,a+r*1.5) for a in center],.35)
    u=(v-center)@right/r;vv=(v-center)@up/r
    c=np.tile([36.,29.,21.],(len(v),1))
    iris=(u*u+vv*vv)>.55;c[iris]=[57,43,26]
    highlight=((u+.28)**2+(vv-.32)**2)<.13**2;c[highlight]=[225,216,187]
    return dict(v=v,f=f,n=n,c=c)

def build_one(skel,b,variant):
    ff,meta=make_fields(skel,b,variant);p=skel['profile'];d=np.array(p['dorsal']);W=p['widths'][0]
    bounds=[(d[5,0]-12,28),(-30,d[0,1]+24),(-W*2.4,W*2.4)]
    v,f,n=extract(ff['exterior'],bounds);part=dict(v=v,f=f,n=n,c=colors(v,ff,b,meta))
    parts={'skin':part};eyedata=[]
    for sign in [-1,1]:
        ex=d[1,0]-3;ey=d[1,1]-2.5
        if b=='maltipoo':ex-=1;ey+=.2
        lo=0.;hi=W*2
        for _ in range(28):
            mid=(lo+hi)/2;q=np.array([[ex,ey,sign*mid]])
            if ff['core'](q)[0]<0:lo=mid
            else:hi=mid
        center=np.array([ex,ey,sign*(lo+.10)])
        normal=np.array([-.58,.13,sign*.81])
        parts['eye_'+str(sign)]=eye_mesh(center,normal,EYE_SIZE[b]);eyedata.append(dict(center=center.tolist(),normal=normal.tolist(),radius=EYE_SIZE[b]))
    meta['eyes']=eyedata
    return dict(parts=parts,metadata=meta,breed=b,variant=variant)

def projected(model,az=50,el=6,show_ears=True):
    t,e=np.radians([az,el]);right=np.array([np.sin(t),0,np.cos(t)])
    front=np.array([-np.cos(t)*np.cos(e),np.sin(e),np.sin(t)*np.cos(e)])
    up=np.cross(front,right);view=np.column_stack([right,up,front]);qq=[];cc=[]
    for key,part in model['parts'].items():
        v,n=part['v']@view,part['n']@view
        light=np.array([-.32,.72,.61]);shade=.73+.24*np.maximum(0,n@light)+.035*np.maximum(0,n[:,1])
        c=np.clip(part['c']*shade[:,None],0,255)
        ix=part['f'][:,[0,1,2,2]];qq.append(v[ix]);cc.append(c[ix])
    return np.concatenate(qq),np.concatenate(cc)

def label(im,x,y,text,size=21,bold=False):
    ImageDraw.Draw(im).text((x,y),text,font=ImageFont.truetype(bones.BOLD if bold else bones.FONT,size),fill=INK)

def board(models,variant):
    im=Image.new('RGB',(2400,1500),BG);dr=ImageDraw.Draw(im)
    label(im,32,24,f'{variant} · 골격 기반 개체별 머리',34,True)
    label(im,32,80,{'A':'가벼운 볼륨','B':'중간 볼륨','C':'도톰한 볼륨'}[variant]+' · 같은 골격과 주둥이 길이 / 볼·정수리 외피 두께만 비교',21)
    views=[('측면',90,0),('사선',48,7),('정면',0,0),('후면',180,0),('윗면',90,90)]
    for j,(name,az,el) in enumerate(views):label(im,35+j*480,135,name,22,True)
    for i,(b,name) in enumerate(zip(BREEDS,NAMES)):
        y=180+i*310;dr.line((25,y,2375,y),fill='#d5dcd6');label(im,32,y+10,name,22,True)
        for j,(_,az,el) in enumerate(views):
            q,c=projected(models[variant][b],az,el);lo=q[:,:,:2].min((0,1));hi=q[:,:,:2].max((0,1));scale=3.3
            center=np.array([j*480+240,y+183])-(lo+hi)/2*np.array([scale,-scale]);paint(im,q,c,center,scale)
    label(im,32,1440,'둥근 눈 · 공통 코 형태/개체별 크기 · 두께 있는 귀 · 짧은 목   |   기본 표정 / 픽셀 간략화 전',19)
    return im

def main():
    skels=load_inputs();selected=sys.argv[1:] or list(VARIANTS)
    if any(v not in VARIANTS for v in selected):raise ValueError('Unknown variant')
    models=pickle.loads((HERE/'geometry.pkl').read_bytes()) if (HERE/'geometry.pkl').exists() else {}
    for variant in selected:
        models[variant]={}
        for b in BREEDS:
            models[variant][b]=build_one(skels[b],b,variant);print('Built',variant,b,flush=True)
    with (HERE/'geometry.pkl').open('wb') as f:pickle.dump(models,f)
    (HERE/'parameters.json').write_text(json.dumps({v:{b:m['metadata'] for b,m in row.items()} for v,row in models.items()},ensure_ascii=False,indent=2),'utf-8')
    for variant in selected:board(models,variant).save(HERE/f'heads-{variant}.png');print('Saved',variant,flush=True)
if __name__=='__main__':main()
