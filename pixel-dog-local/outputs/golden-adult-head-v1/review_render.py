"""Re-render in memory and compare saved pixels; write audit JSON only."""
from pathlib import Path
import importlib.util,hashlib,json,io
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('golden_render_review',HERE/'build.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
rows=m.load_models();out={'artifacts':{},'cells':{'exterior':20,'skeleton':20,'jaw':12},'projection_scales':{'exterior':3.65,'skeleton':3.65,'jaw':4.0},'same_model_per_row':True}
for name,im in m.boards(rows).items():
 saved=Image.open(HERE/name);buf=io.BytesIO();im.save(buf,format='PNG');data=buf.getvalue()
 out['artifacts'][name]={'size':list(saved.size),'mode':saved.mode,'pixels_exact':np.array_equal(np.asarray(saved),np.asarray(im)),'bytes_exact':data==(HERE/name).read_bytes(),'sha256':hashlib.sha256((HERE/name).read_bytes()).hexdigest()}
 print(name,out['artifacts'][name],flush=True)
(HERE/'technical-render-check.json').write_text(json.dumps(out,indent=2),'utf-8')
