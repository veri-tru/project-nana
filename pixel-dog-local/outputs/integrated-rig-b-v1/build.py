"""Build the selected B skeleton. All offsets are in a single body coordinate frame."""
import json
from math import cos, radians, sin, dist, isclose
from pathlib import Path

OUT = Path(__file__).resolve().parent
BODY = OUT.parent / 'body-rig-breeds-v1/rigs.json'
FACE = OUT.parent / 'face-rig-breeds-v1/rigs.json'
FACE_SCALE = 0.4   # Authored face grid to body design units, same for all three.
FORE = ('scapula_fixed','shoulder','elbow','carpus','mcp','foretoe')
HIND = ('hip','stifle','tarsus','mtp','hindtoe')
TAIL = ('tail_root','tail_proximal','tail_mid','tail_distal','tail_tip')
# Illustration controls, not individual caudal vertebrae. Widths and feather
# depths are in body units; angles describe one standing display pose.
TAIL_DEFAULTS = {
    'whippet': dict(span_ratio=.90, angles=(-78,-70,-45,8),
                    core_radius=(.95,.73,.49,.30,.10), underside_feather=(0,0,0,0,0),
                    source_visibility='partially occluded by hind legs; fine tip visible',
                    length_basis='authored ratio informed by long tapering breed tail; not measured'),
    'dachshund': dict(span_ratio=.52, angles=(-12,-16,-15,-3),
                      core_radius=(1.10,.84,.62,.38,.12), underside_feather=(0,0,0,0,0),
                      source_visibility='occluded in source photograph; neutral rig is a breed estimate',
                      length_basis='authored ratio for smooth coat; breed standard gives no numeric length'),
    'golden': dict(angles=(0,6,14,18), core_radius=(1.62,1.36,1.04,.60,.19),
                   underside_feather=(.30,2.45,3.10,1.75,0),
                   source_visibility='raised feathered silhouette visible; skeletal tip obscured by coat',
                   length_basis='tail-root height minus projected hock height when hanging vertically'),
}
# Only these controls accept pitch angles. The remaining nodes are landmarks.
PITCH_CONTROLS = frozenset(
    ['body.pelvis','body.lumbar_pivot','body.neck','body.head','face.jaw_axis']
    + ['body.'+side+joint for side in ('left_','right_') for joint in
       ('shoulder','elbow','carpus','mcp','hip','stifle','tarsus','mtp')]
    + ['body.'+n for n in TAIL[:-1]]
    + ['face.'+side+part for side in ('L_','R_') for part in ('ear_root','ear_fold')]
)

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

def delta(point, origin):
    return [round(a-b,8) for a,b in zip(point,origin,strict=True)]

def body_id(key):
    return 'body.' + key.replace('near_', 'left_').replace('far_', 'right_')

