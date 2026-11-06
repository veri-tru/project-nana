"""Jack Russell authored skull/jaw candidates using the reviewed mesh engine.

Not CT segmentation, measured dimensions, a pixel style asset or a body rig.
The only A/B/C variable is rostral length about the fixed stop.
"""
from pathlib import Path
import argparse, copy, importlib.util, json, pickle, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.interpolate import PchipInterpolator

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'head-skeleton-volume-v2'
sys.path.insert(0,str(SOURCE))
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
bones=module('jack_bones',SOURCE/'build.py')
skin=module('jack_skin',HERE.parent/'skull-based-heads-v2/build.py')
seed=module('jack_seed',HERE/'exterior_seed.py')
skin.base=seed
skin.PALETTE['jack_russell']=([218,211,193],[161,153,132])
skin.EYE_SIZE['jack_russell']=3.2
VARIANTS={'A':.94,'B':1.,'C':1.06}
VIEWS=[('측면',90,0),('사선',48,7),('정면',0,0),('후면',180,0),('윗면',90,90)]
BG=(248,247,242)

def profile(variant):
    d=np.array([[-15,28],[-28,28],[-39,20],[-54,17],[-69,13],[-77,11]],float)
    d[3:,0]=d[2,0]+(d[3:,0]-d[2,0])*VARIANTS[variant]
    return {'dorsal':d.tolist(),'widths':[18.5,17.5,12.5,10.5,7.8],'hinge_x':-15.}

def button_ears(skel,breed):
    """Small forward-folded triangular ear volumes, separate from skull anatomy."""
    d=np.array(skel['profile']['dorsal']);w=skel['profile']['widths'][0]
    yy=np.array([15.,18.,22.,27.,30.])
    xx=d[0,0]+np.array([-13.,-12.,-10.,-5.,-2.])
    zz=w*np.array([1.12,1.20,1.24,1.20,1.08])
    widths=np.array([.18,2.7,5.5,7.0,.2])
    thickness=np.array([.18,1.8,2.2,2.7,.2])
    funcs=[PchipInterpolator(yy,a) for a in [xx,zz,widths,thickness]]
    def ears(q):
        x,y,z=np.moveaxis(q,-1,0);yc=np.clip(y,yy[0],yy[-1]);cx,cz,ww,tt=[f(yc) for f in funcs]
        out=np.full(x.shape,1e4)
        for sign in (-1,1):
            dx=x-cx;dz=z-sign*cz
            wide=dx*.60+sign*dz*.80;depth=-dx*.80+sign*dz*.60
            leaf=(np.sqrt((wide/ww)**2+(depth/tt)**2)-1)*np.minimum(ww,tt)
            leaf=np.maximum(leaf,np.maximum(yy[0]-y,y-yy[-1]))
            root=bones.ellipsoid(q,[d[0,0]-2,25,sign*w*.95],[6.,5.,4.5])
            out=np.minimum(out,bones.smoothmin(leaf,root,2.))
        return out
    return ears,dict(ear_type='forward_button_authored',ear_y=yy.tolist(),ear_x=xx.tolist(),ear_abs_z=zz.tolist(),ear_paths=[np.column_stack([xx,yy,sign*zz]).tolist() for sign in (-1,1)],ear_width_mode='pchip_button_leaf',ear_thickness=None,ear_width_controls=widths.tolist(),ear_thickness_controls=thickness.tolist(),ear_frame=[.60,.80],ear_root=[float(d[0,0]-2),25.,w*.95],ear_root_radii=[6.,5.,4.5],ear_note='Cartilage/skin proxy; not bone. Generic placement, no individual photo fit.')
skin.make_ears=button_ears

def create(variant):
    p=profile(variant)
    skel=bones.build_one(p)
    print('Skeleton built',variant,flush=True)
    face=skin.build_one(skel,'jack_russell','B')
    print('Envelope built',variant,flush=True)
    return {'skeleton':skel,'exterior':face,'settings':{'breed':'jack_russell','size_class':'small','size_basis':'Authored classification; model units are not cm. No class-based face scaling.','variant':variant,'rostral_length_multiplier':VARIANTS[variant],'profile':p,'control_muzzle_to_cranium_x_ratio':abs(p['dorsal'][5][0]-p['dorsal'][2][0])/(5-p['dorsal'][2][0]),'variation_scope':'Only dorsal x coordinates anterior to stop change; jaw/body rebuilding follows that change.','surface_relaxation':'B 400 iterations','muzzle_half_width':seed.JACK_MUZZLE_WIDTH,'muzzle_half_height':seed.JACK_MUZZLE_HEIGHT,'nose_scale':seed.NOSE_SIZE['jack_russell'],'eye_radius':skin.EYE_SIZE['jack_russell'],'authored_not_measured':True}}

