"""Chest tone cleanup must preserve geometry, features and connected lighting."""
from pathlib import Path
import unittest
import numpy as np

from tools.dog_engine import coat, coat_head, coat_head_geometry as geometry
from tools.dog_engine import coat_native64 as native


class ChestToneRules(unittest.TestCase):
    def test_only_small_enclosed_highlight_is_merged(self):
        shades = np.full((30, 30), 2)
        region = np.zeros(shades.shape, dtype=bool); region[2:28, 2:28] = True
        shades[12:15, 12:15] = 3  # enclosed island
        shades[2:5, 5:8] = 3     # touches throat/material boundary
        shades[0, 20] = 3       # outside chest
        shades[20:22, 20:22] = 1 # isolated shadow
        expected = shades.copy(); expected[12:15, 12:15] = 2; expected[20:22, 20:22] = 2
        np.testing.assert_array_equal(native.chest_tones(shades, region), expected)

    def test_large_highlight_mixed_border_and_frame_edge_are_preserved(self):
        for kind in ('large', 'mixed', 'edge'):
            shades = np.full((20, 20), 2); region = np.ones(shades.shape, dtype=bool)
            if kind == 'large': shades[5:15, 5:15] = 3
            elif kind == 'edge': shades[0:2, 6:8] = 3
            else:
                shades[8:10, 8:10] = 3; shades[7, 8] = 1
            with self.subTest(kind=kind):
                np.testing.assert_array_equal(native.chest_tones(shades, region), shades)

    def test_rules_scale_with_projected_chest_area(self):
        small = np.full((20, 20), 2); small[8:10, 8:10] = 3
        region = np.ones(small.shape, dtype=bool)
        for factor in (1, 3, 8):
            expanded = np.repeat(np.repeat(small, factor, axis=0), factor, axis=1)
            mask = np.repeat(np.repeat(region, factor, axis=0), factor, axis=1)
            self.assertTrue(np.all(native.chest_tones(expanded, mask) == 2))


@unittest.skipUnless((coat.ROOT/'private-data/individual-pair-20261107/neck-reference02/model-B.npz').exists(),
                     'Pinned private source required')
class ActualChestTone(unittest.TestCase):
    def test_all_views_resolutions_and_fullness_preserve_non_tonal_channels(self):
        spec, base = coat_head.registered('maltipoo-neck02-soft-v2')
        source = geometry.load_npz(base/spec['model'])
        semantics = native.source_semantics(source)
        for level in ('flat', 'moderate', 'full'):
            request = coat.read_json(coat.ROOT/f'tools/dog_engine/examples/coat-head-fullness-{level}.json')[0]
            model, _ = coat_head.transform(source, coat.describe(request), spec)
            for size in (64, 480):
                for view, plan in native.camera_plan(source, size).items():
                    with self.subTest(level=level, size=size, view=view):
                        before, ids, depth = native.render(model, semantics, plan, chest_tone_cleanup=False)
                        after, new_ids, new_depth = native.render(model, semantics, plan)
                        a, b = np.asarray(before), np.asarray(after)
                        np.testing.assert_array_equal(ids, new_ids)
                        np.testing.assert_array_equal(depth, new_depth)
                        np.testing.assert_array_equal(a[:, :, 3], b[:, :, 3])
                        region = native.chest_region(plan, depth, ids)
                        np.testing.assert_array_equal(a[~region], b[~region])
                        changed = np.any(a != b, axis=2)
                        if changed.any():
                            self.assertTrue(all(tuple(pixel) in (native.PALETTE[1], native.PALETTE[3]) for pixel in a[changed, :3]))
                            self.assertTrue(np.all(b[changed, :3] == native.PALETTE[2]))
                        if view == 'three_quarter':
                            self.assertEqual(bool(changed.any()), level != 'flat')
                            if level == 'full':
                                # Pinned-camera regression: upper-thorax dark
                                # island straddled y=-25 and survived the first fix.
                                col, row = (330, 271) if size == 480 else (44, 36)
                                self.assertEqual(tuple(a[row, col, :3]), native.PALETTE[1])
                                self.assertEqual(tuple(b[row, col, :3]), native.PALETTE[2])


if __name__ == '__main__':
    unittest.main()
