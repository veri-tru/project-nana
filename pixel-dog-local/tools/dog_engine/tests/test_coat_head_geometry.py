"""Real pinned-source checks; no images or production profiles are written."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest

import numpy as np

from tools.dog_engine import coat_head_geometry as coat, renderer

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "private-data/individual-pair-20261107/neck-reference02/model-B.npz"


@unittest.skipUnless(SOURCE.is_file(), "Private pinned coat source NPZ is not present")
class CoatHeadGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = coat.load_npz(SOURCE)
        cls.source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        cls.long, cls.long_report = coat.apply_lengths(cls.model, dict.fromkeys(coat.REGIONS, "long"))

    def test_short_is_exact_baseline_and_returns_independent_arrays(self):
        candidate, report = coat.apply_lengths(self.model, {})
        for key in coat.PARTS:
            for channel in coat.CHANNELS:
                before, after = self.model["parts"][key][channel], candidate["parts"][key][channel]
                self.assertEqual(before.tobytes(), after.tobytes())
                self.assertFalse(np.shares_memory(before, after))
        self.assertTrue(all(change["changed_vertices"] == 0 for change in report["changes"].values()))

    def test_long_keeps_topology_pigment_and_input_immutable(self):
        self.assertEqual(coat._array_digest(self.model["parts"]), coat.ARRAY_SHA256)
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(), self.source_hash)
        for key in coat.PARTS:
            for channel in ("f", "c"):
                np.testing.assert_array_equal(self.model["parts"][key][channel], self.long["parts"][key][channel])
        for key in ("eye_-1", "eye_1"):
            for channel in coat.CHANNELS:
                np.testing.assert_array_equal(self.model["parts"][key][channel], self.long["parts"][key][channel])

    def test_nose_eye_neighbors_jaw_throat_and_ear_roots_are_fixed(self):
        _, masks = coat._weights(self.model)
        for name, mask in masks.items():
            self.assertGreater(mask.sum(), 0, name)
            np.testing.assert_array_equal(self.model["parts"]["head"]["v"][mask],
                                          self.long["parts"]["head"]["v"][mask], err_msg=name)
        for key in ("ear_left", "ear_right"):
            before, after = self.model["parts"][key]["v"], self.long["parts"][key]["v"]
            np.testing.assert_array_equal(before[before[:, 1] >= 15], after[before[:, 1] >= 15])
            np.testing.assert_array_equal(before[:, [0, 2]], after[:, [0, 2]])
            self.assertTrue((after[:, 1] <= before[:, 1]).all())

    def test_each_region_changes_only_its_supported_surface_and_is_monotone(self):
        for region in coat.REGIONS:
            with self.subTest(region=region):
                medium, _ = coat.apply_lengths(self.model, {region: "medium"})
                long, _ = coat.apply_lengths(self.model, {region: "long"})
                active = ("ear_left", "ear_right") if region == "ears" else ("head",)
                for key in coat.PARTS:
                    before = self.model["parts"][key]["v"]
                    first = medium["parts"][key]["v"] - before
                    second = long["parts"][key]["v"] - before
                    if key in active:
                        self.assertGreater(float(np.linalg.norm(second, axis=1).max()), .3)
                        np.testing.assert_allclose(second, 2 * first, atol=1e-5, rtol=0)
                    else:
                        np.testing.assert_array_equal(before, long["parts"][key]["v"])

    def test_maximum_combination_has_no_local_face_reversal_or_collapse(self):
        for key in ("head", "ear_left", "ear_right"):
            old, new = self.model["parts"][key], self.long["parts"][key]
            faces = old["f"]
            old_v, new_v = old["v"].astype(float), new["v"].astype(float)
            old_normal = np.cross(old_v[faces[:, 1]] - old_v[faces[:, 0]], old_v[faces[:, 2]] - old_v[faces[:, 0]])
            new_normal = np.cross(new_v[faces[:, 1]] - new_v[faces[:, 0]], new_v[faces[:, 2]] - new_v[faces[:, 0]])
            dot = np.sum(old_normal * new_normal, axis=1)
            self.assertTrue((dot > 0).all(), key)
            self.assertTrue(np.isfinite(new["n"]).all())
            moved = np.any(old["v"] != new["v"], axis=1)
            np.testing.assert_allclose(np.linalg.norm(new["n"][moved], axis=1), 1, atol=1e-6)
            self.assertLessEqual(float(np.linalg.norm(new_v - old_v, axis=1).max()), 4.00001)
        for key in ("ear_left", "ear_right"):
            self.assertGreaterEqual(self.long_report["free_ear_vertex_clearance_after"][key],
                                    self.long_report["free_ear_vertex_clearance_before"][key] - .01)

    def test_combined_lengths_change_actual_projected_positions_in_all_five_views(self):
        for az, el in ((0, 0), (48, 7), (90, 0), (180, 0), (90, 90)):
            with self.subTest(az=az, el=el):
                before, _ = renderer.projected(self.model, az, el)
                after, _ = renderer.projected(self.long, az, el)
                self.assertEqual(before.shape, after.shape)
                self.assertGreater(float(np.abs(after[..., :2] - before[..., :2]).max()), .5)

    def test_unknown_regions_types_and_unpinned_inputs_are_rejected(self):
        for request in ({"body": "long"}, {"crown": "fluffy"}, {"ears": 2}, {"chest": True}, []):
            with self.subTest(request=request), self.assertRaises(ValueError):
                coat.apply_lengths(self.model, request)
        with self.assertRaisesRegex(ValueError, "pinned source"):
            coat.apply_lengths(self.long, {"crown": "long"})
        for mutation in ("breed", "parts", "vertex"):
            changed = copy.deepcopy(self.model)
            if mutation == "breed":
                changed["breed"] = "golden"
            elif mutation == "parts":
                changed["parts"]["unknown"] = changed["parts"]["head"]
            else:
                changed["parts"]["head"]["v"][0, 0] += 1
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                coat.apply_lengths(changed, {})

    def test_load_rejects_unpinned_npz_before_deserializing(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "untrusted.npz"
            path.write_bytes(b"not a model")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                coat.load_npz(path)


if __name__ == "__main__":
    unittest.main()
