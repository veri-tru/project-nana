"""Offline, profile-driven static pixel maker. No photo/image-model inputs."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3

from PIL import Image, ImageChops, ImageDraw, ImageFilter, __version__ as PIL_VERSION

VERSION = '0.1.0'
ROOT = Path(__file__).resolve().parent
RANGES = dict(head_width=(32,44), head_height=(24,32), ear_width=(9,15),
              ear_length=(23,34), eye_spacing=(14,22), eye_radius=(2,4),
              eye_y=(23,29), muzzle_width=(16,24), muzzle_height=(10,16),
              body_width=(26,38), body_height=(32,42), leg_width=(8,13),
              left_occlusion=(0,3), right_occlusion=(0,3))
COLORS = ('coat','coat_shadow','ear','ear_shadow','muzzle','muzzle_shadow',
          'iris','pupil','nose','nose_light','highlight','collar')

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def validate(p):
    if not isinstance(p,dict) or set(p) != {'schema_version','dog_id','appearance','render','behavior','evidence'}:
        raise ValueError('profile fields must match schema v1')
    if type(p['schema_version']) is not int or p['schema_version'] != 1 or not isinstance(p['dog_id'],str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', p['dog_id']):
        raise ValueError('invalid schema or dog_id')
    a = p['appearance']
    if not isinstance(a,dict) or set(a) != {'geometry','colors','unresolved'} or not isinstance(a['unresolved'], list):
        raise ValueError('invalid appearance')
    if not isinstance(a['geometry'],dict) or set(a['geometry']) != set(RANGES):
        raise ValueError('unsupported or missing geometry fields')
    for key, (lo, hi) in RANGES.items():
        v = a['geometry'][key]
        if type(v) is not int or not lo <= v <= hi:
            raise ValueError(f'{key} outside supported range {lo}..{hi}')
    if not isinstance(a['colors'],dict) or set(a['colors']) != set(COLORS):
        raise ValueError('invalid palette roles')
    if not all(isinstance(v,str) and re.fullmatch(r'#[0-9a-fA-F]{6}',v) for v in a['colors'].values()):
        raise ValueError('colors must be #RRGGBB')
    if not isinstance(p['render'],dict) or set(p['render']) != {'coat_length','collar_visible','owner_selected'}:
        raise ValueError('invalid render fields')
    if p['render']['coat_length'] not in ('short','medium','long'):
        raise ValueError('unsupported coat length')
    if any(type(p['render'][k]) is not bool for k in ('collar_visible','owner_selected')):
        raise ValueError('render flags must be booleans')
    if not isinstance(p['behavior'],dict) or not isinstance(p['evidence'],list):
        raise ValueError('behavior must be object; evidence must be list')
    for e in p['evidence']:
        if not isinstance(e,dict) or set(e) != {'kind','fields','source','note'} or e['kind'] not in ('photo_observation','owner_report','design_default','synthetic'):
            raise ValueError('invalid evidence record')
        if not isinstance(e['fields'],list) or not all(isinstance(e[k],str) for k in ('source','note')):
            raise ValueError('invalid evidence values')
    canonical(p)
    return p

class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS revisions(
            dog_id TEXT NOT NULL, revision INTEGER NOT NULL, payload TEXT NOT NULL,
            parent INTEGER, reason TEXT NOT NULL, PRIMARY KEY(dog_id, revision));
          CREATE TABLE IF NOT EXISTS heads(dog_id TEXT PRIMARY KEY, revision INTEGER NOT NULL);
          CREATE TRIGGER IF NOT EXISTS immutable_revision_update BEFORE UPDATE ON revisions
            BEGIN SELECT RAISE(ABORT,'immutable revision'); END;
        ''')

    def close(self):
        self.db.close()

    def save(self, profile, expected, reason='edit'):
        validate(profile)
        if type(expected) is not int or expected < 0 or not reason.strip():
            raise ValueError('expected revision and reason required')
        dog = profile['dog_id']
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            row = self.db.execute('SELECT revision FROM heads WHERE dog_id=?',(dog,)).fetchone()
            head = row[0] if row else 0
            if head != expected:
                raise ValueError(f'stale revision: expected {expected}, current {head}')
            rev = head+1
            self.db.execute('INSERT INTO revisions VALUES(?,?,?,?,?)',(dog,rev,canonical(profile),head or None,reason))
            self.db.execute('INSERT INTO heads VALUES(?,?) ON CONFLICT(dog_id) DO UPDATE SET revision=excluded.revision',(dog,rev))
        return rev

    def get(self, dog, revision=None):
        if revision is None:
            h=self.db.execute('SELECT revision FROM heads WHERE dog_id=?',(dog,)).fetchone()
            if not h: raise ValueError('unknown dog')
            revision=h[0]
        row=self.db.execute('SELECT payload FROM revisions WHERE dog_id=? AND revision=?',(dog,revision)).fetchone()
        if not row: raise ValueError('unknown dog/revision')
        return json.loads(row[0]), revision

    def rollback(self, dog, target, expected):
        p,_=self.get(dog,target)
        return self.save(p,expected,f'restore revision {target}')

    def history(self,dog):
        return self.db.execute('SELECT revision,parent,reason FROM revisions WHERE dog_id=? ORDER BY revision',(dog,)).fetchall()

def build(profile, style='B2', view='full'):
    validate(profile)
    package=json.loads((ROOT/'styles.json').read_text())
    if style not in package['styles'] or view not in ('full','face'):
        raise ValueError('unsupported style/view')
    g=profile['appearance']['geometry']; colors=dict(profile['appearance']['colors'])
    colors.update(package['styles'][style]); layers=[]
    def points(coords):
        if view=='face': return [(round(48+(x-48)*1.5),round(46+(y-28)*1.5)) for x,y in coords]
        return [(round(x),round(y)) for x,y in coords]
    def polygon(name,coords,role,outline=False,clip=None):
        m=Image.new('L',(96,96)); ImageDraw.Draw(m).polygon(points(coords),fill=255)
        if clip is not None: m=ImageChops.multiply(m,clip)
        if outline:
            edge=ImageChops.subtract(m.filter(ImageFilter.MaxFilter(3)),m)
            layers.append((name+'_outline',edge,'outline'))
        layers.append((name,m,role)); return m
    def ellipse(name,box,role,outline=False,clip=None):
        x0,y0,x1,y1=box
        coords=[((x0+x1)/2+(x1-x0)/2*math.cos(i*math.pi/16),
                 (y0+y1)/2+(y1-y0)/2*math.sin(i*math.pi/16)) for i in range(32)]
        return polygon(name,coords,role,outline,clip)
    w=g['body_width']/2; bottom=89; top=bottom-g['body_height']; foot=g['leg_width']
    if view=='full':
        polygon('tail',[(58,79),(69,77),(75,72),(80,73),(84,70),(87,74),(84,79),(86,80),(78,84),(62,85)],'coat',True)
        polygon('tail_shade',[(64,82),(76,81),(83,77),(79,83),(65,85)],'coat_shadow')
        body=polygon('body',[(40,top),(56,top),(61,top+9),(48+w,73),(49+w,85),(58,89),(38,89),(47-w,85),(48-w,73),(35,top+9)],'coat',True)
        polygon('body_shade',[(55,top+8),(61,top+15),(48+w,76),(48+w,85),(57,89),(49,87),(50,74)],'coat_shadow',clip=body)
        ellipse('left_haunch',(48-w-1,71,40,88),'coat',True)
        ellipse('right_haunch',(56,71,49+w,88),'coat',True)
        for side,x in [('left',40),('right',56)]:
            polygon(side+'_leg',[(x-foot/2,65),(x+foot/2,65),(x+foot/2-1,83),(x+foot/2+1,87),(x+foot/2,90),(x-foot/2-2,90),(x-foot/2-2,86),(x-foot/2,82)],'coat',True)
            polygon(side+'_leg_shade',[(x+foot/2-3,70),(x+foot/2-1,81),(x+foot/2,87),(x+foot/2-2,88),(x+foot/2-4,84)],'coat_shadow')
        polygon('chest',[(37,top),(59,top),(61,57),(57,62),(52,63),(48,66),(44,63),(39,62),(35,57)],'coat')
        if profile['render']['collar_visible']:
            polygon('collar',[(37,44),(59,44),(58,49),(38,49)],'collar')
            polygon('buckle',[(45,45),(51,45),(51,49),(45,49)],'nose')
    hw=g['head_width']/2; hh=g['head_height']; y0=11; yb=y0+hh
    face=polygon('face',[(48-hw+6,y0),(48+hw-6,y0),(48+hw,19),(48+hw,32),(48+hw-4,yb-2),(55,yb+2),(41,yb+2),(48-hw+4,yb-2),(48-hw,32),(48-hw,19)],'coat',True)
    for side,sign in [('left',-1),('right',1)]:
        x=48+sign*(hw-2); ew=g['ear_width']; end=13+g['ear_length']
        xy=lambda a,b:(x+sign*a,b)
        ear=polygon(side+'_ear',[xy(-2,14),xy(5,13),xy(ew-1,20),xy(ew+1,end-9),xy(ew-1,end-3),xy(ew-5,end),xy(1,end-1),xy(-2,end-6)],'ear',True)
        polygon(side+'_ear_shade',[xy(ew-1,23),xy(ew+1,end-9),xy(ew-1,end-3),xy(ew-5,end),xy(1,end-1),xy(0,end-5),xy(5,end-4)],'ear_shadow',clip=ear)
    tuft={'short':1,'medium':3,'long':5}[profile['render']['coat_length']]
    polygon('crown',[(48-hw+4,19),(48-hw+4,12),(39,10),(42,10-tuft),(46,12),(49,9-tuft),(52,12),(57,10),(60,14),(48+hw-4,19)],'coat',True)
    polygon('crown_fill',[(48-hw+5,17),(48+hw-5,17),(48+hw-4,23),(48-hw+4,23)],'coat')
    ey=g['eye_y']; r=g['eye_radius']
    for side,sign in [('left',-1),('right',1)]:
        ex=48+sign*g['eye_spacing']/2
        ellipse(side+'_socket',(ex-r-2,ey-r-2,ex+r+2,ey+r+3),'muzzle_shadow',clip=face)
        eye=ellipse(side+'_eye',(ex-r,ey-r,ex+r,ey+r),'iris',True)
        ellipse(side+'_pupil',(ex-r+1,ey-r,ex+r-1,ey+r-1),'pupil',clip=eye)
        polygon(side+'_highlight',[(ex-1,ey-1),(ex-1,ey-1)],'highlight',clip=eye)
        occ=g[side+'_occlusion']
        if occ:
            polygon(side+'_eyelid',[(ex-r-1,ey-r-1),(ex+r+1,ey-r-1),(ex+r+1,ey-r+occ-1),(ex-r-1,ey-r+occ-1)],'coat',clip=eye)
            polygon(side+'_front_fur',[(ex-r-2,ey-r-2),(ex+r+1,ey-r-2),(ex+r,ey-r+occ-1),(ex,ey-r+occ-1),(ex-2,ey-r+occ-1)],'coat')
    mw=g['muzzle_width']/2; my=yb-5; mh=g['muzzle_height']
    muzzle=ellipse('muzzle',(48-mw,my-mh/2,48+mw,my+mh/2),'muzzle')
    polygon('muzzle_shade',[(48-mw,my+2),(41,my+mh/2),(55,my+mh/2),(48+mw,my+2),(54,my+mh/2-2),(42,my+mh/2-2)],'muzzle_shadow',clip=muzzle)
    polygon('nose',[(44,my-3),(52,my-3),(53,my),(50,my+3),(46,my+3),(43,my)],'nose')
    polygon('nose_light',[(45,my-2),(49,my-2),(49,my-1),(45,my-1)],'nose_light')
    polygon('mouth',[(48,my+3),(48,my+5),(45,my+6),(48,my+5),(51,my+6)],'nose')
    output=Image.new('RGBA',(96,96)); masks={}
    for name,mask,role in layers:
        color=Image.new('RGBA',output.size,colors[role]);color.putalpha(mask)
        output.alpha_composite(color); masks[name]=mask
    geometry_hash=digest(b''.join(n.encode()+m.tobytes() for n,m,_ in layers))
    manifest={'renderer_version':VERSION,'pillow_version':PIL_VERSION,
              'renderer_sha256':digest(Path(__file__).read_bytes()),
              'style_package_sha256':digest((ROOT/'styles.json').read_bytes()),
              'profile_sha256':digest(canonical(profile).encode()),'dog_id':profile['dog_id'],
              'style':style,'view':view,'canvas_px':[96,96],
              'geometry_sha256':geometry_hash,'rgba_sha256':digest(output.tobytes()),
              'opaque_color_count':len({c for c in output.get_flattened_data() if c[3]}),
              'source_images_read':0,'review':{'identity':'unreviewed','style':'unreviewed','owner':'unreviewed'},
              'supported_pose':'front_seated' if view=='full' else 'front_face',
              'animation_supported':False,'layers':list(masks)}
    return output,masks,manifest

def export(profile,revision,directory):
    out=Path(directory)
    out.mkdir(parents=True,exist_ok=False)
    cards=[]
    for view in ('face','full'):
        for style in ('B2','C2'):
            img,masks,meta=build(profile,style,view);name=f'{view}-{style}'
            img.save(out/(name+'.png'))
            img.resize((576,576),Image.Resampling.NEAREST).save(out/(name+'-6x.png'))
            meta['profile_revision']=revision
            (out/(name+'.json')).write_text(json.dumps(meta,ensure_ascii=False,indent=2))
            ld=out/(name+'-layers');ld.mkdir()
            for k,m in masks.items():m.save(ld/(k+'.png'))
            cards.append(f'<figure><figcaption>{view} · {style}</figcaption><img src="{name}.png"></figure>')
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Nana 정적 제작기</title><style>body{font:16px system-ui;background:#f5f0e7;padding:24px}main{display:grid;grid-template-columns:repeat(2,1fr);max-width:900px}img{width:384px;max-width:100%;image-rendering:pixelated}figure{margin:12px}figcaption{font-weight:bold}</style><h1>프로필 기반 정적 출력</h1><p>96×96 · B2/C2 · 닮음·정본 화풍·보호자 검수 대기</p><main>'+''.join(cards)+'</main>')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--db',required=True)
    sub=ap.add_subparsers(dest='cmd',required=True)
    s=sub.add_parser('save');s.add_argument('profile');s.add_argument('--expected',type=int,required=True);s.add_argument('--reason',required=True)
    s=sub.add_parser('render');s.add_argument('dog');s.add_argument('--revision',type=int);s.add_argument('--out',required=True)
    s=sub.add_parser('rollback');s.add_argument('dog');s.add_argument('--target',type=int,required=True);s.add_argument('--expected',type=int,required=True)
    s=sub.add_parser('history');s.add_argument('dog')
    args=ap.parse_args();store=Store(args.db)
    try:
        if args.cmd=='save':print(store.save(json.loads(Path(args.profile).read_text()),args.expected,args.reason))
        elif args.cmd=='render':
            p,rev=store.get(args.dog,args.revision);export(p,rev,args.out);print(args.out)
        elif args.cmd=='rollback':print(store.rollback(args.dog,args.target,args.expected))
        else:print(json.dumps(store.history(args.dog),ensure_ascii=False))
    except (ValueError,FileExistsError) as e:ap.exit(2,str(e)+'\n')
    finally:store.close()

if __name__=='__main__':main()
