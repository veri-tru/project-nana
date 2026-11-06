"""Reproduce the comparison using only the integrated skeleton's neutral pose."""
import json
from math import ceil, hypot
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from build import world_frames, project_offset

HERE = Path(__file__).resolve().parent
PAPER, INK, SUB = '#F9F8F3', '#213833', '#5E7066'
TEAL, RIB, PELVIS, JOIN = '#287864', '#CFE1D5', '#E0E5DA', '#AC522D'
FACE = '#EBEDE2'
FONT = Path('C:/Windows/Fonts')

def tail_envelope(profile, points):
    """Side-plane upper and lower edges; feathering extends the ventral edge."""
    center=[points[n] for n in profile['chain']]
    upper,lower,fringe=[],[],[]
    for i,((x,y,z),r,fur) in enumerate(zip(center,profile['core_radius'],profile['underside_feather'],strict=True)):
        previous=center[max(i-1,0)]
        following=center[min(i+1,len(center)-1)]
        dx,dy=following[0]-previous[0],following[1]-previous[1]
        length=hypot(dx,dy)
        nx,ny=-dy/length,dx/length
        upper.append((x+r*nx,y+r*ny,z))
        lower.append((x-r*nx,y-r*ny,z))
        fringe.append((x-(r+fur)*nx,y-(r+fur)*ny,z))
    return center,upper,lower,fringe


