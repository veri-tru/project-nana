"""Versioned authoring states; legacy observation/profile snapshots are never edited."""
import copy
import json
import re
from pathlib import Path

import maker

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / 'packages' / 'v02'
GEOMETRY = {k:v for k,v in maker.RANGES.items() if k != 'eye_radius'}
GEOMETRY.update(eye_rx=(2,4), eye_ry=(2,4), left_eye_offset=(-1,1), right_eye_offset=(-1,1),
                eye_tilt=(-10,10), nose_width=(6,10), nose_height=(4,7),
                muzzle_offset=(-1,2), jaw_width=(12,20))
COAT_PARTS = ('crown','ears','cheeks','chest','paws')

def package_ref():
    return {'id':'nana-front-static','version':'0.2.0',
            'shapes_sha256':maker.digest((PACKAGE/'shapes.json').read_bytes()),
            'styles_sha256':maker.digest((PACKAGE/'styles.json').read_bytes())}

def migrate(profile, revision):
    maker.validate(profile)
    if type(revision) is not int or revision < 1: raise ValueError('source revision required')
    g=copy.deepcopy(profile['appearance']['geometry']); radius=g.pop('eye_radius')
    g.update(eye_rx=radius,eye_ry=radius,left_eye_offset=0,right_eye_offset=0,
             eye_tilt=0,nose_width=8,nose_height=5,muzzle_offset=0,jaw_width=16)
    return {'schema_version':2,'dog_id':profile['dog_id'],
            'source_profile':{'revision':revision,'sha256':maker.digest(maker.canonical(profile).encode())},
            'package':package_ref(),'geometry':g,'colors':copy.deepcopy(profile['appearance']['colors']),
            'coat':{k:profile['render']['coat_length'] for k in COAT_PARTS},
            'collar_visible':profile['render']['collar_visible'],
            'migration':{'from_schema':1,'coordinate_convention':'screen_left_right',
                         'defaults':['eye_tilt','eye_offsets','nose_dimensions','muzzle_offset','jaw_width'],
                         'classification':'all_coordinates_and_colors_are_authoring_values'},
            'review':{'identity':'unreviewed','style':'unreviewed','owner':'unreviewed'}}

