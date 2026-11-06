"""Compare geometry with lighting and material gradients disabled."""
import importlib.util
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import preview as current

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('before_round',HERE/'preview-before-ear-corners.py')
before = importlib.util.module_from_spec(spec)
spec.loader.exec_module(before)


def flat_polys(mesh, angle):
    vertices, colors = [], []
    for index,feature in enumerate(mesh):
        v,c = current.polys([feature],angle,0)
        tint = (214,211,201) if index==0 else (107,105,98)
        vertices.append(v)
        colors.append(np.broadcast_to(tint,c.shape).copy())
    return np.concatenate(vertices),np.concatenate(colors)


def render():
    rigs,profiles = current.load('B.json')['breeds'],current.load('profiles.json')
    cases=[]
    for breed in current.BREEDS:
        row=[]
        for angle in [90,0,180]:
            for module in [before,current]:
                mesh=module.head_features(rigs[breed],breed,module.local_profile(rigs[breed],profiles[breed]))
                v,c=flat_polys(mesh,angle)
                low,high=v[:,:,:2].min((0,1)),v[:,:,:2].max((0,1))
                row.append((v,c,low,high))
        cases.append(row)
    scale=min(min(270/(hi[0]-lo[0]),190/(hi[1]-lo[1])) for row in cases for _,_,lo,hi in row)
    image=Image.new('RGB',(1800,880),current.BG)
    draw=ImageDraw.Draw(image)
    current.label(image,30,22,'귀 모서리 전후 · 음영 없이 확인',30,bold=True)
    current.label(image,30,72,'같은 카메라·배율·단색 · 머리 밝은 회색 / 귀 진한 회색',17,current.MUTED)
    for column,heading in enumerate(['측면 · 이전','측면 · 수정','정면 · 이전','정면 · 수정','뒷면 · 이전','뒷면 · 수정']):
        current.label(image,30+column*295,117,heading,18,bold=True)
    for index,(row,name) in enumerate(zip(cases,current.NAMES)):
        top=150+index*235
        draw.line((25,top,1775,top),fill=current.LINE)
        current.label(image,30,top+10,name,18,bold=True)
        min_y=min(lo[1] for _,_,lo,_ in row)
        max_y=max(hi[1] for _,_,_,hi in row)
        for column,(v,c,lo,hi) in enumerate(row):
            center=[165+column*295-(lo[0]+hi[0])*scale/2,top+137+(min_y+max_y)*scale/2]
            current.paint(image,v,c,np.array(center),scale)
    return image


if __name__=='__main__':
    render().save(HERE/'ear-geometry-flat.png')
