"""Pinned-mesh coverage of independent length/fullness and protected anatomy."""
import hashlib
from itertools import product
from pathlib import Path
import unittest

import numpy as np

from tools.dog_engine import coat_head_geometry as v1
from tools.dog_engine import coat_head_geometry_v2 as coat
from tools.dog_engine import coat_native64
from tools.dog_engine import renderer

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "private-data/individual-pair-20261107/neck-reference02/model-B.npz"
V1_SHA256 = "cf56bcc3d557a3b84d7a0217b363e45780999f9f07f987b46a1b5942066fd760"


@unittest.skipUnless(SOURCE.is_file(), "Private pinned coat source NPZ is not present")
class CoatHeadGeometryV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = coat.load_npz(SOURCE)
        cls.maximum, cls.maximum_report = coat.apply_preferences(
            cls.base, dict.fromkeys(coat.LENGTH_REGIONS, "long"), dict.fromkeys(coat.VOLUME_REGIONS, "full"))

    def test_v1_and_source_remain_byte_identical_and_baseline_round_trips(self):
        self.assertEqual(hashlib.sha256(Path(v1.__file__).read_bytes()).hexdigest(), V1_SHA256)
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(), coat.SOURCE_SHA256)
        candidate, report = coat.apply_preferences(self.base, {}, {})
        self.assertEqual(v1._array_digest(candidate["parts"]), coat.ARRAY_SHA256)
        self.assertEqual(report["geometry_version"], "envelope-v2")
        for key in coat.PARTS:
            for channel in coat.CHANNELS:
                self.assertFalse(np.shares_memory(self.base["parts"][key][channel], candidate["parts"][key][channel]))

    def test_all_nine_length_fullness_pairs_per_region_have_bounded_valid_geometry(self):
        for region, length, volume in product(coat.VOLUME_REGIONS, coat.LENGTH_LEVELS, coat.VOLUME_LEVELS):
            with self.subTest(region=region, length=length, volume=volume):
                candidate, report = coat.apply_preferences(self.base, {region: length}, {region: volume})
                changed = report["changes"]["head"]
                if length == "short" and volume == "flat":
                    self.assertEqual(changed["changed_vertices"], 0)
                else:
                    self.assertGreater(changed["changed_vertices"], 0)
                    self.assertGreaterEqual(changed["min_face_orientation_cosine"], .8)
                    self.assertGreaterEqual(changed["min_face_area_ratio"], .5)
                    self.assertLessEqual(changed["max_face_area_ratio"], 2)
                for key in ("eye_-1", "eye_1", "ear_left", "ear_right"):
                    np.testing.assert_array_equal(candidate["parts"][key]["v"], self.base["parts"][key]["v"])

    def test_common_nine_pairs_and_mixed_extremes_are_supported(self):
        for length, volume in product(coat.LENGTH_LEVELS, coat.VOLUME_LEVELS):
            with self.subTest(length=length, volume=volume):
                coat.apply_preferences(self.base, dict.fromkeys(coat.LENGTH_REGIONS, length),
                                       dict.fromkeys(coat.VOLUME_REGIONS, volume))
        for seed in range(3):
            lengths = {key: coat.LENGTH_LEVELS[(index + seed) % 3] for index, key in enumerate(coat.LENGTH_REGIONS)}
            volumes = {key: coat.VOLUME_LEVELS[(2 - index + seed) % 3] for index, key in enumerate(coat.VOLUME_REGIONS)}
            coat.apply_preferences(self.base, lengths, volumes)

    def test_fullness_is_independent_noncollinear_displacement_not_length_multiplier(self):
        for region in coat.VOLUME_REGIONS:
            with self.subTest(region=region):
                length_only, _ = coat.apply_preferences(self.base, {region: "long"}, {})
                volume_only, _ = coat.apply_preferences(self.base, {}, {region: "full"})
                combined, _ = coat.apply_preferences(self.base, {region: "long"}, {region: "full"})
                original = self.base["parts"]["head"]["v"]
                length = length_only["parts"]["head"]["v"] - original
                volume = volume_only["parts"]["head"]["v"] - original
                actual = combined["parts"]["head"]["v"] - original
                self.assertGreater(float(np.linalg.norm(length, axis=1).max()), .5)
                self.assertGreater(float(np.linalg.norm(volume, axis=1).max()), .5)
                # Fullness may have a component along hair length (rounded
                # crown), but its complete field must have independent rank.
                a, b = length.astype(float).ravel(), volume.astype(float).ravel()
                residual = b - np.dot(a, b) / np.dot(a, a) * a
                self.assertGreater(float(np.linalg.norm(residual) / np.linalg.norm(b)), .25)
                np.testing.assert_allclose(actual, length + volume, atol=1e-5, rtol=0)

    def test_maximum_preserves_topology_pigment_eyes_nose_roots_and_jawneck(self):
        _, _, _, masks = coat._fields(self.base)
        for name, mask in masks.items():
            self.assertGreater(int(mask.sum()), 0)
            np.testing.assert_array_equal(self.base["parts"]["head"]["v"][mask],
                                          self.maximum["parts"]["head"]["v"][mask], err_msg=name)
        vertices = self.base["parts"]["head"]["v"]
        y = vertices[:, 1]
        complete_jaw_throat_band = (y <= 0) & (y >= -25)
        np.testing.assert_array_equal(vertices[complete_jaw_throat_band],
                                      self.maximum["parts"]["head"]["v"][complete_jaw_throat_band])
        self.assertIn("jaw_throat", self.maximum_report["protection"])
        self.assertNotIn("ventrolateral_cheek_coat_allowed", self.maximum_report["protection_scope"])
        for key in coat.PARTS:
            for channel in ("f", "c"):
                np.testing.assert_array_equal(self.base["parts"][key][channel], self.maximum["parts"][key][channel])
        for key in ("eye_-1", "eye_1"):
            for channel in coat.CHANNELS:
                np.testing.assert_array_equal(self.base["parts"][key][channel], self.maximum["parts"][key][channel])
        for key in ("ear_left", "ear_right"):
            before, after = self.base["parts"][key]["v"], self.maximum["parts"][key]["v"]
            np.testing.assert_array_equal(before[before[:, 1] >= 15], after[before[:, 1] >= 15])
            np.testing.assert_array_equal(before[:, [0, 2]], after[:, [0, 2]])
            self.assertGreaterEqual(self.maximum_report["free_ear_vertex_clearance_after"][key],
                                    self.maximum_report["free_ear_vertex_clearance_before"][key] - .01)
        self.assertEqual(v1._array_digest(self.base["parts"]), coat.ARRAY_SHA256)

    def test_cheek_length_remains_connected_when_cheek_fullness_is_unsupported(self):
        medium, _ = coat.apply_preferences(self.base, {"cheeks": "medium"}, {})
        long, report = coat.apply_preferences(self.base, {"cheeks": "long"}, {})
        original = self.base["parts"]["head"]["v"]
        first = medium["parts"]["head"]["v"] - original
        second = long["parts"]["head"]["v"] - original
        self.assertGreater(float(np.linalg.norm(second, axis=1).max()), 1)
        np.testing.assert_allclose(second, 2 * first, atol=1e-5, rtol=0)
        self.assertEqual(report["lengths"]["cheeks"], "long")
        self.assertNotIn("cheeks", report["volumes"])
        for key in ("eye_-1", "eye_1", "ear_left", "ear_right"):
            np.testing.assert_array_equal(self.base["parts"][key]["v"], long["parts"][key]["v"])
        for level in coat.VOLUME_LEVELS:
            with self.subTest(level=level), self.assertRaisesRegex(ValueError, "Unsupported visible-fullness regions"):
                coat.apply_preferences(self.base, {}, {"cheeks": level})

    def test_chest_fullness_reaches_outer_contour_and_crown_length_has_rounded_falloff(self):
        chest, _ = coat.apply_preferences(self.base, {"chest": "long"}, {"chest": "full"})
        original = self.base["parts"]["head"]["v"]
        self.assertTrue((chest["parts"]["head"]["v"][:, 1] <= original[:, 1]).all())
        x, y, z = original.T
        lateral_outline = (np.abs(z) > 27) & (y < -40) & (y > -60)
        self.assertGreater(int(lateral_outline.sum()), 100)
        increase = np.abs(chest["parts"]["head"]["v"][:, 2]) - np.abs(z)
        self.assertGreater(float(np.median(increase[lateral_outline])), 3)
        crown, _ = coat.apply_preferences(self.base, {"crown": "long"}, {})
        elevation = crown["parts"]["head"]["v"][:, 1] - original[:, 1]
        x, y, z = original.T
        middle = (abs(x + 18) < 1) & (abs(z) < 2) & (y > 38)
        anterior = (abs(x + 30) < 1) & (abs(z) < 2) & (y > 28)
        posterior = (abs(x + 6) < 1) & (abs(z) < 2) & (y > 28)
        self.assertTrue(middle.any() and anterior.any() and posterior.any())
        self.assertGreater(float(elevation[middle].mean()), float(elevation[anterior].mean()) + .3)
        self.assertGreater(float(elevation[middle].mean()), float(elevation[posterior].mean()) + .3)

    def test_fixed_length_fullness_changes_native64_alpha_in_all_five_views(self):
        semantics = coat_native64.source_semantics(self.base)
        plans = coat_native64.camera_plan(self.base)
        models = {}
        for level in coat.VOLUME_LEVELS:
            models[level], _ = coat.apply_preferences(self.base, dict.fromkeys(coat.LENGTH_REGIONS, "long"),
                                                     dict.fromkeys(coat.VOLUME_REGIONS, level))
        for view, plan in plans.items():
            with self.subTest(view=view):
                masks = {level: np.asarray(coat_native64.render(model, semantics, plan)[0])[:, :, 3] > 0
                         for level, model in models.items()}
                for before, after in (("flat", "moderate"), ("moderate", "full")):
                    # Compare silhouette alpha, not RGB/shading differences.
                    self.assertGreaterEqual(int(np.count_nonzero(masks[before] != masks[after])), 8)
                    self.assertGreater(int(masks[after].sum()), int(masks[before].sum()))
                    self.assertFalse(np.any(masks[before] & ~masks[after]))

    def test_each_region_has_native64_front_outline_steps_independent_of_chest(self):
        semantics = coat_native64.source_semantics(self.base)
        plan = coat_native64.camera_plan(self.base)["front"]
        lengths = dict.fromkeys(coat.LENGTH_REGIONS, "long")
        for region in coat.VOLUME_REGIONS:
            with self.subTest(region=region):
                masks = {}
                for level in coat.VOLUME_LEVELS:
                    model, _ = coat.apply_preferences(self.base, lengths, {region: level})
                    masks[level] = np.asarray(coat_native64.render(model, semantics, plan)[0])[:, :, 3] > 0
                for before, after in (("flat", "moderate"), ("moderate", "full")):
                    self.assertGreaterEqual(int(np.count_nonzero(masks[before] != masks[after])), 2)
                    self.assertGreater(int(masks[after].sum()), int(masks[before].sum()))

    def test_normal_transport_is_unit_local_and_exact_for_noop(self):
        for key in ("head", "ear_left", "ear_right"):
            before, after = self.base["parts"][key], self.maximum["parts"][key]
            faces = before["f"]
            changed = np.any(before["v"] != after["v"], axis=1)
            affected = np.unique(faces[changed[faces].any(axis=1)])
            outside = np.ones(len(before["v"]), dtype=bool)
            outside[affected] = False
            self.assertTrue(np.isfinite(after["n"]).all())
            np.testing.assert_allclose(np.linalg.norm(after["n"][affected], axis=1), 1, atol=1e-6)
            np.testing.assert_array_equal(before["n"][outside], after["n"][outside])
            noop = coat._transport_normals(before["v"], before["v"], faces, before["n"])
            self.assertEqual(noop.tobytes(), before["n"].tobytes())
        triangle = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]])
        faces = np.array([[0, 1, 2]])
        normals = np.tile([0., 0., 1.], (3, 1))
        reflected = triangle.copy()
        reflected[:, 0] *= -1
        with self.assertRaisesRegex(ValueError, "Antiparallel"):
            coat._transport_normals(triangle, reflected, faces, normals)

    def test_actual_projection_positions_change_in_all_five_views(self):
        for az, el in ((0, 0), (48, 7), (90, 0), (180, 0), (90, 90)):
            with self.subTest(az=az, el=el):
                before, _ = renderer.projected(self.base, az, el)
                after, _ = renderer.projected(self.maximum, az, el)
                self.assertGreater(float(np.abs(after[..., :2] - before[..., :2]).max()), .5)

    def test_unsupported_preferences_or_chained_model_rejected(self):
        cases = [({"tail": "long"}, {}), ({}, {"ears": "full"}), ({}, {"crown": "dense"}),
                 ({"ears": True}, {}), ({}, {"cheeks": 1}), ([], {}), ({}, None)]
        for lengths, volumes in cases:
            with self.subTest(lengths=lengths, volumes=volumes), self.assertRaises(ValueError):
                coat.apply_preferences(self.base, lengths, volumes)
        with self.assertRaisesRegex(ValueError, "pinned source"):
            coat.apply_preferences(self.maximum, {}, {})


if __name__ == "__main__":
    unittest.main()
