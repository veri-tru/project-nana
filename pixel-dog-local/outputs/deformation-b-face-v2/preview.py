"""Orthographic face volume studies. Coordinates and feature attachments come from B rigs."""
import json
import math
import runpy
from functools import lru_cache
from pathlib import Path

import numpy as np
from numba import njit
from PIL import Image, ImageChops, ImageDraw, ImageFont
from scipy.interpolate import PchipInterpolator

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'deformation-rig-b-v1'
prev = runpy.run_path(str(OLD / 'preview.py'))
pose = prev['world_pose']
BG = (248, 246, 241)
INK = '#23352E'
MUTED = '#65756A'
LINE = '#D7DDD3'
BREEDS = ['golden', 'whippet', 'dachshund']
NAMES = ['골든 리트리버', '휘핏', '닥스훈트']
COLORS = {'golden': ([226,183,123],[188,140,88]), 'whippet': ([190,164,139],[147,120,102]), 'dachshund': ([181,122,83],[139,84,61])}
R = np.array
SIN, COS = np.sin, np.cos
TH = np.linspace(0, 2*np.pi, 49)
def mix(a,b,t):
    return a*(1-t)+b*t


@lru_cache(None)
def font(size, bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/malgun'+('bd' if bold else '')+'.ttf',size)


def label(im, x, y, string, size, fill=INK, bold=False):
    ImageDraw.Draw(im).text((x,y),string,font=font(size,bold),fill=fill,anchor='lt')


def ellipsoid(c, axes):
    lat=np.linspace(-np.pi/2,np.pi/2,21)[:,None]
    u=np.stack(np.broadcast_arrays(COS(lat)*COS(TH), SIN(lat), COS(lat)*SIN(TH)),axis=-1)
    return c+u@R(axes)


def ell(c,radii):
    return ellipsoid(c,np.diag(radii))


def ring_solid(rings):
    # Ring entries are center x, center y, half depth, half width. Interpolation
    # preserves the stop and nose endpoints while rounding each authored cross-section.
    rs=R(rings)
    t=np.arange(len(rs))
    x,y,h,w=PchipInterpolator(t,rs,axis=0)(np.linspace(0,t[-1],32)).T
    return np.stack(np.broadcast_arrays(x[:,None], y[:,None]+h[:,None]*COS(TH),w[:,None]*SIN(TH)),axis=-1)


def make_face(rig,breed):
    world=pose(rig)
    p={k[5:]:R(v)-world['body.head'] for k,v in world.items() if k.startswith('face.')}
    skull,ear=map(R,COLORS[breed])
    features=[]
    def mesh(points,color):
        features.append((points,R(color)))
    occ,top,stop,nose,chin=[p[k] for k in ['occiput','crown','stop','nose','chin']]
    cheek,temple,eye=[p['L_'+k] for k in ['cheek','temple','eye']]
    w=temple[2]; tipw=p['L_nose_wing'][2]; midw=p['L_muzzle_side'][2]
    lip=p['upper_lip']; corner=p['L_mouth_corner']; brow=p['L_brow']
    # The closed mouth, cheek and forehead share one longitudinal skin shell. Each
    # station prescribes a dorsal and ventral height plus width at the fullest point.
    def sec(x,hi,lo,width):
        return (x,hi,lo,width)
    stop_drop={'golden':.15,'whippet':.03,'dachshund':.05}[breed]
    low=min(cheek[1]-.20*w,p['L_jaw_side'][1])
    sections=sorted([
        sec(occ[0]+.15*w,occ[1]-.20*w,occ[1]-.22*w,.024*w),
        sec(occ[0]+.09*w,occ[1]-.015*w,low+.32*w,.62*w),
        sec(occ[0]-.10*w,mix(occ[1],top[1],.62),low+.13*w,.93*w),
        sec(top[0],top[1],low+.035*w,w*1.04),
        sec(brow[0],brow[1]+.11*w,low,.96*w),
        sec(stop[0],stop[1]+.06*w,low,.82*w),
        sec(stop[0]-.12*w,stop[1]-stop_drop*w,low,.74*w),
        sec(p['L_muzzle_side'][0],mix(stop[1],nose[1],.68)-.045*w,p['L_jaw_side'][1],midw),
        sec(chin[0],mix(stop[1],nose[1],.90),chin[1],tipw*1.18),
        sec(nose[0]+.095*w,nose[1]-.012*w,lip[1]-.01*w,tipw*1.03),
        sec(nose[0]-.045*w,nose[1]-.12*w,lip[1]+.13*w,tipw*.78),
        sec(nose[0]-.09*w,nose[1]-.19*w,lip[1]+.21*w,tipw*.06),
    ])
    # Interpolate along caudal x. Squarer sections near the nose preserve lower
    # jaw width and avoid a pointed snout in the retriever.
    sect=R(sections); sect[:,2]=np.minimum(sect[:,2],sect[:,1]-.025*w); data=PchipInterpolator(sect[:,0],sect[:,1:],axis=0)
    xs=np.linspace(sect[0,0],sect[-1,0],204); hi,lo,ww=data(xs).T
    def ring(x,h,l,r,tt):
        return np.stack(np.broadcast_arrays(x,(h+l)/2+(h-l)/2*np.sign(COS(tt))*np.abs(COS(tt))**.80,
                                            r*np.sign(SIN(tt))*np.abs(SIN(tt))**.80),axis=-1)
    shell=ring(xs[:,None],hi[:,None],lo[:,None],ww[:,None],np.linspace(0,2*np.pi,193))
    center=(shell[:-1,:-1]+shell[1:,:-1]+shell[1:,1:]+shell[:-1,1:])*.25
    xx,yy,zz=center.transpose(2,0,1)
    material=np.broadcast_to(skull,xx.shape+(3,)).astype(float).copy()
    def stain(mask,col):
        nonlocal material
        mask=np.clip(mask,0,1)
        material=material*(1-mask[:,:,None])+R(col)*mask[:,:,None]
    # A mild anterior orbital plane bridges the brow and cheek. Rendering follows
    # the exterior skin around a landmark; the painted eyelids never float outside.
    # Integument is painted directly on the continuous shell, including the eyes:
    # no black beads, floating eyelids or second intersecting mouth sheet.
    lip_t=np.clip((xx-nose[0])/(corner[0]-nose[0]),0,1)
    lip_y=mix(lip[1],corner[1],lip_t)-.08*w*SIN(np.pi*lip_t)
    lip_w=.017*w+.045*w*SIN(np.pi*lip_t)
    mask=np.exp(-((yy-lip_y)/lip_w)**2)*np.clip((corner[0]-xx)/(.06*w),0,1)
    stain(mask*.92,[79,60,48])
    lower=(1/(1+np.exp(np.clip((yy-lip_y)/(.06*w),-36,36))))*np.clip((corner[0]+.12*w-xx)/(.2*w),0,1)
    stain(lower*.14,[148,111,83])
    for ss,side in [(1,'L_'),(-1,'R_')]:
        e=p[side+'eye'].copy()
        ew=abs(p[side+'eye_outer'][2]-p[side+'eye_inner'][2])*.63
        eh=max(.34*ew,(p[side+'upper_lid'][1]-p[side+'lower_lid'][1])*.61)
        # Eye plane crosses the sloping skull wall; projected width is read in
        # the surface plane, irrespective of how the camera rotates.
        nearest=((xx-e[0])*.65)**2+((yy-e[1])*1.55)**2+((zz-e[2])*1.50)**2
        ix=np.unravel_index(np.argmin(nearest),xx.shape)
        ex,ey,ez=xx[ix],yy[ix],zz[ix]
        flatdist=np.hypot(xx-ex,zz-ez)
        along=np.sign((xx-ex)+ss*(zz-ez)) * flatdist/ew
        vertical=(yy-ey-.11*(xx-ex))/eh
        visible=(ss*zz>0)&(flatdist<2.7*ew)
        orbital=np.exp(-1.4*(along**2+(vertical*.92+.18)**2))*visible
        stain(.46*orbital,skull*.80)
        distance=along**2+np.abs(vertical)**1.60
        stain(np.clip((1.21-distance)*4.1,0,1)*visible,[55,44,34])
        iris=np.exp(-3.4*((along+.15)**2+(vertical+.24)**2))
        stain(iris*.46*(distance<.90)*visible,[103,75,45])
        pupil=(along+.13)**2+(.58*vertical)**2
        stain(np.clip((.27-pupil)*6.,0,1)*visible,[38,36,31])
        glint=((along+.28)/.14)**2+((vertical-.23)/.23)**2
        stain(np.exp(-glint*.75)*visible,[248,232,200])
    mesh(shell,material)
    for ss,side in [(1,'L_'),(-1,'R_')]:
        root,fold,tip=[p[side+k].copy() for k in ['ear_root','ear_fold','ear_tip']]
        # Broad attachment across the temporal plane; rounded-bottom flaps
        # lie against the cheek in retriever/dachshund, rose ears fold backwards.
        draped=breed!='whippet'
        factor={'golden':1.,'dachshund':.87,'whippet':.70}[breed]
        if draped:
            root[2]=ss*(w*.87)
            fold[2]=ss*max(w*1.005,abs(fold[2])*.93)
            tip[2]=ss*min(w*1.01,abs(tip[2])*.94)
        else:
            root[2]=ss*.80*w
        rows=[]
        for t,rad in [(0,.22),(.12,.43),(.30,.52),(.54,.50),(.74,.43),(.88,.31),(.965,.18),(1,.022)]:
            c=(mix(root,fold,t/.42) if t<=.42 else mix(fold,tip,(t-.42)/.58))
            if draped:
                c[0]+=.10*w*SIN(np.pi*t)
                c[2]+=ss*.045*w*SIN(np.pi*t)
            rows.append([*c,rad*w*factor])
        values=PchipInterpolator([0,.12,.30,.54,.74,.88,.965,1],R(rows),axis=0)(np.linspace(0,1,36))
        # The cross section is tilted towards the front at its rostral edge, so
        # part of the wide pendant pinna is visible from the front as well.
        c=values[:,:3,None]; rad=values[:,3,None]
        tube=c+np.stack(np.broadcast_arrays(
            rad*COS(TH),rad*COS(TH)*(.15 if draped else -.36),
            ss*rad*(.44*SIN(TH)+(.39 if draped else .31)*COS(TH))),axis=1)
        mesh(tube.transpose(0,2,1),ear)
    # Rounded, sloped nasal cap overlaps the dorsal muzzle instead of standing
    # vertically in front of it. The nose occupies the top of the terminal muzzle.
    nb=p['nose_bottom']
    h=max(.065*w,(nose[1]-nb[1])*.47)
    nc=R([nose[0]+.05*w,nose[1]-.74*h,0.])
    mesh(ellipsoid(nc,[[.19*w,.055*w,0],[-.045*w,h,0],[0,0,.98*tipw]]),[64,56,48])
    for ss in (1,-1):
        mesh(ell(nc+R([-.156*w,-.10*h,ss*tipw*.48]),[.021*w,.25*h,tipw*.19]),[39,37,34])
    return features


def polys(features, angle, elev=5):
    a,e=np.deg2rad([angle,elev])
    right=R([SIN(a),0,COS(a)])
    front=R([-COS(a)*COS(e),SIN(e),SIN(a)*COS(e)])
    up=np.cross(front,right)
    view=np.column_stack([right,up,front])
    light=R([-.47,.70,.54]); light/=np.linalg.norm(light)
    xy=[]; zs=[]; colors=[]
    for pts,base in features:
        v=pts@view
        v0,v1,v2,v3=v[:-1,:-1],v[1:,:-1],v[1:,1:],v[:-1,1:]
        norm=np.cross(v2-v0,v3-v1)
        norm/=np.maximum(1e-8,np.linalg.norm(norm,axis=-1,keepdims=True))
        # Draw the camera-facing side of each surface irrespective of its winding.
        norm=norm*np.where(norm[:,:,2:]<0,-1,1)
        # Face-away polygons are removed by the painter's depth ordering.
        shading=.78+.22*np.maximum(0,norm@light)+.065*np.maximum(0,norm[:,:,1])
        color=np.clip(base*shading[:,:,None],0,255).astype(np.uint8)
        quads=np.stack((v0,v1,v2,v3),axis=2).reshape(-1,4,3)
        # Average incident quad colours on each vertex. Gouraud interpolation keeps
        # eyelid pigment and cast-free shading smooth when the head rotates.
        padded=np.pad(color.astype(float),((1,1),(1,1),(0,0)),mode='edge')
        vc=(padded[1:,1:]+padded[:-1,1:]+padded[1:,:-1]+padded[:-1,:-1])*.25
        cc=np.stack([vc[:-1,:-1],vc[1:,:-1],vc[1:,1:],vc[:-1,1:]],axis=2)
        xy.append(quads); colors.append(cc.reshape(-1,4,3))
    points=np.concatenate(xy); colors=np.concatenate(colors); order=np.arange(len(points))
    return points[order],colors[order]


@njit(cache=True)
def raster(px,color,buf,rgb):
    height,width=buf.shape
    for q in range(len(px)):
        for j in (1,2):
            a,b,c=px[q,0],px[q,j],px[q,j+1]
            ax,ay,az=a; bx,by,bz=b; cx,cy,cz=c
            det=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
            if abs(det)<1e-5: continue
            for y in range(max(0,int(np.floor(min(ay,by,cy)))),min(height,int(np.ceil(max(ay,by,cy)))+1)):
                for x in range(max(0,int(np.floor(min(ax,bx,cx)))),min(width,int(np.ceil(max(ax,bx,cx)))+1)):
                    one=((by-cy)*(x+.5-cx)+(cx-bx)*(y+.5-cy))/det
                    two=((cy-ay)*(x+.5-cx)+(ax-cx)*(y+.5-cy))/det
                    thr=1.-one-two
                    if min(one,two,thr)<-.00001: continue
                    z=az*one+bz*two+cz*thr
                    if z>buf[y,x]:
                        buf[y,x]=z
                        for ch in range(3):
                            rgb[y,x,ch]=color[q,0,ch]*one+color[q,j,ch]*two+color[q,j+1,ch]*thr


def paint(im,xyz,colors,center,scale):
    ss=2
    q=xyz.copy(); q[:,:,0]=q[:,:,0]*scale+center[0]; q[:,:,1]=center[1]-q[:,:,1]*scale
    l,t=np.floor(q[:,:,:2].min(axis=(0,1))-2).astype(int)
    r,b=np.ceil(q[:,:,:2].max(axis=(0,1))+2).astype(int)
    q[:,:,:2]=(q[:,:,:2]-np.array([l,t]))*ss
    under=im.crop((l,t,r,b)).resize(((r-l)*ss,(b-t)*ss))
    colors=np.ascontiguousarray(colors,dtype=np.uint8)
    canvas=np.array(under)
    raster(q,colors,np.full(canvas.shape[:2],-np.inf),canvas)
    im.paste(Image.fromarray(canvas).resize((r-l,b-t),Image.Resampling.LANCZOS),(l,t))

def fit_head(im,rig,breed,angle,box,scale=None):
    xy,col=polys(make_face(rig,breed),angle)
    low=xy[:,:,:2].min(axis=(0,1)); high=xy[:,:,:2].max(axis=(0,1))
    l,t,r,b=box
    if scale is None: scale=min((r-l)/(high[0]-low[0]), (b-t)/(high[1]-low[1]))
    center=R([(l+r)/2,(t+b)/2])-(low+high)/2*R([scale,-scale])
    paint(im,xy,col,center,scale)


def board(old,new):
    w,h=1480,942
    im=Image.new('RGB',(w,h),BG); d=ImageDraw.Draw(im)
    label(im,40,24,'NANA    /    CHARACTER STUDY     02',14,'#8E6247',True)
    label(im,39,51,'B 압축형  ·  얼굴 입체감 수정',39,bold=True)
    label(im,40,112,'같은 품종의 이전·수정 골격을 같은 재질, 조명과 배율로 비교했습니다. 오른쪽 두 칸은 수정한 얼굴을 돌려 본 모습입니다.',17,MUTED)
    cols=[(190,473),(499,809),(835,1109),(1135,1445)]
    for (l,r),title in zip(cols,['이전 B   /   ¾','수정 B   /   ¾','정면','측면']):
        label(im,l,161,title,19,bold=True)
    d.line((40,195,w-40,195),LINE,2)
    for i,(breed,kor) in enumerate(zip(BREEDS,NAMES)):
        top=198+i*233
        d.rectangle((40,top+6,44,top+49),fill=tuple(COLORS[breed][1]))
        label(im,57,top+12,kor,21,bold=True)
        label(im,57,top+43,breed.upper(),11,MUTED,True)
        cases=[(old,38),(new,38),(new,0),(new,90)]
        boxes=[(l+5,top+13,r-8,top+204) for l,r in cols]
        # One scale for all four views in a row, based on their real three dimensional extents.
        dims=[]
        for (rs,ang),box in zip(cases,boxes):
            points,_=polys(make_face(rs[breed],breed),ang)
            dx,dy=points[:,:,:2].max(axis=(0,1))-points[:,:,:2].min(axis=(0,1))
            dims.extend([(box[2]-box[0])/dx,(box[3]-box[1])/dy])
        s=min(dims)
        for (rs,ang),box in zip(cases,boxes):
            fit_head(im,rs[breed],breed,ang,box,s)
        d.line((40,top+227,w-40,top+227),LINE,1)
    label(im,40,h-31,'색과 명암은 볼륨 판독용 제작값입니다. 좌우 대칭 중립 서기와 닫힌 입을 기준으로 그렸습니다.',14,MUTED)
    return im


def body_board(rigs):
    im=Image.new('RGB',(1420,425),BG);d=ImageDraw.Draw(im)
    label(im,36,20,'B 압축형  ·  서기에서 본 얼굴과 몸통',31,bold=True)
    for j,(key,kor) in enumerate(zip(BREEDS,NAMES)):
        left=32+j*461; ground=356
        label(im,left,75,kor,20,bold=True)
        rig=rigs[key]; model=prev['Model'](rig,key,1.22); p=model.pts
        # Shallow oblique side projection. The analytical face uses the identical
        # projection as the body, including the lateral contribution to horizontal x.
        proj=np.deg2rad(82)
        s=4.45; ox=left+174
        def xy(v):
            return (ox+s*(np.sin(proj)*v[0]+np.cos(proj)*v[2]),ground-s*v[1])
        def poly(pts,fill):
            d.polygon(prev['smooth_ring']([xy(v) for v in pts]),fill=tuple(map(int,fill)))
        base=R(COLORS[key][0]); rib,pel=model.rib,model.pel
        center,upper,lower,fringe=model.tail
        poly(upper+fringe[::-1],base*.80)
        for side in ('right','left'):
            for chain,radii in [(prev['FRONT'],[2,3,2,1.1,1,.3]),(prev['BACK'],[3.5,3.1,1.5,1.1,.3])]:
                pts=R(model.limb(side,chain)); widths=R(radii)*{'golden':1.25,'whippet':.82,'dachshund':.98}[key]
                tang=np.gradient(pts[:,:2],axis=0);normal=np.stack((-tang[:,1],tang[:,0]),axis=1)
                normal/=np.maximum(.1,np.linalg.norm(normal,axis=1,keepdims=True));off=normal*widths[:,None]
                v1=pts.copy();v2=pts.copy();v1[:,:2]+=off;v2[:,:2]-=off
                v1[:,1]=np.maximum(0,v1[:,1]);v2[:,1]=np.maximum(0,v2[:,1])
                tint=base*(.76 if side=='right' else .95)
                poly(list(v1)+list(v2[::-1]),tint)
                m,to=pts[-2:]; poly([m+[1.1,-m[1],0],m+[.7,.48,0],to+[-.75,1,0],to+[-.92,0,0]],tint)
        poly([*rib[:4],p['body.lumbar_pivot'],model.guide('pelvic_dorsum'),pel[2],p['body.tail_root'],*pel[3:5],
              p['body.left_hip'],model.guide('belly_guide'),*rib[6:]],base)
        poly([p['face.occiput'],p['body.ribcage'],rib[3],p['body.left_shoulder'],rib[-1],p['face.neck_mount'],p['face.L_cheek']],base)
        coords,colors=polys(make_face(rig,key),82,0)
        paint(im,coords,colors,R(xy(p['body.head'])),s)
        d.line((left,ground+1,left+438,ground+1),LINE,1)
    label(im,36,390,'각 품종의 B 몸통과 꼬리에 같은 얼굴 골격을 연결한 중립 자세입니다.',15,MUTED)
    return im


if __name__=='__main__':
    old=json.loads((OLD/'B.json').read_text(encoding='utf8'))['breeds']
    new=json.loads((HERE/'B.json').read_text(encoding='utf8'))['breeds']
    board(old,new).save(HERE/'faces.png')
    body_board(new).save(HERE/'standing.png')






