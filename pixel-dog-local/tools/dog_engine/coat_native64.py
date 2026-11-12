"""Explicit semantic raster of registered coat geometry at the native 64px grid.

Neutral diagnostic palette, not the rejected P1/P2/P3 nor approved B2 artwork.
All views and length variants use the same source-derived camera plan.
"""
import numpy as np
from PIL import Image
from scipy import ndimage

from . import raster

CAMERAS = {'front': (0, 0), 'three_quarter': (48, 7), 'side': (90, 0),
           'back': (180, 0), 'top': (90, 90)}
PART_IDS = {'head': 32, 'ear_left': 64, 'ear_right': 96,
            'eye_-1': 160, 'eye_1': 192}
NOSE_ID = 128
PALETTE = ((45, 49, 52), (100, 105, 109), (166, 171, 174), (225, 228, 230))
CHEST_ISLAND_MAX_FRACTION = .10
TONE_POLICY = 'Merge enclosed small chest light/shadow islands into their sole surrounding middle tone; model y<-25 or posterior upper thorax x>20,y<-10; max 10% of visible region; preserve boundary-connected bands.'


def chest_region(plan, depth, semantic):
    """Recover model-space y at raster sample centres, including occlusion.

    Below the protected throat band, plus the posterior upper thorax: x>20
    stays behind the anterior throat, y<-10 is the source thorax upper extent.
    These authored bounds apply to this registered template, not all breeds.
    Screen positions and absolute pixel counts do not define the region.
    """
    mask = np.isfinite(depth)
    rows, cols = np.nonzero(mask)
    view = rotation(plan['camera'])
    x = (cols + .5 - plan['center'][0]) / plan['scale']
    y = (plan['center'][1] - rows - .5) / plan['scale']
    model_y = x*view[1, 0] + y*view[1, 1] + depth[mask]*view[1, 2]
    model_x = x*view[0, 0] + y*view[0, 1] + depth[mask]*view[0, 2]
    region = np.zeros(mask.shape, dtype=bool)
    eligible = (model_y < -25) | ((model_x > 20) & (model_y < -10))
    region[mask] = eligible & (semantic[mask] == PART_IDS['head'])
    return region


def chest_tones(shades, region):
    """Cel-tone treatment, not a correction of geometry or lighting normals.

    An island must be entirely enclosed by the middle tone inside the chest.
    Tone regions touching the silhouette, throat boundary or another material
    remain intact, regardless of their size. Limits scale with projected area.
    """
    result = shades.copy()
    limit = CHEST_ISLAND_MAX_FRACTION * np.count_nonzero(region)
    # Evaluate both extremes against the original map; never cascade edits.
    for tone in (1, 3):
        labels, _ = ndimage.label(region & (shades == tone), np.ones((3, 3)))
        for label, bounds in enumerate(ndimage.find_objects(labels), start=1):
            if bounds is None:
                continue
            if any(s.start == 0 or s.stop == labels.shape[i] for i, s in enumerate(bounds)):
                continue
            box = tuple(slice(max(0, s.start-1), min(labels.shape[i], s.stop+1))
                        for i, s in enumerate(bounds))
            island = labels[box] == label
            if np.count_nonzero(island) > limit:
                continue
            border = ndimage.binary_dilation(island, structure=np.ones((3, 3))) & ~island
            if not border.any() or not np.all(region[box][border]):
                continue
            surrounding = np.unique(shades[box][border])
            if len(surrounding) == 1 and surrounding[0] == 2:
                result[box][island] = 2
    return result


def rotation(camera):
    az, el = np.radians(camera)
    right = np.array([np.sin(az), 0, np.cos(az)])
    front = np.array([-np.cos(az)*np.cos(el), np.sin(el), np.sin(az)*np.cos(el)])
    return np.column_stack([right, np.cross(front, right), front])


def source_semantics(model):
    if set(model['parts']) != set(PART_IDS):
        raise ValueError('Explicit head/eyes/ears semantic parts required')
    result = {}
    for name, part in model['parts'].items():
        faces = part['f']
        ids = np.full(len(faces), PART_IDS[name], dtype=np.uint8)
        if name == 'head':
            nose_vertices = np.all(part['c'] == [43, 40, 34], axis=1)
            # Freeze face labels from pinned source; no interpolated category IDs.
            ids[nose_vertices[faces].sum(axis=1) >= 2] = NOSE_ID
        result[name] = ids
    return result


