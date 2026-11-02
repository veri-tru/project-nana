import copy
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import maker

class MakerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.p=json.loads((maker.ROOT/'example.json').read_text())
        self.s=maker.Store(self.root/'profiles.sqlite')
    def tearDown(self):
        self.s.close(); self.tmp.cleanup()

    def test_restart_immutable_revision_conflict_and_restore(self):
        self.assertEqual(self.s.save(self.p,0,'initial'),1)
        changed=copy.deepcopy(self.p);changed['appearance']['geometry']['ear_length']=30
        self.assertEqual(self.s.save(changed,1,'ear edit'),2)
        with self.assertRaises(ValueError):self.s.save(self.p,1,'stale client')
        self.assertEqual(self.s.get(self.p['dog_id'],1)[0],self.p)
        with self.assertRaises(sqlite3.IntegrityError):
            with self.s.db:self.s.db.execute('UPDATE revisions SET reason=?',('tamper',))
        self.assertEqual(self.s.rollback(self.p['dog_id'],1,2),3)
        self.s.close();self.s=maker.Store(self.root/'profiles.sqlite')
        self.assertEqual(self.s.get(self.p['dog_id']),(self.p,3))
        self.assertEqual(len(self.s.history(self.p['dog_id'])),3)

    def test_dog_isolation_unknown_and_unsupported(self):
        self.s.save(self.p,0,'a')
        other=copy.deepcopy(self.p);other['dog_id']='another'
        other['behavior']={'habit':None};self.s.save(other,0,'b')
        self.assertIsNone(self.s.get('another')[0]['behavior']['habit'])
        with self.assertRaises(ValueError):self.s.get('missing')
        with self.assertRaises(ValueError):maker.build(self.p,'B2','back')
        other['appearance']['geometry']['eye_radius']=99
        with self.assertRaises(ValueError):self.s.save(other,1,'unsupported')
        self.assertEqual(self.s.get('another')[1],1)

    def test_style_changes_color_only_and_output_contract(self):
        for view in ('face','full'):
            a,ma,aa=maker.build(self.p,'B2',view)
            b,mb,bb=maker.build(self.p,'C2',view)
            self.assertEqual(aa['geometry_sha256'],bb['geometry_sha256'])
            self.assertEqual(a.getchannel('A').tobytes(),b.getchannel('A').tobytes())
            self.assertNotEqual(a.tobytes(),b.tobytes())
            for key in ma:self.assertEqual(ma[key].tobytes(),mb[key].tobytes())
            self.assertEqual(a.size,(96,96))
            self.assertLessEqual(aa['opaque_color_count'],24)
            self.assertEqual(set(a.getchannel('A').get_flattened_data()),{0,255})
            self.assertIn('left_eyelid',ma);self.assertIn('left_front_fur',ma)

    def test_profile_changes_are_effective_and_local(self):
        a,ma,aa=maker.build(self.p)
        p=copy.deepcopy(self.p);p['appearance']['geometry']['left_occlusion']=3
        b,mb,bb=maker.build(p)
        self.assertNotEqual(a.tobytes(),b.tobytes())
        self.assertEqual(ma['right_eye'].tobytes(),mb['right_eye'].tobytes())
        self.assertEqual(ma['body'].tobytes(),mb['body'].tobytes())
        p=copy.deepcopy(self.p);p['appearance']['geometry']['ear_length']=32
        self.assertNotEqual(aa['geometry_sha256'],maker.build(p)[2]['geometry_sha256'])

    def test_no_image_reads_and_three_clean_processes(self):
        with patch('PIL.Image.open',side_effect=AssertionError('source image read')):
            maker.build(self.p)
        for f in ('maker.py','styles.json','example.json'):
            shutil.copyfile(maker.ROOT/f,self.root/f)
        subprocess.run([sys.executable,'maker.py','--db','db.sqlite','save','example.json','--expected','0','--reason','test'],cwd=self.root,check=True,capture_output=True)
        hashes=[]
        for n in range(3):
            subprocess.run([sys.executable,'maker.py','--db','db.sqlite','render',self.p['dog_id'],'--out',str(n)],cwd=self.root,check=True,capture_output=True)
            hashes.append([json.loads((self.root/str(n)/(f+'.json')).read_text())['rgba_sha256'] for f in ('face-B2','face-C2','full-B2','full-C2')])
        self.assertEqual(hashes[0],hashes[1]);self.assertEqual(hashes[1],hashes[2])
        collision=subprocess.run([sys.executable,'maker.py','--db','db.sqlite','render',self.p['dog_id'],'--out','0'],cwd=self.root,capture_output=True)
        self.assertNotEqual(collision.returncode,0)

if __name__=='__main__':unittest.main()
