"""Real registered geometry through explicit semantic 64px raster and CLI routing."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from tools.dog_engine import coat, coat_head, coat_native64 as native
from tools.dog_engine import coat_head_geometry as geometry

ROOT = coat.ROOT
SOURCE = ROOT/'private-data/individual-pair-20261107/neck-reference02/model-B.npz'


@unittest.skipUnless(SOURCE.exists(), 'Pinned private structural source is required')
class CoatNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = geometry.load_npz(SOURCE)
        cls.semantics = native.source_semantics(cls.source)
        cls.plan = native.camera_plan(cls.source)
        cls.long, _ = geometry.apply_lengths(cls.source, {key:'long' for key in geometry.REGIONS})

    def test_source_face_semantics_separate_ears_eyes_nose(self):
        for part in ('ear_left','ear_right','eye_-1','eye_1'):
            self.assertEqual(set(np.unique(self.semantics[part])), {native.PART_IDS[part]})
        head = self.source['parts']['head']
        nose = np.all(head['c']==[43,40,34], axis=1)
        self.assertTrue(nose.any())
        np.testing.assert_array_equal(self.semantics['head']==native.NOSE_ID, nose[head['f']].sum(axis=1)>=2)

    def test_actual64_all_views_respond_with_same_camera_and_valid_semantics(self):
        for name, camera in self.plan.items():
            with self.subTest(view=name):
                short, sm, _ = native.render(self.source, self.semantics, camera)
                long, lm, _ = native.render(self.long, self.semantics, camera)
                self.assertEqual(short.size, (64,64))
                self.assertNotEqual(short.tobytes(), long.tobytes())
                for image, ids in ((short,sm),(long,lm)):
                    pixels=np.asarray(image)
                    self.assertTrue(set(np.unique(pixels[:,:,3])) <= {0,255})
                    self.assertTrue({tuple(c) for c in pixels[pixels[:,:,3]>0,:3]} <= set(native.PALETTE))
                    self.assertFalse(pixels[0,:,3].any() or pixels[-1,:,3].any() or pixels[:,0,3].any() or pixels[:,-1,3].any())
                    self.assertTrue(set(np.unique(ids)) <= {0,native.NOSE_ID,*native.PART_IDS.values()})
                    np.testing.assert_array_equal(ids>0,pixels[:,:,3]>0)
        self.assertEqual(self.plan,native.camera_plan(self.source))

    def test_unknown_parts_and_labels_fail_closed(self):
        model=deepcopy(self.source)
        model['parts']['extra']=model['parts']['head']
        with self.assertRaisesRegex(ValueError,'semantic'):
            native.source_semantics(model)
        labels=deepcopy(self.semantics)
        labels['ear_left'][:]=native.PART_IDS['eye_-1']
        with self.assertRaisesRegex(ValueError,'semantic'):
            native.render(self.source,labels,self.plan['front'])

    def test_hidden_ears_use_same_projection_and_never_become_eye_ink(self):
        for name in ('side','back'):
            visible,vm,_=native.render(self.long,self.semantics,self.plan[name])
            hidden,hm,_=native.render(self.long,self.semantics,self.plan[name],hide_ears=True)
            self.assertNotEqual(visible.tobytes(),hidden.tobytes())
            self.assertFalse(np.isin(hm,[native.PART_IDS['ear_left'],native.PART_IDS['ear_right']]).any())
            self.assertTrue(np.isin(vm,[native.PART_IDS['ear_left'],native.PART_IDS['ear_right']]).any())

    def test_out_of_frame_does_not_auto_rescale(self):
        bad=deepcopy(self.plan['front']);bad['scale']*=20
        with self.assertRaisesRegex(ValueError,'frame'):
            native.render(self.source,self.semantics,bad)

    def test_native_raster_is_deterministic(self):
        a,mask_a,depth_a=native.render(self.long,self.semantics,self.plan['three_quarter'])
        b,mask_b,depth_b=native.render(self.long,self.semantics,self.plan['three_quarter'])
        self.assertEqual(a.tobytes(),b.tobytes())
        np.testing.assert_array_equal(mask_a,mask_b)
        np.testing.assert_array_equal(depth_a,depth_b)

    def test_top_ears_are_visible_material_regions_not_pale_head_fill(self):
        image,ids,_=native.render(self.long,self.semantics,self.plan['top'])
        rgba=np.asarray(image)
        for part in ('ear_left','ear_right'):
            pixels=rgba[ids==native.PART_IDS[part],:3]
            self.assertGreater(len(pixels),0)
            self.assertFalse(np.all(pixels==native.PALETTE[3],axis=1).any())
            self.assertTrue(np.all(pixels==native.PALETTE[0],axis=1).any())


class CoatHeadRoutingTests(unittest.TestCase):
    def setUp(self):
        self.request=coat.read_json(ROOT/'tools/dog_engine/examples/coat-head-medium.json')[0]

    def test_registered_request_supports_structure_not_style(self):
        plan=coat.describe(self.request)
        self.assertEqual(plan['status'],'STRUCTURE_REVIEW_REQUIRED')
        self.assertEqual(set(plan['applicable_patch']),{'crown','ears','cheeks','chest'})
        self.request['regions']['paws']={'length':'long'}
        self.request['regions']['cheeks']['volume']='full'
        self.assertEqual(coat.describe(self.request)['status'],'UNSUPPORTED')

    def test_v2_supports_separate_volume_patch_and_rejects_ear_fullness(self):
        self.request['model_id']='maltipoo-neck02-soft-v2'
        self.request['target']='head-3d'
        self.request['regions']['crown']['volume']='full'
        plan=coat.describe(self.request)
        self.assertEqual(plan['status'],'STRUCTURE_REVIEW_REQUIRED')
        self.assertEqual(plan['volume_patch'],{'crown':'full'})
        self.assertEqual(plan['geometry_version'],'envelope-v2')
        self.assertEqual(plan['applicable_patch']['cheeks'],'medium')
        self.request['regions']['cheeks']['volume']='full'
        self.assertIn('regions.cheeks.volume',coat.describe(self.request)['unsupported'])
        self.request['regions']['ears']['volume']='full'
        with tempfile.TemporaryDirectory(dir=ROOT/'private-data') as folder:
            request=Path(folder)/'request.json';request.write_bytes(coat.encode(self.request))
            with self.assertRaisesRegex(ValueError,'no partial'):
                coat_head.prepare(request,Path(folder)/'output')
            self.assertFalse((Path(folder)/'output').exists())

    def test_native_crown_fullness_is_rejected_but_3d_remains_supported(self):
        self.request['model_id']='maltipoo-neck02-soft-v2'
        for level in ('flat','moderate','full'):
            with self.subTest(level=level):
                self.request['regions']['crown']['volume']=level
                self.request['target']='head-3d'
                self.assertEqual(coat.describe(self.request)['status'],'STRUCTURE_REVIEW_REQUIRED')
                self.request['target']='native64'
                plan=coat.describe(self.request)
                self.assertIn('regions.crown.volume',plan['unsupported'])
                with tempfile.TemporaryDirectory(dir=ROOT/'private-data') as folder:
                    request=Path(folder)/'request.json';request.write_bytes(coat.encode(self.request))
                    with self.assertRaisesRegex(ValueError,'no partial'):
                        coat_head.prepare(request,Path(folder)/'output')
                    self.assertFalse((Path(folder)/'output').exists())

    def test_missing_unknown_or_mismatched_geometry_version_fails_closed(self):
        registry=coat.read_json(coat_head.REGISTRY)[0]
        for version in (None,'envelope-v99'):
            registry['models'][self.request['model_id']]['geometry_version']=version
            with self.assertRaisesRegex(ValueError,'geometry version'):
                coat.describe(self.request,registry=registry)
            with self.assertRaisesRegex(ValueError,'geometry version'):
                coat_head.registered(self.request['model_id'],registry)
        with self.assertRaisesRegex(ValueError,'version differ'):
            coat_head.transform({}, {'geometry_version':'envelope-v1'}, {'geometry_version':'envelope-v2'})

    def test_prepare_binds_registry_and_catalog_to_same_snapshots(self):
        original=coat_head.dependencies
        for source,message in ((coat_head.REGISTRY,'Registry changed'),(coat.CATALOG,'Catalog changed')):
            with self.subTest(source=source.name):
                def changed_snapshot(*args):
                    inputs=original(*args)
                    inputs[str(source.resolve())]='0'*64
                    return inputs
                with tempfile.TemporaryDirectory(dir=ROOT/'private-data') as folder:
                    request=Path(folder)/'request.json';request.write_bytes(coat.encode(self.request))
                    with patch.object(coat_head,'dependencies',side_effect=changed_snapshot):
                        with self.assertRaisesRegex(ValueError,message):
                            coat_head.prepare(request,Path(folder)/'output')
                    self.assertFalse((Path(folder)/'output').exists())

    def test_v03_route_refuses_3d_request(self):
        with tempfile.TemporaryDirectory() as temp:
            request=Path(temp)/'request.json';request.write_bytes(coat.encode(self.request))
            state=ROOT/'tools/dog_engine/examples/coat-source-state.json'
            with self.assertRaisesRegex(ValueError,'3D targets'):
                coat.apply_file(request,state,coat.digest(state.read_bytes()),Path(temp)/'out')
            self.assertFalse((Path(temp)/'out').exists())

    def test_output_restrictions_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError,'inside project'):
                coat_head.staging_target(Path(temp)/'out')
        with tempfile.TemporaryDirectory(dir=ROOT/'outputs') as temp:
            with self.assertRaisesRegex(ValueError,'overwrite'):
                coat_head.staging_target(temp)


if __name__=='__main__':
    unittest.main()
