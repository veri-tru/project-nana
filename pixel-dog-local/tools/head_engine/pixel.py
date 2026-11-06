"""Native 64x64 head frames from the resolved, reviewed 3D head model.

Rasterize once at the native grid; no supersampling, image generation, downscale,
or per-view geometry changes. Pixel styling is intentionally separate from shape.
"""
from pathlib import Path
import argparse, hashlib, importlib, json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import label
try:
    from . import engine
except ImportError:
    import engine

SIZE=64
EXTENT=54.0
OUTLINE_SOFT=(110,76,45)
OUTLINE_DARK=(48,34,23)
INK=(35,29,23)
SHADOW=(171,113,56)
COAT=(216,158,83)
LIGHT=(241,194,121)
STYLES={
    'P1-soft':dict(outline=OUTLINE_SOFT, thresholds=(.77,.89),label='P1 · B2 부드러운 음영'),
    'P2-depth':dict(outline=OUTLINE_SOFT, thresholds=(.81,.93),label='P2 · B2 깊이 강조'),
    'P3-contrast':dict(outline=OUTLINE_DARK, thresholds=(.81,.93),label='P3 · C2 선명한 윤곽'),
}

def project(model,az,el):
    a,e=np.radians([az,el]);right=np.array([np.sin(a),0,np.cos(a)])
    front=np.array([-np.cos(a)*np.cos(e),np.sin(e),np.sin(a)*np.cos(e)])
    view=np.column_stack([right,np.cross(front,right),front])
    triangles=[];signals=[]
    for key,part in model['parts'].items():
        v=part['v']@view;n=part['n']@view
        shade=.73+.24*np.maximum(0,n@np.array([-.32,.72,.61]))+.035*np.maximum(0,n[:,1])
        original=np.asarray(part['c'])
        dark=np.all(original==[43,40,34],axis=1) if key=='skin' else np.ones(len(v),bool)
        ear=np.clip((220-original[:,0])/45,0,1) if key=='skin' else np.zeros(len(v))
        # RGB carries scalar lighting, ear material, and eye/nose membership.
        # Distinct semantic levels keep small visible noses separate from eyes.
        material=dark*(128 if key=='skin' else 255)
        values=np.column_stack([np.clip(shade,0,1)*255,ear*255,material])
        indices=part['f'][:,[0,1,2,2]]
        triangles.append(v[indices]);signals.append(values[indices])
    return np.concatenate(triangles),np.concatenate(signals)

def render_signals(model,mode='normalized',relative_scale=1.,scene_scale=.4):
    projections=[project(model,a,e) for _,a,e in engine.VIEWS]
    bounds=np.array([np.ptp(q[:,:,:2],axis=(0,1)) for q,_ in projections])
    if mode not in ('normalized','relative'):raise ValueError('Unknown pixel display mode')
    if mode=='normalized':scale=EXTENT/bounds.max()
    else:
        relative_scale=engine.number(relative_scale,'relative_scale',.1,3.)
        scene_scale=engine.number(scene_scale,'native_scene_scale',.01,2.)
        scale=relative_scale*scene_scale
    if (bounds*scale>EXTENT+1e-9).any():
        raise ValueError('Relative head exceeds the native canvas; reduce native_scene_scale')
    raster_dir=engine.ROOT/'outputs/head-skeleton-volume-v2'
    if str(raster_dir) not in sys.path:sys.path.insert(0,str(raster_dir))
    # Numba's existing disk cache records the original importable module name.
    raster=importlib.import_module('raster')
    if Path(raster.__file__).resolve()!=(raster_dir/'raster.py').resolve():
        raise ValueError('Unexpected raster module source')
    frames=[]
    for q,values in projections:
        low=q[:,:,:2].min((0,1));high=q[:,:,:2].max((0,1))
        center=np.array([32.,32.])-(low+high)/2*np.array([scale,-scale])
        px=q.copy();px[:,:,0]=px[:,:,0]*scale+center[0];px[:,:,1]=center[1]-px[:,:,1]*scale
        buffer=np.full((SIZE,SIZE),-np.inf)
        rgb=np.zeros((SIZE,SIZE,3),dtype=np.uint8)
        raster.raster(np.ascontiguousarray(px),np.ascontiguousarray(values,dtype=np.uint8),buffer,rgb)
        frames.append((rgb,np.isfinite(buffer)))
    return frames,{'mode':mode,'pixels_per_model_unit':float(scale),'extent_px':EXTENT,
                   'bounds_model_units':bounds.tolist(),'relative_scale_applied':mode=='relative'}

