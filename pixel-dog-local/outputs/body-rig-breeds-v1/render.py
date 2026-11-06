"""Neutral standing body proportions; shoulder-to-hip horizontal span = 30 units."""
from pathlib import Path
import json, math
from PIL import Image, ImageDraw, ImageFont
out=Path(__file__).resolve().parent
# Height above floor in side projection, depths and breadths in the same design units.
# Order: withers, shoulder, elbow, hip, knee, hock, rib depth, rib length, rib width,
# pelvis width, belly rise relative to the brisket, longitudinal offset of lumbar control.
data={
 'whippet':('휘핏',(39,31,21,32,21,9,18,19,10,9,9,24),'깊은 가슴 뒤로 배선이 올라간다.','아래팔과 뒷다리 마디를 길게 둔다.','https://www.ukcdogs.com/whippet'),
 'dachshund':('닥스훈트',(21,16,9,17,11,5,13,22,10,8,2,25),'몸통 길이에 비해 다리가 짧다.','가슴 아래와 바닥 사이 간격이 작다.','https://www.ukcdogs.com/dachshund'),
 'golden':('골든 리트리버',(34,27,18,28,18,8,16,22,15,12,3,25),'흉곽이 깊고 폭이 있으며 허리가 짧다.','가슴 뒤로 이어지는 배선이 완만하다.','https://grca.org/find-a-golden/more-topics-before-you-buy/akc-breed-standard/')}
PAPER='#F8F7F2';INK='#233B36';TEAL='#267664';FILL='#CFE4D8';MUTED='#67796E';RUST='#AB5438';PELV='#E4E7D8'
board=Image.new('RGB',(1260,762),PAPER);pen=ImageDraw.Draw(board)
def label(x,y,s,size,b=False,col=INK):
    f=ImageFont.truetype('C:/Windows/Fonts/malgun'+('bd' if b else '')+'.ttf',size)
    pen.text((x,y),s,font=f,fill=col)
def to_points(points,transform):return [tuple(round(a) for a in transform(p)) for p in points]
def wire(points,transform,c=INK,w=3):pen.line(to_points(points,transform),fill=c,width=w,joint='curve')
def node(p,transform,c=INK,r=3):
    (x,y),=to_points([p],transform);pen.ellipse((x-r,y-r,x+r,y+r),fill=PAPER,outline=c,width=2)
def plate(points,transform,fill,c):
    coords=to_points(points,transform);pen.polygon(coords,fill=fill);pen.line(coords+[coords[0]],fill=c,width=2,joint='curve')
def dotted(a,b,T):
    for i in range(0,12,3):
        wire([tuple(a[j]+(b[j]-a[j])*t/12 for j in (0,1)) for t in [i,i+1.6]],T,MUTED,2)
label(36,16,'몸통 골격의 품종별 비율',34,True)
label(37,72,'왼쪽을 향한 기본 서기  ·  어깨관절과 고관절 사이의 가로 거리를 같게 맞춰 체형을 비교했다.',19)
base_rig=json.loads((out.parent/'skeleton-structures-v1/rigs.json').read_text(encoding='utf8'))['B']['graph']
profiles={}
for i,(key,(name,values,first,second,url)) in enumerate(data.items()):
    H,S,E,G,K,T,D,L,W,P,U,J=values;x=33+410*i
    # Origin at shoulder horizontal coordinate. Toe height = 0.
    brisk=H-D; lumbar=(J,H+(1 if key=='whippet' else -1))
    rib=[(-3,S+2),(0,H-1),(4,H),(L-4,H-1),(L,H-3),(L-1,brisk+5),(L-5,brisk+2),(5,brisk),(0,brisk+1),(-3,brisk+4)]
    pelvis=[(J+1,G+3),(28,G+5),(33,G+3),(35,G),(32,G-3),(28,G-2)]
    fore=[(5,H),(0,S),(5,E),(4,4 if key!='dachshund' else 2.5),(3,1),(0,0)]
    hind=[(30,G),(25,K),(34,T),(33,2),(30,0)]
    neck=[(5,H),(-2,H+3),(-5 if key=='dachshund' else -7,H+(5 if key=='dachshund' else 8))]
    tpts=[(34,G+1),(38,G),(41,G-3)]
    waist=(25,brisk+U)
    def Tside(p):return(x+83+p[0]*6,462-p[1]*6)
    def Ttop(p):return(x+83+p[0]*6,558+p[1]*6)
    pen.line((x,122,x+375,122),fill=TEAL,width=3);label(x,136,name,27,True)
    label(x,189,'측면',15,True,MUTED)
    wire([(-8,0),(43,0)],Tside,'#C9D3C8',2)
    plate(rib,Tside,FILL,TEAL);plate(pelvis,Tside,PELV,MUTED)
    wire([(5,H),(L-2,H-1),lumbar,(28,G+5),(34,G+1)],Tside,TEAL)
    wire(neck,Tside,MUTED);node(neck[-1],Tside,MUTED)
    wire(tpts,Tside,MUTED)
    for a,b in zip([(L-5,brisk+2),waist],[waist,(30,G-3)]):dotted(a,b,Tside)
    for chain in [fore,hind]:
        wire(chain,Tside)
        for p in chain[:-1]:node(p,Tside)
    node(lumbar,Tside,RUST,5)
    label(x,488,'위에서 본 흉곽과 골반',15,True,MUTED)
    def outline(section):
        return [(a,-w/2) for a,w in section]+[(a,w/2) for a,w in reversed(section)]
    rp=outline([(-3,W*.35),(2,W*.88),(8,W),(L-4,W*.85),(L,W*.56)])
    pp=outline([(J+1,P*.65),(29,P),(33,P*.93),(35,P*.48)])
    plate(rp,Ttop,FILL,TEAL);plate(pp,Ttop,PELV,MUTED)
    wire([(-3,0),(35,0)],Ttop,TEAL,2);node((J,0),Ttop,RUST,5)
    label(x,612,first,17,True);label(x,648,second,17)
    profiles[key]=dict(name=name,source=url,side_ribcage=rib,side_pelvis=pelvis,lumbar_pivot=lumbar,
        side_forelimb=fore,side_hindlimb=hind,neck_to_face=neck,top_ribcage=rp,top_pelvis=pp,
        tail=tpts,belly_guide=waist,shoulder_hip_span=30)
label(35,704,'초록 면  흉곽     회록색 면  골반     주황 원  허리 회전축     점선  배 윤곽 참고선',16,False,MUTED)
label(35,734,'같은 B형 연결 구조를 쓴 설계 예시. 좌표와 폭은 작화용 추정값이며 실제 크기는 개체 사진에서 따로 맞춘다.',15,False,MUTED)
board.save(out/'comparison.png')
(out/'rigs.json').write_text(json.dumps(dict(topology=base_rig,units='projected illustration units, 30-unit horizontal shoulder-hip span',profiles=profiles),ensure_ascii=False,indent=2),encoding='utf8')

