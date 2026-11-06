"""Focused, same-scale before/after render of the whippet jaw correction."""
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent

def load(name, filename):
    spec = importlib.util.spec_from_file_location(name,HERE/filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def render():
    old = load('before_whippet','preview-before-jaw-attachment.py')
    new = load('after_whippet','preview.py')
    before,_ = old.build()
    after,_ = new.build()
    cases = []
    for state in ('open','tongue','lick'):
        row = []
        for source,angle in ((before,90),(after,90),(before,38),(after,38)):
            v,c = new.model.polys(source['whippet'][state],angle,0)
            lo,hi = v[:,:,:2].min((0,1)),v[:,:,:2].max((0,1))
            row.append((v,c,lo,hi))
        cases.append(row)
    scale = min(min(280/(hi[0]-lo[0]),190/(hi[1]-lo[1])) for row in cases for _,_,lo,hi in row)
    image = Image.new('RGB',(1310,955),new.model.BG)
    pen = ImageDraw.Draw(image)
    new.model.label(image,28,25,'휘핏 · 턱 뒤쪽 연결 구조',30,bold=True)
    new.model.label(image,30,76,'목 쪽 윤곽 분리 · 볼 안쪽으로 올라가는 아래턱 · 같은 벌림',18,new.model.MUTED)
    for i,label in enumerate(('측면 · 이전','측면 · 수정','사선 · 이전','사선 · 수정')):
        new.model.label(image,28+325*i,126,label,19,bold=True)
    for i,(row,label) in enumerate(zip(cases,('입 벌림','혀 내밀기','코 핥기'))):
        top = 168+250*i
        pen.line((25,top,1285,top),fill=new.model.LINE)
        new.model.label(image,28,top+10,label,19,bold=True)
        lo = np.min([case[2] for case in row],axis=0)
        hi = np.max([case[3] for case in row],axis=0)
        center = np.array([169,top+145])-(lo+hi)/2*np.array([scale,-scale])
        for j,(v,c,_,_) in enumerate(row):
            new.model.paint(image,v,c,center+[325*j,0],scale)
    new.model.label(image,28,928,'제작값 조정 시안 · 동일 배율 · 사용자 검토 대기',15,new.model.MUTED)
    return image

if __name__=='__main__':
    render().save(HERE/'whippet-attachment-before-after.png')
    files = ['whippet_attachment_comparison.py','preview-before-jaw-attachment.py','preview.py','whippet-attachment-before-after.png']
    (HERE/'whippet-attachment-recipe.json').write_text(json.dumps({
        'sha256':{f:hashlib.sha256((HERE/f).read_bytes()).hexdigest() for f in files},
        'change':{'breed':'whippet','rest_depth_scale_max':.55,'rest_depth_cap':1.10,'rest_width_scale':.76,
                  'oral_margin':'shallow arc with horizontal end tangents; front height lowered 2 local units',
                  'arc_dip':.50,'corner_drop':.50,
                  'jaw_half_width_cap':2.98,'hinge_y':'temple.y minus 1.2',
                  'skull_base':'hinge.y minus 1.2; no neck underside restoration'},
        'views':[90,38],'status':'USER_REVIEW_PENDING'
    },indent=2)+'\n',encoding='utf-8')
