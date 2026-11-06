"""Breed-starting facial rigs. Coordinates are illustration defaults, not measurements."""
import json, math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

out=Path(__file__).resolve().parent
# skull half width, eye offset, eye half width, eye height, nose half width,
# muzzle half width, nasal reach, muzzle depth, stop height, ear set height
spec={
 'whippet':('휘핏',(12,8,2.6,19,3.7,5.3,28,5,18,15),'작고 뒤로 접힌 귀','가늘어지는 얼굴과 긴 콧등','https://www.ukcdogs.com/whippet'),
 'dachshund':('닥스훈트',(13,8.5,2.3,20,4.0,6.0,30,6,19,14),'높은 귀뿌리와 둥글게 내려오는 귀끝','길게 이어지는 주둥이','https://www.ukcdogs.com/dachshund'),
 'golden':('골든 리트리버',(17,11,2.7,20,5.5,9,25,9,16,19),'눈높이에서 볼 쪽으로 내려오는 귀','넓은 눈 간격과 깊은 주둥이','https://www.royalkennelclub.org.uk/breed-standards/gundog/retriever-golden/')}
def build(key):
    name,params,_,_,url=spec[key]
    w,e,ew,ey,n,m,z,depth,stop_y,ear_y=params
    p={'neck_mount':(0,33,-10),'skull':(0,21,0),'crown':(0,9,-3),
       'occiput':(0,13,-10),'nose_bottom':(0,26.7,z),
       'stop':(0,stop_y,8),'nose':(0,25,z),'upper_lip':(0,27,z-1),
       'chin':(0,25+depth,z-2)}
    parents={'neck_mount':'body.head','skull':'neck_mount','crown':'skull','occiput':'skull','stop':'skull','nose':'stop','nose_bottom':'nose','upper_lip':'stop','jaw_axis':'skull','chin':'jaw_axis'}
    for side,s in [('L',1),('R',-1)]:
        local={'brow':(.65*w,10,-.5),'eye':(e,ey,7),'eye_inner':(e-ew,ey+.5,7.8),'eye_outer':(e+ew,ey-.5,6),
               'upper_lid':(e,ey-1.45,7.5),'lower_lid':(e,ey+1.1,7.5),'pupil':(e,ey,7.6),
               'temple':(w,15,-3),'cheek':(.88*w,27,0),'nose_wing':(n,25,z-.8),
               'ear_root':(.9*w,ear_y,-5),'jaw_hinge':(.8*w,24,-7),
               'mouth_corner':(.68*w,27,6),'muzzle_side':(m,25,16),
               'jaw_side':(.88*m,25+depth-1,15)}
        fold,tip={'whippet':((w+4,13,-10),(w+4,18,-15)),
                  'dachshund':((w+5,23,-11),(w+2,38,-7)),
                  'golden':((w+4,23,-9),(w+1,32,-6))}[key]
        local.update(ear_fold=fold,ear_tip=tip)
        for n1,(x,y,d) in local.items():
            node=side+'_'+n1;p[node]=(s*x,y,d)
            parent={'eye_inner':'eye','eye_outer':'eye','upper_lid':'eye','lower_lid':'eye','pupil':'eye',
                    'ear_fold':'ear_root','ear_tip':'ear_fold'}.get(n1)
            parents[node]=(side+'_'+parent if parent else {'jaw_side':'jaw_axis','nose_wing':'nose','muzzle_side':'stop','mouth_corner':'skull'}.get(n1,'skull'))
    return dict(name=name,source=url,anchors=p,parents=parents,jaw_axis=['R_jaw_hinge','L_jaw_hinge'])
rigs={k:build(k) for k in spec}
def lower(p,angle):
    # Rotation about the anatomical right-left line through both jaw hinges.
    x,y,z=p; u=y-24;v=z+7;a=math.radians(angle)
    return (x,24+u*math.cos(a)+v*math.sin(a),-7-u*math.sin(a)+v*math.cos(a))
paper='#F9F8F3';line='#30463F';teal='#287965';sage='#D8E6DA';rust='#A64B32';soft='#718578'
im=Image.new('RGB',(1240,880),paper);d=ImageDraw.Draw(im)
def label(pos,s,size,color=line,bold=False):
    f=ImageFont.truetype('C:/Windows/Fonts/malgun'+('bd' if bold else '')+'.ttf',size)
    d.text(pos,s,font=f,fill=color)
