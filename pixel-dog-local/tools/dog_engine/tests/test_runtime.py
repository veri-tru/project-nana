"""Migration checks: real preserved models, pixels, rejection and runtime isolation."""
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.dog_engine import head, pixel, renderer, state


class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.request = head.read_json(ROOT / "tools/head_engine/examples/golden-working.json")
        cls.resolved = head.resolve_profile(cls.request)
        cls.model = head.load_model(cls.resolved)

    def test_all_nine_models_project_identically_to_checkpoint(self):
        old = head.module(ROOT / "outputs/skull-based-heads-v2/build.py", "parity_archive_renderer")
        for preset, spec in head.catalog()["presets"].items():
            request = copy.deepcopy(self.request)
            request["breed"] = spec["breed"]
            request["individual"]["overrides"] = {"geometry_preset": preset}
            request["individual"]["evidence"] = {"geometry_preset": {
                "kind": "authored_default", "source": "regression", "note": "Compare preserved model"}}
            model = head.load_model(head.resolve_profile(request))
            for _, az, el in head.VIEWS:
                with self.subTest(preset=preset, az=az):
                    expected = old.projected(model, az, el)
                    actual = renderer.projected(model, az, el)
                    for a, b in zip(actual, expected):
                        np.testing.assert_array_equal(a, b)

    def test_reference_png_matches_saved_checkpoint_without_archived_imports(self):
        original = head.module
        def guard(path, name):
            self.assertFalse(Path(path).resolve().is_relative_to(ROOT / "outputs"))
            return original(path, name)
        with mock.patch.object(head, "module", side_effect=guard):
            image, _ = head.render_resolved(self.resolved)
        stream = io.BytesIO()
        image.save(stream, format="PNG")
        self.assertEqual(stream.getvalue(), (ROOT / "outputs/golden-pixel-refresh-20261106/engine-reference.png").read_bytes())

    def test_all_native_atlases_match_saved_pixels(self):
        raw, _ = pixel.render_signals(self.model)
        for name, style in pixel.STYLES.items():
            atlas = pixel.make_atlas([pixel.style_frame(frame, style) for frame in raw])
            stream = io.BytesIO()
            atlas.save(stream, format="PNG")
            self.assertEqual(stream.getvalue(), (ROOT / f"outputs/golden-pixel-refresh-20261106/{name}-atlas.png").read_bytes())

    def test_rejected_pixel_export_requires_explicit_diagnostic(self):
        with self.assertRaisesRegex(ValueError, "diagnostic-only"):
            pixel.export("does-not-exist.json", "does-not-exist")

    def test_diagnostic_export_records_blocked_status_and_protects_outputs(self):
        with tempfile.TemporaryDirectory(prefix="runtime-test-", dir=ROOT / "outputs") as tmp:
            folder = Path(tmp)
            resolved_path = folder / "resolved.json"
            head.write_json(resolved_path, self.resolved)
            recipe = pixel.export(resolved_path, folder / "diagnostic", diagnostic=True)
            self.assertEqual(recipe["delivery"], "BLOCKED")
            self.assertEqual(recipe["style_baseline_status"], "USER_REJECTED")
            self.assertEqual(recipe["canonical_style_match"], "NOT_VALIDATED")
            self.assertEqual(recipe["user_selection"], "NOT_REQUESTED_DIAGNOSTIC_ONLY")
            self.assertIn("tools/dog_engine/pixel.py", recipe["runtime_inputs"])
            with self.assertRaisesRegex(ValueError, "overwrite"):
                pixel.export(resolved_path, folder / "diagnostic", diagnostic=True)

    def test_relative_scaling_and_tamper_rejection_are_retained(self):
        request = copy.deepcopy(self.request)
        request["display"]["mode"] = "relative"
        r = head.resolve_profile(request)
        plan = head.projection_plan(r, [[50, 40]] * 5)
        self.assertAlmostEqual(plan["pixels_per_model_unit"], 3.2 * 1.15)
        r["values"]["relative_scale"] = 1.0
        with self.assertRaises(ValueError):
            head.load_model(r)

    def test_runtime_dependency_change_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "inputs.json"
            path.write_text(json.dumps({"tools/dog_engine/renderer.py": "0" * 64}))
            with mock.patch.object(head, "RUNTIME_INPUTS", path):
                with self.assertRaisesRegex(ValueError, "Active renderer dependency changed"):
                    head.load_model(self.resolved)

    def test_state_separates_concept_A_from_geometry_B_and_rejected_pixels(self):
        result = state.current()
        self.assertEqual(result["canonical_head_style"], "breed-head-soft-B2-v1")
        for breed in ("golden", "jack_russell"):
            self.assertEqual(result["concept_selections"][breed]["selected_variant"], "A")
            self.assertTrue(result["geometry_defaults"][breed].endswith("-B"))
        self.assertEqual(result["native64_head"]["delivery"], "BLOCKED")
        self.assertEqual(result["native64_head"]["source_user_decision"], "REJECTED")
        self.assertFalse(result["individual_ears"]["implemented"])

    def test_package_import_does_not_load_any_output_generator(self):
        script = """
import sys
from pathlib import Path
from tools.dog_engine import head, pixel
root=Path.cwd()/'outputs'
assert not any(Path(m.__file__).resolve().is_relative_to(root)
               for m in list(sys.modules.values()) if getattr(m,'__file__',None))
"""
        subprocess.run([sys.executable, "-c", script], cwd=ROOT, check=True)

    def test_config_agrees_with_head_only_style_scope_and_resolution(self):
        config = state.read("config/project.json")
        self.assertEqual(config["art_style"]["selected_head_style_id"], "breed-head-soft-B2-v1")
        self.assertIsNone(config["art_style"]["selected_product_style_id"])
        self.assertEqual(config["animation"]["resolution"]["selected_canvas_px"], [64, 64])
        self.assertEqual(config["art_style"]["native_asset_validation"], "head_native64_style_rejected")


if __name__ == "__main__":
    unittest.main()
