"""Anchor-driven front portrait/seated renderer, using only versioned authoring data."""
import argparse
import base64
import io
import json
import math
import shutil
import tempfile
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, __version__ as PIL_VERSION
import maker
from state_v03 import PACKAGE, ROOT, StateStore, migrate, validate

VERSION='0.3.0'

def union(*masks):
    out=Image.new('L',(96,96))
    for m in masks:out=ImageChops.lighter(out,m)
    return out

def build(state,style='B2',view='full',*,projection=None,turn=0):
    validate(state)
    shapes=json.loads((PACKAGE/'shapes.json').read_text())
    styles=json.loads((PACKAGE/'styles.json').read_text())['styles']
    if style not in styles or view not in ('face','full'):raise ValueError('unsupported style/view')
    g=state['geometry']; colors={**state['colors'],**styles[style]}
    if projection is not None:
        # The experimental part round uses a single contour and four shared
        # fills selected from this dog's palette, in both the body and face.
        colors.update(seam=colors['outline'],ear=colors['muzzle_shadow'],
                      ear_shadow=colors['nose'],coat_shadow=colors['nose'],
                      iris=colors['nose'],pupil=colors['nose'],collar=colors['nose'],
                      nose_light=colors['coat'],highlight=colors['muzzle'])
    coat={k:shapes['lengths'][v] for k,v in state['coat'].items()}
    masks={}; layers=[]
    hw=g['head_width']/2; top=shapes['head_top']+g['head_drop']; chin=top+g['head_height']
    ground=shapes['ground']; body_top=ground-g['body_height']; bw=g['body_width']/2
    shoulder_y=chin+7; shoulder=g['shoulder_width']/2; neck_width=g['neck_width']/2
    hips_width=g['haunch_width']/2; foot_x=g['foot_spacing']/2
    # Stable landmarks do not depend on style or coat lengths.
    anchors={'body_root':[48,body_top+15],'ground':[48,ground],
             'neck_base':[48,shoulder_y],'chin':[48,chin],
             'screen_left_shoulder':[48-shoulder,shoulder_y],
             'screen_right_shoulder':[48+shoulder,shoulder_y],
             'screen_left_ear_attach':[48-hw+1,top+3],
             'screen_right_ear_attach':[48+hw-1,top+3],
             'screen_left_eye_center':[48-g['eye_spacing']/2,g['eye_y']+g['head_drop']+g['left_eye_offset']],
             'screen_right_eye_center':[48+g['eye_spacing']/2,g['eye_y']+g['head_drop']+g['right_eye_offset']],
             'muzzle_center':[48,chin-5+g['muzzle_offset']],
             'screen_left_foot_contact':[48-foot_x,ground], 'screen_right_foot_contact':[48+foot_x,ground],
             'tail_root':[48+hips_width-3,ground-10]}
    # Scale from a shared anatomical model, never a second face profile.
    def transform(pt):
        x,y=pt
        if view=='face':return (round(48+(x-48)*1.40),round(47+(y-(top+g['head_height']/2))*1.40))
        return round(x),round(y)
    def poly(name,coords):
        pts=[transform(p) for p in coords]
        if any(x<1 or x>94 or y<1 or y>94 for x,y in pts):
            raise ValueError(f'{name}: outside supported {view} canvas')
        m=Image.new('L',(96,96));ImageDraw.Draw(m).polygon(pts,fill=255);masks[name]=m
        return m
    def ellipse(name,box,tilt=0):
        x0,y0,x1,y1=box;cx=(x0+x1)/2;cy=(y0+y1)/2;a=math.radians(tilt)
        points=[]
        for n in range(48):
            t=n*math.pi/24;dx=(x1-x0)/2*math.cos(t);dy=(y1-y0)/2*math.sin(t)
            points.append((cx+dx*math.cos(a)-dy*math.sin(a),cy+dx*math.sin(a)+dy*math.cos(a)))
        return poly(name,points)
    def paint(name,m,role,clip=None):
        if clip is not None:m=ImageChops.multiply(m,clip)
        masks[name]=m;layers.append((name,m,role));return m
    def stroke(name,m,role='outline'):
        return paint(name,ImageChops.subtract(m.filter(ImageFilter.MaxFilter(3)),m),role)
    def line(name,points,role,clip=None):
        m=Image.new('L',(96,96));ImageDraw.Draw(m).line([transform(p) for p in points],fill=255,width=1)
        return paint(name,m,role,clip)

    if view=='full':
        tx,ty=anchors['tail_root']
        tail=poly('tail',[(tx+x*25,ty-7+y*14) for x,y in shapes['tail']])
        stroke('tail_outline',tail);paint('tail',tail,'coat')
        ts=poly('tail_shadow',[(tx+2,ty+5),(tx+12,ty+3),(tx+22,ty-2),(tx+17,ty+5),(tx+3,ty+7)])
        paint('tail_shadow',ts,'coat_shadow',tail)
        neck=poly('neck',[(48-neck_width,chin-3),(48+neck_width,chin-3),
              (48+shoulder,shoulder_y+5),(48-shoulder,shoulder_y+5)])
        torso=poly('torso',[(48-neck_width,chin+2),(48+neck_width,chin+2),
              (48+shoulder,shoulder_y),(48+bw,body_top+18),(48+hips_width,ground-12),
              (48+hips_width-3,ground-4),(48+foot_x,ground-2),
              (48-foot_x,ground-2),(48-hips_width+3,ground-4),
              (48-hips_width,ground-12),(48-bw,body_top+18),(48-shoulder,shoulder_y)])
        hips=[];feet=[]
        for side,x,sg in [('screen_left',48-foot_x,-1),('screen_right',48+foot_x,1)]:
            hx=48+sg*(hips_width-3)
            hips.append(ellipse(side+'_haunch',(hx-4,ground-22,hx+4,ground-3)))
            fw=g['leg_width']/2;tuft=coat['paws']
            feet.append(poly(side+'_leg',[(x-fw-1,shoulder_y+9),(x+fw+1,shoulder_y+9),
                (x+fw-1,ground-7),(x+fw+tuft,ground-4),(x+fw+1,ground-1),
                (x+fw-1+(tuft if sg==1 else 0),ground),
                (x-fw-1-(tuft if sg==-1 else 0),ground),(x-fw-2,ground-2),
                (x-fw-1-tuft,ground-4),(x-fw+1,ground-7)]))
        body=union(neck,torso,*hips,*feet)
        gap_width=max(1,foot_x-g['leg_width']/2-1)
        foot_gap=poly('foot_gap',[(48,ground-7),(48+gap_width,ground-4),
                   (48+gap_width,ground+1),(48-gap_width,ground+1),(48-gap_width,ground-4)])
        body=ImageChops.subtract(body,foot_gap)
        stroke('body_outline',body);paint('body',body,'coat')
        bs=poly('body_shadow',[(48+shoulder-3,shoulder_y+2),(48+bw,body_top+18),
              (48+hips_width+1,ground-6),(48+hips_width-4,ground-3),
              (48+foot_x+2,ground-10),(48+foot_x+3,ground-22)])
        paint('body_shadow',bs,'coat_shadow',body)
        # A single underbelly mass separates the forelegs; no two parallel rail lines.
        gap=max(1,foot_x-g['leg_width']/2)
        under=poly('underbelly',[(45,ground-24),(51,ground-24),
              (48+gap+1,ground-15),(48+gap,ground-9),(48,ground-5),
              (48-gap,ground-9),(47-gap,ground-15)])
        paint('underbelly',under,'coat_shadow',body)
        for side,x,sg in [('screen_left',48-foot_x,-1),('screen_right',48+foot_x,1)]:
            line(side+'_haunch_seam',[(x+sg*6,ground-18),(x+sg*5,ground-13),
                 (x+sg*5,ground-8)],'seam',body)
        t=coat['chest']
        chest_top=chin+4; chest_bottom=body_top+17
        chest=poly('chest',[(48-neck_width,chest_top),(48+neck_width,chest_top),
            (48+shoulder-1,shoulder_y+7),(57,chest_bottom-3),(56,chest_bottom+t),
            (52,chest_bottom-1),(49,chest_bottom+3+t),(46,chest_bottom+1),
            (42,chest_bottom+1+t),(40,chest_bottom-3),(49-shoulder,shoulder_y+7)])
        shade=poly('chest_under',[(48-shoulder+1,shoulder_y+7),(48+shoulder-1,shoulder_y+7),
              (57,chest_bottom+2+t),(49,chest_bottom+5+t),(40,chest_bottom+2+t)])
        paint('chest_under',shade,'coat_shadow',body);paint('chest',chest,'coat',body)
        if state['collar_visible']:
            cy=chin+1
            collar=poly('collar',[(48-neck_width,cy),(48+neck_width,cy),
                 (48+neck_width-1,cy+3),(48-neck_width+1,cy+3)])
            paint('collar',collar,'collar',neck)
            buckle=poly('buckle',[(46,cy),(50,cy),(50,cy+3),(46,cy+3)])
            paint('buckle',buckle,'nose',neck)

    jaw=g['jaw_width']/2
    coords=[]
    for x,y in shapes['face']:
        width=hw if y<0.9 else jaw/0.7
        coords.append((48+x*width,top+y*g['head_height']))
    face=poly('face',coords)
    ears=[]
    for side,sign in [('screen_left',-1),('screen_right',1)]:
        ex,ey=anchors[side+'_ear_attach'];ew=g['ear_width'];el=g['ear_length']
        t=coat['ears'];end=ey+el+t
        ec=[(ex+sign*x*ew,ey+y*(el+t)) for x,y in shapes['ear']]
        ears.append(poly(side+'_ear',ec))
    t=coat['crown']
    crown=poly('crown',[(48+x*hw,top+y*g['head_height']-(t if y<0 else 0)) for x,y in shapes['crown']])
    t=coat['cheeks']
    cheeks=[]
    for side,sign in [('screen_left',-1),('screen_right',1)]:
        cheeks.append(poly(side+'_cheek',[(48+sign*(hw-3),chin-12),
          (48+sign*(hw+t),chin-7),(48+sign*(hw-2+t),chin-4),
          (48+sign*(jaw+2),chin+1+t),(48+sign*4,chin+1),(48+sign*5,chin-9)]))
    chin_pad=ellipse('chin_pad',(48-jaw,chin-4,48+jaw,chin+1))
    facial=union(face,crown,chin_pad,*cheeks)
    head=union(facial,*ears)
    stroke('head_outline',head);paint('head',head,'coat')
    for side,sign,ear in [('screen_left',-1,ears[0]),('screen_right',1,ears[1])]:
        paint(side+'_ear',ear,'ear')
        ex,ey=anchors[side+'_ear_attach'];ew=g['ear_width'];el=g['ear_length']+coat['ears']
        shadow=poly(side+'_ear_shadow',[(ex+sign*x*ew,ey+y*el) for x,y in shapes['ear_shade']])
        paint(side+'_ear_shadow',shadow,'ear_shadow',ear)
    paint('facial_coat',facial,'coat')
    # Local folds, not closed outlines on every part.
    for side,sign in [('screen_left',-1),('screen_right',1)]:
        ex,ey=anchors[side+'_ear_attach']
        line(side+'_ear_fold',[(ex+sign*2,ey+8),(ex+sign*3,ey+14),
              (ex+sign*2,ey+19)],'seam',masks[side+'_ear'])
    my=anchors['muzzle_center'][1];mw=g['muzzle_width']/2;mh=g['muzzle_height']
    # Two broad whisker pads. No individual whisker lines or repeated fur noise.
    depth=g['muzzle_lobe_depth']
    muzzle=poly('muzzle',[(48-mw,my-1),(48-mw+2,my-mh/2+2),
        (44,my-mh/2),(48,my-mh/2+depth),(52,my-mh/2),
        (48+mw-2,my-mh/2+2),(48+mw,my-1),(48+mw-1,my+3),
        (53,my+mh/2),(48,my+mh/2-1),(43,my+mh/2),(48-mw+1,my+3)])
    if projection is not None:
        from muzzle import masks as muzzle_masks, ROLES
        part=muzzle_masks((96,96),(48,my),(2*mw,mh),(g['nose_width'],g['nose_height']),
                          projection,turn,transform,lobe_depth=depth/mh)
        muzzle=part['muzzle']
    for side,sign in [('screen_left',-1),('screen_right',1)]:
        ex,ey=anchors[side+'_eye_center'];rx=g['eye_rx'];ry=g['eye_ry']
        socket=ellipse(side+'_socket',(ex-rx-1,ey-ry,ex+rx+1,ey+ry+1))
        paint(side+'_socket',socket,'muzzle',facial)
        eye=ellipse(side+'_eye',(ex-rx,ey-ry,ex+rx,ey+ry),sign*g['eye_tilt'])
        if ImageChops.multiply(eye,muzzle).getbbox():raise ValueError('eye/muzzle collision: adjust spacing, height or muzzle')
        if ImageChops.subtract(eye,facial).getbbox():raise ValueError('eye outside face')
        oc=g['left_occlusion' if sign==-1 else 'right_occlusion']
        lid=poly(side+'_eyelid',[(ex-rx-1,ey-ry-2),(ex+rx+1,ey-ry-2),
            (ex+rx+1,ey-ry+oc-1),(ex,ey-ry+oc-1),(ex-rx-1,ey-ry+oc)])
        lid=ImageChops.multiply(lid,eye) if oc else Image.new('L',(96,96));masks[side+'_eyelid']=lid
        ft=coat['crown']
        fur=poly(side+'_front_fur',[(ex-rx-2,ey-ry-2),(ex+rx+1,ey-ry-2),
            (ex+rx,ey-ry-1+ft),(ex+1,ey-ry-1),(ex-1,ey-ry+ft),(ex-rx-2,ey-ry)])
        fur=ImageChops.multiply(fur,facial);masks[side+'_front_fur']=fur
        visible=ImageChops.subtract(eye,union(lid,fur));masks[side+'_eye_exposure']=visible
        if sum(1 for v in visible.get_flattened_data() if v)<4:raise ValueError('eye exposure too small')
        paint(side+'_iris',visible,'iris')
        prx=rx*g['pupil_percent']/100;pry=ry*g['pupil_percent']/100
        pupil=ellipse(side+'_pupil',(ex-prx,ey-pry,ex+prx,ey+pry),sign*g['eye_tilt'])
        paint(side+'_pupil',pupil,'pupil',visible)
        highlight=Image.new('L',(96,96));ImageDraw.Draw(highlight).point(transform((ex-1,ey)),fill=255)
        paint(side+'_highlight',highlight,'highlight',visible)
        paint(side+'_eyelid',lid,'coat');paint(side+'_front_fur',fur,'coat')
    if projection is None:
        paint('muzzle',muzzle,'muzzle',facial)
        shade=poly('muzzle_shadow',[(48-mw,my+2),(43,my+mh/2),(48,my+mh/2-1),
               (53,my+mh/2),(48+mw,my+2),(53,my+mh/2-1),(48,my+mh/2-2),(43,my+mh/2-1)])
        paint('muzzle_shadow',shade,'muzzle_shadow',ImageChops.multiply(muzzle,facial))
        nw=g['nose_width']/2;nh=g['nose_height'];ny=my-1
        nose=poly('nose',[(48-nw+1,ny-nh/2),(48+nw-1,ny-nh/2),(48+nw,ny),
                          (50,ny+nh/2),(46,ny+nh/2),(48-nw,ny)])
        paint('nose',nose,'nose',muzzle)
        line('nose_light',[(48-nw+2,ny-nh/2+1),(49,ny-nh/2+1)],'nose_light',nose)
        line('philtrum',[(48,ny+nh/2),(48,ny+nh/2+2)],'nose',muzzle)
        line('mouth',[(46,ny+nh/2+2),(50,ny+nh/2+2)],'nose',muzzle)
    else:
        for name,mask in part.items():
            paint(name,mask,ROLES[name],facial)
    output=Image.new('RGBA',(96,96))
    for name,m,role in layers:
        layer=Image.new('RGBA',(96,96),colors[role]);layer.putalpha(m);output.alpha_composite(layer)
    # Landmarks/masks are part of the editable package, not guessed from final pixels.
    package_geometry=maker.digest(b''.join(k.encode()+m.tobytes() for k,m in sorted(masks.items())))
    meta={'renderer_version':VERSION,'pillow_version':PIL_VERSION,'dog_id':state['dog_id'],
          'renderer_sha256':maker.digest(Path(__file__).read_bytes()),
          'state_schema_sha256':maker.digest((ROOT/'state_v03.py').read_bytes()),
          'source_profile':state['source_profile'],'package':state['package'],
          'state_sha256':maker.digest(maker.canonical(state).encode()),
          'style':style,'view':view,'canvas_px':[96,96],
          'anchors':anchors,'display_anchors':{k:transform(v) for k,v in anchors.items() if view=='full' or 'eye' in k or 'ear' in k or k in ('chin','muzzle_center')},
          'geometry_sha256':package_geometry,'rgba_sha256':maker.digest(output.tobytes()),
          'opaque_color_count':len({p for p in output.get_flattened_data() if p[3]}),
          'source_images_read':0,'review':state['review'],'animation_supported':False,
          'layer_order':[n for n,_,_ in layers],'masks':list(masks)}
    return output,masks,meta

