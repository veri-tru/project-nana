"""Shared 3D craniofacial control scaffold, not a measured osteological mesh."""
from pathlib import Path
import json
import numpy as np
from scipy.interpolate import PchipInterpolator
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
FONT=Path('C:/Windows/Fonts/malgun.ttf')
BOLD=Path('C:/Windows/Fonts/malgunbd.ttf')
BG='#f8f7f2';INK='#283831';BLUE='#286c88';ORANGE='#b85e38';GREEN='#508371';PALE='#c5cfcd';GREY='#8c9995'
BREEDS=['golden','whippet','dachshund','maltipoo']
NAMES=['골든 리트리버','휘핏','닥스훈트','말티푸']
CHAIN=['crown','forehead','stop','nasal_bridge','nasal_base','nose_tip']
LABELS=['정수리','이마','이마–주둥이 전이','콧등','코연골 기저','코끝']

def make_rig(p):
    nodes={}
    def add(name,point,group='cranium',kind='structural_guide'):
        nodes[name]={'parent':group,'point':list(map(float,point)),'kind':kind}
    add('cranium',[0,0,0],'body.head','rigid_group')
    for key,xy in zip(CHAIN,p['dorsal']):
        add(key,[*xy,0],kind='soft_tissue_anchor' if key in ('nasal_base','nose_tip') else 'craniofacial_shape_landmark')
    add('occiput',[1,13,0]);add('skull_rear',[1,p['dorsal'][0][1]*.75,0])
    add('maxilla_back',[p['dorsal'][2][0]+9,3.5,0])
    add('maxilla_front',[p['dorsal'][4][0]+2,3.5,0])
    add('nasal_floor',[p['dorsal'][5][0]+1,7,0])
    add('jaw_axis',[p['hinge_x'],10,0],kind='revolute_axis_center')
    add('mandible',[0,0,0],'jaw_axis','rigid_group')
    add('chin',[p['dorsal'][4][0]+1,-2,0],'mandible')
    for side,sign in [('L',1),('R',-1)]:
        add(side+'_tmj',[p['hinge_x'],10,sign*p['widths'][0]*.8],kind='joint_center')
        add(side+'_orbit',[p['dorsal'][1][0]+2,19,sign*p['widths'][1]*.85],kind='orbital_position_guide')
        add(side+'_ear_root',[-8,24,sign*p['widths'][0]*.9],kind='cartilage_attachment_guide')
        add(side+'_zygoma',[-20,7,sign*p['widths'][0]],kind='zygomatic_position_guide')
        add(side+'_ramus',[p['hinge_x']-5,0,sign*p['widths'][0]*.75],'mandible')
        add(side+'_jaw_body',[p['dorsal'][2][0]+4,-4,sign*p['widths'][2]*.85],'mandible')
        add(side+'_jaw_front',[p['dorsal'][4][0]+3,-2,sign*p['widths'][4]*.7],'mandible')
    add('C1',[5,4,0],'body.head','cervical_guide')
    add('C2',[12,-11,0],'body.head','cervical_guide')
    return {'nodes':nodes,'dorsal_guide':CHAIN,'widths':p['widths'],
            'coordinate_note':'x caudal, y dorsal, z animal left; points in shared head-local rest space; parent declares motion ownership',
            'scope':'authored 3D control scaffold, not measured bones or finished skin'}

def point(rig,name,angle=0):
    n=rig['nodes'][name];p=np.array(n['point'],float)
    if n['parent']=='mandible':
        a=np.radians(angle);rot=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]])
        h=np.array(rig['nodes']['jaw_axis']['point']);p=(p-h)@rot.T+h
    return p

def curve(points,count=100):
    points=np.asarray(points,float)
    t=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
    return PchipInterpolator(t,points,axis=0)(np.linspace(0,t[-1],count))

def geometry(rig,angle=0):
    """Every drawn line is made from the same 3D rig, before projection."""
    lines=[]
    def add(names,color,width=2,smooth=True,move=0):
        pts=np.array([point(rig,k) for k in names]);pts=curve(pts) if smooth else pts
        if move:
            a=np.radians(move);rot=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]])
            h=point(rig,'jaw_axis');pts=(pts-h)@rot.T+h
        lines.append((pts,color,width))
    # Fixed dorsal rail is a shape guide, not six independently rotating bones.
    add(['occiput','skull_rear']+CHAIN,BLUE,4)
    add(['nose_tip','nasal_floor','maxilla_front','maxilla_back','occiput'],BLUE,2)
    for index,key in enumerate(CHAIN[:-1]):
        p=point(rig,key);bottom=3.5 if index>0 else 2
        theta=np.linspace(0,2*np.pi,101);cy=(p[1]+bottom)/2;ry=(p[1]-bottom)/2
        ring=np.column_stack([theta*0+p[0],cy+ry*np.cos(theta),rig['widths'][index]*np.sin(theta)])
        lines.append((ring,PALE,1))
    for side,sign in [('L',1),('R',-1)]:
        add(['occiput',side+'_zygoma','maxilla_front'],GREY,2)
        c=point(rig,side+'_orbit');t=np.linspace(0,2*np.pi,70)
        orbit=c+np.column_stack([4*np.cos(t),5*np.sin(t),sign*4*np.cos(t)])
        lines.append((orbit,GREY,2))
        add([side+'_tmj',side+'_ramus',side+'_jaw_body',side+'_jaw_front','chin'],ORANGE,3,move=angle)
    add(['L_tmj','R_tmj'],ORANGE,1,False)
    add(['occiput','C1','C2'],GREEN,3)
    return lines

