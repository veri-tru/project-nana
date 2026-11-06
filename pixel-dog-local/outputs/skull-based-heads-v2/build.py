"""Neutral exterior candidates fitted to reviewed skeletal surfaces.

Bone meshes are actual inputs; authored tissue/coat offsets are not measurements.
No pose training, pixel conversion, or mouth animation is performed here.
"""
from pathlib import Path
import importlib.util,json,pickle,sys,hashlib
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.ndimage import gaussian_filter
from skimage.measure import marching_cubes
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'head-skeleton-volume-v2'
sys.path.insert(0,str(SOURCE))
spec=importlib.util.spec_from_file_location('reviewed_bone_builder',SOURCE/'build.py')
bones=importlib.util.module_from_spec(spec);spec.loader.exec_module(bones)
from raster import paint
bspec=importlib.util.spec_from_file_location('face_reference',HERE.parent/'skull-based-heads-v1'/'build.py')
base=importlib.util.module_from_spec(bspec);bspec.loader.exec_module(base)
BREEDS=bones.BREEDS;NAMES=bones.NAMES
VARIANTS={'A':320,'B':400,'C':480}
STEP=.65
BG=(248,247,242);INK=(38,54,48)
PALETTE={'golden':([220,174,109],[175,127,75]),'whippet':([178,156,134],[131,108,90]),'dachshund':([173,105,65],[126,69,43]),'maltipoo':([237,225,203],[216,198,167])}
EYE_SIZE={'golden':3.7,'whippet':3.1,'dachshund':3.35,'maltipoo':4.8}

def load_inputs():
    status=json.loads((SOURCE/'review-status.json').read_text('utf-8'))
    if status['delivery']!='READY':raise ValueError('Reviewed skeletal candidate required')
    expected='eaec7d20d5ea8abbb8a14e728d6120f4f119e2d3ee238d4af5b3836f06e4d154'
    if hashlib.sha256((SOURCE/'geometry.pkl').read_bytes()).hexdigest()!=expected:raise ValueError('Skeletal source changed')
    return pickle.loads((SOURCE/'geometry.pkl').read_bytes())

