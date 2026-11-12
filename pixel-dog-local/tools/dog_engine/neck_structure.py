"""Head, caudally inclined neck and upper thorax structural study.

Authored neutral pose, not a measured animal or articulated cervical skeleton.
The old chopped neck is replaced at construction, never hidden beneath a new
neck. Independent ears and saved eyes are preserved. Catalog stays unchanged.
"""
from pathlib import Path
import argparse
import os

import numpy as np
from PIL import Image
from scipy.interpolate import PchipInterpolator

from . import ear_structure as ears, head, renderer

VARIANTS = {'A': -2.0, 'B': 0.0, 'C': 2.0}
ROOT = Path(__file__).resolve().parents[2]


def ellipsoid(q, center, radii):
    return (np.linalg.norm((q - center) / radii, axis=-1) - 1) * min(radii)


def neck_field(shift=0):
    # x grows caudally (towards body), y grows upwards. This is an envelope,
    # not vertebral joint coordinates. Upper attachment remains below occiput.
    levels = np.array([-52, -42, -28, -14, 0, 12, 18], float)
    centers = np.array([28, 23, 16, 7, -1, -7, -10], float)
    centers += shift * np.clip((12 - levels) / 52, 0, 1)
    depth = np.array([24, 25, 23, 19, 13, 10, 8], float)
    width = np.array([24, 25, 23, 20, 16, 13.65, 12.6], float)
    functions = [PchipInterpolator(levels, values) for values in (centers, depth, width)]

    def field(q):
        x, y, z = np.moveaxis(q, -1, 0)
        yy = np.clip(y, levels[0], levels[-1])
        cx, rx, rz = [fn(yy) for fn in functions]
        cap = np.where(y > 12, np.sqrt(np.clip(1 - ((y - 12) / 7)**2, 0, 1)), 1)
        value = (np.sqrt(((x - cx) / np.maximum(.1, rx * cap))**2
                         + (z / np.maximum(.1, rz * cap))**2) - 1) * np.minimum(rx, rz)
        value = np.maximum(value, np.maximum(levels[0] - y, y - 19))
        # Longitudinal upper chest/back, with paired shoulder volumes on the
        # sides of the thorax. No horizontal human clavicle/shoulder shelf.
        thorax = ellipsoid(q, [36 + shift, -40, 0], [39, 30, 25])
        body = ears.smooth_union(value, thorax, 10)
        for sign in (-1, 1):
            shoulder = ellipsoid(q, [20 + shift, -39, sign * 20], [17, 23, 9])
            body = ears.smooth_union(body, shoulder, 6)
        return body

    return field, dict(levels=levels.tolist(), center_x=centers.tolist(),
                       depth=depth.tolist(), half_width=width.tolist(),
                       lower_neck_caudal_shift=shift,
                       units='authored model units, not measured cm',
                       reference_scope='qualitative skull-neck-thorax connection, not inferred bones')


def build(variant):
    field, metadata = neck_field(VARIANTS[variant])
    _, base = ears.build_base(field, [(-76, 105), (-101, 59), (-50.4, 50.4)])
    result = ears.with_ears(base, 'B')
    result['variant'] = variant
    result['metadata']['neck_shoulder_study'] = metadata
    return result


def board(rows, title):
    height = 130 + len(rows) * 370
    im = Image.new('RGB', (2200, height), (248, 247, 242))
    renderer.label(im, 22, 15, title, 28, True)
    renderer.label(im, 22, 56, 'Actual same-mesh views | authored pose | upper thorax only | not B2 / native64', 19)
    for row, (name, model, options) in enumerate(rows):
        renderer.label(im, 24, 100 + row * 370, name, 21, True)
        for column, (view, az, el) in enumerate(ears.VIEWS):
            renderer.label(im, 26 + column * 440, 133 + row * 370, view, 17)
            q, c = ears.project(model, az, el, **options)
            low, high = q[:, :, :2].min((0, 1)), q[:, :, :2].max((0, 1))
            scale = 1.75
            center = np.array([column * 440 + 220, row * 370 + 315]) - (low + high) / 2 * [scale, -scale]
            renderer.paint(im, q, c, center, scale)
    return im


def export(folder):
    folder = Path(folder).resolve()
    if folder.exists():
        raise ValueError('Use a new output folder; preserve previous review evidence')
    folder.mkdir(parents=True)
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=3) as pool:
        models = dict(zip(VARIANTS, pool.map(build, VARIANTS)))
    board([(key + ' / lower neck rearward shift ' + str(VARIANTS[key]), model, {})
           for key, model in models.items()], 'Head / neck / shoulder continuity').save(folder / 'variants.png')
    board([('B / visible ears', models['B'], {}),
           ('B / ears hidden, jaw-throat and occiput-neck exposed', models['B'], {'show_ears': False}),
           ('B / same coat material', models['B'], {'uniform': True})],
          'Attachment inspection / same geometry').save(folder / 'structure.png')
    for key, model in models.items():
        arrays = {f'{part}_{channel}': value for part, data in model['parts'].items()
                  for channel, value in data.items() if isinstance(value, np.ndarray)}
        np.savez_compressed(folder / f'model-{key}.npz', **arrays)
    head.write_json(folder / 'parameters.json', {key: model['metadata']['neck_shoulder_study'] for key, model in models.items()})
    source_paths = [Path(__file__), Path(ears.__file__), Path(head.__file__), Path(renderer.__file__),
                    ROOT / 'tools/dog_engine/raster.py', ROOT / 'tools/dog_engine/runtime-inputs.json',
                    ROOT / 'tools/dog_engine/requirements.txt', ROOT / 'tools/head_engine/catalog.json',
                    ears.BONE_PATH, ROOT / 'outputs/skull-based-heads-v2/geometry.pkl',
                    ROOT / 'outputs/skull-based-heads-v2/review-status.json']
    for path in source_paths[:2]:
        (folder / (path.stem + '-snapshot.py')).write_bytes(path.read_bytes())
    inputs = source_paths + list(folder.glob('*.npz')) + list(folder.glob('*-snapshot.py')) + [folder / 'parameters.json']
    head.write_json(folder / 'review-inputs.json', {
        'artifacts': {p.name: head.sha(p) for p in folder.glob('*.png')},
        'inputs': {os.path.relpath(p, folder).replace('\\', '/'): head.sha(p) for p in inputs},
        'status': 'NOT_REVIEWED', 'limitations': ['Not a cervical skeleton, no vertebral articulation',
            'No measured individual anatomy; neutral authored stance', 'Upper thorax only, no full body/animation integration',
            'Not final coat/B2/native64 approval']})
    return folder


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    print(export(args.output))


if __name__ == '__main__':
    main()
