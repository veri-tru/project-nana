"""Bounded behavioral tests for profile precedence and reviewed-model rendering."""
import copy
import importlib.util
import json
from pathlib import Path
import pickle
import tempfile
import unittest

import numpy as np

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("head_engine_under_test", HERE / "engine.py")
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


class HeadEngineTests(unittest.TestCase):
    def setUp(self):
        self.request = engine.read_json(HERE / "examples/golden-working.json")

    def test_defaults_select_golden_adult_B_without_approval(self):
        r = engine.resolve_profile(self.request)
        self.assertEqual(r["values"], {"relative_scale": 1.15, "geometry_preset": "golden-adult-B"})
        self.assertEqual(r["selection"], "WORKING_DEFAULT_USER_REVIEW_PENDING")
        self.assertEqual(r["provenance"]["relative_scale"]["layer"], "size_class")
        self.assertEqual(r["provenance"]["geometry_preset"]["layer"], "breed")

    def test_size_class_does_not_choose_face(self):
        resolved = []
        for size in ("small", "medium", "large"):
            request = {**self.request, "size_class": size}
            resolved.append(engine.resolve_profile(request))
        self.assertEqual([r["values"]["relative_scale"] for r in resolved], [0.85, 1.0, 1.15])
        self.assertTrue(all(r["source"] == resolved[0]["source"] for r in resolved))

    def test_individual_overrides_win_and_keep_evidence(self):
        self.request["individual"] = {
            "id": "example", "overrides": {"relative_scale": 0.95, "geometry_preset": "golden-adult-C"},
            "evidence": {key: {"kind": "authored_default", "source": "design-note-01",
                               "note": "Illustrative candidate; not a measured size."}
                         for key in ("relative_scale", "geometry_preset")}}
        r = engine.resolve_profile(self.request)
        self.assertEqual(r["values"]["relative_scale"], 0.95)
        self.assertEqual(r["values"]["geometry_preset"], "golden-adult-C")
        self.assertTrue(all(p["layer"] == "individual" for p in r["provenance"].values()))
        self.assertEqual(r["provenance"]["geometry_preset"]["source"], "design-note-01")

    def test_reject_unknown_keys_at_each_layer(self):
        for layer in (None, "display", "individual"):
            with self.subTest(layer=layer):
                request = copy.deepcopy(self.request)
                target = request if layer is None else request[layer]
                target["face_roundness"] = 2
                with self.assertRaises(ValueError):
                    engine.resolve_profile(request)
        self.request["individual"]["overrides"] = {"skull_width": 8}
        with self.assertRaises(ValueError):
            engine.resolve_profile(self.request)

    def test_reject_missing_or_mislabelled_override_evidence(self):
        self.request["individual"]["overrides"] = {"relative_scale": 1.1}
        with self.assertRaises(ValueError):
            engine.resolve_profile(self.request)
        self.request["individual"]["evidence"] = {
            "relative_scale": {"kind": "measured_cm", "source": "photo", "note": "Unsupported measurement ingestion"}}
        with self.assertRaises(ValueError):
            engine.resolve_profile(self.request)

    def test_reject_invalid_types_and_nonfinite_display(self):
        for value in (True, "3.2", 0, -1, float("nan"), float("inf"), 11):
            with self.subTest(value=value):
                request = copy.deepcopy(self.request)
                request["display"]["scene_scale"] = value
                with self.assertRaises(ValueError):
                    engine.resolve_profile(request)
        for field, value in [("schema_version", True), ("size_class", []), ("breed", "unknown")]:
            with self.subTest(field=field):
                request = copy.deepcopy(self.request)
                request[field] = value
                with self.assertRaises(ValueError):
                    engine.resolve_profile(request)

    def test_cross_breed_geometry_override_is_rejected(self):
        self.request["individual"]["overrides"] = {"geometry_preset": "whippet-v2-B"}
        self.request["individual"]["evidence"] = {
            "geometry_preset": {"kind": "owner_report", "source": "example", "note": "Not a valid golden preset"}}
        with self.assertRaises(ValueError):
            engine.resolve_profile(self.request)

    def test_resolved_tampering_is_rejected(self):
        resolved = engine.resolve_profile(self.request)
        resolved["source"]["selector"] = ["skeleton"]
        with self.assertRaises(ValueError):
            engine.load_model(resolved)

    def test_other_breeds_are_the_original_saved_B_arrays(self):
        path = engine.ROOT / "outputs/skull-based-heads-v2/geometry.pkl"
        before = engine.sha(path)
        originals = pickle.loads(path.read_bytes())["B"]
        for breed in ("whippet", "dachshund", "maltipoo"):
            request = {**self.request, "breed": breed}
            loaded = engine.load_model(engine.resolve_profile(request))
            for part, arrays in originals[breed]["parts"].items():
                for key, value in arrays.items():
                    np.testing.assert_array_equal(loaded["parts"][part][key], value)
        self.assertEqual(engine.sha(path), before)

    def test_actual_golden_projection_uses_exact_reviewed_B(self):
        r = engine.resolve_profile(self.request)
        path = engine.ROOT / "outputs/golden-adult-head-v1/model-B.pkl"
        before = engine.sha(path)
        original = pickle.loads(path.read_bytes())["exterior"]
        loaded = engine.load_model(r)
        renderer = engine.module(engine.ROOT / "outputs/skull-based-heads-v2/build.py", "head_engine_test_renderer")
        for _, az, el in engine.VIEWS:
            expected = renderer.projected(original, az, el)
            actual = renderer.projected(loaded, az, el)
            for a, b in zip(actual, expected):
                np.testing.assert_array_equal(a, b)
        self.assertEqual(engine.sha(path), before)

    def test_normalized_ignores_size_while_relative_consumes_it(self):
        bounds = [[80, 50], [60, 55], [50, 60], [50, 60], [80, 55]]
        normalized = []
        relative = []
        for size in ("small", "large"):
            request = copy.deepcopy(self.request)
            request["size_class"] = size
            r = engine.resolve_profile(request)
            normalized.append(engine.projection_plan(r, bounds))
            request["display"]["mode"] = "relative"
            relative.append(engine.projection_plan(engine.resolve_profile(request), bounds))
        self.assertEqual(normalized[0], normalized[1])
        self.assertEqual(np.max(normalized[0]["projected_bounds_px"]), 320)
        ratio = relative[1]["pixels_per_model_unit"] / relative[0]["pixels_per_model_unit"]
        self.assertAlmostEqual(ratio, 1.15 / 0.85)
        self.assertAlmostEqual(relative[1]["pixels_per_model_unit"], 3.2 * 1.15)

    def test_relative_clipping_fails_instead_of_silent_resizing(self):
        self.request["display"] = {"mode": "relative", "scene_scale": 10}
        r = engine.resolve_profile(self.request)
        with self.assertRaisesRegex(ValueError, "No automatic rescaling"):
            engine.projection_plan(r, [[80, 50]] * 5)

    def test_duplicate_json_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "request.json"
            path.write_text('{"breed":"golden","breed":"whippet"}', "utf-8")
            with self.assertRaises(ValueError):
                engine.read_json(path)

    def test_source_output_is_protected(self):
        with self.assertRaises(ValueError):
            engine.ensure_new_target(engine.ROOT / "outputs/golden-adult-head-v1")
        with self.assertRaises(ValueError):
            engine.ensure_new_target(engine.ROOT / "tools/head_engine")


if __name__ == "__main__":
    unittest.main()
