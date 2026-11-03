"""Run three projection trials from one photo assessment and one saved dog revision."""
import argparse
import json
import math
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageChops
import maker
import muzzle
from render_v03 import build
from state_v03 import StateStore


def validate_concept(concept):
    required={'dog_id','revision','photo_observations','table_reference','design_choice',
              'unknowns','projection','turn'}
    if not isinstance(concept,dict) or set(concept)!=required:
        raise ValueError('concept must match the documented input fields')
    for key in ('dog_id','table_reference','design_choice'):
        if not isinstance(concept[key],str) or not concept[key].strip():
            raise ValueError(f'{key}: text required')
    for key in ('photo_observations','unknowns'):
        items=concept[key]
        if not isinstance(items,list) or any(not isinstance(v,str) or not v.strip() for v in items):
            raise ValueError(f'{key}: list of text required')
    if not concept['photo_observations']:
        raise ValueError('photo observations with source identifiers required')
    if type(concept['revision'])!=int or concept['revision']<1:
        raise ValueError('positive authoring revision required')
    def number(v):
        return type(v) in (int,float) and math.isfinite(v)
    values=concept['projection']
    if (not isinstance(values,list) or len(values)!=3 or
        any(not number(v) or not 0<=v<=.3 for v in values) or not values[0]<values[1]<values[2]):
        raise ValueError('projection: supply three increasing fractions in [0,0.3]')
    if not number(concept['turn']) or not -1<=concept['turn']<=1:
        raise ValueError('turn: signed lateral direction in [-1,1] required')


def export_round(store, concept, out):
    validate_concept(concept)
    state,revision=store.state_get(concept['dog_id'],concept['revision'])
    if state['schema_version']!=3:
        raise ValueError('rounds require a migrated v3 authoring state')
    def render_trial(depth):
        frame,masks,_=build(state,'B2','full',projection=depth,turn=concept['turn'])
        return frame,masks['muzzle'],masks['far_pad'],masks['near_pad']
    provenance={'authoring_revision':revision,'state_sha256':maker.digest(maker.canonical(state).encode()),
                'source_profile':state['source_profile'],'package':state['package'],
                'renderer_sha256':maker.digest(Path(__file__).with_name('render_v03.py').read_bytes())}
    publish_round(concept,out,render_trial,provenance)


def publish_round(concept,out,render_trial,provenance):
    """Adapters return the frame, editable muzzle mask, and both exposed cheek masks."""
    validate_concept(concept)
    out=Path(out)
    if out.exists():
        raise FileExistsError(out)
    out.parent.mkdir(parents=True,exist_ok=True)
    tmp=Path(tempfile.mkdtemp(prefix='.round-',dir=out.parent))
    try:
        def trial(item):
            label,depth=item
            frame,mask,far_pad,near_pad=render_trial(depth)
            if frame.mode!='RGBA' or mask.mode!='L' or frame.size!=mask.size:
                raise ValueError('expected RGBA frame and matching muzzle mask')
            if not set(frame.getchannel('A').getdata())<={0,255}:
                raise ValueError('fractional alpha')
            if len({px[:3] for px in frame.getdata() if px[3]})>5:
                raise ValueError('palette budget exceeded')
            path=tmp/f'{label}.png'
            frame.save(path)
            return frame,mask,far_pad,near_pad,dict(file=path.name,projection=depth,
                                               exposed_far_pad_px=far_pad.histogram()[255],
                                               sha256=maker.digest(path.read_bytes()))
        with ThreadPoolExecutor(max_workers=3) as pool:
            results=list(pool.map(trial,zip('ABC',concept['projection'])))
        base,base_mask,_,_,_=results[0]
        if len({r[-1]['sha256'] for r in results})!=3:
            raise ValueError('projections are indistinguishable on this grid; choose wider intervals')
        for frame,mask,_,_,_ in results[1:]:
            allowed=ImageChops.lighter(base_mask,mask)
            delta=ImageChops.difference(base.convert('RGB'),frame.convert('RGB'))
            outside=ImageChops.invert(allowed)
            if any(ImageChops.multiply(ch,outside).getbbox() for ch in delta.split()):
                raise ValueError('changed pixels outside the declared muzzle')
            if base.getchannel('A').tobytes()!=frame.getchannel('A').tobytes():
                raise ValueError('body silhouette changed')
        if concept['turn']:
            for (prev,_,previous_pad,_,_),(frame,_,_,near_pad,record) in zip(results,results[1:]):
                transferred=ImageChops.multiply(previous_pad,near_pad)
                diff=ImageChops.difference(prev.convert('RGB'),frame.convert('RGB'))
                changed=sum(bool(v) and rgb!=(0,0,0) for v,rgb in zip(transferred.getdata(),diff.getdata()))
                if not changed or record['exposed_far_pad_px']>=previous_pad.histogram()[255]:
                    raise ValueError('far-pad occlusion is indistinguishable on this grid')
                record['visible_far_to_near_transfer_px']=changed
        manifest={'concept':concept,'provenance':provenance,
                  'part_sha256':maker.digest(Path(__file__).with_name('muzzle.py').read_bytes()),
                  'candidates':[r[-1] for r in results],'review_scope':'rules_and_method_only',
                  'owner_selection':None}
        (tmp/'round.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
        tmp.rename(out)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)