def neighbors(mask):
    pad=np.pad(mask,1)
    return [pad[:-2,1:-1],pad[2:,1:-1],pad[1:-1,:-2],pad[1:-1,2:]]

def feature_masks(rgb,mask):
    """Preserve visible semantic features at native resolution, not 3D edits."""
    nose=(rgb[:,:,2]>=64)&(rgb[:,:,2]<192)&mask
    eyes=(rgb[:,:,2]>=192)&mask
    if nose.any():
        yy,xx=np.where(nose)
        if np.ptp(xx)+1<=2:
            # Side/top nose patches become a visible block by adding just one
            # inward column, clipped to the original projected head silhouette.
            step=1 if xx.mean()<SIZE/2 else -1
            expanded=np.zeros_like(nose)
            nx=xx+step;valid=(nx>=0)&(nx<SIZE)
            expanded[yy[valid],nx[valid]]=True
            nose|=expanded&mask
    ids,count=label(eyes,structure=np.ones((3,3),dtype=int))
    rounded=np.zeros_like(eyes)
    for index in range(1,count+1):
        yy,xx=np.where(ids==index);area=len(xx)
        if area<3:
            rounded|=ids==index;continue
        diameter=4 if area>=8 else 3
        # 3-cell diamond or 4-cell octagon; center stays within half a cell of
        # the visible projected eye centroid. The far eye is never invented.
        x0=int(np.floor(xx.mean()-(diameter-1)/2+.5))
        y0=int(np.floor(yy.mean()-(diameter-1)/2+.5))
        for y in range(diameter):
            for x in range(diameter):
                if x in (0,diameter-1) and y in (0,diameter-1):continue
                px,py=x0+x,y0+y
                if 0<=px<SIZE and 0<=py<SIZE and mask[py,px] and not nose[py,px]:rounded[py,px]=True
    return nose,rounded

def style_frame(signals,style):
    rgb,mask=signals
    if not mask.any():raise ValueError('Empty frame')
    nose,eyes=feature_masks(rgb,mask)
    dark=nose|eyes
    ear=(rgb[:,:,1]>166)&mask&~dark
    body=mask&~ear&~dark
    shade=rgb[:,:,0]/255-rgb[:,:,1]/255*.14
    low,high=style['thresholds']
    rgba=np.zeros((SIZE,SIZE,4),dtype=np.uint8)
    rgba[mask,:3]=COAT
    rgba[mask&(shade<low),:3]=SHADOW
    rgba[mask&(shade>=high),:3]=LIGHT
    rgba[dark,:3]=INK
    # External one-cell outline keeps every native skin pixel and feature.
    outline=np.logical_or.reduce(neighbors(mask))&~mask
    # A short boundary separates the visible ear from the cheek; the upper
    # attachment remains a continuous material transition, not a hollow loop.
    seam=ear&np.logical_or.reduce(neighbors(body))
    if ear.any():
        seam[:np.where(ear)[0].min()+2]=False
    rgba[outline|seam,:3]=style['outline']
    rgba[mask|outline,3]=255
    return Image.fromarray(rgba)

def make_atlas(frames):
    im=Image.new('RGBA',(SIZE*len(frames),SIZE))
    for i,frame in enumerate(frames):im.paste(frame,(i*SIZE,0))
    return im

def comparison(variants):
    im=Image.new('RGB',(2400,1810),(248,247,242));draw=ImageDraw.Draw(im)
    regular='C:/Windows/Fonts/malgun.ttf';bold='C:/Windows/Fonts/malgunbd.ttf'
    def label(x,y,text,size=22,strong=False):
        draw.text((x,y),text,fill=(42,48,43),font=ImageFont.truetype(bold if strong else regular,size))
    label(28,18,'골든 리트리버 · 수정 B 골격의 64×64 픽셀',34,True)
    label(28,72,'세 안의 형상·눈·코·귀 위치 동일 · 윤곽/음영만 비교 · 큰 그림 6배 / 아래 원본 1배',23)
    for j,(name,_,_) in enumerate(engine.VIEWS):label(j*480+35,117,name,23,True)
    for i,(key,frames) in enumerate(variants.items()):
        y=165+i*520;draw.line((24,y,2376,y),fill=(215,219,212));label(28,y+7,STYLES[key]['label'],24,True)
        for j,frame in enumerate(frames):
            big=frame.resize((384,384),Image.Resampling.NEAREST)
            im.paste(big,(j*480+48,y+38),big)
            im.paste(frame,(j*480+208,y+425),frame)
    label(28,1760,'작업 기준 B · 사용자 선택 대기 · 머리/짧은 목 · 실제 기기 검수 전',21)
    return im

