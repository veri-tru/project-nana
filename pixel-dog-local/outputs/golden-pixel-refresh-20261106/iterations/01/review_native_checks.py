"""Independent bounded review of the saved layered-engine/native-pixel deliverable."""
import copy
import io
import json
import sys
from pathlib import Path
from unittest.mock import patch
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools/head_engine'))
import engine
import pixel

evidence = engine.read_json(HERE / 'evidence.json')
for group in ('artifacts', 'inputs'):
    for path, digest in evidence[group].items():
        assert engine.sha(HERE / path) == digest, path
resolved = engine.read_json(HERE / 'resolved-profile.json')
engine.validate_resolved(resolved)
model = engine.load_model(resolved)
original = {name: {k: np.asarray(v).copy() for k,v in part.items()}
            for name, part in model['parts'].items()}
renderer = engine.module(ROOT / 'outputs/skull-based-heads-v2/build.py', 'independent_native_renderer')
for _, az, el in engine.VIEWS:
    native, _ = pixel.project(model, az, el)
    smooth, _ = renderer.projected(model, az, el)
    np.testing.assert_array_equal(native, smooth)

raw, plan = pixel.render_signals(model)
frames = {key: [pixel.style_frame(r, style) for r in raw] for key, style in pixel.STYLES.items()}
reproduced = {'pixel-comparison.png': pixel.comparison(frames)}
reproduced.update({key+'-atlas.png':pixel.make_atlas(f) for key,f in frames.items()})
reference, _ = engine.render_resolved(resolved)
reproduced['engine-reference.png'] = reference
for name, image in reproduced.items():
    blob = io.BytesIO(); image.save(blob, format='PNG')
    assert blob.getvalue() == (HERE / name).read_bytes(), name

board = np.array(Image.open(HERE/'pixel-comparison.png'))
details = {}
for row, key in enumerate(pixel.STYLES):
    atlas = np.array(Image.open(HERE/(key+'-atlas.png')))
    assert atlas.shape == (64,320,4)
    details[key] = []
    for col in range(5):
        a = atlas[:,64*col:64*(col+1)]
        assert set(np.unique(a[:,:,3])) == {0,255}
        mask = a[:,:,3] == 255
        colors = np.unique(a[mask,:3], axis=0)
        assert len(colors) <= 5
        assert not (mask[0].any() or mask[-1].any() or mask[:,0].any() or mask[:,-1].any())
        bg = np.full((64,64,3),(248,247,242),dtype=np.uint8)
        bg[mask] = a[mask,:3]
        y = 165 + row*520
        np.testing.assert_array_equal(board[y+38:y+422,col*480+48:col*480+432], np.repeat(np.repeat(bg,6,0),6,1))
        np.testing.assert_array_equal(board[y+425:y+489,col*480+208:col*480+272], bg)
        rawmask = raw[col][1]
        assert np.all(mask[rawmask])
        outline = np.logical_or.reduce(pixel.neighbors(rawmask)) & ~rawmask
        np.testing.assert_array_equal(mask, rawmask | outline)
        details[key].append({'opaque_pixels':int(mask.sum()),'opaque_colors':len(colors)})
a = np.array(Image.open(HERE/'P2-depth-atlas.png'))
b = np.array(Image.open(HERE/'P3-contrast-atlas.png'))
changed = np.any(a != b,axis=2)
assert (a[changed,:3] == pixel.OUTLINE_SOFT).all()
assert (b[changed,:3] == pixel.OUTLINE_DARK).all()
for key,part in model['parts'].items():
    for field, values in part.items():np.testing.assert_array_equal(values, original[key][field])

request = resolved['request']
for breed in engine.catalog()['breeds']:
    choices = [engine.resolve_profile({**request,'breed':breed,'size_class':size}) for size in ('small','medium','large')]
    assert all(c['source'] == choices[0]['source'] for c in choices)
for value in (float('nan'),float('inf'),-float('inf'),True,0,3.01):
    req = copy.deepcopy(request)
    req['individual']['overrides'] = {'relative_scale':value}
    req['individual']['evidence'] = {'relative_scale':{'kind':'authored_default','source':'review','note':'invalid value test'}}
    try:engine.resolve_profile(req)
    except ValueError:pass
    else:raise AssertionError('Invalid relative scale accepted')
actual_sha = engine.sha
selected_path = (ROOT / resolved['source']['path']).resolve()
with patch.object(engine,'sha',side_effect=lambda p:'0'*64 if Path(p).resolve()==selected_path else actual_sha(p)):
    try:engine.load_model(resolved)
    except ValueError as exc:assert 'Reviewed source changed' in str(exc)
    else:raise AssertionError('Changed model hash accepted')
for target in (ROOT/'outputs/golden-adult-head-v1', ROOT/'outputs/golden-adult-head-v1/nested',ROOT/'tools/head_engine'):
    try:pixel.export(HERE/'resolved-profile.json', target)
    except ValueError:pass
    else:raise AssertionError('Protected target accepted')
result = {'status':'PASS','reviewer':'/root/layered_native_technical',
          'artifact_hashes_verified':len(evidence['artifacts']),'input_hashes_verified':len(evidence['inputs']),
          'all_five_pngs_byte_identical_on_reproduction':True,
          'native_projection_equals_reviewed_renderer_all_views':True,
          'source_arrays_unchanged':True,'saved_board_nearest_6x_and_native_1x_all_15_cells':True,
          'p3_only_outline_recolor_pixels':int(changed.sum()),'frames':details}
engine.write_json(HERE/'technical-checks.json', result)
print(json.dumps(result,ensure_ascii=False))