def png_data(image):
    stream=io.BytesIO();image.save(stream,format='PNG')
    return 'data:image/png;base64,'+base64.b64encode(stream.getvalue()).decode()

def preview(state):
    results={}
    for view in ('face','full'):
        for style in ('B2','C2'):
            img,masks,meta=build(state,style,view)
            overlay=Image.new('RGBA',img.size)
            for n in ('screen_left_eye_exposure','screen_right_eye_exposure','screen_left_front_fur','screen_right_front_fur'):
                m=masks[n];layer=Image.new('RGBA',img.size,'#39B9C4');layer.putalpha(m.point(lambda p:110 if p else 0));overlay.alpha_composite(layer)
            draw=ImageDraw.Draw(overlay)
            for x,y in meta['display_anchors'].values():draw.line([(x-1,y),(x+1,y)],fill='#E5544C');draw.line([(x,y-1),(x,y+1)],fill='#E5544C')
            results[f'{view}-{style}']={'image':png_data(img),'overlay':png_data(overlay),'meta':meta}
    return results

def export(state,revision,directory,previous_state=None):
    """Self-contained review page plus native sprites; no source image reads."""
    if state.get('schema_version')==2:
        from render_v02 import export as old_export
        return old_export(state,revision,directory)
    validate(state)
    if previous_state is not None and (previous_state.get('dog_id')!=state['dog_id'] or
            maker.digest(maker.canonical(previous_state).encode())!=state['migration']['from_state_sha256']):
        raise ValueError('comparison origin mismatch')
    out=Path(directory)
    if out.exists():raise FileExistsError(str(out))
    out.parent.mkdir(parents=True,exist_ok=True)
    tmp=Path(tempfile.mkdtemp(prefix='.nana-export-',dir=out.parent))
    try:
        from render_v02 import build as old_build
        original_upgrade=migrate(previous_state,state['migration']['from_authoring_revision']) if previous_state else None
        cards=[]
        for view in ('face','full'):
            for style in ('B2','C2'):
                key=f'{view}-{style}';img,masks,meta=build(state,style,view)
                img.save(tmp/(key+'.png'));img.resize((576,576),Image.Resampling.NEAREST).save(tmp/(key+'-6x.png'))
                meta['authoring_revision']=revision
                (tmp/(key+'.json')).write_text(json.dumps(meta,ensure_ascii=False,indent=2))
                ld=tmp/(key+'-layers');ld.mkdir()
                for n,m in masks.items():m.save(ld/(n+'.png'))
                samples=[]
                if previous_state is not None:
                    for suffix,label,old in [('v02','0.2 원본',old_build(previous_state,style,view)[0]),
                                             ('v03-default','0.3 구조 변경',build(original_upgrade,style,view)[0])]:
                        old.save(tmp/(key+'-'+suffix+'.png'))
                        samples.append('<div><small>'+label+'</small><img alt="'+label+' '+key+'" src="'+png_data(old)+'"></div>')
                samples.append('<div><small>0.3 현재 제작값</small><img alt="현재 '+key+'" src="'+png_data(img)+'"></div>')
                title=('얼굴' if view=='face' else '앉은 전신')+' · '+style
                cards.append('<figure><figcaption>'+title+'</figcaption><div class="pair">'+''.join(samples)+'</div></figure>')
        report={'schema':1,'authoring_revision':revision,'state_sha256':maker.digest(maker.canonical(state).encode()),
                'comparison_origin':state['migration'],'review':state['review'],
                'changed_from_v03_defaults':{section:{k:v for k,v in state[section].items() if original_upgrade and original_upgrade[section].get(k)!=v}
                                            for section in ('geometry','colors','coat')},
                'note':'manual authoring approximation; not photo measurements or owner approval'}
        (tmp/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
        import html
        details=html.escape(json.dumps(report['changed_from_v03_defaults'],ensure_ascii=False,indent=2))
        page='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Nana · 정적 제작기 0.3 검토</title><style>
:root{font:15px system-ui;color:#423a31;background:#f4eee4;--size:192px;--canvas:#fffcf6}*{box-sizing:border-box}body{margin:0;padding:24px}h1{font-size:25px}p{line-height:1.7}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,620px),1fr));gap:20px}figure{min-width:0;margin:0;border:1px solid #d8cbbb;border-radius:12px;overflow:hidden;background:#fffcf6}figcaption{padding:16px;font-weight:650;border-bottom:1px solid #ddd3c6}.pair{overflow-x:auto;display:flex;gap:14px;justify-content:space-around;flex-wrap:wrap;padding:18px;background:var(--canvas)}.pair>div{text-align:center}img{display:block;width:var(--size);height:var(--size);image-rendering:pixelated}small{display:block;color:#887967;margin-bottom:10px}.toolbar{display:flex;gap:14px;flex-wrap:wrap;margin:20px 0}button,select{font:inherit;padding:8px 12px;border:1px solid #baac99;border-radius:6px;background:#fffdf8}pre{white-space:pre-wrap}body.dark{--canvas:#302e2a}body.dark small{color:#d9cebe}
</style><h1>한 개체 정적 제작기 0.3</h1><p>왼쪽부터 이전 출력 → 구조만 변경 → 개체 제작값 조정입니다.<br>사진 관찰을 참고한 수동 제작 초안이며, 닮음·정본 미감·보호자 검수는 대기 중입니다.</p>
<div class="toolbar"><label>표시 배율 <select id="scale"><option value="96">1배 · 96px</option><option value="192" selected>2배 · 192px</option><option value="384">4배 · 384px</option></select></label><button id="background">밝은 / 어두운 배경</button></div><main>'''+''.join(cards)+'''</main><details><summary>구조 기본값에서 바꾼 제작값</summary><pre>'''+details+'''</pre></details><p>이 페이지의 이미지는 파일 안에 포함되어 있습니다. 확대는 최근접 픽셀 표시이며 실제 기기 검수를 대신하지 않습니다.</p><script>document.getElementById('scale').onchange=e=>document.documentElement.style.setProperty('--size',e.target.value+'px');document.getElementById('background').onclick=()=>document.body.classList.toggle('dark');</script></html>'''
        (tmp/'index.html').write_text(page)
        if out.exists():raise FileExistsError(str(out))
        tmp.rename(out)
    except BaseException:
        shutil.rmtree(tmp,ignore_errors=True);raise

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--db',required=True)
    sub=ap.add_subparsers(dest='cmd',required=True)
    s=sub.add_parser('migrate');s.add_argument('dog');s.add_argument('--from-authoring',type=int);s.add_argument('--expected',type=int,required=True)
    s=sub.add_parser('render');s.add_argument('dog');s.add_argument('--revision',type=int);s.add_argument('--out',required=True)
    s=sub.add_parser('save');s.add_argument('state');s.add_argument('--expected',type=int,required=True);s.add_argument('--reason',required=True)
    s=sub.add_parser('restore');s.add_argument('dog');s.add_argument('--target',type=int,required=True);s.add_argument('--expected',type=int,required=True)
    s=sub.add_parser('state');s.add_argument('dog');s.add_argument('--revision',type=int)
    s=sub.add_parser('history');s.add_argument('dog')
    args=ap.parse_args();store=StateStore(args.db)
    try:
        if args.cmd=='migrate':
            state,rev=store.state_get(args.dog,args.from_authoring);print(store.state_save(migrate(state,rev),args.expected,'explicit v0.2 to v0.3 migration'))
        elif args.cmd=='render':
            state,rev=store.state_get(args.dog,args.revision)
            prior=store.state_get(args.dog,state['migration']['from_authoring_revision'])[0] if state['schema_version']==3 else None
            export(state,rev,args.out,prior);print(args.out)
        elif args.cmd=='save':print(store.state_save(json.loads(Path(args.state).read_text()),args.expected,args.reason))
        elif args.cmd=='restore':print(store.state_restore(args.dog,args.target,args.expected))
        elif args.cmd=='history':print(json.dumps(store.state_history(args.dog),ensure_ascii=False))
        else:print(json.dumps(store.state_get(args.dog,args.revision)[0],ensure_ascii=False,indent=2))
    except (ValueError,FileExistsError) as e:ap.exit(2,str(e)+'\n')
    finally:store.close()

if __name__=='__main__':main()
