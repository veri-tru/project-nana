"""Neutral exterior candidates fitted to reviewed skeletal surfaces.

Bone meshes are actual inputs; authored tissue/coat offsets are not measurements.
No pose training, pixel conversion, or mouth animation is performed here.
"""
from pathlib import Path
import importlib.util,json,pickle,sys,hashlib
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.spatial import ConvexHull
from scipy.ndimage import gaussian_filter1d,gaussian_filter,map_coordinates
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
    expected='eaec7d20d5ea8abbb8a14e728d6120f4f119e2d3ee238d4af5b3836f06e4d154'
    if hashlib.sha256((SOURCE/'geometry.pkl').read_bytes()).hexdigest()!=expected:raise ValueError('Skeletal source changed')
    return pickle.loads((SOURCE/'geometry.pkl').read_bytes())

def ellipsoid(q,c,r):return bones.ellipsoid(q,c,r)
def union(a,b,k=2.):return bones.smoothmin(a,b,k)

def sections(skel,b,fullness):
    """Local angular tissue envelope; never spread one maximal width over the face."""
    p=skel['profile'];d=np.array(p['dorsal']);W=p['widths'][0]
    points=np.concatenate([skel['parts'][k]['v'] for k in ['upper','jaw']])
    pad=fullness*TISSUE[b]
    xs=np.linspace(points[:,0].min()-.35,points[:,0].max()+.35,67)
    records=[];radii=[];theta=np.linspace(-np.pi,np.pi,97)
    for x in xs:
        local=points[np.abs(points[:,0]-x)<2.2]
        if not len(local):local=points[np.argsort(np.abs(points[:,0]-x))[:80]]
        cy=(local[:,1].max()+local[:,1].min())/2
        if x>d[0,0]-7:
            cy={'golden':14.,'whippet':10.,'dachshund':12.,'maltipoo':14.}[b]
        yz=np.column_stack([local[:,1]-cy,local[:,2]])
        hull=ConvexHull(yz);normals=hull.equations[:,:2];offset=hull.equations[:,2]
        row=[]
        for t in theta:
            direction=np.array([np.cos(t),np.sin(t)])
            denom=normals@direction
            raw=np.min(-offset[denom>1e-7]/denom[denom>1e-7])
            # Thin skin on the muzzle/chin; crown coat remains a local allowance.
            cranial=np.clip((x-d[2,0])/(d[0,0]-d[2,0]),0,1)
            extra=1.0+pad*(.12+.26*cranial)*(.45+.55*max(0,np.cos(t)))
            row.append(raw+extra)
        records.append(cy);radii.append(row)
    cy=gaussian_filter1d(np.array(records),1.0)
    radius=gaussian_filter(np.array(radii),(1.7,2.5),mode=('nearest','wrap'))+.4
    # The occipital bone is not a second visible skull. Fit one posterior
    # elliptical envelope around all posterior bone sections, joined at its equator.
    equator=d[0,0]-7; tip=xs[-1]+5
    posterior=xs>=equator
    cap=np.sqrt(np.maximum(.001,1-((xs[posterior]-equator)/(tip-equator))**2))
    amplitude=np.max(radius[posterior]/cap[:,None],axis=0)
    for i,x in enumerate(xs):
        if x>=equator:radius[i]=amplitude*np.sqrt(max(.001,1-((x-equator)/(tip-equator))**2))
        elif x>equator-12:
            t=(x-equator+12)/12;t=t*t*(3-2*t)
            radius[i]=radius[i]*(1-t)+np.maximum(radius[i],amplitude)*t
    return dict(xs=xs,cy=cy,radius=radius,pad=pad,points=points)

