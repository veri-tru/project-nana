"""Explicit v2 -> v3 authoring migration; both historical render routes remain valid."""
import copy
import json

import maker
import state_v02 as previous

ROOT = previous.ROOT
PACKAGE = ROOT / 'packages' / 'v03'
COAT_PARTS = previous.COAT_PARTS
EXTRA = dict(head_drop=(0,10), neck_width=(14,24), shoulder_width=(20,36),
             haunch_width=(20,36), foot_spacing=(12,22), muzzle_lobe_depth=(0,3),
             pupil_percent=(45,75))
GEOMETRY = {**previous.GEOMETRY, **EXTRA}

def package_ref():
    return {'id':'nana-front-static','version':'0.3.0',
            'shapes_sha256':maker.digest((PACKAGE/'shapes.json').read_bytes()),
            'styles_sha256':maker.digest((PACKAGE/'styles.json').read_bytes())}

def migrate(state, revision):
    previous.validate(state)
    if type(revision) is not int or revision < 1:raise ValueError('source authoring revision required')
    result=copy.deepcopy(state)
    result['schema_version']=3
    result['package']=package_ref()
    defaults=json.loads((PACKAGE/'shapes.json').read_text())['defaults']
    result['geometry'].update(defaults)
    result['migration']={'from_schema':2,'from_authoring_revision':revision,
                         'from_state_sha256':maker.digest(maker.canonical(state).encode()),
                         'coordinate_convention':'screen_left_right','defaults':defaults,
                         'classification':'all_coordinates_and_colors_are_authoring_values'}
    return result

def validate(state):
    if not isinstance(state,dict) or type(state.get('schema_version')) is not int or state['schema_version']!=3:
        raise ValueError('authoring schema v3 required')
    if state.get('package')!=package_ref():raise ValueError('package version/hash mismatch; migrate explicitly')
    g=state.get('geometry')
    if not isinstance(g,dict) or set(g)!=set(GEOMETRY):raise ValueError('unsupported geometry fields')
    for k,(lo,hi) in EXTRA.items():
        if type(g[k]) is not int or not lo<=g[k]<=hi:raise ValueError(f'{k}: supported range {lo}..{hi}')
    legacy=copy.deepcopy(state);legacy['schema_version']=2;legacy['package']=previous.package_ref()
    legacy['geometry']={k:v for k,v in g.items() if k not in EXTRA}
    previous.validate(legacy)
    migration=state['migration']
    if migration.get('from_schema')!=2 or type(migration.get('from_authoring_revision')) is not int or migration['from_authoring_revision']<1:
        raise ValueError('v2 migration origin required')
    if not isinstance(migration.get('from_state_sha256'),str) or len(migration['from_state_sha256'])!=64:
        raise ValueError('migration state hash required')
    if g['neck_width']>g['shoulder_width']:raise ValueError('neck wider than shoulders')
    if g['foot_spacing']<g['leg_width']+2:raise ValueError('front feet overlap')
    if g['shoulder_width']>g['head_width']+2:raise ValueError('shoulders outside supported silhouette')
    if 11+g['head_height']+g['head_drop']>90-g['body_height']+5:
        raise ValueError('head too low for chest; reduce head drop or body height')
    return state

def build_any(state,style='B2',view='full'):
    if state.get('schema_version')==2:
        from render_v02 import build
    else:
        from render_v03 import build
    return build(state,style,view)

class StateStore(previous.StateStore):
    def state_save(self,state,expected,reason):
        if isinstance(state,dict) and state.get('schema_version')==2:
            return super().state_save(state,expected,reason)
        validate(state)
        if type(expected) is not int or expected<0 or not isinstance(reason,str) or not reason.strip():
            raise ValueError('expected revision and reason required')
        for view in ('full','face'):build_any(state,'B2',view)
        dog=state['dog_id']
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            source,_=self.get(dog,state['source_profile']['revision'])
            if maker.digest(maker.canonical(source).encode())!=state['source_profile']['sha256']:
                raise ValueError('source snapshot hash mismatch')
            migration=state['migration']
            ancestor,rev=self.state_get(dog,migration.get('from_authoring_revision'))
            if ancestor['schema_version']!=2 or maker.digest(maker.canonical(ancestor).encode())!=migration.get('from_state_sha256'):
                raise ValueError('migration source mismatch')
            if ancestor['source_profile']!=state['source_profile']:
                raise ValueError('migration source profile mismatch')
            r=self.db.execute('SELECT revision FROM render_heads WHERE dog_id=?',(dog,)).fetchone()
            head=r[0] if r else 0
            if head!=expected:raise ValueError(f'stale authoring revision: expected {expected}, current {head}')
            revision=head+1
            self.db.execute('INSERT INTO render_states VALUES(?,?,?,?,?)',(dog,revision,maker.canonical(state),head or None,reason))
            self.db.execute('INSERT INTO render_heads VALUES(?,?) ON CONFLICT(dog_id) DO UPDATE SET revision=excluded.revision',(dog,revision))
        return revision
