"""Render three independent rig proposals on the same 64-unit pose grid."""
from pathlib import Path
from math import hypot,cos,sin,radians,sqrt
from PIL import Image, ImageDraw, ImageFont
import json

OUT=Path(__file__).resolve().parent
PAPER='#F8F7F2'; INK='#203633'; TEAL='#247467'; FILL='#CFE3D7'
LIGHT='#E6E9DE'; MUTED='#687972'; RUST='#B85835'
fontroot=Path('C:/Windows/Fonts')
def font(n,b=False): return ImageFont.truetype(str(fontroot/('malgunbd.ttf' if b else 'malgun.ttf')),n)
def text(d,xy,s,n=18,c=INK,b=False): d.text(xy,s,font=font(n,b),fill=c)
def rot(p,a,origin):
    x,y=p[0]-origin[0],p[1]-origin[1];t=radians(a)
    return (origin[0]+x*cos(t)-y*sin(t),origin[1]+x*sin(t)+y*cos(t))
def dist(a,b): return hypot(a[0]-b[0],a[1]-b[1])
def elbow(s,w,l1,l2):
    dx,dy=w[0]-s[0],w[1]-s[1];span=hypot(dx,dy)
    assert abs(l1-l2)<span<l1+l2,(s,w,l1,l2,span)
    u=(l1*l1-l2*l2+span*span)/(2*span);h=sqrt(l1*l1-u*u)
    return (s[0]+(u*dx+h*dy)/span,s[1]+(u*dy-h*dx)/span)
rigs={
 'A':dict(title='몸통 한 덩어리',structure='몸통 1개에 네 다리와 목을 연결',control='몸통 고정  /  앞다리만 굽힘',use='정지 자세에서 체형 비율을 맞추기 쉽다.',limit='가슴만 따로 들 수 없다.',
          graph={'body':['neck','near_scapula_fixed','far_scapula_fixed','near_hip','far_hip','tail_root']}),
 'B':dict(title='흉곽과 골반 분리',structure='골반과 흉곽 사이에 허리 회전축 추가',control='허리 +12°  /  양어깨와 목이 함께 이동',use='앉거나 일어날 때 가슴 기울기를 조절한다.',limit='양쪽 어깨가 흉곽을 함께 따라간다.',
          graph={'pelvis':['lumbar_pivot','near_hip','far_hip','tail_root'],'lumbar_pivot':['ribcage'],'ribcage':['neck','near_scapula_fixed','far_scapula_fixed']}),
 'C':dict(title='좌우 견갑 독립',structure='단일 몸통에 좌우 견갑 회전축을 각각 연결',control='가까운 견갑 +25°  /  반대 어깨 고정',use='한쪽 앞발을 뻗을 때 어깨부터 움직인다.',limit='좌우 견갑을 각각 맞춰야 한다.',
          graph={'body':['neck','near_scapular_pivot','far_scapular_pivot','near_hip','far_hip','tail_root'],'near_scapular_pivot':['near_scapula'],'far_scapular_pivot':['far_scapula']})
}
base={'near':[(28,29),(22,36),(26,43),(24,53),(22,56),(19,57)],
      'far':[(25,28),(19,34),(25,40),(19,49),(17,52),(14,53)]}
lumbar=(37,37); pelvis=(45,43)
def pose(k,lift):
    ang=12 if k=='B' and lift else 0
    chest=lambda p:rot(p,ang,lumbar)
    limbs={}
    for side,(top,s,e,w,m,t) in base.items():
        top1,s1=chest(top),chest(s)
        if k=='C' and lift and side=='near':
            s1=rot(s1,25,top1)
        dx,dy=(-4,-7) if lift and side=='near' else (0,0)
        foot=[(x+dx,y+dy) for x,y in (w,m,t)]
        bend=elbow(s1,foot[0],dist(s,e),dist(e,w))
        limbs[side]=[top1,s1,bend,*foot]
        assert abs(dist(s1,bend)-dist(s,e))<1e-6 and abs(dist(bend,foot[0])-dist(e,w))<1e-6
    return chest,limbs