def export_template_round(template_path,concept,out):
    """Render on registered base/slot layers. The slot must be free of a baked nose."""
    validate_concept(concept)
    package=json.loads(template_path.read_text(encoding='utf-8-sig'))
    if package.get('dog_id')!=concept['dog_id'] or package.get('revision')!=concept['revision']:
        raise ValueError('concept and template must identify the same dog and revision')
    base_path=template_path.parent/package['base']
    slot_path=template_path.parent/package['slot']
    with Image.open(base_path) as src:
        base=src.convert('RGBA')
    with Image.open(slot_path) as src:
        slot=src.convert('L')
    if base.size!=slot.size or not slot.getbbox() or not set(slot.getdata())<={0,255}:
        raise ValueError('expected a nonempty binary slot on the same canvas as the base')
    if ImageChops.subtract(slot,base.getchannel('A')).getbbox():
        raise ValueError('slot exceeds the opaque character')
    colors=package['colors']
    if set(colors)!={'outline','coat','muzzle','muzzle_shadow','nose'} or any(
        not isinstance(c,str) or len(c)!=7 or c[0]!='#' for c in colors.values()
    ):
        raise ValueError('expected one contour and four fill colours in #RRGGBB')
    palette={tuple(bytes.fromhex(value[1:])) for value in colors.values()}
    if colors['outline'].lower() in {c.lower() for k,c in colors.items() if k!='outline'}:
        raise ValueError('contour ink must be distinct from fills')
    if any(px[:3] not in palette for px in base.getdata() if px[3]):
        raise ValueError('base must use the declared palette')

    def render_trial(depth):
        part=muzzle.masks(base.size,package['center'],package['span'],package['nose_size'],
                          depth,concept['turn'],lambda pt:tuple(round(v) for v in pt),
                          lobe_depth=package.get('lobe_depth',0))
        frame=base.copy()
        for name,mask in part.items():
            role=muzzle.ROLES[name]
            frame.paste(colors[role],mask=ImageChops.multiply(slot,mask))
        allowed=ImageChops.multiply(slot,part['muzzle'])
        if not allowed.getbbox() or not part['nose'].getbbox() or ImageChops.subtract(part['nose'],slot).getbbox():
            raise ValueError('registered slot must contain the projected nose')
        return frame,allowed,ImageChops.multiply(slot,part['far_pad']),ImageChops.multiply(slot,part['near_pad'])

    provenance={'template_sha256':maker.digest(template_path.read_bytes()),
                'base_sha256':maker.digest(base_path.read_bytes()),
                'slot_sha256':maker.digest(slot_path.read_bytes())}
    publish_round(concept,out,render_trial,provenance)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('concept',type=Path)
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--db',type=Path)
    source.add_argument('--template',type=Path)
    parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args()
    try:
        concept=json.loads(args.concept.read_text(encoding='utf-8-sig'))
        if args.template:
            export_template_round(args.template,concept,args.out)
        else:
            store=StateStore(args.db)
            try:
                export_round(store,concept,args.out)
            finally:
                store.close()
    except (ValueError,FileExistsError,KeyError) as exc:
        parser.exit(2,f'{exc}\n')

if __name__=='__main__':
    main()
