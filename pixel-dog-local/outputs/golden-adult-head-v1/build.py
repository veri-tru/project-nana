"""Golden-only authored adult proportion study; actual skeleton and skin meshes.

Reuses the reviewed v2/13 construction, never edits its source or saved models.
The three strengths are design hypotheses, not measured biological dimensions.
"""
from pathlib import Path
import copy, hashlib, importlib.util, json, pickle, sys
import numpy as np
from PIL import Image, ImageDraw

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'head-skeleton-volume-v2'
sys.path.insert(0,str(SOURCE))
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
bones=module('golden_bones',SOURCE/'build.py')
skin=module('golden_skin',HERE.parent/'skull-based-heads-v2/build.py')
seed=module('golden_exterior_seed',HERE/'exterior_seed.py')
skin.base=seed
original_ears=skin.make_ears
def attached_ears(skel,breed):
    # A broader skull and lower crown do not require equally wide ear roots.
    ear_skel=copy.deepcopy(skel)
    width=ear_skel['profile']['widths'][0]
    ear_skel['profile']['widths'][0]=21+(width-21)*.55
    field,meta=original_ears(ear_skel,breed)
    meta['ear_placement_width']=ear_skel['profile']['widths'][0]
    return field,meta
skin.make_ears=attached_ears
STRENGTHS={'A':.75,'B':1.0,'C':1.25}
VIEWS=[('측면',90,0),('사선',48,7),('정면',0,0),('후면',180,0),('윗면',90,90)]
BG=(248,247,242)

def profile(t):
    p=copy.deepcopy(json.loads((SOURCE/'profiles.json').read_text('utf-8'))['golden'])
    p['widths']=(np.array(p['widths'])+t*np.array([3.,3.,3.,3.,2.])).tolist()
    delta=np.array([[0,-2],[0,-.5],[0,.5],[-2,1],[-4,1],[-4,0]])
    p['dorsal']=(np.array(p['dorsal'])+t*delta).tolist()
    return p

def create(variant):
    t=STRENGTHS[variant];p=profile(t)
    seed.GOLDEN_MUZZLE_WIDTH=13+3*t
    seed.GOLDEN_MUZZLE_HEIGHT=10.8+1.2*t
    # Increase lower-jaw support independently of the slightly flatter crown.
    original=bones.params
    def adult_params(p):
        a=original(p);a['body_height']*=1+.12*t;return a
    bones.params=adult_params
    try:skel=bones.build_one(p)
    finally:bones.params=original
    print('Built skeleton',variant,flush=True)
    face=skin.build_one(skel,'golden','B')
    print('Built skin',variant,flush=True)
    result={'skeleton':skel,'exterior':face,'settings':{
        'variant':variant,'strength':t,'profile':p,
        'muzzle_envelope_half_width':seed.GOLDEN_MUZZLE_WIDTH,
        'muzzle_envelope_height':seed.GOLDEN_MUZZLE_HEIGHT,
        'jaw_body_multiplier':1+.12*t,
        'nose_template_scale':seed.NOSE_SIZE['golden'],
        'eye_radius':skin.EYE_SIZE['golden'],
        'ear_placement_width':21+(p['widths'][0]-21)*.55,
        'surface_relaxation_variant':'B',
        'authored_not_measured':True}}
    with (HERE/f'model-{variant}.pkl').open('wb') as f:pickle.dump(result,f)
    (HERE/f'parameters-{variant}.json').write_text(json.dumps(result['settings'],ensure_ascii=False,indent=2),'utf-8')
    return result

def load_models():
    oldbones=pickle.loads((SOURCE/'geometry.pkl').read_bytes())['golden']
    oldskin=pickle.loads((HERE.parent/'skull-based-heads-v2/geometry.pkl').read_bytes())['B']['golden']
    rows=[('기존',{'skeleton':oldbones,'exterior':oldskin})]
    rows.extend((v,pickle.loads((HERE/f'model-{v}.pkl').read_bytes())) for v in STRENGTHS)
    return rows

def draw_skin(im,model,box,az,el,scale=3.65):
    q,c=skin.projected(model,az,el);lo=q[:,:,:2].min((0,1));hi=q[:,:,:2].max((0,1))
    l,t,r,b=box;center=np.array([(l+r)/2,(t+b)/2])-(lo+hi)/2*np.array([scale,-scale])
    skin.paint(im,q,c,center,scale)

def boards(rows):
    result={}
    for kind,title in [('exterior','골든 리트리버 · 성견 비율 비교'),('skeleton','골든 리트리버 · 골격 지지 구조 비교')]:
        im=Image.new('RGB',(2400,1480),BG);dr=ImageDraw.Draw(im)
        skin.label(im,28,20,title,34,True)
        skin.label(im,28,72,'기존 / A 약하게 / B 중간 / C 강하게 · 동일 배율 · 각 행은 하나의 실제 3D 모델',21)
        for j,(name,_,_) in enumerate(VIEWS):skin.label(im,25+j*480,117,name,22,True)
        for i,(name,row) in enumerate(rows):
            y=160+i*305;dr.line((24,y,2376,y),fill='#d5dcd6')
            skin.label(im,28,y+8,name,23,True)
            for j,(_,az,el) in enumerate(VIEWS):
                box=(j*480+15,y+40,j*480+465,y+295)
                if kind=='exterior':draw_skin(im,row[kind],box,az,el)
                else:bones.render_cell(im,row[kind],box,az,el,scale=3.65)
        skin.label(im,28,1410,'골든만 변경 · 두개부/주둥이 폭과 깊이 보강 · 제작 가설/선택 전 · 픽셀 재작화 전',20)
        result[kind+'-comparison.png']=im
    # Neutral, intermediate and open jaw diagnose the actual edited joint supports.
    im=Image.new('RGB',(2000,1260),BG);dr=ImageDraw.Draw(im)
    skin.label(im,24,20,'골든 · 아래턱 회전 확인',32,True)
    skin.label(im,24,66,'각 후보의 같은 골격 · 0 / 10 / 20도 · 외피 표정 제작은 별도',20)
    for j,(name,_) in enumerate(rows):skin.label(im,j*500+25,115,name,24,True)
    for i,angle in enumerate([0,10,20]):
        y=160+i*345;skin.label(im,24,y,str(angle)+'°',23,True)
        for j,(_,row) in enumerate(rows):bones.render_cell(im,row['skeleton'],(j*500+10,y+30,j*500+490,y+325),70,4,angle,scale=4.0)
    result['jaw-check.png']=im
    return result

def render():
    rows=load_models()
    for name,im in boards(rows).items():im.save(HERE/name);print('Saved',name,flush=True)
    settings={k:r.get('settings',{}) for k,r in rows}
    (HERE/'parameters.json').write_text(json.dumps(settings,ensure_ascii=False,indent=2),'utf-8')

if __name__=='__main__':
    args=sys.argv[1:]
    if args==['render']:render()
    else:
        for variant in args or STRENGTHS:create(variant)
        if not args:render()
