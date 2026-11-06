"""Join independently measured final evidence and write the reviewer verdict."""
from pathlib import Path
import hashlib,json,pickle
import numpy as np
HERE=Path(__file__).resolve().parent
def read(name):return json.loads((HERE/name).read_text('utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def eq(a,b):
 if isinstance(a,np.ndarray):return isinstance(b,np.ndarray) and a.dtype==b.dtype and np.array_equal(a,b)
 if isinstance(a,dict):return a.keys()==b.keys() and all(eq(a[k],b[k]) for k in a)
 if isinstance(a,(list,tuple)):return len(a)==len(b) and all(eq(x,y) for x,y in zip(a,b))
 return a==b
evidence=read('evidence.json');ac=read('technical-measurements-ac-final.json');bm=read('technical-measurements.json');renders=read('technical-final-isolation-render.json')
rows={**ac['variants'],'B':bm['variants']['B']}
assert set(rows)==set('ABC')
for name,h in {**evidence['inputs'],**evidence['artifacts']}.items():assert sha(HERE/name)==h,name
source_guard={p:sha(HERE/p)==h for p,h in read('source-guards.json').items()};assert all(source_guard.values())
rootb=pickle.loads((HERE/'model-B.pkl').read_bytes());devb=pickle.loads((HERE/'development/model-B-r3.pkl').read_bytes());assert eq(rootb,devb)
assert bm['variants']['B']['model_sha256']==sha(HERE/'development/model-B-r3.pkl')
assert all(rows['B']['reproduction'].values())
for v,row in rows.items():
 if v!='B':assert row['model_sha256']==sha(HERE/f'model-{v}.pkl')
 assert all(row['finite'].values())
 for layer in row['topology'].values():
  for p in layer.values():assert p['components']==1 and all(p[k]==0 for k in ['boundary_edges','nonmanifold_edges','zero_area_faces'])
 assert row['topology']['exterior']['skin']['euler']==2
 for p in row['containment'].values():assert p['outside']==0 and p['crossings']['intersecting_pairs']==0 and p['all_sampled_minimum_certified']
 for p in row['self_crossings'].values():assert p['intersecting_pairs']==0
 for p in row['jaw_motion'].values():assert p['inside_upper']==0 and p['crossings']['intersecting_pairs']==0
 for p in row['eyes'].values():assert p['inside_samples']>0 and p['outside_samples']>0 and p['surface_crossing_faces']>0
 for p in row['ears']:assert p['actual_shared_mesh_edges_near_root']>0 and p['initial_field_overlap_samples']>0
 assert row['nose']['material_components']==1 and row['nose']['shared_boundary_edges']>0
 row['final_root_model_sha256']=sha(HERE/f'model-{v}.pkl')
for row in renders['variation_isolation'].values():
 assert all(row[k] for k in ['only_anterior_x','widths_hinge_fixed','rostral_delta_exact'])
 assert set(row['changed_settings'])=={'variant','rostral_length_multiplier','profile','control_muzzle_to_cranium_x_ratio'}
for row in renders['render_reproduction'].values():assert row['pixels_exact'] and row['png_bytes_exact']
old={v:pickle.loads((HERE/f'iterations/01/model-{v}.pkl').read_bytes()) for v in 'ABC'}
unchanged={}
for v in 'ABC':
 model=pickle.loads((HERE/f'model-{v}.pkl').read_bytes())
 unchanged[v]={k:eq(old[v]['skeleton']['parts'][k],model['skeleton']['parts'][k]) for k in ['upper','jaw']}
 assert all(unchanged[v].values())
final={'evidence':evidence,'variants':rows,'variation_isolation':renders['variation_isolation'],'render_reproduction':renders['render_reproduction'],'source_guard_current':source_guard,'upper_jaw_unchanged_from_initial':unchanged,'B_development_root_recursive_exact':True,'B_reproduction_scope':'Full create(B) with fresh bones, nasal_support, skin and settings. A/C actual meshes fully audited; full geometry regeneration not repeated for the same one-variable path.','all_final_input_artifact_hashes_current':True}
(HERE/'technical-final-measurements.json').write_text(json.dumps(final,indent=2),'utf-8')
table='\n'.join('| '+v+' | '+' | '.join(f"{rows[v]['containment'][k]['minimum_distance']:.6f}" for k in ['upper','jaw','cartilage'])+' |' for v in 'ABC')
text='''# Independent technical review — final revision 03

Reviewer: `/root/jack_skeleton_technical`. **TECHNICAL = PASS**. Unresolved technical BLOCKER/MAJOR/MINOR: none. This is candidate-delivery eligibility, not user selection, CT accuracy, breed validation, or a pixel asset approval.

## Scope and direct checks

All 18 saved component meshes were checked: A/B/C × upper skull, mandible, nasal support, skin, left eye and right eye. All are finite, single connected closed manifold components, with no boundary/nonmanifold edges or zero-area triangles. Final skin Euler characteristic is 2 in every variant. B mandible has one finite nonzero small sampling triangle below the absolute 1e-10 double-area warning threshold: double-area 3.3343e-11, edges 4.26e-6 to 8.53e-6, and area/maximum-edge-squared ratio 0.4583. Its relative shape is healthy, rather than collinear; it is unchanged from the initial mandible and passes the static and discrete-motion checks. `technical-small-triangle.json` records dtype, coordinates and signed area. This absolute-size warning is retained as a numerical limitation, not a failed mesh. The skull's nonzero genus represents its intentionally modelled anatomical openings and is not confused with an open mesh boundary.

For all nine skull/mandible/nasal-support-to-skin combinations, every vertex and triangle-centroid sample is inside the actual saved final skin, and the triangle-pair crossing test reports 0. Upper, jaw, nasal support and skin self-crossing tests report 0. Nearest-distance lower bounds certify the following minima over the tested samples, in arbitrary model units; these are not millimetres or a continuous-surface minimum claim.

| Variant | Upper skull | Mandible | Nasal support |
|---|---:|---:|---:|
'''+table+'''

All nine A/B/C × 0/10/20-degree jaw states have 0 vertices/centroids inside the upper skull and 0 upper-jaw triangle intersections. These are three discrete rigid-rotation checks, not continuous-animation, tooth/bite or exterior-mouth-opening validation. Each eye intersects the skin with both buried and exposed surface samples; each ear has actual shared skin edges at its root. Each black nose patch is one connected material region on the continuous skin mesh.

## Corrections and isolation

JRT-01 is resolved: the old protruding generic nasal-cartilage proxy was replaced by a smaller authored internal nasal support in the actual production path. It is contained in all final skins, has no crossings, and was included in the fresh B reproduction. JRT-02 is resolved: added local ear support removes both attachment passages; all final skins are closed genus-zero surfaces. The intermediate revision 02 mandibular corner protrusion (54 samples) is also resolved in all final variants. Initial failure and development preflight records remain available.

The contradictory inherited hanging-ear metadata was replaced by actual button-ear controls. Final B reproduction matches all metadata and settings. The upper-skull and mandible arrays remain exactly equal to initial revision 01 for every variant. Only nasal support and exterior construction changed during correction. All 11 protected prior-source/asset hashes remain equal to the startup guard; the reviewed common builder hashes also match prior canonical records. No older breed asset, selected Golden A artwork or source builder was edited by the reviewer.

A/B/C change only dorsal x controls 3,4,5 anterior to the fixed stop, with multipliers .94/1/1.06. Widths, hinge, cranial controls, tissue controls, eye/nose dimensions and ear construction are shared. Downstream regenerated geometry and grid sampling follow that single control change; this is not a claim that different tessellation arrays must have identical posterior vertex indices.

## Reproduction and output coverage

One complete fresh `create('B')` rebuild reproduces every skeleton/exterior array (including dtype), metadata and setting exactly. The development B used for this audit and final root B compare recursively equal. Their pickle bytes differ because serialization object references differ; this is not misreported as identical pickle SHA. A/C received complete actual saved-mesh audits; full creation was not redundantly repeated for the same one-variable code path.

All three boards were regenerated in memory, including PNG encoding: their final PNG bytes are exactly equal. The two comparison boards are RGB 2400×1190; the jaw board is RGB 1800×1210. The reviewer directly opened all 39 final cells: exterior 3×5 views, skeleton 3×5 views, and jaw 3×3 states. The changed final exterior was reopened after revision 03; skeleton/jaw images retain their previously opened exact hashes. Labels, shared scale, view coverage and clipping were checked. The independent visual review remains a separate gate.

## Provenance and limits

[FCI Standard 345, p.3](https://www.fci.be/Nomenclature/Standards/345g03-en.pdf) and the [Royal Kennel Club head and ear standard](https://www.royalkennelclub.com/breed-standards/terrier/jack-russell-terrier) were opened directly. They support qualitative cranial/muzzle proportion and folded-ear direction; they do not provide the authored model coordinates. References explicitly distinguish generic skull anatomy, breed photographs and authored offsets. This is a Jack Russell head/mandible and neutral short-neck exterior study, with no measured breed CT, individual photo fit, cervical vertebrae, teeth, occlusion, full body, pixel style production or animation claim.

Generation dependency closure includes the local builder and dedicated seed, shared skeleton and raster builders, shared surface builder and its transitively imported v1 module, saved models/settings, reference records/images and both fonts. The final 25 input hashes and all 3 artifact hashes were independently verified against `evidence.json`. AST-loaded individual geometry audit functions were reused without executing old review modules or writing their reports. Audit code and measurements are reviewer evidence, not substituted for generation inputs.

Evidence: `technical-final-measurements.json`, `technical-measurements-ac-final.json`, B row of `technical-measurements.json`, `technical-final-isolation-render.json`, and `technical-context.json`. Earlier general guard booleans in the development-stage B run may be false because root candidate files/reference metadata were intentionally replaced during that run; the final frozen 25-input/3-artifact check and per-model equivalence above resolve that transition explicitly.

'''
marker={'status':'PASS','reviewer':'/root/jack_skeleton_technical',**evidence,'coverage_complete':True,'unresolved':{}}
(HERE/'technical-review.md').write_text(text+'<!-- review-verdict: '+json.dumps(marker,separators=(',',':'))+' -->\n','utf-8')
print('TECHNICAL PASS: 18 meshes, 9 support containment cases, 9 jaw states, 3 byte-identical boards; 25 input hashes current.')