def project(points,view):
    p=np.asarray(points)
    if view=='side':return p[:,[0,1]]*np.array([1,-1])
    if view=='front':return p[:,[2,1]]*np.array([1,-1])
    if view=='top':return p[:,[0,2]]
    raise ValueError(view)

def text(im,xy,s,size=20,color=INK,bold=False):
    ImageDraw.Draw(im).text(xy,s,font=ImageFont.truetype(str(BOLD if bold else FONT),size),fill=color)

def draw_rig(im,rig,view,origin,scale,angle=0,numbers=False):
    d=ImageDraw.Draw(im)
    for pts,color,width in geometry(rig,angle):
        xy=project(pts,view)*scale+origin
        d.line([tuple(p) for p in xy],fill=color,width=width,joint='curve')
    for index,key in enumerate(CHAIN):
        q=project([point(rig,key)],view)[0]*scale+origin
        d.ellipse((q[0]-4,q[1]-4,q[0]+4,q[1]+4),fill=BLUE)
        if numbers:text(im,(q[0]-7,q[1]-25),str(index+1),16,BLUE,True)
    for key in ['L_tmj','R_tmj','L_ear_root','R_ear_root']:
        q=project([point(rig,key)],view)[0]*scale+origin;c=ORANGE if 'tmj' in key else GREY
        d.ellipse((q[0]-4,q[1]-4,q[0]+4,q[1]+4),outline=c,width=2)

def boards(rigs):
    im=Image.new('RGB',(1660,1470),BG)
    text(im,(30,24),'머리 골격부터 다시 · 네 개체, 같은 연결 구조',30,bold=True)
    text(im,(30,72),'파랑: 고정 두개골·위턱  /  주황: 아래턱  /  초록: 뒤통수–경추  /  회색: 폭·눈·귀 부착 가이드',18)
    text(im,(30,103),'정수리·이마·코끝은 형태 기준점입니다. 점마다 회전하는 관절을 뜻하지 않습니다.',17)
    for j,title in enumerate(['측면','정면','윗면']):text(im,(70+550*j,150),title,22,bold=True)
    for i,(b,name) in enumerate(zip(BREEDS,NAMES)):
        y=198+305*i;ImageDraw.Draw(im).line((25,y,1630,y),fill='#d7ddd7')
        text(im,(30,y+10),name,21,bold=True)
        draw_rig(im,rigs[b],'side',np.array([465,y+192]),3.3,numbers=True)
        draw_rig(im,rigs[b],'front',np.array([805,y+192]),3.3)
        draw_rig(im,rigs[b],'top',np.array([1580,y+168]),3.3)
    text(im,(30,1430),'1 정수리   2 이마   3 이마–주둥이 전이   4 콧등   5 코연골 기저   6 코끝  ·  비율은 제작값, 실측 해골 복제 아님',17)
    detail=Image.new('RGB',(1360,850),BG)
    text(detail,(32,25),'정수리에서 코끝까지 · 하나의 고정된 머리 구조',30,bold=True)
    text(detail,(32,78),'골든 예시 / 선은 공통 3D 골격의 측면 투영 / 입 벌림 0°와 18° 비교',19)
    r=rigs['golden'];origin=np.array([1100,480]);scale=9
    draw_rig(detail,r,'side',origin,scale)
    d=ImageDraw.Draw(detail)
    for pts,color,width in geometry(r,18):
        if color!=ORANGE:continue
        xy=project(pts,'side')*scale+origin
        for k in range(0,len(xy)-2,6):d.line([tuple(v) for v in xy[k:k+3]],fill='#d6a48b',width=2)
    for i,key in enumerate(CHAIN):
        q=project([point(r,key)],'side')[0]*scale+origin
        label_y=125 if i%2==0 else 172
        lx=q[0]-45
        d.line((q[0],q[1]-8,q[0],label_y+28),fill=BLUE,width=1)
        text(detail,(lx,label_y),f'{i+1} {LABELS[i]}',19,BLUE,True)
    text(detail,(480,470),'위턱·경구개 방향',21,BLUE,True)
    text(detail,(540,575),'아래턱 — 좌우 턱관절 축으로만 회전',21,ORANGE,True)
    text(detail,(1000,570),'뒤통수에서 목으로',18,GREEN)
    text(detail,(32,700),'고정 구조: 두개골 + 위턱 + 콧등 지지 → 코연골·코끝 부착',23,bold=True)
    text(detail,(32,742),'품종별로 바꾸는 값: 이마 경사 · 전이 깊이 · 주둥이 길이와 폭 · 턱 깊이',21)
    text(detail,(32,788),'털·볼살·귀 외피·표정은 아직 적용하지 않았습니다. 코끝을 뼈로 취급하지 않습니다.',18)
    return {'comparison.png':im,'chain-guide.png':detail}

def main():
    profiles=json.loads((HERE/'profiles.json').read_text(encoding='utf-8'))
    rigs={b:make_rig(profiles[b]) for b in BREEDS}
    (HERE/'rigs.json').write_text(json.dumps(rigs,ensure_ascii=False,indent=2),encoding='utf-8')
    for name,im in boards(rigs).items():im.save(HERE/name);print(name)

if __name__=='__main__':main()