def draw_board(profiles):
    # Keep the original 6px per body unit, widening all columns equally if needed.
    layouts={}
    column=454
    for key,breed in profiles.items():
        frames=world_frames(breed)
        p={k:v[0] for k,v in frames.items()}
        tail=tail_envelope(breed['tail_profile'],p)
        xs=[v[0] for v in p.values()]+[v[0] for edge in tail[1:] for v in edge]
        column=max(column,ceil((max(xs)-min(xs))*6)+52)
        layouts[key]=(frames,p,tail,(min(xs)+max(xs))*.5)
    width=48+3*column
    image = Image.new('RGB',(width,880),PAPER)
    draw = ImageDraw.Draw(image)
    def label(x,y,txt,size,bold=False,color=INK):
        f = ImageFont.truetype(str(FONT/('malgunbd.ttf' if bold else 'malgun.ttf')),size)
        draw.text((x,y),txt,font=f,fill=color)
    def dot(p,r,c,fill=PAPER):
        x,y=p
        draw.ellipse((x-r,y-r,x+r,y+r),outline=c,fill=fill,width=2)

    label(38,20,'B형 전신 골격',38,True)
    label(39,84,'골반에서 흉곽과 목을 거쳐 얼굴까지 연결한 세 품종의 기본 서기',21,color=SUB)

    for index, key in enumerate(('whippet','dachshund','golden')):
        breed=profiles[key]
        frames,p,tail,mid=layouts[key]
        x0=38+index*column
        draw.line((x0,144,x0+column-28,144),fill=TEAL,width=3)
        label(x0,156,breed['name'],27,True)
        label(x0+column-142,175,'전신  /  측면',16,True,SUB)
        def side(v): return (round(x0+(column-28)/2+(v[0]-mid)*6),round(555-v[1]*6))
        def mapped(ids,project):
            return [project(p[n]) for n in ids]
        def path(ids,project,color=INK,width=3):
            draw.line(mapped(ids,project),fill=color,width=width,joint='curve')
        def polygon(points,fill,outline):
            draw.polygon(points,fill=fill)
            draw.line(points+points[:1],fill=outline,width=2,joint='curve')
        def b(names):return ['body.'+n for n in names.split()]
        def f(names):return ['face.'+n for n in names.split()]

        draw.line((x0+12,556,x0+column-40,556),fill='#D8DDD3',width=2)
        center,upper,lower,fringe=tail
        if any(breed['tail_profile']['underside_feather']):
            polygon([side(v) for v in lower+fringe[::-1]],'#E5CFAD','#B39C7E')
        polygon([side(v) for v in upper+lower[::-1]],'#FAEFDA','#A68C69')
        draw.line([side(v) for v in center],fill='#754B31',width=2,joint='curve')
        for name,fill,outline in [('ribcage',RIB,TEAL),('pelvis',PELVIS,SUB)]:
            surf=breed['surfaces'][name]
            pts=[side(project_offset(frames[surf['owner']],v)) for v in surf['offsets']]
            polygon(pts,fill,outline)
        def guide(name):
            g=breed[name]
            return side(project_offset(frames[g['owner']],g['offset']))
        def dotted(points,color):
            for a,bp in zip(points,points[1:]):
                length=max(1,((a[0]-bp[0])**2+(a[1]-bp[1])**2)**.5)
                for i in range(0,int(length),7):
                    ends=[tuple(round(v+(w-v)*min(t/length,1)) for v,w in zip(a,bp)) for t in (i,i+3)]
                    draw.line(ends,fill=color,width=2)
        draw.line(mapped(b('ribcage lumbar_pivot'),side)+[guide('pelvic_dorsum'),side(p['body.tail_root'])],fill=TEAL,width=2)
        dotted([guide('rear_brisket'),guide('belly_guide'),side(p['body.left_hip'])],SUB)
        path(b('ribcage neck head'),side,SUB,4)
        # The contralateral limbs coincide exactly in this neutral side projection.
        for chain in ('left_scapula_fixed left_shoulder left_elbow left_carpus left_mcp left_foretoe',
                      'left_hip left_stifle left_tarsus left_mtp left_hindtoe'):
            ids=b(chain);path(ids,side)
            for n in ids[:-1]:dot(side(p[n]),3,INK)
        skull=f('occiput crown L_brow stop nose upper_lip chin L_jaw_side L_cheek neck_mount')
        polygon(mapped(skull,side),FACE,SUB)
        ear=f('L_ear_root L_ear_fold L_ear_tip')
        path(ear,side,TEAL,2)
        path(f('L_jaw_hinge L_jaw_side chin'),side,INK,2)
        path(f('upper_lip L_mouth_corner'),side,INK,2)
        dot(side(p['face.L_eye']),2,INK,INK)
        dot(side(p['face.nose']),2,TEAL,TEAL)
        for n in ('body.lumbar_pivot','face.neck_mount'):
            dot(side(p[n]),5,JOIN)
        label(x0,582,'같은 골격의 얼굴  /  정면 확대',15,True,SUB)
        # Frontal projection uses anatomical left/right (third world axis).
        fpts=[v for n,v in p.items() if n.startswith('face.')]
        face_mid=.5*(max(v[1] for v in fpts)+min(v[1] for v in fpts))
        def front(v): return (round(x0+(column-28)/2+v[2]*10),round(702-(v[1]-face_mid)*10))
        polygon(mapped(f('crown L_brow L_temple L_cheek L_jaw_side chin R_jaw_side R_cheek R_temple R_brow'),front),FACE,SUB)
        for s in ('L','R'):
            def sn(parts):return f(' '.join(s+'_'+part for part in parts.split()))
            ear=sn('ear_root ear_fold ear_tip')
            path(ear,front,TEAL,2)
            dot(front(p[ear[0]]),3,TEAL)
            polygon(mapped(sn('eye_inner upper_lid eye_outer lower_lid'),front),PAPER,INK)
            dot(front(p['face.'+s+'_pupil']),2,INK,INK)
            path(sn('eye_inner muzzle_side nose_wing'),front,SUB,2)
            path(['face.'+s+'_mouth_corner','face.upper_lip'],front,INK,2)
        polygon(mapped(f('R_nose_wing L_nose_wing nose_bottom'),front),TEAL,TEAL)
        path(f('R_jaw_side chin L_jaw_side'),front,INK,2)
    draw.line((38,796,width-40,796),fill='#CBD4C9',width=1)
    label(39,810,'초록 면은 흉곽, 회록색 면은 골반. 전신의 주황색 고리는 허리 회전축과 목·머리 접점을 표시한다.',18,color=SUB)
    label(39,846,'갈색 선은 꼬리뼈 중심선, 베이지색 바깥 면은 장식털이다. 닥스훈트의 꼬리는 사진에서 가려져 단모형의 품종 기준으로 추정했다.',15,color=SUB)
    return image


if __name__=='__main__':
    rig=json.loads((HERE/'rigs.json').read_text(encoding='utf-8'))
    draw_board(rig['breeds']).save(HERE/'comparison.png')

