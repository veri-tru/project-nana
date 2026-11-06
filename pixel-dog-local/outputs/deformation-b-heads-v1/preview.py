"""Apply the selected B head-unit scale to the completed v3 head meshes only."""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent/'deformation-b-face-v3'
spec = importlib.util.spec_from_file_location('head_source_v3', SOURCE/'preview.py')
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)
STYLE_PATH = HERE.parent/'deformation-rig-b-v1/B.json'
HEAD_SCALE = json.loads(STYLE_PATH.read_text(encoding='utf-8'))['deformation']['head_scale']
CAMERAS = [('측면',90),('정면',0),('뒷면',180)]


def build_heads():
    rigs, profiles = model.load('B.json')['breeds'], model.load('profiles.json')
    result = {}
    for breed in model.BREEDS:
        rig = rigs[breed]
        source = model.head_features(rig,breed,model.local_profile(rig,profiles[breed]))
        # All vertices are already local to body.head. Scale the finished unit,
        # including its ears, eyes and common nose, around that unchanged origin.
        applied = [(vertices*HEAD_SCALE,np.array(color,copy=True)) for vertices,color in source]
        result[breed] = (source,applied)
    return result


def render(heads):
    cases = []
    for breed in model.BREEDS:
        row = []
        for _, angle in CAMERAS:
            pair = []
            for mesh in heads[breed]:
                vertices, colors = model.polys(mesh,angle,0)
                low,high = vertices[:,:,:2].min((0,1)),vertices[:,:,:2].max((0,1))
                pair.append((vertices,colors,low,high))
            row.append(pair)
        cases.append(row)
    # One world-to-pixel scale for every breed, view and before/after panel.
    scale = min(min(266/(pair[1][3][0]-pair[1][2][0]),
                    210/(pair[1][3][1]-pair[1][2][1])) for row in cases for pair in row)
    image = Image.new('RGB',(1800,1010),model.BG)
    pen = ImageDraw.Draw(image)
    model.label(image,30,22,'머리만 · 기존 B 데포르메 적용',32,bold=True)
    model.label(image,32,76,'머리·귀 전체 ×1.70   /   얼굴 내부 비례 유지   /   모든 칸 같은 배율',18,model.MUTED)
    for i,(name,_) in enumerate(CAMERAS):
        for variant,title in enumerate(['현재','B 적용']):
            model.label(image,30+(i*2+variant)*295,127,f'{name} · {title}',19,bold=True)
    for row_index,(row,name) in enumerate(zip(cases,model.NAMES)):
        top = 170+row_index*265
        pen.line((25,top,1775,top),fill=model.LINE)
        model.label(image,30,top+12,name,20,bold=True)
        low_y = min(pair[1][2][1] for pair in row)
        high_y = max(pair[1][3][1] for pair in row)
        origin_y = top+149+(low_y+high_y)*scale/2
        for view_index,pair in enumerate(row):
            # Both members share the same projected attachment origin within
            # their panel; before is never independently centered or auto-fit.
            origin_offset_x = 161-(pair[1][2][0]+pair[1][3][0])*scale/2
            for variant,(vertices,colors,_,_) in enumerate(pair):
                x = (view_index*2+variant)*295+origin_offset_x
                model.paint(image,vertices,colors,np.array([x,origin_y]),scale)
    model.label(image,32,977,'완성된 머리의 균등 확대입니다. 눈·주둥이·귀의 상대 비율과 색은 그대로이며 몸통은 이번 범위에서 제외했습니다.',15,model.MUTED)
    return image,scale


def main():
    heads = build_heads()
    image,scale = render(heads)
    image.save(HERE/'heads-before-after.png')
    arrays = {}
    for breed,(_,applied) in heads.items():
        for index,(vertices,color) in enumerate(applied):
            arrays[f'{breed}_surface_{index}'] = vertices
            arrays[f'{breed}_material_{index}'] = color
    np.savez_compressed(HERE/'heads-B.npz',**arrays)
    evidence = {
        'scope':'heads only; body not modified or rendered',
        'classification':'existing authored B scale applied to photo-registered completed heads',
        'head_scale':HEAD_SCALE,
        'pivot':'body.head; origin in each local head mesh',
        'transform_matrix':np.diag([HEAD_SCALE,HEAD_SCALE,HEAD_SCALE,1.0]).tolist(),
        'cameras':[{'label':name,'azimuth':angle,'elevation':0} for name,angle in CAMERAS],
        'pixels_per_model_unit':scale,
        'independent_panel_auto_fit':False,
        'body_proportion_claim':False,
        'inputs_sha256':{str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in [SOURCE/'preview.py',SOURCE/'B.json',SOURCE/'profiles.json',STYLE_PATH]},
        'image_sha256':hashlib.sha256((HERE/'heads-before-after.png').read_bytes()).hexdigest(),
        'mesh_archive_sha256':hashlib.sha256((HERE/'heads-B.npz').read_bytes()).hexdigest(),
        'status':'USER_REVIEW_PENDING',
    }
    (HERE/'recipe.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
