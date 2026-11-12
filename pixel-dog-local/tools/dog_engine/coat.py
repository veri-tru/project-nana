"""Describe coat requests and prepare isolated v03 authoring drafts, never art."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
CATALOG = Path(__file__).with_name('coat-references.json')
BRIDGE = ROOT / 'tools/static_maker/coat_bridge.py'
SUPPORTED = ('crown', 'ears', 'cheeks', 'chest', 'paws')
REGIONS = (*SUPPORTED, 'body', 'neck', 'muzzle', 'tail', 'left_ear', 'right_ear', 'legs')
LABELS = dict(crown='정수리', ears='양쪽 귀', cheeks='볼', chest='가슴', paws='발',
              body='몸통', neck='목', muzzle='주둥이', tail='꼬리',
              left_ear='왼쪽 귀', right_ear='오른쪽 귀', legs='다리')
LENGTHS = dict(short='짧게', medium='중간', long='길게')
LIMITS = [
    'static-v03: 96px front portrait/seated authoring only; not head 3D or native64.',
    'short/medium/long are authored offsets, not measured millimetres.',
    'ears applies to both ears; texture, volume and grooming shape are unsupported.',
    'References describe source examples, not presets or same-dog before/after pairs.',
    'Draft validation does not approve anatomy, likeness, style or user preference.',
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f'Duplicate JSON key: {key}')
            result[key] = value
        return result
    def bad_constant(value):
        raise ValueError(f'Non-finite JSON value: {value}')
    raw = Path(path).read_bytes()
    return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=pairs,
                      parse_constant=bad_constant), raw


def keys(value, allowed, required, name):
    if not isinstance(value, dict):
        raise ValueError(f'{name} must be an object')
    if set(value) - set(allowed) or set(required) - set(value):
        raise ValueError(f'{name}: unknown or missing fields')


def choice(value, options, name, nullable=True):
    if nullable and value is None:
        return
    if not isinstance(value, str) or value not in options:
        raise ValueError(f'{name}: expected one of {list(options)}')


def describe(request, *, catalog=None, registry=None):
    keys(request, ['schema_version', 'dog_id', 'target', 'model_id', 'intent', 'regions',
                   'texture', 'coat_layers', 'grooming', 'reference_ids'],
         ['schema_version', 'dog_id', 'target', 'intent', 'regions'], 'coat request')
    if type(request['schema_version']) is not int or request['schema_version'] != 1:
        raise ValueError('Coat request schema_version must be 1')
    if not isinstance(request['dog_id'], str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', request['dog_id']):
        raise ValueError('Invalid dog_id')
    choice(request['target'], ['static-v03', 'head-3d', 'native64'], 'target', False)
    keys(request['intent'], ['kind', 'note'], ['kind', 'note'], 'intent')
    choice(request['intent']['kind'], ['owner_request', 'authored_example'], 'intent.kind', False)
    note = request['intent']['note']
    if not isinstance(note, str) or not note.strip() or len(note) > 1000:
        raise ValueError('intent.note must be a nonempty string of at most 1000 characters')
    regions = request['regions']
    keys(regions, REGIONS, [], 'regions')
    patch, volume_patch, unsupported, phrases = {}, {}, [], []
    volume_regions = ()
    geometry_version = None
    supported_regions = SUPPORTED if request['target'] == 'static-v03' else ()
    model_id = request.get('model_id')
    if request['target'] == 'static-v03' and model_id is not None:
        raise ValueError('model_id belongs to registered 3D targets only')
    if request['target'] != 'static-v03':
        if model_id is None:
            unsupported.append('model_id_required_for_' + request['target'])
        else:
            if registry is None:
                registry = read_json(Path(__file__).with_name('coat-head-models.json'))[0]
            if not isinstance(model_id, str) or model_id not in registry['models']:
                raise ValueError('Unknown registered coat head model')
            spec = registry['models'][model_id]
            geometry_version = spec.get('geometry_version')
            if geometry_version not in ('envelope-v1', 'envelope-v2'):
                raise ValueError('Unknown registered coat geometry version')
            supported_regions = spec['length_regions']
            capability = 'native_volume_regions' if request['target'] == 'native64' else 'volume_regions'
            volume_regions = spec.get(capability, ()) if geometry_version == 'envelope-v2' else ()
    for name in REGIONS:
        if name not in regions:
            continue
        values = regions[name]
        keys(values, ['length', 'volume', 'length_mm'], [], f'regions.{name}')
        if not values or all(v is None for v in values.values()):
            raise ValueError(f'regions.{name} must contain a requested value')
        choice(values.get('length'), LENGTHS, f'{name}.length')
        choice(values.get('volume'), ['flat', 'moderate', 'full'], f'{name}.volume')
        mm = values.get('length_mm')
        if mm is not None and (type(mm) not in (int, float) or not math.isfinite(mm) or not 0 < mm <= 1000):
            raise ValueError(f'{name}.length_mm must be a positive finite number <= 1000')
        for field, value in values.items():
            if value is None:
                continue
            if field == 'length' and name in supported_regions:
                patch[name] = value
            elif field == 'volume' and name in volume_regions:
                volume_patch[name] = value
            else:
                unsupported.append(f'regions.{name}.{field}')
        if values.get('length'):
            phrases.append(f'{LABELS[name]} {LENGTHS[values["length"]]}')
        if values.get('volume'):
            phrases.append(f'{LABELS[name]} 풍성함={values["volume"]}')
        if mm is not None:
            phrases.append(f'{LABELS[name]} 요청 길이={mm}mm')
    choice(request.get('texture'), ['straight', 'wavy', 'curly', 'wire'], 'texture')
    choice(request.get('coat_layers'), ['single', 'double'], 'coat_layers')
    grooming = request.get('grooming')
    if grooming is not None and (not isinstance(grooming, str) or not grooming.strip() or len(grooming) > 500):
        raise ValueError('grooming must be null or a nonempty string of at most 500 characters')
    for field in ('texture', 'coat_layers', 'grooming'):
        if request.get(field) is not None:
            unsupported.append(field)
            phrases.append(f'{field}={request[field]}')
    references = request.get('reference_ids', [])
    if not isinstance(references, list) or any(not isinstance(v, str) for v in references) or len(references) != len(set(references)):
        raise ValueError('reference_ids must be a list of unique IDs')
    if references:
        if catalog is None:
            catalog, _ = read_json(CATALOG)
        known = {item['id'] for item in catalog['references']}
        if set(references) - known:
            raise ValueError('Unknown coat reference ID')
    if not phrases:
        raise ValueError('At least one coat preference is required')
    supported_status = 'SUPPORTED_DRAFT_ONLY' if request['target'] == 'static-v03' else 'STRUCTURE_REVIEW_REQUIRED'
    limits = LIMITS if request['target'] == 'static-v03' else [
        'Registered maltipoo-neck02 structural template only; not a measured individual.',
        'crown/cheeks/ears/chest lengths are authored envelope offsets, not mm.',
        'Prepare changed 3D structure, review it independently, then export native64.',
        'Native64 uses a neutral diagnostic palette; B2 matching and user approval remain pending.',
        'No texture/grooming shape, paws, body or independent ear lengths.',
        ('Fullness: '+('/'.join(volume_regions) or 'none')+' only for this target; authored spread, not hair count or density; omitted volume=flat and length=short.'
         if geometry_version == 'envelope-v2' else 'Fullness unsupported.')]
    result = dict(schema_version=1, dog_id=request['dog_id'], target=request['target'],
                role='render_preference_not_observation',
                status='UNSUPPORTED' if unsupported else supported_status,
                description_ko=' / '.join(phrases), applicable_patch=patch,
                unsupported=unsupported, reference_ids=references, limitations=limits)
    if geometry_version:
        result.update(geometry_version=geometry_version, volume_patch=volume_patch)
    return result


def apply_file(request_path, state_path, expected_hash, output):
    request, request_raw = read_json(request_path)
    state, state_raw = read_json(state_path)
    catalog, catalog_raw = read_json(CATALOG)
    plan = describe(request, catalog=catalog)
    if request['target'] != 'static-v03':
        raise ValueError('3D targets use head-prepare and head-native64, not v03 apply')
    if plan['unsupported']:
        raise ValueError('No partial application; unsupported: ' + ', '.join(plan['unsupported']))
    if not isinstance(expected_hash, str) or not re.fullmatch('[0-9a-f]{64}', expected_hash) or digest(state_raw) != expected_hash:
        raise ValueError('Source state hash mismatch; inspect the current state before applying')
    if not isinstance(state, dict) or state.get('dog_id') != request['dog_id']:
        raise ValueError('Request and state dog_id differ')
    target = Path(output).resolve()
    if target.exists():
        raise ValueError('Refusing to overwrite an existing output directory')
    for ancestor in (target, *target.parents):
        if (ancestor / 'review-status.json').exists():
            raise ValueError('Use a new directory outside an existing reviewed artifact')
    inputs = {str(Path(request_path).resolve()): digest(request_raw),
              str(Path(state_path).resolve()): digest(state_raw),
              str(CATALOG.resolve()): digest(catalog_raw)}
    dependencies = [Path(__file__), BRIDGE]
    dependencies.extend(ROOT / 'tools/static_maker' / rel for rel in (
        'maker.py', 'state_v02.py', 'state_v03.py', 'render_v03.py',
        'packages/v02/shapes.json', 'packages/v02/styles.json',
        'packages/v03/shapes.json', 'packages/v03/styles.json'))
    for path in dependencies:
        inputs[str(path.resolve())] = digest(path.read_bytes())
    result = subprocess.run([sys.executable, str(BRIDGE)],
                            input=encode(dict(state=state, patch=plan['applicable_patch'])),
                            capture_output=True, check=False,
                            env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
    if result.returncode:
        raise ValueError('v03 draft validation failed: ' + result.stderr.decode('utf-8', errors='replace').strip())
    bridged = json.loads(result.stdout)
    draft = bridged['state']
    expected = deepcopy(state)
    expected['coat'].update(plan['applicable_patch'])
    if draft != expected:
        raise ValueError('Bridge changed fields outside the requested coat lengths')
    draft_raw = encode(draft)
    record = dict(schema_version=1, request=request, plan=plan, inputs=inputs,
                  artifacts={'draft-state.json': digest(draft_raw)},
                  validation=bridged['validation'], review='UNREVIEWED',
                  source_binding='state_schema_only_not_database_authenticated',
                  saved_images=0, database_modified=False)
    # Validate everything before publishing; stage beside the target for same-volume rename.
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.coat-draft-', dir=target.parent))
    try:
        (staging / 'draft-state.json').write_bytes(draft_raw)
        (staging / 'application.json').write_bytes(encode(record))
        for name, expected_digest in inputs.items():
            if digest(Path(name).read_bytes()) != expected_digest:
                raise ValueError('Input changed during application: ' + name)
        if target.exists():
            raise ValueError('Refusing to overwrite an existing output directory')
        staging.rename(target)
    except BaseException:
        shutil.rmtree(staging)
        raise
    return record


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('references')
    desc = sub.add_parser('describe')
    desc.add_argument('--request', type=Path, required=True)
    apply = sub.add_parser('apply')
    apply.add_argument('--request', type=Path, required=True)
    apply.add_argument('--state', type=Path, required=True)
    apply.add_argument('--expected-state-sha256', required=True)
    apply.add_argument('--out', type=Path, required=True)
    prep = sub.add_parser('head-prepare')
    prep.add_argument('--request', type=Path, required=True)
    prep.add_argument('--out', type=Path, required=True)
    native = sub.add_parser('head-native64')
    native.add_argument('--prepared', type=Path, required=True)
    native.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'references':
            result = read_json(CATALOG)[0]
        elif args.command == 'describe':
            result = describe(read_json(args.request)[0])
        elif args.command in ('head-prepare', 'head-native64'):
            from . import coat_head
            record = (coat_head.prepare(args.request, args.out) if args.command == 'head-prepare'
                      else coat_head.render_native(args.prepared, args.out))
            result = dict(output=str(args.out), delivery=record['delivery'])
        else:
            result = apply_file(args.request, args.state, args.expected_state_sha256, args.out)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 2 if result.get('status') == 'UNSUPPORTED' else 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f'coat: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
