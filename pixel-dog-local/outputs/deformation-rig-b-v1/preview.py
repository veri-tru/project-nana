"""Draw the three proportion studies directly from their integrated B rigs."""
import importlib.util
import json
import math
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / 'integrated-rig-b-v1'
sys.path.insert(0, str(BASE))
from build import project_offset, world_frames, world_pose

spec = importlib.util.spec_from_file_location('base_preview', BASE / 'preview.py')
base_preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_preview)

BREEDS = ('whippet', 'dachshund', 'golden')
NAMES = ('휘핏', '닥스훈트', '골든 리트리버')
EN = ('WHIPPET', 'DACHSHUND', 'GOLDEN RETRIEVER')
TITLES = {'A': '성견 비율형', 'B': '압축형', 'C': '큰 머리형'}
BG, DARK, MUTED, RULE = '#FAF8F2', '#213C37', '#53685F', '#CAD2C6'
GREEN, RED = '#176B5E', '#AD4E2B'
SKIN, REAR, EAR, NOSE = '#B2C4AE', '#758F82', '#91A995', '#27463E'
FRONT = 'scapula_fixed shoulder elbow carpus mcp foretoe'.split()
BACK = 'hip stifle tarsus mtp hindtoe'.split()


@lru_cache(None)
def font(size, bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/'+('malgunbd.ttf' if bold else 'malgun.ttf'), size)


def txt(draw, xy, value, size, color=DARK, bold=False):
    draw.text(xy, value, font=font(size, bold), fill=color, anchor='lt')


def smooth_ring(vertices):
    """Cut polygon corners twice while retaining the anatomical landmarks nearby."""
    for _ in range(2):
        out = []
        for p, q in zip(vertices, vertices[1:] + vertices[:1]):
            out += [tuple(.84*a+.16*b for a,b in zip(p,q)), tuple(.16*a+.84*b for a,b in zip(p,q))]
        vertices = out
    return vertices


class Model:
    def __init__(self, rig, breed, paw_scale):
        self.paw_scale = paw_scale
        self.rig = rig
        self.key = breed
        self.frames = world_frames(rig)
        self.pts = world_pose(rig)
        self.tail = base_preview.tail_envelope(rig['tail_profile'], self.pts)
        self.rib = self.surface('ribcage')
        self.pel = self.surface('pelvis')

    def nodes(self, prefix, ids):
        return [self.pts[prefix + n] for n in ids.split()]

    def surface(self, key):
        s = self.rig['surfaces'][key]
        return [project_offset(self.frames[s['owner']], off) for off in s['offsets']]

    def guide(self,key):
        g = self.rig[key]
        return project_offset(self.frames[g['owner']],g['offset'])

    def limb(self, side, names):
        return [self.pts['body.' + side + '_' + n] for n in names]

    def paint(self, image, origin, scale, overlay):
        draw = ImageDraw.Draw(image)
        def xy(v):
            # A shallow oblique projection separates contralateral limbs; y=0 is ground.
            x,y,z = v
            return origin[0]+(x-.44*z)*scale, origin[1]-y*scale
        def poly(pts, color, rounded=True):
            vertices = [xy(v) for v in pts]
            draw.polygon(smooth_ring(vertices) if rounded else vertices, fill=color)
        def stroke(pts,color,width=1):
            draw.line([xy(v) for v in pts],fill=color,width=max(1,round(width)),joint='curve')
        def dot(v,r,c):
            x,y=xy(v)
            draw.ellipse((x-r,y-r,x+r,y+r),fill=c)
        def taper(pts, radii, color, flat=False):
            a,b=[],[]
            for i,((x,y,z),r) in enumerate(zip(pts,radii)):
                u,v=pts[max(0,i-1)],pts[min(i+1,len(pts)-1)]
                dx,dy=v[0]-u[0],v[1]-u[1]
                length=math.hypot(dx,dy) or 1
                nx,ny=-dy/length,dx/length
                a.append((x+nx*r,max(0,y+ny*r) if flat else y+ny*r,z))
                b.append((x-nx*r,max(0,y-ny*r) if flat else y-ny*r,z))
            poly(a+b[::-1],color)
        p=self.pts
        f=lambda names:self.nodes('face.',names)
        b=lambda names:self.nodes('body.',names)
        rib,pel=self.rib,self.pel
        center,upper,lower,fringe=self.tail
        poly(upper+fringe[::-1],REAR,False)
        heft={'whippet':.78,'dachshund':.94,'golden':1.20}[self.key]
        foot_factor=self.paw_scale
        for side,tint in [('right',REAR),('left',SKIN)]:
            for order,chain in enumerate((FRONT,BACK)):
                pts=self.limb(side,chain)
                widths=([2.0,3.0,2.0,1.0,1.05,.24] if order==0 else [3.9,3.25,1.35,1.14,.24])
                taper(pts,[w*heft for w in widths],tint,True)
                (mx,my,mz),(tx,ty,tz)=pts[-2:]
                w=heft*foot_factor
                poly([(mx+1.35*w,0,mz),(mx+.85*w,my+.48*w,mz),
                      (mx-.75*w,my+.48*w,mz),(tx-.55*w,.88*w,tz),
                      (tx-.78*w,0,tz)],tint)
        shoulder=self.limb('left',FRONT)[1]
        hip=self.limb('left',BACK)[0]
        belly=self.guide('belly_guide')
        # The integrated chest profile controls the depth and rear edge of the rib barrel.
        poly([rib[0],*rib[1:4],p['body.lumbar_pivot'],self.guide('pelvic_dorsum'),
              pel[2],p['body.tail_root'],pel[3],pel[4],(hip[0]-1,hip[1]-4,0),
              belly,rib[6],*rib[7:]], SKIN)
        # Neck joins occiput to withers, and jaw to brisket.
        poly([*f('occiput crown'),*b('ribcage'),rib[3],shoulder,rib[-1],
              *f('neck_mount L_cheek L_jaw_hinge')], SKIN)
        poly(f('occiput crown L_brow stop nose nose_bottom upper_lip chin L_jaw_side L_cheek neck_mount'),SKIN)
        ear=f('L_ear_root L_ear_fold L_ear_tip')
        earw=math.dist(ear[0],ear[2])*.24
        taper(ear,[earw,earw*.91,earw*.26],EAR)
        dot(p['face.nose'],max(.6,scale*.68),NOSE)
        dot(p['face.L_eye'],max(.51,scale*.45),NOSE)
        stroke(f('upper_lip L_mouth_corner'),NOSE,max(1,scale*.25))
        if not overlay:
            return
        for surf in (rib,pel):
            vs=[xy(v) for v in surf]
            draw.line(vs+vs[:1],fill='#5B8A79',width=1,joint='curve')
        for chain in (FRONT,BACK):
            pts=self.limb('left',chain)
            stroke(pts,GREEN,2)
            for v in pts[:-1]:
                dot(v,2.7,GREEN)
                dot(v,1.0,BG)
        stroke(b('tail_root pelvis lumbar_pivot ribcage neck head'),GREEN,2)
        stroke(center,RED,2)
        for v in center[1:-1]:dot(v,2,RED)
        for v in b('lumbar_pivot head'):
            dot(v,3.8,RED)
            dot(v,1.5,BG)
        stroke(ear,GREEN,1.5)
        for v in ear:dot(v,1.6,GREEN)

    def face(self, image, cx, base_y, scale):
        d=ImageDraw.Draw(image)
        def xy(n):
            _,y,z=self.pts['face.'+n]
            return cx+z*scale, base_y-(y-self.pts['face.crown'][1])*scale
        def shape(names,color):
            vs=[xy(n) for n in names.split()]
            d.polygon(vs,fill=color)
            d.line(vs+[vs[0]],fill=GREEN,width=2,joint='curve')
        shape('crown L_brow L_temple L_cheek L_jaw_side chin R_jaw_side R_cheek R_temple R_brow', '#DCE5D7')
        for side in ('L_', 'R_'):
            def line(names,c):
                d.line([xy(side+n) for n in names.split()], fill=c,width=2,joint='curve')
            line('ear_root ear_fold ear_tip',GREEN)
            shape(' '.join(side+n for n in ('eye_inner','upper_lid','eye_outer','lower_lid')),BG)
            x,y=xy(side+'pupil')
            d.ellipse((x-2,y-2,x+2,y+2),fill=DARK)
            line('eye_inner muzzle_side nose_wing','#799184')
            d.line([xy('upper_lip'),xy(side+'mouth_corner')],fill=DARK,width=2)
        shape('L_nose_wing R_nose_wing nose_bottom',GREEN)


def make_board(studies, single=False):
    keys=list(studies)
    width=1670
    row_h=266
    start=208
    height=start+len(keys)*row_h+(195 if single else 0)+74
    out=Image.new('RGB',(width,height),BG)
    d=ImageDraw.Draw(out)
    txt(d,(38,24),'NANA     /     CHARACTER DEVELOPMENT                                      STUDY    01—03',13,GREEN,True)
    txt(d,(38,53),('골격 데포르메 비교' if not single else f'{keys[0]}안   {TITLES[keys[0]]}'),43,DARK,True)
    txt(d,(40,124),'통합 B 골격에 적용한 세 가지 비례. 같은 품종을 세로로 비교하면 머리 크기, 배 아래 여백, 다리 길이의 변화가 보입니다.' if not single else '통합 B 골격에서 계산한 전신과 얼굴. 같은 투영과 축척으로 세 품종의 비례를 비교합니다.',19,MUTED)
    xstart=199; col=478
    for j,(kor,en) in enumerate(zip(NAMES,EN)):
        x=xstart+j*col
        txt(d,(x+10,177),kor,21,DARK,True)
        txt(d,(x+188,184),en,13,MUTED,True)
    for i,k in enumerate(keys):
        y=start+i*row_h
        d.line((38,y,width-38,y),RULE,2)
        txt(d,(42,y+30),k,59,GREEN,True)
        if k=='A': txt(d,(99,y+62),'선택안',15,GREEN,True)
        txt(d,(43,y+111),TITLES[k],23,DARK,True)
        desc={'A':['본래 다리 길이와','성견의 허리선'],'B':['짧은 몸통과','넓은 발 지지면'],'C':['큰 머리와 귀,','짧은 팔다리']}
        for t,line in enumerate(desc[k]):txt(d,(44,y+157+t*24),line,16,MUTED)
        for j,b in enumerate(BREEDS):
            model=studies[k][b]
            x=xstart+j*col
            if j: d.line((x-6,y+13,x-6,y+row_h-17),RULE,1)
            ground=y+223
            d.line((x+10,ground+1,x+323,ground+1),RULE,1)
            # Common ground, scale and x origin across candidates (no pose-fitting).
            model.paint(out,(x+140,ground),3.3,True)
            tile=Image.new('RGB',(64,64),BG)
            model.paint(tile,(27,54),.64,False)
            bounds=ImageChops.difference(tile, Image.new('RGB',tile.size,BG)).getbbox()
            assert bounds and all(v >= 2 for v in (*bounds[:2],64-bounds[2],64-bounds[3])), (k,b,bounds)
            left=x+332
            d.rectangle((left,ground-107,left+130,ground+23),outline=RULE,width=1)
            out.paste(tile.resize((128,128),Image.Resampling.NEAREST),(left+1,ground-106))
            txt(d,(x+10,ground+11),'골격  /  전신',13,MUTED)
            txt(d,(left+3,ground-128),'64 px   ×2',13,MUTED)
    end=start+len(keys)*row_h
    if single:
        d.line((38,end,width-38,end),RULE,1)
        txt(d,(43,end+28),'얼굴 골격',21,DARK,True)
        txt(d,(43,end+66),'정면 확대',16,MUTED)
        for j,b in enumerate(BREEDS):
            studies[keys[0]][b].face(out,xstart+j*col+213,end+25,6.7)
        end+=195
    d.line((38,end,width-38,end),RULE,1)
    txt(d,(39,end+22),'초록 선  주요 관절과 귀     /     적갈색  목·허리 회전점과 꼬리 중심선',16,MUTED)
    txt(d,(840,end+22),'면은 비례를 확인하기 위한 외형 가이드입니다. 닥스훈트 꼬리는 단모형 품종 기준을 따랐습니다.',15,MUTED)
    return out


if __name__ == '__main__':
    studies={}
    for k in 'ABC':
        data=json.loads((HERE/f'{k}.json').read_text(encoding='utf-8'))
        studies[k]={b:Model(data["breeds"][b],b,data["deformation"]["paw_scale"]) for b in BREEDS}
    for k,models in studies.items():
        make_board({k:models},True).save(HERE/f'{k}.png')
    make_board(studies).save(HERE/'comparison.png')