def diagram(k,lift):
    im=Image.new('RGB',(320,320),PAPER);d=ImageDraw.Draw(im)
    def pt(p):return (round(p[0]*5),round(p[1]*5))
    def line(ps,color=INK,w=4):d.line([pt(p) for p in ps],fill=color,width=w,joint='curve')
    def poly(ps,fill,edge):d.polygon([pt(p) for p in ps],fill=fill);line(ps+ps[:1],edge,3)
    def joint(p,stroke=INK,r=4,fill=PAPER):
        x,y=pt(p);d.ellipse((x-r,y-r,x+r,y+r),fill=fill,outline=stroke,width=2)
    ch,limbs=pose(k,lift)
    for toe in ([base['far'][-1],(36,56)] + ([] if lift else [base['near'][-1]])):
        x,y=toe; line([(x-1,y+.3),(x+2,y+.3)],'#9CAC9F',3)
    # The far hindlimb is modeled but occluded in this 3/4 projection.
    line(limbs['far'],MUTED,3)
    for p in limbs['far'][1:-1]:joint(p,MUTED,3)
    line([(47,44),(52,48),(54,53),(58,55),(61,52)],MUTED)
    if k=='B':
        poly([(39,38),(45,39),(50,43),(48,47),(43,47),(40,44)],LIGHT,MUTED)
        poly([ch(p) for p in [(24,29),(29,26),(34,29),(37,35),(34,40),(29,40),(24,37)]],FILL,TEAL)
        line([ch((31,32)),lumbar,pelvis],TEAL,4);joint(lumbar,RUST,8)
    else:
        poly([(23,31),(28,27),(33,29),(40,35),(48,40),(50,44),(47,47),(42,46),(34,40),(26,39),(22,36)],FILL,TEAL)
        line([(28,31),(45,43)],TEAL,3)
    # Independent head, shared ground contacts and identical world-space target.
    line([ch((28,31)),ch((24,25)),ch((21,21))],MUTED,5)
    poly([ch(p) for p in [(11,18),(14,16),(17,12),(22,11),(25,13),(26,17),(24,21),(20,23),(17,21),(12,21),(9,20)]],LIGHT,MUTED)
    line([ch((23,13)),ch((26,14)),ch((25,17))],MUTED,3)
    line([ch((12,19)),ch((16,19))],MUTED,2)
    hind=[(45,43),(37,47),(47,52),(40,55),(36,56)]
    line(hind);[joint(p) for p in hind[:-1]]
    # Red denotes the mechanism highlighted in each proposal.
    near=limbs['near']
    if k=='C':
        far=limbs['far']
        line(far[:2],RUST,4);joint(far[0],RUST,6)
        line(near[:2],RUST,7);joint(near[0],RUST,7)
    else: line(near[:2],TEAL,5)
    line(near[1:])
    for p in near[1:-1]:joint(p)
    if k=='A':joint((37,37),TEAL,5,TEAL)
    if lift:
        old=base['near'][-1]
        joint(old,MUTED,4)
        joint(near[-1],RUST,5,RUST)
    return im

def draw_card(k):
    v=rigs[k];im=Image.new('RGB',(396,930),PAPER);d=ImageDraw.Draw(im)
    d.line((8,2,383,2),fill=TEAL,width=3)
    text(d,(10,17),k,30,TEAL,True);text(d,(55,17),v['title'],27,INK,True)
    text(d,(10,66),v['structure'],16)
    text(d,(10,108),'01   기준 자세',15,MUTED,True)
    im.paste(diagram(k,False),(30,124))
    text(d,(10,443),'02   같은 앞발 들기',15,MUTED,True)
    im.paste(diagram(k,True),(30,463))
    text(d,(10,780),v['control'],16,RUST,True)
    d.line((10,826,380,826),fill='#CCD4CB')
    text(d,(10,845),v['use'],16);text(d,(10,880),v['limit'],16,MUTED)
    return im

board=Image.new('RGB',(1280,1110),PAPER);d=ImageDraw.Draw(board)
text(d,(36,15),'앉은 개의 공통 골격 구조 3안',34,INK,True)
text(d,(37,74),'같은 체형과 시작 자세에서 가까운 앞발을 앞으로 4칸, 위로 7칸 옮긴다. 나머지 발은 고정한다.',19)
for i,k in enumerate(rigs):
    card=draw_card(k);card.save(OUT/f'{k}.png');board.paste(card,(35+409*i,130))
text(d,(38,1065),'64칸 설계 격자  ·  관절 위치와 각도는 구조 비교용 작화값  ·  빈 점은 이전 발끝, 주황 점은 새 발끝',16,MUTED)
board.save(OUT/'comparison.png')
for side in ('near','far'):
    for k,r in rigs.items():
        g=r['graph'];blade=f'{side}_scapula'+('' if k=='C' else '_fixed')
        chain=[blade,*[f'{side}_{n}' for n in ('shoulder','elbow','carpus','mcp','foretoe')]]
        leg=[f'{side}_{n}' for n in ('hip','stifle','tarsus','mtp','hindtoe')]
        for path in (chain,leg):
            for a,b in zip(path,path[1:]):g[a]=[b]
for k,r in rigs.items():
    r['graph'].update(neck=['head'],tail_root=['tail_mid'],tail_mid=['tail_tip'])
    r['front_chains']={name:pose(k,lift)[1] for name,lift in [('rest',False),('lift',True)]}
(OUT/'rigs.json').write_text(json.dumps(rigs,ensure_ascii=False,indent=2),encoding='utf-8')


