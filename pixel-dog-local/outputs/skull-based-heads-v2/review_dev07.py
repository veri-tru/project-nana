"""Pinned development field/warp audit; no candidate extraction or full rebuild."""
from pathlib import Path
import importlib.util,hashlib,json,pickle,numpy as np
HERE=Path(__file__).resolve().parent
source=HERE/'build.py';digest=hashlib.sha256(source.read_bytes()).hexdigest();spec=importlib.util.spec_from_file_location('review_v2_dev07',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
skels=m.load_inputs();baseline=pickle.loads((HERE.parent/'skull-based-heads-v1/geometry.pkl').read_bytes())['B'];report={'development_field_only':True,'source_sha256':digest,'baseline_source_sha256':hashlib.sha256((HERE.parent/'skull-based-heads-v1/build.py').read_bytes()).hexdigest(),'variant':'B','breeds':{}}
def closure(f):return dict(zip(f.__code__.co_freevars,[c.cell_contents for c in f.__closure__]))
def warp_function(core):
 cc=closure(core);sample,coeff,ys=cc['sample'],cc['coeff'],cc['ys'];old_nose=cc['old_nose']
 def warp(q):
  x,y,z=np.moveaxis(q,-1,0);change=sample(coeff[0],y,z);change=np.where((y>ys[0]+2)&(y<16)&(np.abs(z)<40),change,0.);nd=old_nose(q);keep=np.clip((nd-1.8)/1.5,0,1);keep=keep*keep*(3-2*keep);change*=keep;active=np.abs(change)>1e-7;wq=np.array(q,copy=True)
  if active.any():
   front=sample(coeff[1],y[active],z[active]);back=sample(coeff[2],y[active],z[active]);nf=front+change[active];t=np.clip((back-x[active])/np.maximum(back-nf,1.),0,1);weight=t*t*(3-2*t);wq[...,0][active]=x[active]-change[active]*weight
  return wq
 return warp,cc
reference_nose=None
for b in m.BREEDS:
 ff,meta=m.make_fields(skels[b],b,'B');old,oldmeta=m.base.make_fields(skels[b],b,'B');row={'bones':{},'metadata':{'patch':{k:v for k,v in meta['front_patch'].items() if k not in ['old_front','new_front','grid_y','grid_z']},'base_face_variant':meta['base_face_variant'],'unchanged_baseline_sections':meta['sections']==oldmeta['sections'],'unchanged_baseline_muzzle_support':meta['muzzle_support']==oldmeta['muzzle_support']}}
 for k in ['upper','jaw']:
  p=skels[b]['parts'][k];q=np.concatenate([p['v'],p['v'][p['f']].mean(1)]);val=ff['exterior'](q);i=int(val.argmax());row['bones'][k]={'samples':len(q),'outside':int((val>0).sum()),'max_field':float(val[i]),'worst_point':q[i].tolist()}
 d=np.array(skels[b]['profile']['dorsal'])
 ax=np.linspace(-1.6,1.6,21);unit=np.stack(np.meshgrid(ax,ax,ax,indexing='ij'),axis=-1);size=meta['nose_size'];q=unit*size+np.array(meta['nose_center']);vals=ff['nose'](q)/size;oldvals=old['nose'](q)/size
 if reference_nose is None:reference_nose=vals
 row['nose']={'normalized_samples':int(vals.size),'normalized_old_template_max_delta':float(np.max(np.abs(vals-oldvals))),'normalized_cross_breed_template_max_delta':float(np.max(np.abs(vals-reference_nose))),'size_unchanged':size==oldmeta['nose_size'],'center_unchanged':meta['nose_center']==oldmeta['nose_center']}
 eyes=[]
 for sign,expected in zip([-1,1],baseline[b]['metadata']['eyes']):
  W=skels[b]['profile']['widths'][0];origin=np.array([d[1,0]+2,20.5 if b=='maltipoo' else 19.,sign*W*.60]);normal=np.array([-.88,.02,sign*.47]);normal/=np.linalg.norm(normal);lo=0.;hi=W*2
  for _ in range(28):
   mid=(lo+hi)/2
   if ff['core']((origin+normal*mid)[None])[0]<0:lo=mid
   else:hi=mid
  surface=origin+normal*lo;gradient=np.array([(ff['core']((surface+np.eye(3)[k]*.05)[None])[0]-ff['core']((surface-np.eye(3)[k]*.05)[None])[0])/.1 for k in range(3)]);normal=gradient/np.linalg.norm(gradient);center=surface-normal*m.EYE_SIZE[b]*.2;eyes.append({'center_max_delta':float(np.max(np.abs(center-np.array(expected['center'])))),'normal_max_delta':float(np.max(np.abs(normal-np.array(expected['normal'])))),'radius_same':m.EYE_SIZE[b]==expected['radius']})
 row['eyes']=eyes
 report['breeds'][b]=row;print(b,'outside',sum(v['outside'] for v in row['bones'].values()),'nasal preservation',row['nose']['normalized_old_template_max_delta'],flush=True)
 (HERE/'review-dev07-progress.json').write_text(json.dumps(report,indent=2),'utf-8')
report['source_stable']=digest==hashlib.sha256(source.read_bytes()).hexdigest();(HERE/'review-dev07-field-template.json').write_text(json.dumps(report,indent=2),'utf-8');print('DONE source stable',report['source_stable'],flush=True)
