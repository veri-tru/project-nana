"""Experimental, separately owned hanging ears; never mutates catalog presets.

Replays the stored maltipoo tissue envelope without its ear boolean. The face
fairing algorithm is migrated from the frozen v2 builder, not imported from it.
All distances are authored model units, not measurements of the two pets.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import pickle

import numpy as np
from PIL import Image
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter, map_coordinates
from scipy.sparse import coo_matrix
from scipy.spatial import cKDTree
from skimage.measure import marching_cubes

from . import head, renderer

ROOT = Path(__file__).resolve().parents[2]
BONE_PATH = ROOT / 'outputs/head-skeleton-volume-v2/geometry.pkl'
BONE_SHA = 'eaec7d20d5ea8abbb8a14e728d6120f4f119e2d3ee238d4af5b3836f06e4d154'
VIEWS = [('FRONT', 0, 0), ('3/4', 48, 7), ('SIDE', 90, 0),
         ('BACK', 180, 0), ('TOP', 90, 90)]
VARIANTS = {'A': -1.0, 'B': 0.0, 'C': 1.0}
EAR_KEYS = ('ear_left', 'ear_right')


def smooth_union(a, b, radius):
    h = np.clip(.5 + .5 * (b - a) / radius, 0, 1)
    return b * (1 - h) + a * h - radius * h * (1 - h)


def head_fields(meta, neck_field=None):
    """Reconstruct only the stored head/neck envelope, with no ear field."""
    sections = meta['sections']
    xs, cy_values, radii = (np.asarray(sections[k]) for k in ('xs', 'cy', 'radius'))
    cy_fn = PchipInterpolator(xs, cy_values)
    support = meta['muzzle_support']
    front, tip = support['front'], support['tip']
    dorsal = np.asarray(meta['profile']['dorsal'])
    nc, size = np.asarray(meta['nose_center']), meta['nose_size']
    neck = meta['neck']
    neck_fns = [PchipInterpolator(neck['y'], neck[k]) for k in ('center_x', 'depth', 'half_width')]

    def nose(q):
        v = (q - nc) / size
        width = 1.18 * (1 + .12 * np.clip(v[..., 1], -1, 1))
        return (np.sqrt((v[..., 0] / .68)**2 + (v[..., 1] / .70)**2
                        + (v[..., 2] / width)**2) - 1) * size * .68

    def field(q):
        x, y, z = np.moveaxis(q, -1, 0)
        xc = np.clip(x, front, xs[-1])
        cy = np.where(x < front, support['center_y'], cy_fn(xc))
        theta = np.arctan2(z, y - cy)
        ix = np.interp(xc, xs, np.arange(len(xs)))
        iy = (theta + np.pi) / (2 * np.pi) * (radii.shape[1] - 1)

        def sample(index):
            return map_coordinates(radii, [np.broadcast_to(index, x.shape).ravel(), iy.ravel()],
                                   order=1, mode='nearest').reshape(x.shape)

        radius = sample(ix)
        front_radius = sample(np.interp(front, xs, np.arange(len(xs))))
        pad = 1 / np.sqrt((np.cos(theta) / support['minimum_half_height'])**2
                          + (np.sin(theta) / support['minimum_half_width'])**2)
        pad = np.maximum(pad, front_radius + .5)
        radius = np.where(x < dorsal[2, 0], -smooth_union(-radius, -pad, 3), radius)
        cap = np.sqrt(np.maximum(0, 1 - ((x - front) / (front - tip))**2))
        radius = np.where(x < front, -smooth_union(-front_radius, -pad, 3) * cap, radius)
        equator, end = dorsal[0, 0] - 7, xs[-1] + 5
        rear_cap = sample(len(xs) - 1) * np.sqrt(np.maximum(0, 1 - ((x - equator) / (end - equator))**2))
        rear_cap /= np.sqrt(1 - ((xs[-1] - equator) / (end - equator))**2)
        radius = np.where(x > xs[-1], rear_cap, radius)
        body = np.maximum(np.hypot(y - cy, z) - radius, np.maximum(tip - x, x - end))
        core = smooth_union(body, nose(q), 2.2)
        if neck_field is not None:
            return smooth_union(core, neck_field(q), 6.5)
        yy = np.clip(y, -21, 18)
        cx, depth, width = [fn(yy) for fn in neck_fns]
        cap = np.where(y > 12, np.sqrt(np.clip(1 - ((y - 12) / 7)**2, 0, 1)), 1)
        neck_value = (np.sqrt(((x - cx) / np.maximum(.1, depth * cap))**2
                             + (z / np.maximum(.1, width * cap))**2) - 1) * np.minimum(depth, width)
        neck_value = np.maximum(neck_value, np.maximum(-21 - y, y - 19))
        return smooth_union(core, neck_value, 6.5)

    return field, nose


def mesh(field, bounds, step=.65, color=(237, 225, 203)):
    axes = [np.arange(low, high + step, step) for low, high in bounds]
    points = np.stack(np.meshgrid(*axes, indexing='ij'), axis=-1)
    values = gaussian_filter(field(points).astype(np.float32), .65)
    v, f, n, _ = marching_cubes(values, 0, spacing=(step,) * 3, allow_degenerate=False)
    v += np.array([low for low, _ in bounds])
    return dict(v=v, f=f, n=-n, c=np.tile(np.asarray(color, float), (len(v), 1)))


def fair_face(part, bones, meta):
    """Same v2 anterior fairing and bone obstacle; ears are never in this mesh."""
    v, f = part['v'].copy(), part['f']
    original = v.copy()
    edges = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
    edges = np.unique(np.sort(edges, axis=1), axis=0)
    ii, jj = np.r_[edges[:, 0], edges[:, 1]], np.r_[edges[:, 1], edges[:, 0]]
    degree = np.bincount(ii, minlength=len(v))
    adj = coo_matrix((1 / degree[ii], (ii, jj)), shape=(len(v), len(v))).tocsr()

    def smooth(t):
        t = np.clip(t, 0, 1)
        return t**3 * (t * (t * 6 - 15) + 10)

    dorsal = np.asarray(meta['profile']['dorsal'])
    weight = (1 - smooth((original[:, 1] - 12) / 8)) * (1 - smooth((original[:, 0] - (dorsal[1, 0] - 4)) / 12))
    black = np.all(part['c'] == [43, 40, 34], axis=1)
    fixed = black.copy()
    fixed[np.unique(f[black[f].any(axis=1)])] = True
    weight[fixed] = 0
    active = np.flatnonzero(weight > 1e-6)
    bv = np.concatenate([bones['parts'][key]['v'] for key in ('upper', 'jaw')])
    bn = np.concatenate([bones['parts'][key]['n'] for key in ('upper', 'jaw')])
    tree = cKDTree(bv)
    for iteration in range(400):
        v += .35 * weight[:, None] * (adj @ v - v)
        if iteration % 4 == 3 or iteration == 399:
            distance, index = tree.query(v[active])
            normal = bn[index]
            signed = np.sum((v[active] - bv[index]) * normal, axis=1)
            v[active] += normal * np.where((distance < 3) & (signed < .70), .70 - signed, 0)[:, None]
    for _ in range(160):
        v += .25 * weight[:, None] * (adj @ v - v)

    def normals(points):
        fn = np.cross(points[f[:, 1]] - points[f[:, 0]], points[f[:, 2]] - points[f[:, 0]])
        nn = np.zeros_like(points)
        for j in range(3):
            np.add.at(nn, f[:, j], fn)
        nn /= np.maximum(np.linalg.norm(nn, axis=1)[:, None], 1e-12)
        if np.mean(np.sum(nn * part['n'], axis=1)) < 0:
            nn = -nn
        return nn

    distance = cKDTree(original[fixed]).query(original)[0]
    v += .65 * (weight * smooth(distance / 4))[:, None] * normals(v)
    part.update(v=v, n=normals(v))


def ear_field(sign, drop=0):
    """A closed thick flap. Only the upper stalk intersects the head.

    Below y=20 the inner surface must clear the head. A root is not simulated
    by a drawn dividing line, nor is the leaf blended into the occiput.
    """
    levels = np.array([-5, -2, 5, 15, 22, 28, 34], float)
    controls = [
        [-18, -18, -18, -17, -17, -16, -16],  # anterior/posterior centre
        [33, 33.5, 34, 34, 32, 26, 20],      # lateral centre
        [.10, 5.5, 9, 10, 9, 7, .10],       # half width in x
        [.10, 1.8, 2.8, 3, 4, 4.5, .10],    # half thickness in z
    ]
    fns = [PchipInterpolator(levels, values) for values in controls]

    def field(q):
        x, y, z = np.moveaxis(q, -1, 0)
        # Warp only the lower flap, keeping the complete root field invariant.
        # Changing PCHIP knots would also change derivatives above the knot.
        t = np.clip((15 - y) / 10, 0, 1)
        local_y = y - drop * t * t * (3 - 2 * t)
        yy = np.clip(local_y, levels[0], levels[-1])
        cx, cz, width, thickness = [fn(yy) for fn in fns]
        value = (np.sqrt(((x - cx) / width)**2 + ((sign * z - cz) / thickness)**2) - 1) * np.minimum(width, thickness)
        return np.maximum(value, np.maximum(levels[0] - local_y, local_y - levels[-1]))

    return field


def build_base(neck_field=None, bounds=None):
    resolved = head.resolve_profile(dict(schema_version=1, size_class='small', breed='maltipoo',
                                        display=dict(mode='normalized', scene_scale=1)))
    original = head.load_model(resolved)
    if head.sha(BONE_PATH) != BONE_SHA:
        raise ValueError('Pinned skeletal input changed')
    bones = pickle.loads(BONE_PATH.read_bytes())['maltipoo']
    meta = copy.deepcopy(original['metadata'])
    field, nose = head_fields(meta, neck_field)
    skin = mesh(field, bounds or [(-76, 28), (-30, 59), (-50.4, 50.4)])
    v = skin['v']
    variation = .9 * np.sin(v[:, 0] * .60 + v[:, 1] * .30) * np.sin(v[:, 2] * .65)
    skin['c'] += variation[:, None]
    black = (nose(v) < 1.1) & (v[:, 0] < meta['nose_center'][0] + meta['nose_size'] * .5)
    skin['c'][black] = [43, 40, 34]
    fair_face(skin, bones, meta)
    parts = {'head': skin, **{key: copy.deepcopy(part) for key, part in original['parts'].items() if key.startswith('eye_')}}
    return original, dict(parts=parts, metadata=meta, breed='maltipoo', variant='experimental-separated-ears')


def with_ears(base, variant='B'):
    if variant not in VARIANTS:
        raise ValueError('Unknown ear variant')
    model = copy.deepcopy(base)
    for key, sign in zip(EAR_KEYS, (-1, 1)):
        model['parts'][key] = mesh(ear_field(sign, VARIANTS[variant]),
                                  [(-33, 0), (-9, 36), (-40, -17) if sign < 0 else (17, 40)],
                                  step=.4, color=(226, 213, 190))
        model['parts'][key]['semantic'] = key
    model['variant'] = variant
    return model


def project(model, az, el, show_ears=True, semantic=False, uniform=False):
    parts = {}
    colors = {'head': [190, 194, 190], 'ear_left': [116, 160, 187], 'ear_right': [214, 153, 114]}
    for key, part in model['parts'].items():
        if not show_ears and key in EAR_KEYS:
            continue
        if (semantic or uniform) and not key.startswith('eye_'):
            color = np.tile(colors.get(key, [190, 194, 190]) if semantic else [220, 214, 201], (len(part['v']), 1))
            if not semantic:
                black = np.all(part['c'] == [43, 40, 34], axis=1)
                color[black] = [43, 40, 34]
            part = {**part, 'c': color}
        parts[key] = part
    return renderer.projected({'parts': parts}, az, el)


def board(rows, title):
    im = Image.new('RGB', (2000, 120 + len(rows) * 310), (248, 247, 242))
    renderer.label(im, 24, 12, title, 25, True)
    renderer.label(im, 24, 49, 'Actual 3D projection | authored geometry | structure study, not B2 or native64', 18)
    for row, (name, model, options) in enumerate(rows):
        renderer.label(im, 24, 90 + row * 310, name, 20, True)
        for col, (view, az, el) in enumerate(VIEWS):
            renderer.label(im, col * 400 + 26, 119 + row * 310, view, 17)
            q, c = project(model, az, el, **options)
            low, high = q[:, :, :2].min((0, 1)), q[:, :, :2].max((0, 1))
            scale = 3.1
            center = np.array([col * 400 + 200, row * 310 + 267]) - (low + high) / 2 * [scale, -scale]
            renderer.paint(im, q, c, center, scale)
    return im


def export(folder):
    folder = Path(folder).resolve()
    if folder.exists():
        raise ValueError('Output directory must be new; review evidence is never overwritten')
    folder.mkdir(parents=True)
    (folder / 'generator-snapshot.py').write_bytes(Path(__file__).read_bytes())
    original, base = build_base()
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=3) as pool:
        models = dict(zip(VARIANTS, pool.map(lambda key: with_ears(base, key), VARIANTS)))
    board([(key + ' / tip offset ' + str(VARIANTS[key]), model, {}) for key, model in models.items()],
          'Separated ear structure / A B C').save(folder / 'variants.png')
    board([('Old fused skin', original, {}), ('B / same material', models['B'], {'uniform': True}),
           ('B / part ownership', models['B'], {'semantic': True}), ('Head / ears hidden', models['B'], {'show_ears': False})],
          'Ear-root / free-edge / occiput verification').save(folder / 'structure.png')
    report = {}
    head_fn, _ = head_fields(base['metadata'])
    for key, model in models.items():
        arrays = {f'{part}_{channel}': values for part, data in model['parts'].items()
                  for channel, values in data.items() if isinstance(values, np.ndarray)}
        np.savez_compressed(folder / f'model-{key}.npz', **arrays)
        checks = {}
        for ear in EAR_KEYS:
            v = model['parts'][ear]['v']
            distance = head_fn(v)
            free = v[:, 1] < 20
            contact = distance < 0
            checks[ear] = dict(free_edge_min_implicit_residual=float(distance[free].min()),
                               attachment_vertex_count=int(contact.sum()),
                               attachment_lowest_y=float(v[contact, 1].min()) if contact.any() else None)
        report[key] = checks
    head.write_json(folder / 'geometry-checks.json', report)
    inputs = [Path(__file__), ROOT / 'tools/dog_engine/head.py', ROOT / 'tools/dog_engine/renderer.py',
              ROOT / 'tools/dog_engine/raster.py', ROOT / 'tools/dog_engine/runtime-inputs.json',
              ROOT / 'tools/head_engine/catalog.json', BONE_PATH,
              ROOT / 'outputs/skull-based-heads-v2/geometry.pkl',
              ROOT / 'outputs/skull-based-heads-v2/review-status.json',
              ROOT / 'tools/dog_engine/requirements.txt', folder / 'generator-snapshot.py']
    import os
    manifest = dict(artifacts={p.name: head.sha(p) for p in sorted(folder.glob('*.png'))},
                    inputs={os.path.relpath(p, folder).replace('\\', '/'): head.sha(p) for p in inputs},
                    status='EXPERIMENTAL_NOT_REVIEWED', variants=VARIANTS,
                    limitations=['No photo-derived bone measurements', 'Not B2 artwork or native64',
                                 'Rebuilt tissue seed with anterior fairing; not identical to prior skin topology',
                                 'Maltipoo hanging-ear study only; catalog defaults unchanged'])
    for p in sorted(folder.glob('model-*.npz')):
        manifest['inputs'][p.name] = head.sha(p)
    manifest['inputs']['geometry-checks.json'] = head.sha(folder / 'geometry-checks.json')
    head.write_json(folder / 'review-inputs.json', manifest)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(export(args.output), indent=2))


if __name__ == '__main__':
    main()
