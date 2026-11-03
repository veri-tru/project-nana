import sys
import unittest
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from face_views import MuzzleProfile, View, projected_head, render_view


class PairedViewsTest(unittest.TestCase):
    def setUp(self):
        self.body=Image.new('RGBA',(64,64))
        self.head=self.body.copy()
        ImageDraw.Draw(self.body).ellipse((10,23,44,46),fill='#706b73')
        ImageDraw.Draw(self.head).ellipse((1,6,33,33),fill='#aba3a2')
        self.pivot=(16,21)
        self.profile=MuzzleProfile((14.5,23,11),18,10,5.4,4.4)
        self.colors=dict(light='#f5efe5',mid='#aba3a2',coat='#706b73',dark='#332c32',outline='#575058')
        self.colors={k:tuple(bytes.fromhex(v[1:]))+(255,) for k,v in self.colors.items()}

    def test_same_profile_two_views(self):
        projected,surface=projected_head(self.head,self.pivot,.61,View(0))
        self.assertEqual(projected.tobytes(),self.head.tobytes())
        self.assertGreater(surface.getpixel(self.pivot),0)
        coverage=[]
        for depth in (4,7,10):
            views=[]
            for cam in [View(0),View(55,10)]:
                im,m,fp=render_view(self.body,self.head,self.pivot,.61,self.profile,depth,cam,self.colors)
                self.assertTrue(m['nose'].getbbox() and m['lip'].getbbox())
                self.assertIsNone(ImageChops.multiply(m['lip'],m['nose'].filter(ImageFilter.MaxFilter(3))).getbbox())
                self.assertLessEqual({p for p in im.getdata() if p[3]},set(self.colors.values()))
                views.append(m)
            self.assertGreater(views[1]['nose'].getbbox()[0],views[0]['nose'].getbbox()[0])
            self.assertLess(views[1]['right'].histogram()[255],views[0]['right'].histogram()[255])
            coverage.append(ImageChops.multiply(fp['right'],views[1]['left']).histogram()[255])
        self.assertTrue(0<coverage[0]<coverage[1]<coverage[2])

    def test_side_fur_adjustment_preserves_front_and_nose(self):
        for view in (View(0),View(55,10,12)):
            frames=[render_view(self.body,self.head,self.pivot,.61,self.profile,4,
                                view,self.colors,side_fur_slope=slope)
                    for slope in (.4,1.1)]
            self.assertEqual(frames[0][0].tobytes()==frames[1][0].tobytes(),view.yaw==0)
            self.assertEqual(frames[0][1]['nose'].getbbox(),frames[1][1]['nose'].getbbox())