def draw_face(im,model,box,az,el,scale=3.65):
    q,c=skin.projected(model,az,el);lo=q[:,:,:2].min((0,1));hi=q[:,:,:2].max((0,1))
    l,t,r,b=box;center=np.array([(l+r)/2,(t+b)/2])-(lo+hi)/2*np.array([scale,-scale])
    skin.paint(im,q,c,center,scale)

def boards(models):
    result={}
    for kind,title in [('exterior','잭 러셀 테리어 · 골격을 감싼 중립 외형'),('skeleton','잭 러셀 테리어 · 머리 골격 3안')]:
        im=Image.new('RGB',(2400,1190),BG);dr=ImageDraw.Draw(im)
        bones.label(im,28,20,title,33,True)
        bones.label(im,28,70,'A 주둥이 -6% / B 기준 / C +6% · 동일 배율 · 각 행은 하나의 실제 3D 모델',21)
        for j,(name,_,_) in enumerate(VIEWS):bones.label(im,25+j*480,115,name,23,True)
        for i,(variant,model) in enumerate(models.items()):
            y=160+i*305;dr.line((24,y,2376,y),fill='#d5dcd6');bones.label(im,28,y+7,variant,24,True)
            for j,(_,az,el) in enumerate(VIEWS):
                box=(j*480+15,y+42,j*480+465,y+297)
                if kind=='exterior':draw_face(im,model[kind],box,az,el)
                else:bones.render_cell(im,model[kind],box,az,el,scale=3.65)
        if kind=='skeleton':
            bones.label(im,28,1092,'청회 두개부 · 황토 비골/위턱 · 녹회 광대활/관절 받침 · 갈색 아래턱',20)
            bones.label(im,28,1134,'품종 기준을 반영한 제작 비율 · CT/실측 복제 아님 · 치열/경추/전신 미포함',18)
        else:
            bones.label(im,28,1092,'골격 연결 확인용 무늬 없는 외피 · 귀는 뼈가 아닌 부착 부피 · 털색/픽셀 화풍 확정 전',19)
            bones.label(im,28,1134,'평평한 두개부 · 뚜렷하되 과하지 않은 이마 꺾임 · 튼튼한 주둥이/턱 · 사용자 선택 전',18)
        result[kind+'-comparison.png']=im
    im=Image.new('RGB',(1800,1210),BG);dr=ImageDraw.Draw(im)
    bones.label(im,28,20,'잭 러셀 · 아래턱 회전과 관절 확인',32,True)
    bones.label(im,28,70,'위턱 고정 / 아래턱 전체를 같은 관절축에서 0° · 10° · 20° 회전',21)
    for j,v in enumerate(models):bones.label(im,28+j*600,118,v,23,True)
    for i,angle in enumerate([0,10,20]):
        y=160+i*315;dr.line((24,y,1776,y),fill='#d5dcd6');bones.label(im,28,y+7,str(angle)+'°',21,True)
        for j,m in enumerate(models.values()):bones.render_cell(im,m['skeleton'],(j*600+15,y+40,j*600+585,y+300),70,4,angle,scale=4.3)
    bones.label(im,28,1140,'턱관절/광대활 간섭 검토용 · 외피 개폐·치열·교합·표정 애니메이션은 후속 범위',19)
    result['jaw-check.png']=im
    return result

def load_models():return {v:pickle.loads((HERE/f'model-{v}.pkl').read_bytes()) for v in VARIANTS}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['build','render']);ap.add_argument('--variant',choices=list(VARIANTS));args=ap.parse_args()
    if (HERE/'review-status.json').exists():raise ValueError('Reviewed output protected; use a new version folder')
    if args.mode=='build':
        for v in ([args.variant] if args.variant else VARIANTS):
            if (HERE/f'model-{v}.pkl').exists():raise ValueError('Refusing to overwrite existing model')
            m=create(v);(HERE/f'model-{v}.pkl').write_bytes(pickle.dumps(m))
            (HERE/f'parameters-{v}.json').write_text(json.dumps(m['settings'],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if args.mode=='render' or not args.variant:
        models=load_models()
        for name,im in boards(models).items():im.save(HERE/name);print('Saved',name,flush=True)

if __name__=='__main__':main()
