import copy, sys, unittest
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import engine, pixel

class NativePixelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.request=engine.read_json(engine.HERE/'examples/golden-working.json')
        cls.resolved=engine.resolve_profile(cls.request)
        cls.model=engine.load_model(cls.resolved)
        cls.raw,cls.plan=pixel.render_signals(cls.model)
        cls.frames={key:[pixel.style_frame(r,s) for r in cls.raw] for key,s in pixel.STYLES.items()}

    def test_native_contract_and_feature_invariance(self):
        report=pixel.validate_frames(self.frames)
        self.assertEqual(set(report),set(pixel.STYLES))
        for frames in self.frames.values():
            for image in frames:
                self.assertEqual(image.mode,'RGBA')
                self.assertGreater(np.count_nonzero(np.array(image)[:,:,3]),200)
        # P3 changes only P2's outline color, never silhouette, eyes or shading.
        a=np.array(pixel.make_atlas(self.frames['P2-depth']))
        b=np.array(pixel.make_atlas(self.frames['P3-contrast']))
        changed=np.any(a!=b,axis=2)
        self.assertGreater(changed.sum(),0)
        self.assertTrue((a[changed,:3]==pixel.OUTLINE_SOFT).all())
        self.assertTrue((b[changed,:3]==pixel.OUTLINE_DARK).all())

    def test_every_six_x_block_and_native_thumbnail(self):
        board=pixel.comparison(self.frames)
        for i,frames in enumerate(self.frames.values()):
            y=165+i*520
            for j,frame in enumerate(frames):
                expected=Image.new('RGB',(384,384),(248,247,242))
                enlarged=frame.resize((384,384),Image.Resampling.NEAREST)
                expected.paste(enlarged,(0,0),enlarged)
                actual=board.crop((j*480+48,y+38,j*480+432,y+422))
                self.assertTrue(np.array_equal(np.array(actual),np.array(expected)))
                small=Image.new('RGB',(64,64),(248,247,242));small.paste(frame,(0,0),frame)
                actual=board.crop((j*480+208,y+425,j*480+272,y+489))
                self.assertTrue(np.array_equal(np.array(actual),np.array(small)))

    def test_relative_size_changes_without_replacing_geometry(self):
        original={k:p['v'].copy() for k,p in self.model['parts'].items()}
        _,small=pixel.render_signals(self.model,'relative',.85,.4)
        _,large=pixel.render_signals(self.model,'relative',1.15,.4)
        self.assertAlmostEqual(large['pixels_per_model_unit']/small['pixels_per_model_unit'],1.15/.85)
        _,normalized=pixel.render_signals(self.model,'normalized',2.,.4)
        self.assertEqual(normalized['pixels_per_model_unit'],self.plan['pixels_per_model_unit'])
        for key,vertices in original.items():self.assertTrue(np.array_equal(vertices,self.model['parts'][key]['v']))

    def test_overflow_rejected_instead_of_silent_fit(self):
        with self.assertRaisesRegex(ValueError,'exceeds'):
            pixel.render_signals(self.model,'relative',3.,2.)

    def test_visible_features_survive_without_changing_silhouette(self):
        for index,(rgb,mask) in enumerate(self.raw):
            original_nose=(rgb[:,:,2]>=64)&(rgb[:,:,2]<192)&mask
            original_eyes=(rgb[:,:,2]>=192)&mask
            nose,eyes=pixel.feature_masks(rgb,mask)
            self.assertFalse(((nose|eyes)&~mask).any())
            self.assertFalse((nose&eyes).any())
            self.assertTrue((nose[original_nose]).all())
            allowed=original_nose.copy()
            allowed[:,1:]|=original_nose[:,:-1]
            allowed[:,:-1]|=original_nose[:,1:]
            self.assertFalse((nose&~allowed).any())
            if index in (0,4):
                self.assertGreaterEqual(np.ptp(np.where(nose)[1])+1,3)
                self.assertGreaterEqual(nose.sum(),9)
            old_ids,old_count=pixel.label(original_eyes,structure=np.ones((3,3),int))
            new_ids,new_count=pixel.label(eyes,structure=np.ones((3,3),int))
            self.assertEqual(new_count,old_count)
            for component in range(1,old_count+1):
                before=np.array(np.where(old_ids==component)).mean(axis=1)
                after=np.array(np.where(new_ids==component)).mean(axis=1)
                self.assertLessEqual(np.max(abs(after-before)),.75)
            if index==3:self.assertFalse((nose|eyes).any())

    def test_regeneration_matches_saved_atlases(self):
        folder=engine.ROOT/'outputs/golden-pixel-refresh-20261106'
        for key,frames in self.frames.items():
            path=folder/(key+'-atlas.png')
            if not path.exists():self.skipTest('Project artifact not present')
            self.assertTrue(np.array_equal(np.array(pixel.make_atlas(frames)),np.array(Image.open(path))))

if __name__=='__main__':unittest.main()