def assemble(graph, b, f, breed):
    pos = {}
    parents = {'body.pelvis': None}
    for parent, children in graph.items():
        for child in children:
            parents[body_id(child)] = body_id(parent)
    def store(name, xy, side=0):
        pos['body.'+name] = [*xy,side]
    store('pelvis',b['side_hindlimb'][0])
    store('lumbar_pivot',b['lumbar_pivot'])
    for name,xy in zip(('ribcage','neck','head'),b['neck_to_face'],strict=True):
        store(name,xy)
    defaults=TAIL_DEFAULTS[breed]
    tx,ty=b['tail'][0]
    length=(ty-b['side_hindlimb'][2][1] if breed=='golden'
            else b['shoulder_hip_span']*defaults['span_ratio'])
    store(TAIL[0],(tx,ty))
    segment_lengths=[length*fraction for fraction in (.31,.29,.23,.17)]
    for parent,child,seg,angle in zip(TAIL[:-1],TAIL[1:],segment_lengths,defaults['angles'],strict=True):
        parents['body.'+child]='body.'+parent
        tx+=seg*cos(radians(angle))
        ty+=seg*sin(radians(angle))
        store(child,(tx,ty))
    for chain, nodes, outline in [('side_forelimb',FORE,'top_ribcage'),('side_hindlimb',HIND,'top_pelvis')]:
        # Neutral bilateral spacing is an authored estimate from plate half-width.
        half_width = max(p[1] for p in b[outline]) * 0.8
        for side,sign in [('left_',1),('right_',-1)]:
            for key,xy in zip(nodes,b[chain],strict=True):
                store(side+key,xy,sign*half_width)
    mount = f['anchors']['neck_mount']
    for key, point in f['anchors'].items():
        x,y,z = delta(point,mount)
        pos['face.'+key] = [a + FACE_SCALE*t for a,t in zip(pos['body.head'],(-z,-y,x))]
    hinges = [pos['face.'+n] for n in f['jaw_axis']]
    pos['face.jaw_axis'] = [(a+b)/2 for a,b in zip(*hinges)]
    for child,parent in f['parents'].items():
        parents['face.'+child] = parent if parent=='body.head' else 'face.'+parent
    assert set(pos)==set(parents)
    nodes = {k:dict(parent=parent,offset=delta(pos[k],pos[parent] if parent else [0,0,0]))
             for k,parent in parents.items()}
    surfaces = {}
    for label,owner in [('ribcage','body.ribcage'),('pelvis','body.pelvis')]:
        center = pos[owner]
        side = [[x,y,0] for x,y in b['side_'+label]]
        top = [[x,center[1],z] for x,z in b['top_'+label]]
        surfaces[label] = dict(owner=owner,offsets=[delta(p,center) for p in side],
                               top_offsets=[delta(p,center) for p in top])
    def guide(owner,xy):
        return dict(owner=owner,offset=delta([*xy,0],pos[owner]))
    return dict(name=b['name'],nodes=nodes,surfaces=surfaces,
                pelvic_dorsum=guide('body.pelvis',max(b['side_pelvis'],key=lambda xy:xy[1])),
                rear_brisket=guide('body.ribcage',b['side_ribcage'][6]),
                tail_profile=dict(chain=['body.'+n for n in TAIL],segment_lengths=segment_lengths,
                                  length_basis=defaults['length_basis'],core_radius=defaults['core_radius'],
                                  underside_feather=defaults['underside_feather'],
                                  neutral_segment_angles_deg=defaults['angles'],
                                  visibility=dict(neutral='shown',source=defaults['source_visibility']),
                                  evidence='review.md#꼬리-후속-조사--2026-11-05'),
                belly_guide=dict(owner='body.pelvis',offset=delta([*b['belly_guide'],0],pos['body.pelvis'])),
                jaw_hinges=['face.'+n for n in f['jaw_axis']],references=[b['source'],f['source']])

def project_offset(frame, offset):
    origin,angle=frame
    dx,dy,dz=offset
    a=radians(angle)
    return (origin[0]+cos(a)*dx-sin(a)*dy,origin[1]+sin(a)*dx+cos(a)*dy,origin[2]+dz)

def world_frames(rig, rotations=None):
    """Hierarchical side-plane FK; angles in degrees about the left-right axis."""
    rotations = rotations or {}
    nodes = rig['nodes']
    if rotations.keys() - nodes.keys():
        raise ValueError('unknown joint in pose')
    if rotations.keys() - PITCH_CONTROLS:
        raise ValueError('rotation requested on fixed landmark')
    solved = {}
    def visit(k):
        if k not in solved:
            parent=nodes[k]['parent']
            origin,angle=visit(parent) if parent else ((0,0,0),0)
            xyz=project_offset((origin,angle),nodes[k]['offset'])
            solved[k]=(xyz,angle+rotations.get(k,0))
        return solved[k]
    return {k:visit(k) for k in nodes}

def world_pose(rig, rotations=None):
    return {k:v[0] for k,v in world_frames(rig,rotations).items()}

