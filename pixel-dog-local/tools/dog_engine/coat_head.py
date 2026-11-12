"""Registered coat request -> changed 3D envelope -> reviewed native64 diagnostic.

Prepare structure first. Native export requires independent review of that exact
new structure contract. No archived generator or image model is called.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont, __version__ as PIL_VERSION

from . import coat, head, structure_gate
from . import coat_native64 as native

ROOT = head.ROOT
REGISTRY = Path(__file__).with_name('coat-head-models.json')


def registered(model_id, registry=None):
    if registry is None:
        registry = coat.read_json(REGISTRY)[0]
    if model_id not in registry['models']:
        raise ValueError('Unknown registered coat head model')
    spec = registry['models'][model_id]
    if spec.get('geometry_version') not in ('envelope-v1', 'envelope-v2'):
        raise ValueError('Unknown registered coat geometry version')
    base = ROOT / spec['directory']
    for filename, field in ((spec['model'], 'model_sha256'),
                            ('structure-contract.json', 'contract_sha256'),
                            ('review-status.json', 'status_sha256')):
        if head.sha(base / filename) != spec[field]:
            raise ValueError('Registered structural source changed: ' + filename)
    errors = structure_gate.check(base / 'review-status.json', base / 'structure-contract.json')
    if errors:
        raise ValueError('Registered source structure blocked: ' + '; '.join(errors))
    return spec, base


def dependencies(base, request_path):
    files = [Path(__file__), REGISTRY, coat.CATALOG, Path(coat.__file__), Path(native.__file__),
             Path(structure_gate.__file__), head.HERE/'coat_head_geometry.py',
             head.HERE/'coat_head_geometry_v2.py',
             head.HERE/'raster.py', head.HERE/'head.py',
             ROOT/'tools/review/check_delivery.py', Path(request_path).resolve(),
             base/'review-status.json', base/'structure-contract.json',
             Path('C:/Windows/Fonts/malgun.ttf')]
    status = coat.read_json(base/'review-status.json')[0]
    files.extend((base/name).resolve() for name in status['inputs'])
    files.extend((base/item['path']).resolve() for item in status['artifacts'])
    files.extend((base/review['report']).resolve() for review in status['reviews'].values())
    return {str(path.resolve()): head.sha(path) for path in files}


def verify_hashes(inputs):
    for path, expected in inputs.items():
        if head.sha(path) != expected:
            raise ValueError('Input changed: ' + path)


def transform(source, plan, spec):
    version = spec.get('geometry_version')
    if plan.get('geometry_version') != version:
        raise ValueError('Coat plan and registered geometry version differ')
    if version == 'envelope-v1':
        if plan.get('volume_patch'):
            raise ValueError('Fullness unsupported by envelope-v1')
        from .coat_head_geometry import apply_lengths
        return apply_lengths(source, plan['applicable_patch'])
    if version == 'envelope-v2':
        from .coat_head_geometry_v2 import apply_preferences
        return apply_preferences(source, plan['applicable_patch'], plan['volume_patch'])
    raise ValueError('Unknown registered coat geometry version')


def staging_target(output):
    target = Path(output).resolve()
    if not any(target.is_relative_to((ROOT/name).resolve()) for name in ('private-data', 'outputs')):
        raise ValueError('Output must be inside project private-data or outputs')
    if target.exists():
        raise ValueError('Refusing to overwrite existing output')
    if any((parent/'review-status.json').exists() for parent in (target, *target.parents)):
        raise ValueError('Use a new directory outside reviewed artifacts')
    target.parent.mkdir(parents=True, exist_ok=True)
    return target, Path(tempfile.mkdtemp(prefix='.coat-head-', dir=target.parent))


def publish(staging, target, inputs):
    verify_hashes(inputs)
    if target.exists():
        raise ValueError('Refusing to overwrite existing output')
    staging.rename(target)


def save_model(path, model):
    arrays = {name+'_'+channel: part[channel] for name, part in model['parts'].items()
              for channel in ('v', 'f', 'n', 'c')}
    np.savez_compressed(path, **arrays)


def sheet(images, names, title, scale=1):
    cell = 480
    rows = (len(images)+4)//5
    board = Image.new('RGB', (cell*5, rows*(cell+40)+80), '#f5f5f3')
    draw = ImageDraw.Draw(board)
    font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 20)
    draw.text((20, 20), title, font=font, fill='#303438')
    for i, (image, name) in enumerate(zip(images, names)):
        x, y = i%5*cell, 80+i//5*(cell+40)
        draw.text((x+16, y), name, font=font, fill='#303438')
        if scale != 1:
            image = image.resize((image.width*scale, image.height*scale), Image.Resampling.NEAREST)
        board.paste(image, (x+(cell-image.width)//2, y+34), image)
    return board


def prepare(request_path, output):
    from . import coat_head_geometry as geometry
    request, request_raw = coat.read_json(request_path)
    registry, registry_raw = coat.read_json(REGISTRY)
    catalog, catalog_raw = coat.read_json(coat.CATALOG)
    plan = coat.describe(request, registry=registry, catalog=catalog)
    if request['target'] not in ('head-3d', 'native64') or plan['unsupported']:
        raise ValueError('A supported registered 3D coat request is required; no partial application')
    spec, base = registered(request['model_id'], registry)
    inputs = dependencies(base, request_path)
    if inputs[str(REGISTRY.resolve())] != coat.digest(registry_raw):
        raise ValueError('Registry changed while validating')
    if inputs[str(coat.CATALOG.resolve())] != coat.digest(catalog_raw):
        raise ValueError('Catalog changed while validating')
    if inputs[str(Path(request_path).resolve())] != coat.digest(request_raw):
        raise ValueError('Request changed while validating')
    source = geometry.load_npz(base/spec['model'])
    model, changes = transform(source, plan, spec)
    semantics = native.source_semantics(source)
    cameras = native.camera_plan(source, 480)
    native_cameras = native.camera_plan(source, 64)
    target, staging = staging_target(output)
    try:
        save_model(staging/'model.npz', model)
        np.savez_compressed(staging/'semantics.npz', **semantics)
        model_hash = head.sha(staging/'model.npz')
        renders, hidden, images, names = [], [], [], []
        for name, camera in cameras.items():
            image, _, _ = native.render(model, semantics, camera)
            image.save(staging/(name+'.png'))
            record = dict(view=name, artifact=name+'.png', model_sha256=model_hash, **camera)
            record['projection_id'] = structure_gate.projection_id(record)
            renders.append(record)
            images.append(image)
            names.append(name)
        for name in ('side', 'back'):
            image, _, _ = native.render(model, semantics, cameras[name], hide_ears=True)
            filename = name+'-hidden.png'
            image.save(staging/filename)
            record = dict(view=name, artifact=filename, model_sha256=model_hash, **cameras[name])
            record['projection_id'] = structure_gate.projection_id(record)
            hidden.append(record)
            images.append(image)
            names.append(name+' / ears hidden')
        rect = [0, 0, 480, 280]
        with Image.open(staging/'side.png') as side:
            cropped = side.crop(rect)
            cropped.save(staging/'side-short-crop.png')
            images.append(cropped.copy())
            names.append('side / same-camera crop')
        sheet(images, names, 'Actual 3D coat envelope | fixed cameras | structure review required').save(staging/'structure-sheet.png')
        pngs = sorted(path.name for path in staging.glob('*.png'))
        row = dict(model='model.npz', model_sha256=model_hash, views=list(cameras),
                   frame='head_neck_upper_thorax', ears_hidden_diagnostic=True,
                   same_mesh_same_camera_crop_comparison=True, artifacts=pngs,
                   renders=renders, ears_hidden_renders=hidden,
                   crop_comparison=dict(source_artifact='side.png', artifact='side-short-crop.png',
                                        source_rect=rect, model_sha256=model_hash,
                                        projection_id=next(r['projection_id'] for r in renders if r['view']=='side')))
        contract = dict(schema_version=1, scope='head_neck_shoulders', geometry_kind='actual_mesh',
                        models={'model.npz': model_hash}, appearance_reference_artifacts=['structure-sheet.png'],
                        view_sets=[row])
        (staging/'structure-contract.json').write_bytes(coat.encode(contract))
        record = dict(schema_version=1, request=request, plan=plan, inputs=inputs,
                      source_model_sha256=spec['model_sha256'], changes=changes,
                      model_sha256=model_hash, semantics_sha256=head.sha(staging/'semantics.npz'),
                      structure_contract_sha256=head.sha(staging/'structure-contract.json'),
                      native_cameras=native_cameras, source_cameras=cameras,
                      semantic_policy='Pinned source face IDs; nose when at least 2 of 3 source vertices are nose; flat categorical faces',
                      tone_policy=native.TONE_POLICY,
                      source_identity=spec['kind'], visual_review='NOT_REVIEWED', delivery='BLOCKED',
                      runtime=dict(python=sys.version.split()[0], pillow=PIL_VERSION, numpy=np.__version__))
        (staging/'preparation.json').write_bytes(coat.encode(record))
        publish(staging, target, inputs)
    except BaseException:
        shutil.rmtree(staging)
        raise
    return record


def render_native(prepared, output):
    from . import coat_head_geometry as geometry
    prepared = Path(prepared).resolve()
    record = coat.read_json(prepared/'preparation.json')[0]
    if type(record.get('schema_version')) is not int or record['schema_version'] != 1:
        raise ValueError('Unsupported preparation schema')
    errors = structure_gate.check(prepared/'review-status.json', prepared/'structure-contract.json')
    if errors:
        raise ValueError('Changed coat structure review required: ' + '; '.join(errors))
    review = coat.read_json(prepared/'review-status.json')[0]
    for name in ('preparation.json', 'model.npz', 'semantics.npz'):
        if review['inputs'].get(name) != head.sha(prepared/name):
            raise ValueError('Prepared coat data is not covered by structural review: ' + name)
    verify_hashes(record['inputs'])
    for file, field in (('model.npz', 'model_sha256'), ('semantics.npz', 'semantics_sha256'),
                        ('structure-contract.json', 'structure_contract_sha256')):
        if head.sha(prepared/file) != record[field]:
            raise ValueError('Prepared data changed: ' + file)
    registry, registry_raw = coat.read_json(REGISTRY)
    catalog, catalog_raw = coat.read_json(coat.CATALOG)
    if record['inputs'].get(str(REGISTRY.resolve())) != coat.digest(registry_raw):
        raise ValueError('Registered geometry snapshot changed')
    if record['inputs'].get(str(coat.CATALOG.resolve())) != coat.digest(catalog_raw):
        raise ValueError('Reference catalog snapshot changed')
    plan = coat.describe(record['request'], registry=registry, catalog=catalog)
    if (record['request']['target'] not in ('head-3d', 'native64') or plan['unsupported']
            or record['plan'] != plan):
        raise ValueError('Prepared request is unsupported or plan changed; no partial application')
    export_plan = coat.describe({**record['request'], 'target':'native64'}, registry=registry, catalog=catalog)
    if export_plan['unsupported']:
        raise ValueError('Native64 cannot represent this preference; no partial application: '
                         + ', '.join(export_plan['unsupported']))
    spec, base = registered(record['request']['model_id'], registry)
    if record['source_model_sha256'] != spec['model_sha256'] or record['source_identity'] != spec['kind']:
        raise ValueError('Prepared structural source binding changed')
    source = geometry.load_npz(base/spec['model'])
    expected, changes = transform(source, plan, spec)
    expected_arrays = {name+'_'+channel:part[channel] for name, part in expected['parts'].items()
                       for channel in ('v', 'f', 'n', 'c')}
    with np.load(prepared/'model.npz', allow_pickle=False) as stored_model:
        if set(stored_model.files) != set(expected_arrays):
            raise ValueError('Prepared model has unexpected channels')
        for name, value in expected_arrays.items():
            if stored_model[name].dtype != value.dtype or not np.array_equal(stored_model[name], value):
                raise ValueError('Prepared model does not reproduce its request')
    model = expected
    cameras = native.camera_plan(source, 64)
    if record['native_cameras'] != cameras or record['changes'] != changes:
        raise ValueError('Camera plan or coat changes were edited')
    semantics = native.source_semantics(source)
    with np.load(prepared/'semantics.npz', allow_pickle=False) as stored:
        if set(stored.files) != set(semantics) or any(not np.array_equal(stored[k], v) for k, v in semantics.items()):
            raise ValueError('Prepared semantic labels changed')
    inputs = dependencies(prepared, prepared/'preparation.json')
    if inputs[str(REGISTRY.resolve())] != coat.digest(registry_raw):
        raise ValueError('Registry changed while validating')
    if inputs[str(coat.CATALOG.resolve())] != coat.digest(catalog_raw):
        raise ValueError('Catalog changed while validating')
    inputs.update(record['inputs'])
    inputs[str((prepared/'model.npz').resolve())] = head.sha(prepared/'model.npz')
    inputs[str((prepared/'semantics.npz').resolve())] = head.sha(prepared/'semantics.npz')
    target, staging = staging_target(output)
    try:
        frames, masks, depths = [], {}, {}
        for name, camera in cameras.items():
            image, mask, depth = native.render(model, semantics, camera)
            image.save(staging/(name+'.png'))
            frames.append(image)
            masks[name] = mask
            depths[name] = depth
        atlas = Image.new('RGBA', (320, 64))
        for i, frame in enumerate(frames):
            atlas.paste(frame, (i*64, 0))
        atlas.save(staging/'native64-atlas.png')
        sheet(frames, list(cameras), 'Native64 diagnostic | direct raster | 6x nearest preview | NOT B2 approval', 6).save(staging/'native64-preview.png')
        np.savez_compressed(staging/'semantic-masks.npz', **masks)
        np.savez_compressed(staging/'depth.npz', **depths)
        result = dict(schema_version=1, renderer='coat-semantic-native64-v2-chest-tone', request=record['request'],
                      inputs=inputs, model_sha256=record['model_sha256'], cameras=cameras,
                      artifacts={p.name:head.sha(p) for p in sorted(staging.iterdir())},
                      source_grid='direct 64x64 depth-buffer raster; no resize',
                      frame_size=[64,64], frame_order=list(cameras), palette=native.PALETTE,
                      tone_policy=native.TONE_POLICY,
                      geometry_review='PASS', appearance_review='NOT_REVIEWED', delivery='BLOCKED',
                      canonical_style_match='NOT_VALIDATED', user_selection='PENDING',
                      runtime=dict(python=sys.version.split()[0], pillow=PIL_VERSION, numpy=np.__version__),
                      limitations=['Neutral engineering diagnostic, not approved B2 artwork.',
                                   'Head, neck and upper thorax only; no full body or animation.',
                                   'Hair lengths are authored envelope offsets, not mm or density.'])
        (staging/'native64-record.json').write_bytes(coat.encode(result))
        publish(staging, target, inputs)
    except BaseException:
        shutil.rmtree(staging)
        raise
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--request', type=Path, required=True)
    prep.add_argument('--out', type=Path, required=True)
    render = sub.add_parser('native64')
    render.add_argument('--prepared', type=Path, required=True)
    render.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = prepare(args.request, args.out) if args.command == 'prepare' else render_native(args.prepared, args.out)
        print(json.dumps({'output':str(args.out), 'delivery':result['delivery']}, ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f'coat-head: {exc}\n')


if __name__ == '__main__':
    main()
