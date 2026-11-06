"""Independent non-mutating render and geometry checks for the saved candidate."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('candidate', HERE/'preview.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def main():
    heads, evidence = m.build()
    rigs, profiles = m.model.load('B.json')['breeds'], m.model.load('profiles.json')
    baseline = np.load(m.SOURCE/'heads-B-round-eyes.npz')
    results = {}
    for breed in m.model.BREEDS:
        rig = rigs[breed]
        profile = m.profile_for(rig, profiles[breed],breed)
        base = m.model.head_features(rig, breed, profile)
        neutral_exact = all(np.array_equal(heads[breed]['neutral'][i][j],
                            baseline[f'{breed}_{kind}_{i}'])
                            for i in range(3) for j,kind in enumerate(('surface','material')))
        mesh0, d0 = m.mouth(base, rig, profile, 0)
        fixed_vertices = np.all(mesh0[0][0]==base[0][0],axis=-1)
        fixed_faces = fixed_vertices[:-1,:-1]&fixed_vertices[1:,:-1]&fixed_vertices[:-1,1:]&fixed_vertices[1:,1:]
        changed_fixed_faces = int(np.count_nonzero(np.any(mesh0[0][1]!=base[0][1],axis=-1)&fixed_faces))
        checks = []
        for nominal in (4,6,8):
            angle = nominal*profile['mouth_style'][1]
            mesh,d = m.mouth(base, rig, profile, angle)
            restored = m.rotate_jaw(d['lower_posed'], d['pivot'],
                                   np.full(len(d['lower_posed']), -np.deg2rad(angle)))
            hinge = m.rotate_jaw(d['hinge_axis'][None], d['pivot'], np.array([np.deg2rad(angle)]))
            picks = np.linspace(0,d['lower_rest'].reshape(-1,3).shape[0]-1,45).astype(int)
            a,b = d['lower_rest'].reshape(-1,3)[picks],d['lower_posed'].reshape(-1,3)[picks]
            distance_error = np.abs(np.linalg.norm(a[:,None]-a[None,:],axis=2)-
                                    np.linalg.norm(b[:,None]-b[None,:],axis=2)).max()
            checks.append(dict(angle=angle,rest_exact=np.array_equal(d0['lower_rest'],d['lower_rest']),
                inverse_error=float(np.abs(restored-d['lower_rest']).max()),
                pair_distance_error=float(distance_error),hinge_error=float(np.abs(hinge[0]-d['hinge_axis']).max()),
                upper_exact=all(np.array_equal(mesh0[0][j],mesh[0][j]) for j in (0,1)),
                ears_exact=all(np.array_equal(mesh[-2+i][j],base[1+i][j]) for i in (0,1) for j in (0,1))))
        tongue_checks = []
        for name,nominal in [('tongue',6),('lick',4)]:
            angle = nominal*profile['mouth_style'][1]
            mesh,d = m.mouth(base,rig,profile,angle)
            (surface,color),info = m.tongue(d,profiles[breed]['half_width'],name=='lick')
            pts = surface[:61].reshape(-1,3)
            floor = np.interp(pts[:,0],d['floor'][:,0],d['floor'][:,1])
            ceiling = np.interp(pts[:,0],d['xs'],d['roof_y'])
            root_expected = m.floor_at(d,(d['front']+d['back'])/2)
            tongue_checks.append(dict(state=name,floor_clearance=float((pts[:,1]-floor).min()),
                roof_clearance=float((ceiling-pts[:,1]).min()),root_error=float(np.linalg.norm(root_expected-info['root'])),
                contact_error=None if info['contact'] is None else float(np.linalg.norm(np.array(info['tip'])-info['contact'])),
                lip_support_error=float(np.linalg.norm(surface[60,32]-info['lip_floor_contact'])),
                outside_max_thickness=float(np.linalg.norm(surface[60:,0]-surface[60:,32],axis=1).max()),
                recorded_outside_thickness=info['outside_max_thickness'],
                finite=bool(np.isfinite(surface).all()),seam_error=float(np.abs(surface[:,0]-surface[:,-1]).max())))
        results[breed] = dict(neutral_exact=neutral_exact,unchanged_geometry_material_changes=changed_fixed_faces,jaw=checks,tongue=tongue_checks)

    captured = {}
    original_save = Image.Image.save
    def capture(image, fp, *args, **kwargs):
        stream = io.BytesIO()
        original_save(image,stream,format='PNG')
        captured[Path(fp).name] = stream.getvalue()
    with patch.object(Image.Image,'save',capture), patch.object(Path,'write_text',lambda *args,**kwargs:0), patch.object(m,'build',lambda:(heads,evidence)):
        m.main()
    results['renders'] = {name:dict(byte_identical=data==(HERE/name).read_bytes(),
                         sha256=hashlib.sha256(data).hexdigest()) for name,data in captured.items()}
    recipe=json.loads((HERE/'recipe.json').read_text(encoding='utf-8'))
    results['recipe_inputs_exact']=all(hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==digest
                                        for name,digest in recipe['input_sha256'].items())
    results['recipe_images_exact']=all(hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest
                                        for name,digest in recipe['image_sha256'].items())
    results['source_sha256']=hashlib.sha256((HERE/'preview.py').read_bytes()).hexdigest()
    (HERE/'review-checks.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(results,ensure_ascii=False))


if __name__=='__main__':
    main()
