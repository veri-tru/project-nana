import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import Image, ImageChops
import muzzle
from appearance_round import export_round, export_template_round, publish_round
from state_v03 import ROOT, StateStore, migrate
from state_v02 import migrate as migrate_v2
from render_v03 import build


class AppearanceRoundTest(unittest.TestCase):
    def test_depth_reverses_with_view_and_front_is_balanced(self):
        def parts(width,depth,turn):
            return muzzle.masks((65,65),(32,30),(width,14),(6,4),depth,turn,
                                lambda p:tuple(round(v) for v in p))
        for width in (18,24):
            exposure=[]
            for depth in (0,.15,.3):
                left,right=parts(width,depth,-.6),parts(width,depth,.6)
                for key in ('muzzle','far_pad','near_pad','bridge','nose','mouth'):
                    self.assertEqual(left[key].transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes(),
                                     right[key].tobytes(),key)
                exposure.append(left['far_pad'].histogram()[255])
                self.assertEqual(left['muzzle'].getbbox()[2]-left['muzzle'].getbbox()[0],width+1)
                front=parts(width,depth,0)
                shade=ImageChops.lighter(front['far_underside'],front['near_underside'])
                for mask in (front['bridge'],front['muzzle'],front['nose'],front['mouth'],shade):
                    self.assertEqual(mask.tobytes(),mask.transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes())
            self.assertGreater(exposure[0],exposure[1])
            self.assertGreater(exposure[1],exposure[2])
        for depth in (0,.15,.3):
            narrow=parts(18,depth,0)
            wide=parts(24,depth,0)
            self.assertEqual(narrow['nose'].tobytes(),wide['nose'].tobytes())
            self.assertGreater(wide['muzzle'].histogram()[255],narrow['muzzle'].histogram()[255])

    def test_nose_only_pixel_changes_cannot_pass_as_cheek_occlusion(self):
        root=Path(self.enterContext(tempfile.TemporaryDirectory()))
        concept={'dog_id':'fixture','revision':1,'photo_observations':['synthetic fixture'],
                 'table_reference':'fixture','design_choice':'projection only',
                 'unknowns':[],'turn':-.55,'projection':[0,.15,.3]}
        def render(depth):
            k=round(depth/.15)
            frame=Image.new('RGBA',(8,8),'#eeeeee')
            frame.putpixel((3+k,3),(30,30,30,255))
            far=Image.new('L',frame.size);far.paste(255,(1,2,6-k,4))
            near=Image.new('L',frame.size);near.paste(255,(1,4,7,6))
            return frame,Image.new('L',frame.size,255),far,near
        with self.assertRaisesRegex(ValueError,'occlusion is indistinguishable'):
            publish_round(concept,root/'failed',render,{})
        self.assertFalse((root/'failed').exists())

    def test_two_dogs_source_bound_projection_without_widening(self):
        directory=self.enterContext(tempfile.TemporaryDirectory())
        root=Path(directory)
        store=StateStore(root/'test.sqlite')
        self.addCleanup(store.close)
        hashes=[]
        for dog,width in [('short-coat-example',18),('long-coat-example',23)]:
            p=json.loads((ROOT/'example.json').read_text())
            p['dog_id']=dog
            p['appearance']['geometry']['muzzle_width']=width
            p['render']['coat_length']='short' if width==18 else 'long'
            store.save(p,0,'synthetic')
            v2=migrate_v2(p,1)
            store.state_save(v2,0,'v2')
            v3=migrate(v2,1)
            store.state_save(v3,1,'v3')
            concept={'dog_id':dog,'revision':2,'photo_observations':['Synthetic geometry fixture'],
                     'table_reference':'Synthetic test; no breed inference',
                     'design_choice':'Change projected nose depth while holding span fixed',
                     'unknowns':['3D anatomy'],'turn':-.5,'projection':[0,.15,.3]}
            before=build(v3)[2]['rgba_sha256']
            export_round(store,concept,root/dog)
            data=json.loads((root/dog/'round.json').read_text(encoding='utf8'))
            hashes.append([r['sha256'] for r in data['candidates']])
            self.assertEqual(data['provenance']['source_profile'],v3['source_profile'])
            self.assertIsNone(data['owner_selection'])
            masks=[build(v3,projection=v,turn=-.5)[1] for v in concept['projection']]
            self.assertEqual(len({m['muzzle'].getbbox()[::2] for m in masks}),1)
            self.assertNotEqual(masks[0]['nose'].tobytes(),masks[-1]['nose'].tobytes())
            deeper=copy.deepcopy(v3)
            deeper['geometry']['muzzle_lobe_depth']=3
            shallower=copy.deepcopy(v3)
            shallower['geometry']['muzzle_lobe_depth']=0
            for value in concept['projection']:
                self.assertNotEqual(build(deeper,projection=value)[0].tobytes(),
                                    build(shallower,projection=value)[0].tobytes())
            self.assertEqual(build(v3)[2]['rgba_sha256'],before)
            invalid=copy.deepcopy(concept);invalid['projection']=[0,.00001,.00002]
            with self.assertRaisesRegex(ValueError,'indistinguishable'):
                export_round(store,invalid,root/'failed')
            self.assertFalse((root/'failed').exists())
            with self.assertRaises(FileExistsError):
                export_round(store,concept,root/dog)
        self.assertNotEqual(hashes[0],hashes[1])

    def test_registered_template_with_shared_fill_and_edge_failure(self):
        root=Path(self.enterContext(tempfile.TemporaryDirectory()))
        Image.new('RGBA',(32,32),'#888888').save(root/'base.png')
        Image.new('L',(32,32),255).save(root/'slot.png')
        package={'dog_id':'fixture','revision':1,'base':'base.png','slot':'slot.png',
                 'center':[15,15],'span':[19,16],'nose_size':[6,4],
                 'colors':{'outline':'#333333','muzzle':'#eeeeee','nose':'#222222',
                           'muzzle_shadow':'#888888','coat':'#888888'}}
        concept={'dog_id':'fixture','revision':1,'photo_observations':['synthetic fixture'],
                 'table_reference':'test fixture','design_choice':'depth only',
                 'unknowns':[],'turn':-.55,'projection':[0,.15,.3]}
        template=root/'template.json'
        template.write_text(json.dumps(package))
        export_template_round(template,concept,root/'valid')
        for y in (-4,1):
            package['center']=[15,y];template.write_text(json.dumps(package))
            with self.assertRaisesRegex(ValueError,'outside the target canvas'):
                export_template_round(template,concept,root/'invalid')
            self.assertFalse((root/'invalid').exists())