def verify(rig):
    rest=world_pose(rig)
    nodes=rig['nodes']
    tail=rig['tail_profile']
    chain=tail['chain']
    bent=world_pose(rig,{chain[0]:-9,chain[2]:25})
    assert all(dist(rest[k],bent[k])<1e-7 for k in nodes if k not in chain[1:])
    assert dist(rest[chain[-1]],bent[chain[-1]])>1e-3
    for a,b,length in zip(chain[:-1],chain[1:],tail['segment_lengths'],strict=True):
        assert nodes[b]['parent']==a
        for points in (rest,bent):
            assert abs(dist(points[a],points[b])-length)<1e-7
    assert [k for k,v in nodes.items() if v['parent'] is None]==['body.pelvis']
    assert dist(rest['body.head'],rest['face.neck_mount'])<1e-7
    assert all(abs(rest['body.'+s+t][1])<1e-7 for s in ('left_','right_') for t in ('foretoe','hindtoe'))
    # Exercise this skeleton only: front toes may move with the chest in FK.
    raised=world_pose(rig,{'body.lumbar_pivot':-12})
    jaw=world_pose(rig,{'face.jaw_axis':12})
    combined=world_pose(rig,{'body.lumbar_pivot':-12,'face.jaw_axis':12})
    for p in (raised, jaw, combined):
        assert dist(p['face.neck_mount'],p['body.head'])<1e-7
        for k,node in nodes.items():
            parent=node['parent']
            if parent:
                assert isclose(dist(p[k],p[parent]),dist(rest[k],rest[parent]),abs_tol=1e-7)
    assert raised['face.nose'][1]>rest['face.nose'][1]
    assert raised['body.left_hip']==rest['body.left_hip']
    moved={k for k in rest if dist(rest[k],jaw[k])>1e-7}
    assert moved=={'face.chin','face.L_jaw_side','face.R_jaw_side'}
    for k in rest:
        if k not in moved:
            assert dist(combined[k],raised[k])<1e-7
    assert jaw['face.chin'][1]<rest['face.chin'][1]
    a,b=rig['jaw_hinges']
    assert all(abs(s-t)<1e-7 for s,t in zip(rest[a][:2],rest[b][:2]))
    for side in ('left','right'):
        try:
            world_pose(rig,{'body.'+side+'_scapula_fixed':25})
        except ValueError as error:
            assert 'fixed landmark' in str(error)
        else:
            raise AssertionError('B requires a fixed scapula')
    posed=world_frames(rig,{'body.lumbar_pivot':-12})
    pivot=rest['body.lumbar_pivot']
    for name,surf in rig['surfaces'].items():
        owner=surf['owner']
        for v in surf['offsets']+surf['top_offsets']:
            initial=project_offset((rest[owner],0),v)
            expected=project_offset((pivot,-12),delta(initial,pivot)) if name=='ribcage' else initial
            assert dist(project_offset(posed[owner],v),expected)<1e-7
    return dict(nodes=len(nodes),roots=1,jaw_only_moved=sorted(moved),neck_seam_and_segment_lengths='pass')

def main():
    body,face=load(BODY),load(FACE)
    assert body['profiles'].keys()==face.keys()
    breeds={k:assemble(body['topology'],v,face[k],k) for k,v in body['profiles'].items()}
    assert all(r['nodes'].keys()==next(iter(breeds.values()))['nodes'].keys() for r in breeds.values())
    model=dict(version='integrated-rig-b-v1',structure='B',units='shoulder to hip projected span = 30',
               axes=['caudal','up','anatomical left'],face_scale=FACE_SCALE,pitch_controls=sorted(PITCH_CONTROLS),breeds=breeds)
    results={k:verify(r) for k,r in breeds.items()}
    (OUT/'rigs.json').write_text(json.dumps(model,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(results,ensure_ascii=False))
if __name__=='__main__':
    main()
