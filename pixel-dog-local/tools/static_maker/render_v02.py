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
from state_v02 import PACKAGE, ROOT, StateStore, migrate, validate

VERSION='0.2.0'

def union(*masks):
    out=Image.new('L',(96,96))
    for m in masks:out=ImageChops.lighter(out,m)
    return out

def build(state,style='B2',view='full'):
    validate(state)
    shapes=json.loads((PACKAGE/'shapes.json').read_text())
    styles=json.loads((PACKAGE/'styles.json').read_text())['styles']
    if style not in styles or view not in ('face','full'):raise ValueError('unsupported style/view')
    g=state['geometry']; colors={**state['colors'],**styles[style]}
    coat={k:shapes['lengths'][v] for k,v in state['coat'].items()}
    masks={}; layers=[]
    hw=g['head_width']/2; top=shapes['head_top']; chin=top+g['head_height']
    ground=shapes['ground']; body_top=ground-g['body_height']; bw=g['body_width']/2
    # Stable landmarks do not depend on style or coat lengths.
    anchors={'body_root':[48,body_top+15],'ground':[48,ground],
             'neck_base':[48,body_top+3],'chin':[48,chin],
             'screen_left_ear_attach':[48-hw+1,top+3],
             'screen_right_ear_attach':[48+hw-1,top+3],
             'screen_left_eye_center':[48-g['eye_spacing']/2,g['eye_y']+g['left_eye_offset']],
             'screen_right_eye_center':[48+g['eye_spacing']/2,g['eye_y']+g['right_eye_offset']],
             'muzzle_center':[48,chin-5+g['muzzle_offset']],
             'screen_left_foot_contact':[40,ground], 'screen_right_foot_contact':[56,ground],
             'tail_root':[48+bw-5,ground-10]}
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
        neck=poly('neck',[(40,chin-3),(56,chin-3),(59,body_top+8),(37,body_top+8)])
        torso=poly('torso',[(40,body_top),(56,body_top),(60,body_top+8),
              (48+bw,ground-18),(48+bw,ground-7),(58,ground-2),
              (38,ground-2),(48-bw,ground-7),(48-bw,ground-18),(36,body_top+8)])
        hips=[];feet=[]
        for side,x,sg in [('screen_left',40,-1),('screen_right',56,1)]:
            hips.append(ellipse(side+'_haunch',(48+sg*bw-6,ground-23,48+sg*bw+6,ground-2)))
            fw=g['leg_width']/2;tuft=coat['paws']
            feet.append(poly(side+'_leg',[(x-fw,body_top+13),(x+fw,body_top+13),
                (x+fw-1,ground-7),(x+fw+tuft,ground-4),(x+fw+1,ground-1),
                (x+fw-1+(tuft if sg==1 else 0),ground),
                (x-fw-1-(tuft if sg==-1 else 0),ground),(x-fw-2,ground-2),
                (x-fw-1-tuft,ground-4),(x-fw+1,ground-7)]))
        body=union(neck,torso,*hips,*feet)
        stroke('body_outline',body);paint('body',body,'coat')
        bs=poly('body_shadow',[(58,body_top+8),(48+bw,ground-18),(48+bw+3,ground-6),
              (60,ground-2),(55,ground-8),(55,ground-19)])
        paint('body_shadow',bs,'coat_shadow',body)
        # Open seams only below the chest; no closed rectangles at the shoulders.
        for side,x in [('screen_left',44),('screen_right',52)]:
            line(side+'_leg_seam',[(x,ground-20),(x,ground-8),(x-1 if x<48 else x+1,ground-3)],'seam',body)
        t=coat['chest']
        chest=poly('chest',[(38,body_top+1),(58,body_top+1),(60,body_top+10),
            (57,body_top+13),(57,body_top+15+t),(53,body_top+14),
            (49,body_top+17+t),(46,body_top+15),(42,body_top+16+t),(40,body_top+13),(36,body_top+10)])
        shade=poly('chest_under',[(38,body_top+9),(58,body_top+9),(58,body_top+16+t),
              (49,body_top+20+t),(39,body_top+16+t)])
        paint('chest_under',shade,'coat_shadow',body);paint('chest',chest,'coat',body)
        if state['collar_visible']:
            cy=chin+1
            collar=poly('collar',[(40,cy),(56,cy),(56,cy+3),(40,cy+3)])
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
    crown=poly('crown',[(48-hw+4,top+7),(48-hw+5,top+1),(41,top-1),
           (44,top-2-t),(47,top),(50,top-3-t),(53,top),(57,top-1),(60,top+3),(48+hw-4,top+7)])
    t=coat['cheeks']
    cheeks=[]
    for side,sign in [('screen_left',-1),('screen_right',1)]:
        cheeks.append(poly(side+'_cheek',[(48+sign*(hw-3),chin-12),
          (48+sign*(hw+t),chin-7),(48+sign*(hw-2+t),chin-4),
          (48+sign*(jaw+2),chin+1+t),(48+sign*4,chin+1),(48+sign*5,chin-9)]))
    facial=union(face,crown,*cheeks)
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
        line(side+'_ear_fold',[(ex+sign*2,ey+7),(ex+sign*3,ey+15),(ex+sign*1,ey+21)],'seam',head)
    my=anchors['muzzle_center'][1];mw=g['muzzle_width']/2;mh=g['muzzle_height']
    muzzle=ellipse('muzzle',(48-mw,my-mh/2,48+mw,my+mh/2))
    for side,sign in [('screen_left',-1),('screen_right',1)]:
        ex,ey=anchors[side+'_eye_center'];rx=g['eye_rx'];ry=g['eye_ry']
        socket=ellipse(side+'_socket',(ex-rx-1,ey-ry-1,ex+rx+1,ey+ry+2))
        paint(side+'_socket',socket,'muzzle_shadow',facial)
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
        pupil=ellipse(side+'_pupil',(ex-rx+1,ey-ry+1,ex+rx-1,ey+ry-1),sign*g['eye_tilt'])
        paint(side+'_pupil',pupil,'pupil',visible)
        highlight=Image.new('L',(96,96));ImageDraw.Draw(highlight).point(transform((ex-1,ey)),fill=255)
        paint(side+'_highlight',highlight,'highlight',visible)
        paint(side+'_eyelid',lid,'coat');paint(side+'_front_fur',fur,'coat')
    paint('muzzle',muzzle,'muzzle',facial)
    shade=poly('muzzle_shadow',[(48-mw,my+2),(42,my+mh/2),(54,my+mh/2),(48+mw,my+2),
           (54,my+mh/2-2),(42,my+mh/2-2)])
    paint('muzzle_shadow',shade,'muzzle_shadow',ImageChops.multiply(muzzle,facial))
    nw=g['nose_width']/2;nh=g['nose_height'];ny=my-1
    nose=poly('nose',[(48-nw+1,ny-nh/2),(48+nw-1,ny-nh/2),(48+nw,ny),
                      (50,ny+nh/2),(46,ny+nh/2),(48-nw,ny)])
    paint('nose',nose,'nose',muzzle)
    line('nose_light',[(48-nw+2,ny-nh/2+1),(49,ny-nh/2+1)],'nose_light',nose)
    line('philtrum',[(48,ny+nh/2),(48,ny+nh/2+2)],'nose',muzzle)
    line('mouth',[(46,ny+nh/2+2),(50,ny+nh/2+2)],'nose',muzzle)
    output=Image.new('RGBA',(96,96))
    for name,m,role in layers:
        layer=Image.new('RGBA',(96,96),colors[role]);layer.putalpha(m);output.alpha_composite(layer)
    # Landmarks/masks are part of the editable package, not guessed from final pixels.
    package_geometry=maker.digest(b''.join(k.encode()+m.tobytes() for k,m in sorted(masks.items())))
    meta={'renderer_version':VERSION,'pillow_version':PIL_VERSION,'dog_id':state['dog_id'],
          'renderer_sha256':maker.digest(Path(__file__).read_bytes()),
          'state_schema_sha256':maker.digest((ROOT/'state_v02.py').read_bytes()),
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

def export(state,revision,directory,legacy_profile=None):
    out=Path(directory)
    if out.exists():raise FileExistsError(str(out))
    out.parent.mkdir(parents=True,exist_ok=True)
    tmp=Path(tempfile.mkdtemp(prefix='.nana-export-',dir=out.parent))
    try:
        data=preview(state);cards=[]
        for key,info in data.items():
            view,style=key.split('-');img,masks,meta=build(state,style,view)
            img.save(tmp/(key+'.png'));img.resize((576,576),Image.Resampling.NEAREST).save(tmp/(key+'-6x.png'))
            meta['authoring_revision']=revision
            (tmp/(key+'.json')).write_text(json.dumps(meta,ensure_ascii=False,indent=2))
            ld=tmp/(key+'-layers');ld.mkdir()
            for n,m in masks.items():m.save(ld/(n+'.png'))
            before=''
            if legacy_profile is not None:
                old,_,_=maker.build(legacy_profile,style,view);old.save(tmp/(key+'-v01.png'))
                before='<div><small>0.1</small><img src="'+key+'-v01.png"></div>'
            cards.append('<figure><figcaption>'+key+'</figcaption><div class="pair">'+before+'<div><small>0.2 · 검수 대기</small><img src="'+key+'.png"></div></div></figure>')
        (tmp/'index.html').write_text('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nana 0.2</title><style>body{font:16px system-ui;background:#f4eee4;padding:20px;color:#46382e}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(400px,1fr))}figure{margin:10px;background:#fffaf3;border-radius:12px;padding:12px}.pair{display:flex;gap:8px}.pair>div{flex:1}img{width:100%;image-rendering:pixelated}small{display:block}figcaption{font-weight:700}</style><h1>한 개체 정적 제작기 0.2</h1><p>동일 관찰 프로필에서 분리한 제작 상태 · 96×96 · 닮음/정본 미감 검수 대기</p><main>'+''.join(cards)+'</main>')
        # Rename only complete artifacts. Failed builds never become published output directories.
        if out.exists():raise FileExistsError(str(out))
        tmp.rename(out)
    except BaseException:
        shutil.rmtree(tmp,ignore_errors=True);raise

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--db',required=True)
    sub=ap.add_subparsers(dest='cmd',required=True)
    s=sub.add_parser('migrate');s.add_argument('dog');s.add_argument('--profile-revision',type=int);s.add_argument('--expected',type=int,default=0)
    s=sub.add_parser('render');s.add_argument('dog');s.add_argument('--revision',type=int);s.add_argument('--out',required=True)
    s=sub.add_parser('save');s.add_argument('state');s.add_argument('--expected',type=int,required=True);s.add_argument('--reason',required=True)
    s=sub.add_parser('restore');s.add_argument('dog');s.add_argument('--target',type=int,required=True);s.add_argument('--expected',type=int,required=True)
    s=sub.add_parser('state');s.add_argument('dog');s.add_argument('--revision',type=int)
    s=sub.add_parser('history');s.add_argument('dog')
    args=ap.parse_args();store=StateStore(args.db)
    try:
        if args.cmd=='migrate':
            p,rev=store.get(args.dog,args.profile_revision);print(store.state_save(migrate(p,rev),args.expected,'explicit v0.1 migration'))
        elif args.cmd=='render':
            state,rev=store.state_get(args.dog,args.revision);p,_=store.get(args.dog,state['source_profile']['revision']);export(state,rev,args.out,p);print(args.out)
        elif args.cmd=='save':print(store.state_save(json.loads(Path(args.state).read_text()),args.expected,args.reason))
        elif args.cmd=='restore':print(store.state_restore(args.dog,args.target,args.expected))
        elif args.cmd=='history':print(json.dumps(store.state_history(args.dog),ensure_ascii=False))
        else:print(json.dumps(store.state_get(args.dog,args.revision)[0],ensure_ascii=False,indent=2))
    except (ValueError,FileExistsError) as e:ap.exit(2,str(e)+'\n')
    finally:store.close()

if __name__=='__main__':main()
