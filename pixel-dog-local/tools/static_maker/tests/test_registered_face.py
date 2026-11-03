import sys
import unittest
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from registered_face import draw_face,eye_ink,registration


class RegistrationTest(unittest.TestCase):
    def test_sclera_only_on_vacated_side_and_inside_aperture(self):
        socket=Image.new('L',(9,9))
        ImageDraw.Draw(socket).ellipse((1,1,7,7),fill=255)
        for gaze in (0,-1,1):
            pupil,white=eye_ink(socket.size,socket,3,2,('.#.','###','###','.#.'),gaze)
            self.assertEqual(white.getbbox() is None,gaze==0)
            self.assertIsNone(ImageChops.subtract(ImageChops.lighter(pupil,white),socket).getbbox())
            self.assertIsNone(ImageChops.multiply(pupil,white).getbbox())
            for y in range(9):
                exposed=[x for x in range(9) if white.getpixel((x,y))]
                self.assertLessEqual(len(exposed),1)
                for x in exposed:
                    self.assertTrue(pupil.getpixel((x+gaze,y)))

    def test_similarity_uses_both_eyes(self):
        place=registration([(0,0),(4,0)],[(8,6),(8,14)])
        self.assertEqual(place(4,0),(8,14))
        self.assertEqual(place(1,2),(4,8))

    def test_excessive_fringe_cannot_erase_eye(self):
        body=Image.new('P',(22,22));body.putpalette([c for i in range(256) for c in [i]*3])
        body.info['transparency']=0
        points=[(6,9),(15,10)]
        face=[(2,2),(19,2),(19,18),(2,18)]
        kwargs=dict(body=body,source_eyes=points,grid_eyes=points,contour=face,
                    layers=[(2,face)],outline=1,eyes=[(2,4,5,3)]*2)
        draw_face(fringe=(3,[(3,3),(8,3),(8,5),(3,5)],0),**kwargs)
        with self.assertRaisesRegex(ValueError,'collapses'):
            draw_face(fringe=(3,[(3,3),(8,3),(8,5),(3,5)],8),**kwargs)
