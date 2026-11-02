import copy
from http.client import HTTPConnection
import json
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from PIL import ImageChops
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import maker
from editor_v02 import make_server
from render_v02 import build, export
from state_v02 import ROOT, StateStore, migrate

class V02Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.db=self.root/'profiles.sqlite';self.store=StateStore(self.db)
        self.p=json.loads((ROOT/'example.json').read_text())
        self.store.save(self.p,0,'fixture');self.s=migrate(self.p,1)
    def tearDown(self):self.store.close();self.tmp.cleanup()

    def test_migration_observations_unchanged_restore_and_restart(self):
        oldhash=maker.build(self.p)[2]['rgba_sha256']
        self.assertEqual(self.store.state_save(self.s,0,'migration'),1)
        changed=copy.deepcopy(self.s);changed['geometry']['ear_length']=26
        self.store.state_save(changed,1,'ears')
        with self.assertRaisesRegex(ValueError,'stale'):self.store.state_save(self.s,1,'conflict')
        self.assertEqual(self.store.state_restore(self.p['dog_id'],1,2),3)
        self.assertEqual(self.store.get(self.p['dog_id']),(self.p,1))
        self.assertEqual(maker.build(self.store.get(self.p['dog_id'])[0])[2]['rgba_sha256'],oldhash)
        with self.assertRaises(sqlite3.IntegrityError):
            with self.store.db:self.store.db.execute("UPDATE render_states SET reason='edited'")
        self.store.close();self.store=StateStore(self.db)
        self.assertEqual(self.store.state_get(self.p['dog_id']),(self.s,3))

    def test_source_dog_and_package_binding(self):
        bad=copy.deepcopy(self.s);bad['source_profile']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'hash mismatch'):self.store.state_save(bad,0,'bad source')
        other=copy.deepcopy(self.p);other['dog_id']='other';self.store.save(other,0,'other')
        bad=copy.deepcopy(self.s);bad['dog_id']='other'
        with self.assertRaisesRegex(ValueError,'hash mismatch'):self.store.state_save(bad,0,'wrong dog')
        bad=copy.deepcopy(self.s);bad['package']['version']='0.9'
        with self.assertRaisesRegex(ValueError,'package'):build(bad)
        bad=copy.deepcopy(self.s);bad['review']['owner']='pass'
        with self.assertRaisesRegex(ValueError,'drafts'):self.store.state_save(bad,0,'approval bypass')

    def test_neck_connection_collar_and_geometry_bounds(self):
        for height in (24,28,32):
            for body in (32,40,42):
                for collar in (False,True):
                    s=copy.deepcopy(self.s);g=s['geometry'];g.update(head_height=height,body_height=body,eye_y=23,muzzle_height=10,nose_height=4)
                    s['collar_visible']=collar
                    img,m,meta=build(s)
                    chin=int(meta['anchors']['chin'][1]);base=int(meta['anchors']['neck_base'][1])
                    for y in range(chin,base+1):self.assertEqual(img.getpixel((48,y))[3],255)
                    self.assertNotIn('screen_left_leg_outline',m)
                    self.assertEqual(img.getchannel('A').getbbox()[3],92)
                    self.assertEqual(meta['anchors']['screen_left_foot_contact'][1],90)

    def test_occlusion_masks_no_leaking_features(self):
        for amount in (0,1,3):
            s=copy.deepcopy(self.s);s['geometry']['left_occlusion']=amount
            _,m,_=build(s)
            visible=m['screen_left_eye_exposure']
            for part in ('iris','pupil','highlight'):
                self.assertIsNone(ImageChops.subtract(m['screen_left_'+part],visible).getbbox())
            self.assertIsNone(ImageChops.multiply(visible,m['screen_left_front_fur']).getbbox())
            self.assertIsNone(ImageChops.multiply(visible,m['screen_left_eyelid']).getbbox())
        original=build(self.s)[1];s=copy.deepcopy(self.s);s['geometry']['left_occlusion']=3
        changed=build(s)[1]
        self.assertEqual(original['screen_right_eye_exposure'].tobytes(),changed['screen_right_eye_exposure'].tobytes())
        self.assertEqual(original['body'].tobytes(),changed['body'].tobytes())
        self.assertNotEqual(original['screen_left_eye_exposure'].tobytes(),changed['screen_left_eye_exposure'].tobytes())

    def test_views_share_landmarks_styles_share_geometry(self):
        for view in ('face','full'):
            a,ma,aa=build(self.s,'B2',view);b,mb,bb=build(self.s,'C2',view)
            self.assertEqual(aa['geometry_sha256'],bb['geometry_sha256'])
            self.assertEqual(a.getchannel('A').tobytes(),b.getchannel('A').tobytes())
            self.assertNotEqual(a.tobytes(),b.tobytes())
            self.assertLessEqual(aa['opaque_color_count'],24)
            self.assertEqual(set(a.getchannel('A').get_flattened_data()),{0,255})
        self.assertEqual(build(self.s,'B2','face')[2]['anchors'],build(self.s,'B2','full')[2]['anchors'])

    def test_supported_coat_regions_change_without_moving_anchors(self):
        a,ma,aa=build(self.s)
        expected={'crown':'crown','ears':'screen_left_ear','cheeks':'screen_left_cheek','chest':'chest','paws':'screen_left_leg'}
        for region,mask in expected.items():
            s=copy.deepcopy(self.s);s['coat'][region]='long'
            b,mb,bb=build(s)
            self.assertEqual(aa['anchors'],bb['anchors'])
            self.assertNotEqual(ma[mask].tobytes(),mb[mask].tobytes(),region)
            self.assertNotEqual(maker.digest(a.tobytes()),maker.digest(b.tobytes()),region)

    def test_incompatible_combinations_and_export_atomicity(self):
        for change,reason in [({'eye_spacing':22,'eye_rx':4,'head_width':32},'eyes too wide'),
                              ({'nose_height':7,'muzzle_height':10},'nose/mouth'),
                              ({'head_width':44,'ear_width':15},'canvas')]:
            bad=copy.deepcopy(self.s);bad['geometry'].update(change)
            with self.assertRaisesRegex(ValueError,reason):export(bad,1,self.root/'bad')
            self.assertFalse((self.root/'bad').exists())
        export(self.s,1,self.root/'good',self.p)
        with self.assertRaises(FileExistsError):export(self.s,1,self.root/'good')
        self.assertFalse(list(self.root.glob('.nana-export-*')))

    def test_clean_process_render_no_image_inputs_and_reproducibility(self):
        with patch('PIL.Image.open',side_effect=AssertionError('image input used')):build(self.s)
        clean=self.root/'clean';clean.mkdir()
        for name in ('maker.py','styles.json','state_v02.py','render_v02.py','example.json'):
            shutil.copyfile(ROOT/name,clean/name)
        shutil.copytree(ROOT/'packages',clean/'packages')
        def run(*args):return subprocess.run([sys.executable,*args],cwd=clean,check=True,capture_output=True)
        run('maker.py','--db','p.sqlite','save','example.json','--expected','0','--reason','fixture')
        run('render_v02.py','--db','p.sqlite','migrate',self.p['dog_id'])
        hashes=[]
        for n in range(3):
            run('render_v02.py','--db','p.sqlite','render',self.p['dog_id'],'--out',str(n))
            hashes.append([json.loads((clean/str(n)/(v+'.json')).read_text())['rgba_sha256'] for v in ('face-B2','face-C2','full-B2','full-C2')])
        self.assertEqual(hashes[0],hashes[1]);self.assertEqual(hashes[1],hashes[2])

    def test_editor_api_preview_save_conflict_restore(self):
        self.store.state_save(self.s,0,'initial')
        server=make_server(str(self.db),self.p['dog_id'],0)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        conn=HTTPConnection('127.0.0.1',server.server_port)
        try:
            conn.request('GET','/');res=conn.getresponse();page=res.read().decode()
            token=re.search("const token='([^']+)'",page).group(1)
            def call(path,payload,session=token):
                conn.request('POST',path,json.dumps(payload),{'Content-Type':'application/json','X-Nana-Session':session})
                r=conn.getresponse();return r.status,json.loads(r.read())
            badstatus,_=call('/api/save',{'state':self.s,'expected':1,'reason':'csrf'},'wrong')
            self.assertEqual(badstatus,403)
            changed=copy.deepcopy(self.s);changed['geometry']['ear_length']=26
            status,result=call('/api/preview',{'state':changed})
            self.assertEqual(status,200);self.assertEqual(len(result['preview']),4)
            status,result=call('/api/save',{'state':changed,'expected':1,'reason':'editor edit'})
            self.assertEqual(status,200);self.assertEqual(result['revision'],2)
            self.assertEqual(call('/api/save',{'state':changed,'expected':1,'reason':'stale'})[0],409)
            status,result=call('/api/restore',{'target':1,'expected':2})
            self.assertEqual(status,200);self.assertEqual(result['state'],self.s)
            self.assertEqual(self.store.get(self.p['dog_id']),(self.p,1))
        finally:conn.close();server.shutdown();thread.join();server.server_close()

if __name__=='__main__':unittest.main()
