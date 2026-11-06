"""Pinned development field/warp audit; no candidate extraction or full rebuild."""
from pathlib import Path
import importlib.util,hashlib,json,pickle,numpy as np
HERE=Path(__file__).resolve().parent
source=HERE/'build.py';digest=hashlib.sha256(source.read_bytes()).hexdigest();spec=importlib.util.spec_from_file_location('review_v2_dev04',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
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
for b in m.BREEDS:
 ff,meta=m.make_fields(skels[b],b,'B');old,oldmeta=m.base.make_fields(skels[b],b,'B');row={'bones':{},'metadata':{'patch':{k:v for k,v in meta['front_patch'].items() if k not in ['old_front','new_front','grid_y','grid_z']},'base_face_variant':meta['base_face_variant'],'unchanged_baseline_sections':meta['sections']==oldmeta['sections'],'unchanged_baseline_muzzle_support':meta['muzzle_support']==oldmeta['muzzle_support']}}
 for k in ['upper','jaw']:
  p=skels[b]['parts'][k];q=np.concatenate([p['v'],p['v'][p['f']].mean(1)]);val=ff['exterior'](q);i=int(val.argmax());row['bones'][k]={'samples':len(q),'outside':int((val>0).sum()),'max_field':float(val[i]),'worst_point':q[i].tolist()}
 warp,cc=warp_function(ff['core']);d=np.array(skels[b]['profile']['dorsal']);axes=[np.arange(d[5,0]-15,22,.5),np.arange(-13.75,16,.75),np.arange(-39.75,40,.75)];q=np.stack(np.meshgrid(*axes,indexing='ij'),axis=-1);wx=warp(q)[...,0];der=np.diff(wx,axis=0)/.5;i=np.unravel_index(int(der.argmin()),der.shape);point=(q[i]+q[(i[0]+1,i[1],i[2])])/2;delta=np.array([.001,0,0]);precise=(warp((point+delta)[None])[0,0]-warp((point-delta)[None])[0,0])/.002;negative=der<=0
 row['warp']={'tested_x_intervals':int(der.size),'nonpositive_intervals':int(negative.sum()),'minimum_finite_slope':float(der.min()),'worst_midpoint':point.tolist(),'local_derivative_h001':float(precise),'worst_old_core':float(old['core'](point[None])[0]),'worst_new_core':float(ff['core'](point[None])[0]),'reconstructed_warp_matches_core':float(np.max(np.abs(ff['core'](q[::10,::4,::4])-cc['old_core'](warp(q[::10,::4,::4])))))}
 skin=baseline[b]['parts']['skin'];v=skin['v'];nosemask=np.all(skin['c']==[43,40,34],axis=1);protected=old['nose'](v)<1.8;row['nose']={'template_field_max_delta':float(np.max(np.abs(ff['nose'](v)-old['nose'](v)))),'baseline_nasal_material_vertices':int(nosemask.sum()),'max_core_delta_at_nasal_material':float(np.max(np.abs(ff['core'](v[nosemask])-old['core'](v[nosemask])))),'max_exterior_delta_at_nasal_material':float(np.max(np.abs(ff['exterior'](v[nosemask])-old['exterior'](v[nosemask])))),'max_core_delta_in_preserve_band':float(np.max(np.abs(ff['core'](v[protected])-old['core'](v[protected]))))}
 eyes=[]
 for sign,expected in zip([-1,1],baseline[b]['metadata']['eyes']):
  W=skels[b]['profile']['widths'][0];origin=np.array([d[1,0]+2,20.5 if b=='maltipoo' else 19.,sign*W*.60]);normal=np.array([-.88,.02,sign*.47]);normal/=np.linalg.norm(normal);lo=0.;hi=W*2
  for _ in range(28):
   mid=(lo+hi)/2
   if ff['core']((origin+normal*mid)[None])[0]<0:lo=mid
   else:hi=mid
  surface=origin+normal*lo;gradient=np.array([(ff['core']((surface+np.eye(3)[k]*.05)[None])[0]-ff['core']((surface-np.eye(3)[k]*.05)[None])[0])/.1 for k in range(3)]);normal=gradient/np.linalg.norm(gradient);center=surface-normal*m.EYE_SIZE[b]*.2;eyes.append({'center_max_delta':float(np.max(np.abs(center-np.array(expected['center'])))),'normal_max_delta':float(np.max(np.abs(normal-np.array(expected['normal'])))),'radius_same':m.EYE_SIZE[b]==expected['radius']})
 row['eyes']=eyes
 # Actual warp continuity at the hard upper-orbit support boundary.
 ys=np.array([16-.001,16,16+.001]);xs=np.arange(d[5,0],d[1,0]+8,1.);zs=np.arange(-25,26,1.);qq=np.stack(np.meshgrid(xs,ys,zs,indexing='ij'),axis=-1);xx=warp(qq)[...,0];left=(xx[:,1]-xx[:,0])/.001;right=(xx[:,2]-xx[:,1])/.001;gap=np.abs(left-right);ii=np.unravel_index(int(gap.argmax()),gap.shape);row['upper_boundary']={'max_dwarp_dy_jump_estimate':float(gap.max()),'x_z':[float(xs[ii[0]]),float(zs[ii[1]])],'finite_value_jump_below':float(np.max(np.abs(xx[:,0]-xx[:,1])))}
 report['breeds'][b]=row;print(b,'outside',sum(v['outside'] for v in row['bones'].values()),'warp nonpositive',row['warp']['nonpositive_intervals'],'min slope',row['warp']['minimum_finite_slope'],flush=True)
 (HERE/'review-dev04-progress.json').write_text(json.dumps(report,indent=2),'utf-8')
report['source_stable']=digest==hashlib.sha256(source.read_bytes()).hexdigest();(HERE/'review-dev04-field-warp.json').write_text(json.dumps(report,indent=2),'utf-8');print('DONE source stable',report['source_stable'],flush=True)
