"""Round the eyes only on the already scaled B heads."""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
BASE = HERE.parent/'deformation-b-heads-v1'
spec = importlib.util.spec_from_file_location('scaled_heads',BASE/'preview.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
model = base.model
CAMERAS = [('측면',90),('정면',0)]


def build_heads():
    previous = base.build_heads()
    rigs,profiles = model.load('B.json')['breeds'],model.load('profiles.json')
    result,settings = {},{}
    for breed in model.BREEDS:
        profile = model.local_profile(rigs[breed],profiles[breed])
        old_w,old_h = profile['eye_radius']
        radius = float(np.sqrt(old_w*old_h))
        profile.update(eye_radius=(radius,radius),eye_tilt=0.0,eye_power=2.0)
        mesh = model.head_features(rigs[breed],breed,profile)
        after = [(v*base.HEAD_SCALE,np.array(c,copy=True)) for v,c in mesh]
        result[breed] = (previous[breed][1],after)
        settings[breed] = dict(previous_radius=[old_w,old_h],radius=[radius,radius],
                               tilt=0.0,power=2.0,head_scale=base.HEAD_SCALE)
    return result,settings


def render(heads):
    cases = []
    for breed in model.BREEDS:
        row = []
        for _,angle in CAMERAS:
            for mesh in heads[breed]:
                vertices,colors = model.polys(mesh,angle,0)
                lo,hi = vertices[:,:,:2].min((0,1)),vertices[:,:,:2].max((0,1))
                row.append((vertices,colors,lo,hi))
        cases.append(row)
    scale = min(min(350/(hi[0]-lo[0]),224/(hi[1]-lo[1])) for row in cases for _,_,lo,hi in row)
    image = Image.new('RGB',(1560,1040),model.BG)
    pen = ImageDraw.Draw(image)
    model.label(image,30,23,'B 머리 · 눈만 원에 가깝게',32,bold=True)
    model.label(image,32,77,'눈 중심 유지 · 가로/세로 반경 통일 · 머리·코·귀 형상과 1.70배 설정 유지',18,model.MUTED)
    for column,title in enumerate(['측면 · 이전','측면 · 수정','정면 · 이전','정면 · 수정']):
        model.label(image,32+column*385,129,title,20,bold=True)
    for index,(row,name) in enumerate(zip(cases,model.NAMES)):
        top = 172+index*274
        pen.line((25,top,1535,top),fill=model.LINE)
        model.label(image,30,top+12,name,20,bold=True)
        lo_y,hi_y = min(lo[1] for _,_,lo,_ in row),max(hi[1] for _,_,_,hi in row)
        cy = top+151+(lo_y+hi_y)*scale/2
        for column,(vertices,colors,lo,hi) in enumerate(row):
            cx = 196+column*385-(lo[0]+hi[0])*scale/2
            model.paint(image,vertices,colors,np.array([cx,cy]),scale)
    model.label(image,32,1006,'눈의 가로·세로 비율과 기울기만 조정했습니다. 곡면 위의 눈이므로 시점에 따라 타원으로 보일 수 있습니다.',15,model.MUTED)
    return image,scale


def main():
    heads,settings = build_heads()
    image,scale = render(heads)
    image.save(HERE/'round-eyes-before-after.png')
    arrays = {f'{breed}_{kind}_{i}':array
              for breed,(_,mesh) in heads.items() for i,(v,c) in enumerate(mesh)
              for kind,array in [('surface',v),('material',c)]}
    np.savez_compressed(HERE/'heads-B-round-eyes.npz',**arrays)
    evidence = dict(scope='eye material shape only on B 1.70 heads',settings=settings,
                    pixels_per_model_unit=scale,cameras=CAMERAS,status='USER_REVIEW_PENDING',
                    projection='same head-attached eye material in both cameras; no view-specific eye scaling',
                    input_sha256={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in [BASE/'preview.py',BASE/'heads-B.npz',model.HERE/'preview.py',
                                            model.HERE/'B.json',model.HERE/'profiles.json']},
                    image_sha256=hashlib.sha256((HERE/'round-eyes-before-after.png').read_bytes()).hexdigest())
    (HERE/'recipe.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