def validate(state):
    required={'schema_version','dog_id','source_profile','package','geometry','colors','coat','collar_visible','migration','review'}
    if not isinstance(state,dict) or set(state)!=required or type(state['schema_version']) is not int or state['schema_version']!=2:
        raise ValueError('authoring schema v2 required')
    if not isinstance(state['dog_id'],str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',state['dog_id']):
        raise ValueError('invalid dog_id')
    source=state['source_profile']
    if not isinstance(source,dict) or set(source)!={'revision','sha256'} or type(source['revision']) is not int or source['revision']<1 or not isinstance(source['sha256'],str) or not re.fullmatch('[0-9a-f]{64}',source['sha256']):
        raise ValueError('invalid source profile binding')
    if state['package']!=package_ref(): raise ValueError('package version/hash mismatch; migrate explicitly')
    g=state['geometry']
    if not isinstance(g,dict) or set(g)!=set(GEOMETRY):raise ValueError('unsupported geometry fields')
    for k,(lo,hi) in GEOMETRY.items():
        if type(g[k]) is not int or not lo<=g[k]<=hi:raise ValueError(f'{k}: supported range {lo}..{hi}')
    colors=state['colors']
    if not isinstance(colors,dict) or set(colors)!=set(maker.COLORS) or not all(isinstance(v,str) and re.fullmatch('#[0-9a-fA-F]{6}',v) for v in colors.values()):
        raise ValueError('invalid color roles')
    if not isinstance(state['coat'],dict) or set(state['coat'])!=set(COAT_PARTS) or any(v not in ('short','medium','long') for v in state['coat'].values()):
        raise ValueError('unsupported coat selection')
    if type(state['collar_visible']) is not bool:raise ValueError('collar_visible must be boolean')
    if not isinstance(state['migration'],dict) or state['migration'].get('coordinate_convention')!='screen_left_right':
        raise ValueError('unsupported coordinate convention')
    if state['review']!={'identity':'unreviewed','style':'unreviewed','owner':'unreviewed'}:
        raise ValueError('editor saves drafts only; approval is a separate workflow')
    # Combination checks are explicit: never silently clamp a supported parameter.
    if g['eye_spacing']/2+g['eye_rx']+2 > g['head_width']/2:
        raise ValueError('eyes too wide for face')
    chin=11+g['head_height']
    my=chin-5+g['muzzle_offset']
    if my+g['muzzle_height']/2 > chin+3:raise ValueError('muzzle extends below supported jaw')
    if my-g['muzzle_height']/2 < g['eye_y']+min(g['left_eye_offset'],g['right_eye_offset'])-1:
        raise ValueError('muzzle too high relative to eyes')
    if g['nose_height']+4 > g['muzzle_height']:raise ValueError('nose/mouth do not fit muzzle')
    if g['jaw_width'] > g['head_width']-10:raise ValueError('jaw too wide')
    maker.canonical(state)
    return state

class StateStore(maker.Store):
    def __init__(self,path):
        super().__init__(path)
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS render_states(dog_id TEXT NOT NULL, revision INTEGER NOT NULL,
            payload TEXT NOT NULL,parent INTEGER,reason TEXT NOT NULL,PRIMARY KEY(dog_id,revision));
          CREATE TABLE IF NOT EXISTS render_heads(dog_id TEXT PRIMARY KEY,revision INTEGER NOT NULL);
          CREATE TRIGGER IF NOT EXISTS immutable_render_update BEFORE UPDATE ON render_states
            BEGIN SELECT RAISE(ABORT,'immutable render state'); END;
        ''')

    def state_get(self,dog,revision=None):
        if revision is None:
            h=self.db.execute('SELECT revision FROM render_heads WHERE dog_id=?',(dog,)).fetchone()
            if not h:raise ValueError('no authoring state; run migrate first')
            revision=h[0]
        r=self.db.execute('SELECT payload FROM render_states WHERE dog_id=? AND revision=?',(dog,revision)).fetchone()
        if not r:raise ValueError('unknown authoring revision')
        return json.loads(r[0]),revision

    def state_save(self,state,expected,reason):
        validate(state)
        if type(expected) is not int or expected<0 or not isinstance(reason,str) or not reason.strip():
            raise ValueError('expected revision and reason required')
        # Validate rendering, including clipping and mask relations, before persistence.
        from render_v02 import build
        for view in ('full','face'):build(state,'B2',view)
        dog=state['dog_id']
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            source,_=self.get(dog,state['source_profile']['revision'])
            if maker.digest(maker.canonical(source).encode())!=state['source_profile']['sha256']:
                raise ValueError('source snapshot hash mismatch')
            r=self.db.execute('SELECT revision FROM render_heads WHERE dog_id=?',(dog,)).fetchone()
            head=r[0] if r else 0
            if head!=expected:raise ValueError(f'stale authoring revision: expected {expected}, current {head}')
            revision=head+1
            self.db.execute('INSERT INTO render_states VALUES(?,?,?,?,?)',(dog,revision,maker.canonical(state),head or None,reason))
            self.db.execute('INSERT INTO render_heads VALUES(?,?) ON CONFLICT(dog_id) DO UPDATE SET revision=excluded.revision',(dog,revision))
        return revision

    def state_restore(self,dog,target,expected):
        s,_=self.state_get(dog,target)
        return self.state_save(s,expected,f'restore authoring revision {target}')

    def state_history(self,dog):
        return self.db.execute('SELECT revision,parent,reason FROM render_states WHERE dog_id=? ORDER BY revision',(dog,)).fetchall()