def validate_frames(variants):
    report={}
    for key,frames in variants.items():
        palette={tuple(c) for c in [STYLES[key]['outline'],INK,SHADOW,COAT,LIGHT]}
        report[key]=[]
        for frame in frames:
            a=np.asarray(frame);colors={tuple(c) for c in a[a[:,:,3]>0,:3]}
            assert frame.size==(64,64) and colors<=palette and len(colors)<=5
            assert set(np.unique(a[:,:,3]))<={0,255}
            mask=a[:,:,3]>0
            assert not (mask[0].any() or mask[-1].any() or mask[:,0].any() or mask[:,-1].any())
            report[key].append({'size':[64,64],'opaque_colors':len(colors),'alpha':[0,255],
                                'bbox':list(frame.getbbox())})
    for i in range(5):
        arrays=[np.array(frames[i]) for frames in variants.values()]
        assert all(np.array_equal(arrays[0][:,:,3],a[:,:,3]) for a in arrays[1:])
        assert all(np.array_equal(np.all(arrays[0][:,:,:3]==INK,axis=2),np.all(a[:,:,:3]==INK,axis=2)) for a in arrays[1:])
    return report

def export(resolved_path,output,*,mode=None,native_scene_scale=.4):
    resolved=engine.read_json(resolved_path);model=engine.load_model(resolved)
    if resolved['breed']!='golden':raise ValueError('This initial pixel palette adapter supports golden only')
    mode=resolved['display']['mode'] if mode is None else mode
    native_scene_scale=engine.number(native_scene_scale,'native_scene_scale',.01,2.)
    target=Path(output).resolve();root=(engine.ROOT/'outputs').resolve()
    if not target.is_relative_to(root):raise ValueError('Output must stay in project outputs')
    if any((p/'review-status.json').exists() for p in [target,*target.parents] if p.is_relative_to(root)):
        raise ValueError('Use a new folder; reviewed output is protected')
    names=[key+'-atlas.png' for key in STYLES]+['pixel-comparison.png','pixel-recipe.json','pixel-validation.json']
    if any((target/n).exists() for n in names):raise ValueError('Refusing to overwrite pixel outputs')
    raw,plan=render_signals(model,mode,resolved['values']['relative_scale'],native_scene_scale)
    variants={key:[style_frame(frame,s) for frame in raw] for key,s in STYLES.items()}
    report=validate_frames(variants);target.mkdir(parents=True,exist_ok=True)
    for key,frames in variants.items():make_atlas(frames).save(target/(key+'-atlas.png'))
    comparison(variants).save(target/'pixel-comparison.png')
    recipe={'renderer':'head-native64-v1','resolved_profile_sha256':engine.sha(resolved_path),
            'source_model':resolved['source'],'plan':plan,'frame_order':[v[0] for v in engine.VIEWS],
            'frame_size':[64,64],'atlas_size':[320,64],'styles':STYLES,
            'outline_colors':1,'fill_colors_max':4,'comparison_scale':6,'anti_aliasing':False,
            'source_grid':'direct 64x64 depth-buffer raster','user_selection':'PENDING',
            'native_scene_scale':native_scene_scale,
            'eye_nose_policy':'Visible nose <=2px wide: add one inward column within silhouette. Visible eye >=3px: 3px diamond or 4px octagon at projected centroid. No hidden eyes or highlights invented.',
            'limitations':['Head-only adapter; full body and animation are not produced.',
                           'Relative scale is authored, not measured centimeters.',
                           'Device rendering has not been tested.']}
    engine.write_json(target/'pixel-recipe.json',recipe)
    engine.write_json(target/'pixel-validation.json',report)
    return recipe

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('resolved',type=Path);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--mode',choices=['normalized','relative'],default=None)
    parser.add_argument('--native-scene-scale',type=float,default=.4)
    args=parser.parse_args();export(args.resolved,args.out,mode=args.mode,native_scene_scale=args.native_scene_scale)
    print('Saved native64 golden atlases and comparison to',args.out)

if __name__=='__main__':main()
