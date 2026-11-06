"""Show the current head meshes from three orthographic cameras."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import preview as model

HERE = Path(__file__).resolve().parent
CAMERAS = [('측면', 90), ('정면', 0), ('뒷면', 180)]


def render():
    rigs = model.load('B.json')['breeds']
    profiles = model.load('profiles.json')
    cases = []
    for breed in model.BREEDS:
        mesh = model.head_features(rigs[breed], breed, model.local_profile(rigs[breed], profiles[breed]))
        views = []
        for name, angle in CAMERAS:
            vertices, colors = model.polys(mesh, angle, 0)
            lo = vertices[:, :, :2].min(axis=(0, 1))
            hi = vertices[:, :, :2].max(axis=(0, 1))
            views.append((vertices, colors, lo, hi))
        cases.append(views)
    scale = min(min(380/(hi[0]-lo[0]), 216/(hi[1]-lo[1]))
                for views in cases for _, _, lo, hi in views)
    image = Image.new('RGB', (1320, 1010), model.BG)
    draw = ImageDraw.Draw(image)
    model.label(image, 30, 24, '현재 얼굴 · 측면 / 정면 / 뒷면', 32, bold=True)
    model.label(image, 32, 77, '부착 중심을 유지한 귀 모서리 둥글림 · 세 품종 같은 배율과 카메라 조건', 18, model.MUTED)
    for column, (name, _) in enumerate(CAMERAS):
        model.label(image, 40+column*430, 125, name, 21, bold=True)
    for row, (views, name) in enumerate(zip(cases, model.NAMES)):
        top = 166+row*267
        draw.line((30, top, 1290, top), fill=model.LINE)
        model.label(image, 32, top+12, name, 20, bold=True)
        low_y = min(lo[1] for _, _, lo, _ in views)
        high_y = max(hi[1] for _, _, _, hi in views)
        center_y = top+151+(low_y+high_y)*scale/2
        for column, (vertices, colors, lo, hi) in enumerate(views):
            center_x = 230+column*430-(lo[0]+hi[0])*scale/2
            model.paint(image, vertices, colors, np.array([center_x, center_y]), scale)
    model.label(image, 32, 978, '부착 중심·전체 크기는 유지하고 모서리만 원호로 다듬었습니다. 얼굴·코·귀 색상은 그대로입니다.', 15, model.MUTED)
    return image, scale


if __name__ == '__main__':
    image, scale = render()
    image.save(HERE / 'faces-side-front-back.png')
    evidence = {
        'cameras': [{'label': name, 'azimuth_degrees': angle, 'elevation_degrees': 0} for name, angle in CAMERAS],
        'common_pixels_per_unit': scale,
        'view_specific_geometry_changes': False,
        'model_revision': 'ear_corner_fillet_v6',
        'inputs_sha256': {name: hashlib.sha256((HERE/name).read_bytes()).hexdigest()
                          for name in ['preview.py', 'B.json', 'profiles.json']},
        'image_sha256': hashlib.sha256((HERE/'faces-side-front-back.png').read_bytes()).hexdigest(),
    }
    (HERE / 'faces-side-front-back.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