def ellipsoid(q,c,r):return bones.ellipsoid(q,c,r)
def union(a,b,k=2.):return bones.smoothmin(a,b,k)
def make_ears(skel,b):
    p=skel['profile'];d=np.array(p['dorsal']);W=p['widths'][0]
    earpaths=[]
    if b=='golden':
        pts=[[d[0,0]+2,25,W*.95],[d[0,0],19,W*1.45],[d[0,0]-2,4,W*1.50],[d[0,0]-3,-8,W*1.35]]
        widths=[3.8,9.5,13.,10.];thick=3.5
    elif b=='whippet':
        pts=[[d[0,0],22,W*.95],[d[0,0]+4,23,W*1.40],[d[0,0]+7,21,W*1.67],[d[0,0]+4,13,W*1.60]]
        widths=[3.,5.5,5.,2.];thick=2.4
    elif b=='dachshund':
        pts=[[d[0,0]+3,25,W*1.0],[d[0,0]-1,17,W*1.50],[d[0,0]-4,-6,W*1.65],[d[0,0]-7,-20,W*1.48]]
        widths=[4.,10.2,12.,8.5];thick=3.8
    else:
        pts=[[d[0,0]+4,26,W*1.14],[d[0,0]+1,18,W*1.42],[d[0,0]-2,7,W*1.49],[d[0,0]-3,2,W*1.43]]
        widths=[4.6,11.,11.,6.];thick=5.0
    for sign in [-1,1]:
        path=np.array(pts,float);path[:,2]*=sign;earpaths.append(path)
    thicknesses=[3.,5.5,4.5,2.5] if b=='maltipoo' else [thick]*4
    ear_lofts=[]
    if b!='whippet':
        for path in earpaths:
            yy=np.r_[path[-1,1]-4.5,path[::-1,1],path[0,1]+3.8]
            xx=np.r_[path[-1,0],path[::-1,0],path[0,0]]
            zz=np.r_[path[-1,2],path[::-1,2],path[0,2]]
            ww=np.r_[widths[-1],widths[::-1],.08]
            tt=np.r_[thicknesses[-1],thicknesses[::-1],.08]
            ear_lofts.append((yy,[PchipInterpolator(yy,v) for v in [xx,zz,ww,tt]]))
    path_tip={b:pts[-1][1]}
    def ears(q):
        result=np.full(q.shape[:-1],1e4)
        if b=='maltipoo':
            for sign in [-1,1]:
                center=np.array([d[0,0],12.,sign*W*1.44]);off=q-center
                wide=off[...,0]*.88-sign*off[...,2]*np.sqrt(1-.88**2)
                depth=off[...,0]*np.sqrt(1-.88**2)+sign*off[...,2]*.88
                value=(np.sqrt((wide/10.8)**2+(off[...,1]/16.)**2+(depth/4.8)**2)-1)*4.8
                root=ellipsoid(q,[d[0,0]+4,26,sign*W*1.14],[4.,6.,4.])
                result=np.minimum(result,union(value,root,3.))
            return result
        if ear_lofts:
            x,y,z=np.moveaxis(q,-1,0)
            for (yy,interp),sign in zip(ear_lofts,[-1,1]):
                yc=np.clip(y,yy[0],yy[-1]);xx,zz,ww,tt=[fun(yc) for fun in interp]
                cap_t=np.clip((path_tip[b]-y)/4.5,0,1)
                cap=np.sqrt(np.maximum(.0001,1-cap_t*cap_t))
                ww=np.where(y<path_tip[b],widths[-1]*cap,ww)
                tt=np.where(y<path_tip[b],thicknesses[-1]*cap,tt)
                ww=np.maximum(.08,ww);tt=np.maximum(.08,tt)
                dx=x-xx;dz=z-zz
                a,bb={'golden':(1.,0.),'dachshund':(.98,-np.sqrt(1-.98**2)),'maltipoo':(.88,-np.sqrt(1-.88**2))}[b]
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
                distance=(np.sqrt((wide/ww)**2+(off[...,1]/3.0)**2+(depth/thick)**2)-1)*thick
                ear=np.minimum(ear,distance)
            support=ellipsoid(q,[d[0,0]+4,19,sign*W*1.40],[6.,5.5,3.])
            ear=union(ear,support,1.2)
            result=np.minimum(result,ear)
        return result
    record=dict(ear_paths=[v.tolist() for v in earpaths],ear_width_controls=widths,ear_thickness=thick,
                ear_thickness_controls=thicknesses,ear_width_mode='compact_fold_with_leaf_support' if b=='whippet' else 'breed_pchip_width_and_thickness')
    if b=='maltipoo':
        record.update(ear_paths=[[path[0].tolist()] for path in earpaths],ear_width_controls=None,
                      ear_thickness=4.8,ear_thickness_controls=None,ear_width_mode='oriented_ellipsoid_with_root_union',
                      ear_leaf_centers=[[float(d[0,0]),12.,sign*W*1.44] for sign in [-1,1]],
                      ear_leaf_radii=[10.8,16.,4.8],ear_yaw_cos=.88,ear_root_radii=[4.,6.,4.],ear_root_blend=3.)
    else:
        record['ear_frame']='swept_fold_0.60_0.80' if b=='whippet' else ('lateral_plane' if b=='golden' else 'yaw_cos_0.98')
    return ears,record

def make_fields(skel,b,variant):
    old,metadata=base.make_fields(skel,b,'B')
    core=old['core'];patch=dict(method='constrained_surface_relaxation',iterations=VARIANTS[variant])
    ears,earmeta=make_ears(skel,b)
    def head(q):return union(core(q),old['neck'](q),6.5)
    def exterior(q):return union(head(q),ears(q),3.0)
    metadata={**metadata,**earmeta,'variant':variant,'front_patch':patch,'base_face_variant':'B','construction_metadata_note':'sections and muzzle_support describe the pre-relaxation seed; final surface is stored in geometry.pkl','surface_grid_step':STEP,'surface_grid_gaussian_sigma':.65}
    return dict(core=core,head=head,neck=old['neck'],ears=ears,nose=old['nose'],exterior=exterior),metadata

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
    nose=(ff['nose'](v)<1.1)&(x<nc[0]+size*.5)
    c[nose]=[43,40,34]
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

