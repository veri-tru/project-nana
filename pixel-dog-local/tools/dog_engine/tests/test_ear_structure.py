"""Structural regression checks beyond output labels or file existence."""
import copy
import unittest

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

from tools.dog_engine import ear_structure as ears, pixel


class EarStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original, cls.base = ears.build_base()
        cls.models = {name: ears.with_ears(cls.base, name) for name in ears.VARIANTS}

    def test_no_legacy_fused_skin_and_ear_hiding_preserves_complete_head(self):
        for model in self.models.values():
            self.assertEqual(set(model['parts']), {'head', 'ear_left', 'ear_right', 'eye_-1', 'eye_1'})
            for _, az, el in ears.VIEWS:
                for a, b in zip(ears.project(model, az, el, show_ears=False), ears.project(self.base, az, el)):
                    np.testing.assert_array_equal(a, b)
                self.assertGreater(len(ears.project(model, az, el)[0]), len(ears.project(self.base, az, el)[0]))

    def test_variant_changes_do_not_move_head_eyes_or_root(self):
        for model in self.models.values():
            for name in self.base['parts']:
                for channel in ('v', 'f', 'n', 'c'):
                    np.testing.assert_array_equal(model['parts'][name][channel], self.base['parts'][name][channel])
        # The field above y=15 is unaffected by the lower-ear drop controls.
        q = np.array([[-17, 18, 34], [-16, 27, 27], [-18, 31, 23]], float)
        for value in (-1, 1):
            np.testing.assert_allclose(ears.ear_field(1, value)(q), ears.ear_field(1, 0)(q), atol=1e-10)
        self.assertLess(self.models['A']['parts']['ear_left']['v'][:, 1].min(),
                        self.models['C']['parts']['ear_left']['v'][:, 1].min())

    def test_all_parts_are_closed_connected_surfaces(self):
        for model in self.models.values():
            for part in model['parts'].values():
                v, f = part['v'], part['f']
                edges = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
                _, counts = np.unique(np.sort(edges, axis=1), axis=0, return_counts=True)
                self.assertTrue(np.all(counts == 2))
                self.assertTrue(np.isfinite(v).all())
                area = np.linalg.norm(np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]), axis=1)
                # Marching cubes can produce tiny but nonzero pole triangles.
                self.assertTrue(np.all(area > 1e-12))
                adjacency = coo_matrix((np.ones(len(edges)), (edges[:, 0], edges[:, 1])), shape=(len(v), len(v)))
                self.assertEqual(connected_components(adjacency, directed=False, return_labels=False), 1)
                # Each connected closed part is genus zero (no seam holes).
                self.assertEqual(len(v) - len(counts) + len(f), 2)

    def test_ear_field_support_and_free_lower_surface(self):
        field, _ = ears.head_fields(self.base['metadata'])
        for model in self.models.values():
            for key in ears.EAR_KEYS:
                vertices = model['parts'][key]['v']
                residual = field(vertices)
                self.assertGreater(float(residual[vertices[:, 1] < 20].min()), 0)
                self.assertTrue((residual < 0).any(), 'Detached ear has no root attachment')
                self.assertGreater(vertices[residual < 0, 1].min(), 20)

    def test_native_pixel_does_not_treat_new_ear_parts_as_eyes(self):
        for model in self.models.values():
            with self.assertRaisesRegex(ValueError, 'explicit semantic mapping required'):
                pixel.render_signals(model)

    def test_projection_does_not_recolor_source_models(self):
        model = self.models['B']
        before = copy.deepcopy(model)
        ears.project(model, 48, 7, uniform=True)
        ears.project(model, 48, 7, semantic=True)
        for part in model['parts']:
            for channel in ('v', 'f', 'n', 'c'):
                np.testing.assert_array_equal(before['parts'][part][channel], model['parts'][part][channel])


if __name__ == '__main__':
    unittest.main()
