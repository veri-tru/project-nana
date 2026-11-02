import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import ImageChops
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import maker
import render_v02
import state_v02
from render_v03 import build, export
from state_v03 import ROOT, StateStore, migrate

class V03Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.store=StateStore(self.root/'profiles.sqlite')
        self.p=json.loads((ROOT/'example.json').read_text());self.store.save(self.p,0,'synthetic')
        self.old=state_v02.migrate(self.p,1);self.store.state_save(self.old,0,'v2')
        self.s=migrate(self.old,1)
    def tearDown(self):self.store.close();self.tmp.cleanup()

    def test_migration_and_mixed_version_restore_preserve_pixels(self):
        pinned=json.loads((ROOT/'tests/fixtures/v02-pixels.json').read_text())
        for key,digest in pinned.items():
            view,style=key.split('-')
            self.assertEqual(render_v02.build(self.old,style,view)[2]['rgba_sha256'],digest)
        self.assertEqual(self.store.state_save(self.s,1,'upgrade'),2)
        edited=copy.deepcopy(self.s);edited['geometry']['shoulder_width']=30
        self.store.state_save(edited,2,'shoulder')
        self.assertEqual(self.store.state_restore(self.p['dog_id'],1,3),4)
        self.assertEqual(self.store.state_get(self.p['dog_id']),(self.old,4))
        self.assertEqual(self.store.state_restore(self.p['dog_id'],3,4),5)
        self.assertEqual(self.store.get(self.p['dog_id']),(self.p,1))
        self.store.close();self.store=StateStore(self.root/'profiles.sqlite')
        self.assertEqual(self.store.state_get(self.p['dog_id']),(edited,5))
        self.assertEqual(self.old['geometry'],{k:v for k,v in self.s['geometry'].items() if k in self.old['geometry']})

    def test_migration_binding_conflicts_and_invalid_combinations(self):
        bad=copy.deepcopy(self.s);bad['migration']['from_state_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'migration source'):self.store.state_save(bad,1,'tampered')
        bad=copy.deepcopy(self.s);bad['source_profile']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'source snapshot'):self.store.state_save(bad,1,'source')
        self.store.state_save(self.s,1,'upgrade')
        with self.assertRaisesRegex(ValueError,'stale'):self.store.state_save(self.s,1,'stale')
        bad=copy.deepcopy(self.s);bad['package']['version']='3'
        with self.assertRaisesRegex(ValueError,'package'):build(bad)
        for g,reason in [({'neck_width':24,'shoulder_width':20},'neck'),
                         ({'foot_spacing':12,'leg_width':13},'feet'),
                         ({'eye_spacing':22,'eye_rx':4,'head_width':32},'eyes'),
                         ({'nose_height':7,'muzzle_height':10},'nose/mouth')]:
            bad=copy.deepcopy(self.s);bad['geometry'].update(g)
            with self.assertRaisesRegex(ValueError,reason):build(bad)

    def test_body_controls_local_face_stable_and_parameter_effects(self):
        face=build(self.s,'B2','face')[2]['rgba_sha256'];a,m,meta=build(self.s)
        for key,value in [('head_drop',8),('neck_width',22),('shoulder_width',30),('haunch_width',32),('foot_spacing',20)]:
            s=copy.deepcopy(self.s);s['geometry'][key]=value
            img,_,result=build(s)
            self.assertNotEqual(result['rgba_sha256'],meta['rgba_sha256'],key)
            self.assertEqual(build(s,'B2','face')[2]['rgba_sha256'],face,key)
            self.assertEqual(result['anchors']['ground'],meta['anchors']['ground'])
        for key,value in [('muzzle_lobe_depth',0),('pupil_percent',75)]:
            s=copy.deepcopy(self.s);s['geometry'][key]=value
            self.assertNotEqual(build(s,'B2','face')[2]['rgba_sha256'],face,key)

    def test_connections_feet_and_sampled_body_boundaries(self):
        for drop in (0,6,10):
            for height in (32,40,42):
                s=copy.deepcopy(self.s);s['geometry'].update(head_drop=drop,body_height=height)
                s['collar_visible']=False
                img,m,meta=build(s)
                for y in range(int(meta['anchors']['chin'][1]),int(meta['anchors']['neck_base'][1])+1):
                    self.assertEqual(img.getpixel((48,y))[3],255)
                self.assertEqual(img.getpixel((48,90))[3],0)
                for side in ('screen_left','screen_right'):
                    point=tuple(round(n) for n in meta['anchors'][side+'_foot_contact'])
                    self.assertEqual(img.getpixel(point)[3],255)
                self.assertEqual(img.getchannel('A').getbbox()[3],92)
                self.assertNotIn('screen_left_leg_seam',m)

    def test_eye_masks_iris_visibility_and_style_geometry(self):
        for view in ('face','full'):
            a,ma,aa=build(self.s,'B2',view);b,mb,bb=build(self.s,'C2',view)
            self.assertEqual(aa['geometry_sha256'],bb['geometry_sha256'])
            self.assertEqual(a.getchannel('A').tobytes(),b.getchannel('A').tobytes())
            self.assertNotEqual(aa['rgba_sha256'],bb['rgba_sha256'])
            self.assertLessEqual(aa['opaque_color_count'],24)
            self.assertEqual(set(a.getchannel('A').get_flattened_data()),{0,255})
        for amount in (0,1,3):
            s=copy.deepcopy(self.s);s['geometry']['left_occlusion']=amount
            _,m,_=build(s)
            exposed=m['screen_left_eye_exposure']
            for name in ('iris','pupil','highlight'):
                self.assertIsNone(ImageChops.subtract(m['screen_left_'+name],exposed).getbbox())
            self.assertIsNotNone(ImageChops.subtract(exposed,m['screen_left_pupil']).getbbox())
            self.assertLessEqual(sum(bool(v) for v in m['screen_left_highlight'].get_flattened_data()),1)
        self.assertEqual(build(self.s,'B2','face')[2]['anchors'],build(self.s)[2]['anchors'])

    def test_coat_regions_remain_effective(self):
        before,_,meta=build(self.s)
        for part in self.s['coat']:
            s=copy.deepcopy(self.s);s['coat'][part]='long'
            _,_,after=build(s)
            self.assertNotEqual(after['rgba_sha256'],meta['rgba_sha256'],part)
            self.assertEqual(after['anchors'],meta['anchors'])

    def test_export_embeds_comparison_and_preserves_failure_atomicity(self):
        out=self.root/'review'
        export(self.s,2,out,self.old)
        page=(out/'index.html').read_text()
        self.assertEqual(page.count('src="data:image/png;base64,'),12)
        self.assertNotIn('src="face-',page)
        self.assertEqual(json.loads((out/'review.json').read_text())['changed_from_v03_defaults'],{'geometry':{},'coat':{},'colors':{}})
        with self.assertRaises(FileExistsError):export(self.s,2,out,self.old)
        bad=copy.deepcopy(self.old);bad['dog_id']='wrong'
        with self.assertRaisesRegex(ValueError,'origin'):export(self.s,2,self.root/'bad',bad)
        self.assertFalse((self.root/'bad').exists())
        self.assertFalse(list(self.root.glob('.nana-export-*')))

    def test_three_isolated_processes_without_image_inputs(self):
        with patch('PIL.Image.open',side_effect=AssertionError('image input')):build(self.s)
        clean=self.root/'clean';clean.mkdir()
        for name in ('maker.py','styles.json','state_v02.py','render_v02.py','state_v03.py','render_v03.py','example.json'):
            shutil.copyfile(ROOT/name,clean/name)
        shutil.copytree(ROOT/'packages',clean/'packages')
        def run(*args):return subprocess.run([sys.executable,*args],cwd=clean,check=True,capture_output=True)
        run('maker.py','--db','p.sqlite','save','example.json','--expected','0','--reason','synthetic')
        run('render_v02.py','--db','p.sqlite','migrate',self.p['dog_id'])
        run('render_v03.py','--db','p.sqlite','migrate',self.p['dog_id'],'--expected','1')
        hashes=[]
        for n in range(3):
            run('render_v03.py','--db','p.sqlite','render',self.p['dog_id'],'--out',str(n))
            hashes.append([json.loads((clean/str(n)/(v+'.json')).read_text())['rgba_sha256'] for v in ('face-B2','face-C2','full-B2','full-C2')])
        self.assertEqual(hashes[0],hashes[1]);self.assertEqual(hashes[1],hashes[2])

if __name__=='__main__':unittest.main()