def make_fields(skel,b,variant):
    p=skel['profile'];d=np.array(p['dorsal']);W=p['widths'][0];s=sections(skel,b,VARIANTS[variant])
    cy_interp=PchipInterpolator(s['xs'],s['cy'])
    front=d[5,0]+7.;rear=s['xs'][-1]
    # Same nasal template, isotropic individual scale. It is united with the skin.
    size=NOSE_SIZE[b];nc=np.array([d[5,0]+2.3,d[5,1]-.2,0.])
    muzzle_tip=d[5,0]-.5
    def nose(q):
        v=(q-nc)/size
        w=1.18*(1+.12*np.clip(v[...,1],-1,1))
        return (np.sqrt((v[...,0]/.68)**2+(v[...,1]/.70)**2+(v[...,2]/w)**2)-1)*size*.68
    muzzle_width={'golden':11.6,'whippet':7.2,'dachshund':8.5,'maltipoo':11.2}[b]
    muzzle_height={'golden':9.8,'whippet':8.2,'dachshund':9.1,'maltipoo':9.4}[b]
    muzzle_y=4.5
    def core(q):
        x,y,z=np.moveaxis(q,-1,0);xc=np.clip(x,front,rear)
        cy=cy_interp(xc)
        t=np.clip((x-front)/(d[3,0]-front),0,1);blend=1-t*t*(3-2*t)
        cy=cy*(1-blend)+muzzle_y*blend
        theta=np.arctan2(z,y-cy)
        ix=np.interp(xc,s['xs'],np.arange(len(s['xs'])))
        iy=(theta+np.pi)/(2*np.pi)*(s['radius'].shape[1]-1)
        radius=map_coordinates(s['radius'],[ix.ravel(),iy.ravel()],order=1,mode='nearest').reshape(x.shape)
        # Rounded finite muzzle pad with independent upper nasal attachment.
        pad_radius=1/np.sqrt((np.cos(theta)/muzzle_height)**2+(np.sin(theta)/muzzle_width)**2)
        radius=radius*(1-blend)+pad_radius*blend
        cap=np.sqrt(np.maximum(0,1-((x-front)/(front-muzzle_tip))**2))
        radius=np.where(x<front,pad_radius*cap,radius)
        # Continue the same posterior ellipsoid beyond the last bone section.
        end_r=map_coordinates(s['radius'],[np.full(ix.size,len(s['xs'])-1.),iy.ravel()],order=1,mode='nearest').reshape(x.shape)
        prev_r=map_coordinates(s['radius'],[np.full(ix.size,len(s['xs'])-2.),iy.ravel()],order=1,mode='nearest').reshape(x.shape)
        equator=d[0,0]-7;endtip=rear+5
        end_cap=end_r*np.sqrt(np.maximum(0,1-((x-equator)/(endtip-equator))**2))/np.sqrt(1-((rear-equator)/(endtip-equator))**2)
        radius=np.where(x>rear,end_cap,radius)
        value=np.hypot(y-cy,z)-radius
        body=np.maximum(value,np.maximum(muzzle_tip-x,x-endtip))
        return union(body,nose(q),2.2)
    neck_top=np.array([d[0,0]+10,7.,0.]);neck_bottom=np.array([d[0,0]+18,-21.,0.])
    def neck(q):
        x,y,z=np.moveaxis(q,-1,0);yy=np.clip(y,-21,18)
        levels=[-21,-10,2,12,18]
        cx=PchipInterpolator(levels,d[0,0]+np.array([15,12,9,7,4]))(yy)
        depth=PchipInterpolator(levels,[8,9,10,10,8])(yy)
        width=PchipInterpolator(levels,W*np.array([.50,.55,.60,.65,.60]))(yy)
        cap=np.where(y>12,np.sqrt(np.clip(1-((y-12)/7)**2,0,1)),1.)
        value=(np.sqrt(((x-cx)/np.maximum(.1,depth*cap))**2+(z/np.maximum(.1,width*cap))**2)-1)*np.minimum(depth,width)
        return np.maximum(value,np.maximum(-21.-y,y-19))
    earpaths=[];earwidths=[]
    if b=='golden':
        pts=[[d[0,0]+2,25,W*.95],[d[0,0]+6,21,W*1.30],[d[0,0]+13,4,W*1.32],[d[0,0]+12,-8,W*1.22]]
        widths=[3.8,8.5,11.,3.8];thick=3.2
    elif b=='whippet':
        pts=[[d[0,0],22,W*.95],[d[0,0]+9,23,W*1.25],[d[0,0]+19,18,W*1.30],[d[0,0]+24,9,W*1.25]]
        widths=[3.,5.3,4.,1.5];thick=2.1
    elif b=='dachshund':
        pts=[[d[0,0]+3,25,W*1.0],[d[0,0]+7,17,W*1.38],[d[0,0]+10,-6,W*1.48],[d[0,0]+6,-20,W*1.35]]
        widths=[4.,9.2,11.3,4.];thick=3.3
    else:
        pts=[[d[0,0]+4,26,W*1.0],[d[0,0]+12,18,W*1.40],[d[0,0]+13,2,W*1.38],[d[0,0]+7,-5,W*1.20]]
        widths=[4.6,11.4,12.8,4.8];thick=4.6
    for sign in [-1,1]:
        path=np.array(pts,float);path[:,2]*=sign;earpaths.append(path)
    ear_lofts=[]
    if b!='whippet':
        for path in earpaths:
            yy=np.r_[path[-1,1]-4.5,path[::-1,1],path[0,1]+3.8]
            xx=np.r_[path[-1,0],path[::-1,0],path[0,0]]
            zz=np.r_[path[-1,2],path[::-1,2],path[0,2]]
            ww=np.r_[.08,widths[::-1],.08]
            tt=np.r_[.08,np.full(4,thick),.08]
            ear_lofts.append((yy,[PchipInterpolator(yy,v) for v in [xx,zz,ww,tt]]))
    def ears(q):
        result=np.full(q.shape[:-1],1e4)
        if ear_lofts:
            x,y,z=np.moveaxis(q,-1,0)
            for (yy,interp),sign in zip(ear_lofts,[-1,1]):
                yc=np.clip(y,yy[0],yy[-1]);xx,zz,ww,tt=[fun(yc) for fun in interp]
                u=(yc-yy[0])/(yy[-1]-yy[0]);roundness=np.sqrt(np.maximum(0,np.sin(np.pi*u)))
                ww=np.maximum(.08,max(widths)*roundness);tt=np.maximum(.08,thick*roundness)
                dx=x-xx;dz=z-zz
                a=.80 if b=='maltipoo' else .90;bb=np.sqrt(1-a*a)
                wide=dx*a+sign*dz*bb;depth=-dx*bb+sign*dz*a
                value=(np.sqrt((wide/ww)**2+(depth/tt)**2)-1)*np.minimum(ww,tt)
                value=np.maximum(value,np.maximum(yy[0]-y,y-yy[-1]));result=np.minimum(result,value)
            return result
        for path,sign in zip(earpaths,[-1,1]):
            ctr=bones.curved(path,18)
            w=PchipInterpolator(np.linspace(0,1,4),widths)(np.linspace(0,1,18))
            ear=np.full(q.shape[:-1],1e4)
            for i,(a,bb) in enumerate(zip(ctr[:-1],ctr[1:])):
                delta=bb-a;t=np.clip(np.sum((q-a)*delta,axis=-1)/np.dot(delta,delta),0,1)
                off=q-a-t[...,None]*delta
                wide=off[...,0]*.60+sign*off[...,2]*.80
                depth=off[...,0]*(-.80)+sign*off[...,2]*.60
                ww=w[i]*(1-t)+w[i+1]*t
                distance=(np.sqrt((wide/ww)**2+(off[...,1]/4.7)**2+(depth/thick)**2)-1)*thick
                ear=np.minimum(ear,distance)
            result=np.minimum(result,ear)
        return result
    def head(q):return union(core(q),neck(q),6.5)
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
    yn=(y-nc[1])/(size*.72);zn=z/(size*1.18*(1+.12*np.clip(yn,-1,1)))
    nose=(ff['nose'](v)<1.1)&(x<nc[0]+size*.5)
    c[nose]=[43,40,34]
    # Shallow curved closed-mouth lip on the surface, ending well before the joint.
    d=np.array(p['profile']['dorsal']);start=d[4,0]+2;end=d[1,0]-1
    t=np.clip((x-start)/(end-start),0,1)
    lip=1.0+1.4*t+.3*np.sin(t*np.pi)
    # Neutral closed lips need no decorative exterior outline. Jaw support is
    # retained in the actual surface; open-mouth work remains a later task.
    return c

