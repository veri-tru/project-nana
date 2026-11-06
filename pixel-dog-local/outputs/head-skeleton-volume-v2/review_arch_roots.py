"""Independent local 3D attachment test; base intentionally excludes arches."""
import hashlib,importlib.util,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('arch_root_review',HERE/'build.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
source=hashlib.sha256((HERE/'build.py').read_bytes()).hexdigest();profiles=json.loads((HERE/'profiles.json').read_text('utf-8'));result={}
for b,p in profiles.items():
    ff,a=m.fields(p)
    if 'base' in ff:base=ff['base']
    else:
        free=dict(zip(ff['upper'].__code__.co_freevars,[c.cell_contents for c in ff['upper'].__closure__]));recess=free['recess']
        def base(q):return np.maximum(m.smoothmin(ff['cranial'](q),ff['rostrum'](q),1.0),-recess(q))
    rec={}
    for side,path in zip(['R','L'],a['arch_paths']):
        root=np.array(path[0]);axes=[np.linspace(root[i]-4,root[i]+4,41) for i in range(3)];q=np.stack(np.meshgrid(*axes,indexing='ij'),axis=-1);af=ff['arches'](q);bf=base(q);both=(af<-.1)&(bf<-.1)
        rec[side]=dict(root=root.tolist(),base_at_root=float(base(root[None])[0]),overlap_samples_both_lt_minus01=int(both.sum()),sample_spacing=.2,overlap_volume_estimate=float(both.sum()*.2**3),overlap_bbox=[q[both].min(0).tolist(),q[both].max(0).tolist()] if both.any() else None,min_base_in_arch=float(bf[af<-.1].min()))
    result[b]=rec
report=dict(source_sha256=source,source_unchanged=source==hashlib.sha256((HERE/'build.py').read_bytes()).hexdigest(),field_only=True,breeds=result)
(HERE/'review-arch-root-overlap.json').write_text(json.dumps(report,indent=2)+'\n','utf-8');print(json.dumps(report,indent=2))