def view(r,ox,oy,profile):
    p=r['anchors']
    def xy(v):
        x,y,z=v
        return (round(ox+(-z if profile else x)*4.7),round(oy+y*4.7))
    def pts(names):return [xy(p[n]) for n in names.split()]
    def path(names,col=line,width=3):d.line(pts(names),fill=col,width=width,joint='curve')
    def face(names,fill):
        a=pts(names);d.polygon(a,fill=fill);d.line(a+a[:1],fill=line,width=2,joint='curve')
    def dot(n,c=teal,rad=4):
        x,y=xy(p[n]);d.ellipse((x-rad,y-rad,x+rad,y+rad),fill=c,outline=paper,width=1)
    if profile:
        face('neck_mount L_jaw_hinge occiput crown L_brow stop nose upper_lip L_mouth_corner L_cheek', '#E8ECE1')
        face('L_ear_root L_ear_fold L_ear_tip L_ear_root',sage)
        path('stop nose',teal);dot('stop');dot('nose')
        path('L_jaw_hinge L_jaw_side chin upper_lip',line)
        path('L_mouth_corner upper_lip',line)
        open_pts=[xy(lower(p[n],12)) for n in ['L_jaw_hinge','L_jaw_side','chin']]
        d.line(open_pts,fill=rust,width=4)
        for n in ['L_jaw_hinge','L_mouth_corner']:dot(n,rust)
        dot('L_eye',line);dot('L_ear_root');dot('L_ear_fold');dot('L_ear_tip');dot('neck_mount',soft)
    else:
        face('crown L_brow L_temple L_cheek L_jaw_side chin R_jaw_side R_cheek R_temple R_brow','#E8ECE1')
        for s in ['L','R']:
            root,fold,tip=[s+'_'+n for n in ['ear_root','ear_fold','ear_tip']]
            a,b,c=pts(' '.join([root,fold,tip]))
            w=(1 if s=='L' else -1)*(6 if r['name']=='휘핏' else 15)
            d.polygon([a,(b[0]+w,b[1]),(c[0]+w,c[1]-8),(c[0]+w*.6,c[1]-1),c,(c[0]-w*.55,c[1]-4),(c[0]-w*.7,c[1]-12)],fill=sage,outline=soft)
            path(' '.join([root,fold,tip]),teal,2)
            for n in [root,tip]:dot(n)
            face(' '.join(s+'_'+n for n in ['eye_inner','upper_lid','eye_outer','lower_lid']),paper)
            dot(s+'_pupil',line,3)
            path(s+'_eye_inner '+s+'_muzzle_side '+s+'_nose_wing',soft,2)
            path(s+'_mouth_corner upper_lip',line,2);dot(s+'_mouth_corner',rust,3)
        face('R_nose_wing L_nose_wing nose_bottom',teal);dot('stop');dot('nose')
        path('R_jaw_side chin L_jaw_side',rust,2)
label((36,18),'공통 얼굴 골격과 품종별 비율',34,line,True)
label((38,75),'같은 기준점을 정면과 왼쪽을 향한 측면에 투영했다. 세 얼굴의 눈금과 턱 열림 각도는 같다.',18)
for i,(k,r) in enumerate(rigs.items()):
    x=33+405*i;d.line((x,130,x+366,130),fill=teal,width=3)
    label((x,145),r['name'],28,line,True)
    label((x,206),'01   정면  ·  눈 간격과 귀의 접힘',16,soft)
    view(r,x+172,240,False)
    label((x,450),'02   측면  ·  콧등과 아래턱의 회전',16,soft)
    view(r,x+212,473,True)
    d.line((x,699,x+366,699),fill='#C7D1C6')
    label((x,721),spec[k][2],18,line,True);label((x,758),spec[k][3],17)
label((35,817),'초록  귀·콧등 기준점       주황  입꼬리·아래턱 (측면은 12° 열림)       회색 점  목 연결점',17)
label((35,849),'좌표는 품종 표준과 기존 사진을 참고한 설계값이다. 개체별 사진에서 확인한 비율을 우선한다.',15,soft)
im.save(out/'comparison.png')
(out/'rigs.json').write_text(json.dumps(rigs,ensure_ascii=False,indent=2),encoding='utf-8')
