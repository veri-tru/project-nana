"""Independent read-only audit of the explicitly scoped muzzle shortening."""
from pathlib import Path
import copy, hashlib, importlib.util, importlib.metadata, io, json
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
BEFORE=HERE/'iterations/before-muzzle-shortening'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def equal(a,b):
    if isinstance(a,np.ndarray):return isinstance(b,np.ndarray) and np.array_equal(a,b)
    if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
    if isinstance(a,(list,tuple)):return isinstance(b,type(a)) and len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    return a==b
source=HERE/'skeleton.py';initial=sha(source)
spec=importlib.util.spec_from_file_location('independent_skeleton_review',source)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
profiles=json.loads((HERE/'profiles.json').read_text('utf-8'))
oldprofiles=json.loads((BEFORE/'profiles.json').read_text('utf-8'))
rigs={b:m.make_rig(profiles[b]) for b in m.BREEDS}
oldrigs=json.loads((BEFORE/'rigs.json').read_text('utf-8'))
savedrigs=json.loads((HERE/'rigs.json').read_text('utf-8'))
result={'source_unchanged_from_before':source.read_bytes()==(BEFORE/'skeleton.py').read_bytes(),'saved_rigs_exactly_rebuilt':rigs==savedrigs,'breeds':{},'images':{}}
for b in m.BREEDS:
    cur,old=profiles[b],oldprofiles[b]
    changes=[]
    for i,(a,z) in enumerate(zip(cur['dorsal'],old['dorsal'])):
        for j,(x,y) in enumerate(zip(a,z)):
            if x!=y:changes.append([i,j,y,x])
    changed_nodes=[];unchanged_nodes=[];deltas={}
    for key,node in rigs[b]['nodes'].items():
        if node!=oldrigs[b]['nodes'][key]:
            changed_nodes.append(key);deltas[key]=(np.array(node['point'])-oldrigs[b]['nodes'][key]['point']).tolist()
        else:unchanged_nodes.append(key)
    oldlen=old['dorsal'][2][0]-old['dorsal'][5][0];newlen=cur['dorsal'][2][0]-cur['dorsal'][5][0]
    rec=dict(profile_changes=changes,other_profile_fields_exact=all(cur[k]==old[k] for k in cur if k!='dorsal'),changed_nodes=changed_nodes,unchanged_nodes=unchanged_nodes,node_deltas=deltas,stop_to_tip_x_before=oldlen,stop_to_tip_x_after=newlen,reduction_percent=100*(oldlen-newlen)/oldlen,nasal_base_to_tip_vector_exact=equal(np.array(cur['dorsal'][5])-cur['dorsal'][4],np.array(old['dorsal'][5])-old['dorsal'][4]),same_node_topology=all((n['parent'],n['kind'])==(oldrigs[b]['nodes'][k]['parent'],oldrigs[b]['nodes'][k]['kind']) for k,n in rigs[b]['nodes'].items()),geometry_exact=equal(m.geometry(rigs[b]),m.geometry(oldrigs[b])))
    assert rec['other_profile_fields_exact'] and rec['nasal_base_to_tip_vector_exact'] and rec['same_node_topology']
    if b=='maltipoo':assert not changes and not changed_nodes and rec['geometry_exact']
    else:
        assert [x[:2] for x in changes]==[[3,0],[4,0],[5,0]]
        assert set(changed_nodes)=={'nasal_bridge','nasal_base','nose_tip','maxilla_front','nasal_floor','chin','L_jaw_front','R_jaw_front'}
        shift=cur['dorsal'][4][0]-old['dorsal'][4][0]
        assert all(deltas[k]==[shift,0.,0.] for k in ['nasal_base','nose_tip','maxilla_front','nasal_floor','chin','L_jaw_front','R_jaw_front'])
    rec['jaw_rigid_errors']={}
    rest=m.geometry(rigs[b],0);h=m.point(rigs[b],'jaw_axis')
    for angle in [9,18]:
        a=np.radians(angle);rot=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]])
        posed=m.geometry(rigs[b],angle)
        errors=[]
        for (v,c,w),(vv,cc,ww) in zip(rest,posed):
            expected=(v-h)@rot.T+h if c==m.ORANGE else v
            errors.append(float(np.abs(expected-vv).max()))
        rec['jaw_rigid_errors'][str(angle)]=max(errors)
        assert max(errors)<1e-10
    result['breeds'][b]=rec
out=HERE/'review-muzzle-reproduction';out.mkdir(exist_ok=True)
for name,im in m.boards(rigs).items():
    buf=io.BytesIO();im.save(buf,format='PNG');data=buf.getvalue()
    actual=HERE/name
    record=dict(sha256=hashlib.sha256(data).hexdigest(),candidate_sha256=sha(actual),bytes_equal=data==actual.read_bytes(),size=list(im.size))
    assert record['bytes_equal']
    if name=='comparison.png':
        with Image.open(BEFORE/name) as before:
            # Maltipoo row, from its divider to just before the global footer.
            box=(0,1113,im.width,1418)
            record['maltipoo_row_pixels_exact']=im.crop(box).tobytes()==before.crop(box).tobytes()
            assert record['maltipoo_row_pixels_exact']
    (out/name).write_bytes(data);result['images'][name]=record
refs=json.loads((HERE/'references.json').read_text('utf-8'))
paths=[source,HERE/'profiles.json',HERE/'references.json',m.FONT,m.BOLD]
for ref in refs['references']:
    refpath=Path(ref['path']);assert sha(refpath)==ref['sha256'];paths.append(refpath)
import os
result['inputs']={os.path.relpath(p,HERE).replace('\\','/'):sha(p) for p in paths}
result['before_evidence']={p.name:sha(p) for p in BEFORE.iterdir() if p.is_file()}
result['source_unchanged_during_review']=initial==sha(source)
result['libraries']={x:importlib.metadata.version(x) for x in ['numpy','scipy','Pillow']}
assert result['source_unchanged_from_before'] and result['saved_rigs_exactly_rebuilt'] and result['source_unchanged_during_review']
(HERE/'muzzle-technical-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({'status':'SCOPED_CHECKS_PASS','whole_candidate':'BLOCKED_SK01_SK02_SK03','images':result['images'],'reductions':{b:r['reduction_percent'] for b,r in result['breeds'].items()}},indent=2))