def camera_plan(source, size=64):
    if type(size) is not int or size not in (64, 480):
        raise ValueError('Supported diagnostic sizes: 64 or 480')
    bounds = {}
    for name, camera in CAMERAS.items():
        points = np.concatenate([part['v'] @ rotation(camera) for part in source['parts'].values()])
        bounds[name] = (points[:, :2].min(0), points[:, :2].max(0))
    # Reserve 8 authored units on each side for the bounded coat envelope.
    extent = max(float((hi-lo).max()) for lo, hi in bounds.values()) + 16
    scale = (size-12*size/64) / extent
    return {name: dict(camera=list(CAMERAS[name]), scale=scale,
                       center=(np.array([size/2, size/2]) - (lo+hi)/2*[scale, -scale]).tolist(),
                       canvas=[size, size]) for name, (lo, hi) in bounds.items()}


def render(model, semantics, plan, *, hide_ears=False, chest_tone_cleanup=True):
    if set(model['parts']) != set(PART_IDS) or set(semantics) != set(PART_IDS):
        raise ValueError('Missing semantic part mapping')
    size = plan['canvas']
    if size not in ([64, 64], [480, 480]):
        raise ValueError('Invalid diagnostic canvas')
    view = rotation(plan['camera'])
    triangles, colors = [], []
    for name, part in model['parts'].items():
        if hide_ears and name.startswith('ear_'):
            continue
        faces = part['f']
        ids = np.asarray(semantics[name])
        allowed = {PART_IDS[name], NOSE_ID} if name == 'head' else {PART_IDS[name]}
        if ids.shape != (len(faces),) or not set(np.unique(ids)) <= allowed:
            raise ValueError('Invalid semantic face labels for ' + name)
        points = part['v'] @ view
        normals = part['n'] @ view
        light = np.array([-.32, .72, .61])
        shade = np.clip(.58 + .40*np.maximum(0, normals @ light), 0, 1)*255
        ix = faces[:, [0, 1, 2, 2]]
        q = points[ix].copy()
        q[:, :, 0] = q[:, :, 0]*plan['scale'] + plan['center'][0]
        q[:, :, 1] = plan['center'][1] - q[:, :, 1]*plan['scale']
        if (q[:, :, :2] < 1).any() or (q[:, :, :2] > size[0]-2).any():
            raise ValueError('Coat exceeds fixed diagnostic frame; no automatic rescale')
        signals = np.zeros((*ix.shape, 3))
        signals[:, :, 0] = shade[ix]
        signals[:, :, 1] = ids[:, None]
        triangles.append(q)
        colors.append(signals)
    rgb = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    depth = np.full((size[1], size[0]), -np.inf)
    # Category planes are constant per triangle. Float arithmetic can round an
    # integer down by one; decode only the discrete known IDs afterward.
    raster.raster(np.ascontiguousarray(np.concatenate(triangles)),
                  np.ascontiguousarray(np.concatenate(colors), dtype=np.uint8), depth, rgb)
    mask = np.isfinite(depth)
    valid_ids = np.array([0, *PART_IDS.values(), NOSE_ID], dtype=np.uint8)
    distances = abs(rgb[:, :, 1, None].astype(int) - valid_ids.astype(int))
    semantic = valid_ids[np.argmin(distances, axis=2)]
    semantic[~mask] = 0
    if (np.min(distances, axis=2)[mask] > 1).any():
        raise ValueError('Interpolated or unrecognized semantic value')
    rgba = np.zeros((*mask.shape, 4), dtype=np.uint8)
    shades = np.digitize(rgb[:, :, 0], [175, 215]) + 1
    if chest_tone_cleanup:
        shades = chest_tones(shades, chest_region(plan, depth, semantic))
    rgba[mask, :3] = np.asarray(PALETTE, dtype=np.uint8)[shades[mask]]
    features = mask & np.isin(semantic, [NOSE_ID, PART_IDS['eye_-1'], PART_IDS['eye_1']])
    rgba[features, :3] = PALETTE[0]
    if size == [64, 64]:
        # Keep projected ear ownership visible where pale head/ear light bands
        # otherwise merge at native resolution. Never grow geometry or features.
        ears = np.isin(semantic, [PART_IDS['ear_left'], PART_IDS['ear_right']]) & mask
        rgba[ears, :3] = np.asarray(PALETTE, dtype=np.uint8)[np.maximum(1, shades[ears]-1)]
        padded = np.pad(semantic, 1)
        adjacent_head = ((padded[:-2,1:-1] == PART_IDS['head'])
                         | (padded[2:,1:-1] == PART_IDS['head'])
                         | (padded[1:-1,:-2] == PART_IDS['head'])
                         | (padded[1:-1,2:] == PART_IDS['head']))
        rgba[ears & adjacent_head, :3] = PALETTE[0]
    rgba[mask, 3] = 255
    return Image.fromarray(rgba), semantic, depth