def relax_surface(part,skel,variant):
    v=part['v'].copy();original=v.copy();f=part['f'];d=np.array(skel['profile']['dorsal'])
    edges=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);edges=np.unique(np.sort(edges,axis=1),axis=0)
    ii=np.r_[edges[:,0],edges[:,1]];jj=np.r_[edges[:,1],edges[:,0]]
    degree=np.bincount(ii,minlength=len(v));adj=coo_matrix((1/degree[ii],(ii,jj)),shape=(len(v),len(v))).tocsr()
    def smooth(t):
        t=np.clip(t,0,1);return t*t*t*(t*(t*6-15)+10)
    weight=(1-smooth((original[:,1]-12)/8))*(1-smooth((original[:,0]-(d[1,0]-4))/12))
    black=np.all(part['c']==[43,40,34],axis=1)
    fixed=black.copy();fixed[np.unique(f[black[f].any(axis=1)])]=True
    weight[fixed]=0;active=np.flatnonzero(weight>1e-6)
    bv=np.concatenate([skel['parts'][k]['v'] for k in ['upper','jaw']]);bn=np.concatenate([skel['parts'][k]['n'] for k in ['upper','jaw']]);tree=cKDTree(bv)
    count=VARIANTS[variant]
    for it in range(count):
        v+=.35*weight[:,None]*(adj@v-v)
        if it%4==3 or it==count-1:
            distance,index=tree.query(v[active]);norm=bn[index];signed=np.sum((v[active]-bv[index])*norm,axis=1)
            push=np.where((distance<3)&(signed<.70),.70-signed,0.)
            v[active]+=norm*push[:,None]
    # A final positional fairing pass removes contact tessellation dents.
    for it in range(160):
        v+=.25*weight[:,None]*(adj@v-v)
    # Offset the fair surface smoothly to retain tissue clearance. The original
    # black nose and its boundary triangles remain geometrically fixed.
    def mesh_normals(points):
        fn=np.cross(points[f[:,1]]-points[f[:,0]],points[f[:,2]]-points[f[:,0]])
        nn=np.zeros_like(points)
        for j in range(3):np.add.at(nn,f[:,j],fn)
        nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-12)
        if np.mean(np.sum(nn*part['n'],axis=1))<0:nn=-nn
        return nn
    distance_to_pin=cKDTree(original[fixed]).query(original)[0]
    clearance_weight=weight*smooth(distance_to_pin/4.)
    v+=.65*clearance_weight[:,None]*mesh_normals(v)
    normals=mesh_normals(v)
    part['v']=v;part['n']=normals
    return dict(method='mesh_laplacian_relaxation_with_bone_obstacle',iterations=count,step=.35,
                black_vertices_pinned=int(black.sum()),boundary_vertices_pinned=int(fixed.sum()),
                bone_obstacle_margin=.70,polish_cycles=160,polish_steps=[.25],clearance_offset=.65,nose_offset_taper=4.,maximum_displacement=float(np.linalg.norm(v-original,axis=1).max()))

def build_one(skel,b,variant):
    ff,meta=make_fields(skel,b,variant);p=skel['profile'];d=np.array(p['dorsal']);W=p['widths'][0]
    bounds=[(d[5,0]-12,28),(-30,d[0,1]+24),(-W*2.4,W*2.4)]
    v,f,n=extract(ff['exterior'],bounds);part=dict(v=v,f=f,n=n,c=colors(v,ff,b,meta))
    meta['surface_relaxation']=relax_surface(part,skel,variant)
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
    label(im,32,80,{'A':'연결 곡면 A','B':'연결 곡면 B','C':'연결 곡면 C'}[variant]+' · 같은 머리·코 / 볼과 윗입술 연결 비교 · 품종별 귀',21)
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

