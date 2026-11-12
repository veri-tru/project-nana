"""Fail-closed evidence gate before anatomy-dependent appearance work.

This checks hashes and explicit review scope, not whether an animal looks
anatomically correct. Human visual judgment remains a separate required gate.
No image generation or review approval is performed by this module.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import math

import numpy as np
from PIL import Image

from . import head

REQUIRED_VIEWS = {'front', 'three_quarter', 'side', 'back', 'top'}
REQUIRED_CHECKS = {'ear_root_and_free_edge', 'independent_occiput',
                   'jaw_to_throat', 'dorsal_neck_to_withers', 'throat_to_chest',
                   'canine_attachment_not_pedestal'}
SCOPE = 'head_neck_shoulders'
REJECTION_REGISTRY = head.ROOT / 'config/anatomy-rejections.json'
CAMERAS = {'front': (0, 0), 'three_quarter': (48, 7), 'side': (90, 0),
           'back': (180, 0), 'top': (90, 90)}


def projection_id(record):
    values = {key: record[key] for key in ('model_sha256', 'camera', 'scale', 'center', 'canvas')}
    return hashlib.sha256(json.dumps(values, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def view_evidence_errors(base, status, row):
    """Verify typed view/crop relationships, never infer anatomy from pixels."""
    errors = []
    artifacts = {item['path'] for item in status['artifacts']}
    renders = row.get('renders', [])
    if len(renders) != 5 or {v.get('view') for v in renders} != REQUIRED_VIEWS:
        return ['Typed five-view render evidence is required; booleans are insufficient']
    normal = {r['view']: r for r in renders}
    hidden = row.get('ears_hidden_renders', [])
    if len(hidden) != 2 or {r.get('view') for r in hidden} != {'side', 'back'}:
        errors.append('Typed ears-hidden side/back evidence is required')
    if len({r.get('artifact') for r in renders + hidden}) != len(renders + hidden):
        errors.append('Every diagnostic view needs a distinct saved image')
    for record in renders + hidden:
        name = record['view']
        if record.get('model_sha256') != row['model_sha256']:
            errors.append('Render record uses a different model')
        def finite_pair(value):
            return (isinstance(value, list) and len(value) == 2
                    and all(type(v) in (float, int) and math.isfinite(v) for v in value))

        if not finite_pair(record.get('camera')) or tuple(record['camera']) != CAMERAS.get(name):
            errors.append('View camera does not match its declared view')
        if not finite_pair(record.get('center')):
            errors.append('Render center must contain two finite numbers')
        canvas = record.get('canvas')
        if not isinstance(canvas, list) or len(canvas) != 2 or any(type(v) is not int or v <= 0 for v in canvas):
            errors.append('Render canvas must contain two positive integers')
        if type(record.get('scale')) not in (float, int) or not math.isfinite(record['scale']) or record['scale'] <= 0:
            errors.append('Invalid render scale')
        if record.get('projection_id') != projection_id(record):
            errors.append('Stale or incorrect model/camera/scale projection ID')
        if record.get('artifact') not in artifacts:
            errors.append('Render evidence image was not reviewed')
            continue
        with Image.open(base / record['artifact']) as image:
            if list(image.size) != record.get('canvas'):
                errors.append('Render evidence canvas does not match saved image')
        if record in hidden:
            reference = normal[name]
            if record['projection_id'] != reference['projection_id']:
                errors.append('Hidden-ear diagnostic changed camera/model/scale')
            with Image.open(base / record['artifact']) as hidden_image, Image.open(base / reference['artifact']) as visible_image:
                if np.array_equal(np.asarray(hidden_image.convert('RGBA')), np.asarray(visible_image.convert('RGBA'))):
                    errors.append('Hidden-ear pixels are identical to the visible-ear image')
    crop = row.get('crop_comparison', {})
    reference = normal['side']
    if crop.get('source_artifact') != reference['artifact'] or crop.get('projection_id') != reference['projection_id']:
        errors.append('Crop comparison does not use the same side-view model and camera')
    if crop.get('model_sha256') != row['model_sha256']:
        errors.append('Crop comparison uses another model')
    if crop.get('artifact') not in artifacts:
        errors.append('Missing reviewed short-crop image')
        return errors
    rect = crop.get('source_rect', [])
    with Image.open(base / reference['artifact']) as source, Image.open(base / crop['artifact']) as cropped:
        if (len(rect) != 4 or any(type(v) is not int for v in rect)
                or not (0 <= rect[0] < rect[2] <= source.width and 0 <= rect[1] < rect[3] <= source.height)
                or rect == [0, 0, source.width, source.height]):
            errors.append('Invalid or untrimmed crop rectangle')
        elif not np.array_equal(np.asarray(source.crop(tuple(rect)).convert('RGBA')), np.asarray(cropped.convert('RGBA'))):
            errors.append('Short crop is not the exact saved full image region; camera/scale/content changed')
    return errors


def rejected_hashes():
    records = head.read_json(REJECTION_REGISTRY)
    if records.get('schema_version') != 1 or not isinstance(records.get('blocked_artifacts'), list):
        raise ValueError('Invalid anatomy rejection registry')
    return {item['sha256'] for item in records['blocked_artifacts']}


def blocked_artifact_errors(status):
    blocked = rejected_hashes()
    # Hash identity survives file rename, subsets and extra-file additions.
    for event in status.get('history', []):
        if event.get('event') == 'USER_REJECTED':
            blocked.update(event.get('artifacts', {}).values())
    return ['Blocked artifact content reused: ' + item['path']
            for item in status.get('artifacts', []) if item['sha256'] in blocked]


def verdict(path):
    markers = re.findall(r'^<!-- review-verdict: (.+) -->\r?$', path.read_text('utf-8'), re.MULTILINE)
    if len(markers) != 1:
        raise ValueError('Exactly one review verdict is required')
    return json.loads(markers[0])


def check(status_path, contract_path):
    """Both reviews must explicitly cover the current complete structural scope."""
    status_path, contract_path = Path(status_path).resolve(), Path(contract_path).resolve()
    checker = head.module(head.ROOT / 'tools/review/check_delivery.py', 'structure_delivery_checker')
    errors = checker.check(status_path)
    try:
        status = head.read_json(status_path)
        contract = head.read_json(contract_path)
        errors.extend(blocked_artifact_errors(status))
        relative = os.path.relpath(contract_path, status_path.parent).replace('\\', '/')
        if status.get('inputs', {}).get(relative) != head.sha(contract_path):
            errors.append('Structure contract is not covered by the current review input hashes')
        if contract.get('schema_version') != 1 or contract.get('scope') != SCOPE:
            errors.append('Full head/neck/shoulders scope is required; ear-only PASS cannot be promoted')
        if contract.get('geometry_kind') != 'actual_mesh':
            errors.append('Image-generated views cannot establish same-mesh structural correctness')
        models = contract.get('models', {})
        if not models:
            errors.append('Missing saved structural models')
        approved_images = {item['path'] for item in status.get('artifacts', [])}
        appearance_refs = contract.get('appearance_reference_artifacts', [])
        if not appearance_refs or not set(appearance_refs) <= approved_images:
            errors.append('Corrected appearance reference images must be explicitly selected from reviewed artifacts')
        for name, digest in models.items():
            if status.get('inputs', {}).get(name) != digest:
                errors.append('Structural model is not covered by review: ' + name)
        rows = contract.get('view_sets', [])
        if len(rows) != len(models):
            errors.append('Every saved model requires an explicit full view set')
        seen = set()
        for row in rows:
            name = row.get('model')
            if name in seen or name not in models:
                errors.append('Duplicate or unknown model view set')
            seen.add(name)
            if row.get('model_sha256') != models.get(name):
                errors.append('Mixed/stale model across views')
            if set(row.get('views', [])) != REQUIRED_VIEWS:
                errors.append('Front/three-quarter/side/back/top views are all required')
            if row.get('frame') != 'head_neck_upper_thorax':
                errors.append('Short neck crop is insufficient to judge canine attachment')
            if row.get('ears_hidden_diagnostic') is not True:
                errors.append('Ears-hidden attachment inspection is required')
            if row.get('same_mesh_same_camera_crop_comparison') is not True:
                errors.append('Same-mesh/same-camera crop comparison is required to separate framing from geometry')
            images = row.get('artifacts', [])
            if not images or not set(images) <= approved_images:
                errors.append('View evidence images are not in the reviewed artifact set')
            errors.extend(view_evidence_errors(status_path.parent, status, row))
        if seen != set(models):
            errors.append('Model coverage is incomplete')
        for role in ('visual', 'technical'):
            report = status.get('reviews', {}).get(role, {}).get('report')
            if not report:
                continue  # Base gate reports this missing evidence.
            v = verdict(status_path.parent / report)
            evidence = v.get('structure_review', {})
            if evidence.get('scope') != SCOPE or evidence.get('contract_sha256') != head.sha(contract_path):
                errors.append(role + ': full structural scope was not explicitly reviewed')
            checks = evidence.get('checks', {})
            if set(checks) != REQUIRED_CHECKS or any(result != 'PASS' for result in checks.values()):
                errors.append(role + ': required attachment findings are missing or not PASS')
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        errors.append('Invalid structure evidence: ' + str(exc))
    return errors


def prepare(status_path, contract_path, output):
    errors = check(status_path, contract_path)
    if errors:
        raise ValueError('Appearance work blocked:\n- ' + '\n- '.join(errors))
    status_path = Path(status_path).resolve()
    contract_path = Path(contract_path).resolve()
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Refusing to overwrite an appearance input plan')
    status = head.read_json(status_path)
    contract = head.read_json(contract_path)
    record = {
        'schema_version': 1, 'scope': SCOPE, 'status': 'STRUCTURE_INPUTS_VERIFIED_ONLY',
        'structure_status': {'path': str(status_path), 'sha256': head.sha(status_path)},
        'structure_contract': {'path': str(contract_path), 'sha256': head.sha(contract_path)},
        'required_structure_images': {str((status_path.parent / a['path']).resolve()): a['sha256']
                                      for a in status['artifacts'] if a['path'] in contract['appearance_reference_artifacts']},
        'limitations': ['Not appearance approval', 'Revalidate before generation; no cached PASS',
                        'Final art needs fresh visual and technical reviews of ear AND neck continuity',
                        'Do not describe imagegen variants as exact parameter-only comparisons'],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    head.write_json(output, record)
    return record


def check_art_inputs(plan_path, generation_path):
    """Revalidate immediately before a built-in image_gen call; no cached PASS."""
    errors = []
    try:
        plan = head.read_json(plan_path)
        generation = head.read_json(generation_path)
        if plan.get('schema_version') != 1 or plan.get('scope') != SCOPE:
            errors.append('Invalid appearance plan scope/version')
        for key in ('structure_status', 'structure_contract'):
            if head.sha(plan[key]['path']) != plan[key]['sha256']:
                errors.append('Changed ' + key)
        status_path = Path(plan['structure_status']['path']).resolve()
        status = head.read_json(status_path)
        contract = head.read_json(plan['structure_contract']['path'])
        errors.extend(check(status_path, plan['structure_contract']['path']))
        expected = {str((status_path.parent / a['path']).resolve()): a['sha256'] for a in status['artifacts']
                    if a['path'] in contract['appearance_reference_artifacts']}
        if not expected or plan.get('required_structure_images') != expected:
            errors.append('Appearance plan references differ from original structural evidence')
        actual = {str(Path(path).resolve()) for path in generation.get('referenced_image_paths', [])}
        for path, digest in expected.items():
            if path not in actual or head.sha(path) != digest:
                errors.append('Missing/changed actual structural image input: ' + path)
        for path in actual:
            if head.sha(path) in rejected_hashes():
                errors.append('Rejected art reused as generation input: ' + path)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        errors.append('Invalid appearance inputs: ' + str(exc))
    return errors


def check_art_delivery(status_path, plan_path, generation_path):
    status_path = Path(status_path).resolve()
    checker = head.module(head.ROOT / 'tools/review/check_delivery.py', 'appearance_delivery_checker')
    errors = checker.check(status_path) + check_art_inputs(plan_path, generation_path)
    try:
        status = head.read_json(status_path)
        errors.extend(blocked_artifact_errors(status))
        for path in (plan_path, generation_path):
            relative = os.path.relpath(Path(path).resolve(), status_path.parent).replace('\\', '/')
            if status.get('inputs', {}).get(relative) != head.sha(path):
                errors.append('Appearance plan/generation record is not covered by final reviews')
        # Prove the structural files were among the reviewed final inputs too.
        plan = head.read_json(plan_path)
        for path, digest in plan['required_structure_images'].items():
            relative = os.path.relpath(path, status_path.parent).replace('\\', '/')
            if status.get('inputs', {}).get(relative) != digest:
                errors.append('Final reviews omit structural image input: ' + path)
        generation = head.read_json(generation_path)
        for path in generation.get('referenced_image_paths', []):
            relative = os.path.relpath(Path(path).resolve(), status_path.parent).replace('\\', '/')
            if status.get('inputs', {}).get(relative) != head.sha(path):
                errors.append('Final reviews omit or have stale actual generation input: ' + path)
        for role in ('visual', 'technical'):
            report = status.get('reviews', {}).get(role, {}).get('report')
            if not report:
                continue
            evidence = verdict(status_path.parent / report).get('appearance_review', {})
            if evidence.get('scope') != SCOPE or evidence.get('plan_sha256') != head.sha(plan_path):
                errors.append(role + ': final ear AND neck appearance not explicitly reviewed')
            checks = evidence.get('checks', {})
            if set(checks) != REQUIRED_CHECKS or any(v != 'PASS' for v in checks.values()):
                errors.append(role + ': final appearance has missing or failed structural checks')
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        errors.append('Invalid final appearance evidence: ' + str(exc))
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--status', type=Path)
    parser.add_argument('--contract', type=Path)
    parser.add_argument('--output-plan', type=Path)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--generation', type=Path)
    parser.add_argument('--art-status', type=Path)
    args = parser.parse_args(argv)
    if args.plan:
        if not args.generation or args.status or args.contract or args.output_plan:
            parser.error('--plan requires --generation and cannot combine with structure-stage arguments')
        problems = (check_art_delivery(args.art_status, args.plan, args.generation) if args.art_status
                    else check_art_inputs(args.plan, args.generation))
        print(json.dumps({'appearance_gate': 'BLOCKED' if problems else 'READY', 'reasons': problems}, ensure_ascii=False, indent=2))
        if problems:
            raise ValueError('Appearance evidence is not ready')
    elif not args.status or not args.contract or args.generation or args.art_status:
        parser.error('Structure stage requires --status and --contract')
    elif args.output_plan:
        prepare(args.status, args.contract, args.output_plan)
        print('STRUCTURE_INPUTS_VERIFIED_ONLY')
    else:
        problems = check(args.status, args.contract)
        print(json.dumps({'generation_gate': 'BLOCKED' if problems else 'READY', 'reasons': problems}, ensure_ascii=False, indent=2))
        if problems:
            raise ValueError('Structure review is not ready for appearance work')


if __name__ == '__main__':
    main()