def eye_mesh(center,normal,r):
    normal=np.array(normal,float);normal/=np.linalg.norm(normal)
    up=np.array([0.,1.,0.]);up-=normal*np.dot(up,normal);up/=np.linalg.norm(up)
    right=np.cross(up,normal)
    def fn(q):
        v=q-center
        return (np.sqrt((v@right/r)**2+(v@up/r)**2+(v@normal/(r*.65))**2)-1)*r*.65
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
        origin=np.array([d[1,0]+2,20.5 if b=='maltipoo' else 19.,sign*W*.60])
        normal=np.array([-.88,.02,sign*.47]);normal/=np.linalg.norm(normal)
        lo=0.;hi=W*2
        for _ in range(28):
            mid=(lo+hi)/2;q=(origin+normal*mid)[None]
            if ff['core'](q)[0]<0:lo=mid
            else:hi=mid
        surface=origin+normal*lo
        gradient=np.array([(ff['core']((surface+np.eye(3)[k]*.05)[None])[0]-ff['core']((surface-np.eye(3)[k]*.05)[None])[0])/.1 for k in range(3)])
        normal=gradient/np.linalg.norm(gradient)
        center=surface-normal*EYE_SIZE[b]*.2
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
    label(im,32,80,{'A':'가벼운 볼륨','B':'중간 볼륨','C':'도톰한 볼륨'}[variant]+' · 같은 골격과 주둥이 길이 / 외피 볼륨 비교 · 눈은 표면에 맞춰 부착',21)
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
