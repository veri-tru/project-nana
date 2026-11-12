"""Current state must reject drift in selections, review evidence and dependencies."""
import copy
import importlib.metadata
import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

from tools.dog_engine import state
from tools.dog_engine.__main__ import main


class StateDriftTests(unittest.TestCase):
    def changed_pair(self, **changes):
        original = state.read

        def read(path):
            data = original(path)
            if path == "config/individual-pair-canonical.json":
                data = copy.deepcopy(data)
                data.update(changes)
            return data

        return mock.patch.object(state, "read", side_effect=read)

    def test_current_state_preserves_selected_pair_and_actual_coat_limits(self):
        from tools.dog_engine.coat_head_geometry_v2 import LENGTH_REGIONS, VOLUME_REGIONS
        result = state.current()
        self.assertEqual(result["individual_pair_canonical"]["status"], "USER_ACCEPTED")
        self.assertEqual(result["individual_pair_canonical"]["selected_variant"], "C")
        spec = result["coat"]["registered_head_models"]["maltipoo-neck02-soft-v2"]
        self.assertEqual(spec["length_regions"], list(LENGTH_REGIONS))
        self.assertEqual(spec["fullness_3d_regions"], list(VOLUME_REGIONS))
        self.assertEqual(spec["fullness_native64_regions"], ["chest"])
        self.assertFalse(result["coat"]["b2_native64_style_approved"])
        self.assertEqual(result["native64_head"]["delivery"], "BLOCKED")

    def test_changed_selected_image_is_not_reported_as_current(self):
        with self.changed_pair(sha256="0" * 64):
            with self.assertRaisesRegex(ValueError, "selection changed"):
                state.current()

    def test_changed_selection_record_is_not_reported_as_current(self):
        with self.changed_pair(selection_sha256="0" * 64):
            with self.assertRaisesRegex(ValueError, "selection changed"):
                state.current()

    def test_metadata_cannot_silently_expand_selected_scope(self):
        with self.changed_pair(scope="Approved native64 and full-body runtime assets"):
            with self.assertRaisesRegex(ValueError, "selection conflicts: scope"):
                state.current()

    def test_invalidated_review_blocks_previously_selected_pair(self):
        with mock.patch("tools.review.check_delivery.check", return_value=["Input hash changed"]):
            with self.assertRaisesRegex(ValueError, "review blocked: Input hash changed"):
                state.current()

    def test_transitive_verification_dependency_drift_fails_doctor(self):
        original = importlib.metadata.version
        with mock.patch("importlib.metadata.version", side_effect=lambda package:
                        "0.0" if package == "imageio" else original(package)):
            result = state.doctor()
        self.assertEqual(result["environment_and_sources"], "FAIL")
        self.assertTrue(any("imageio:" in item for item in result["problems"]))
        self.assertIn("engine.ps1", result["remedy"])

    def test_verify_stops_before_rendering_in_wrong_environment(self):
        with mock.patch.object(state, "doctor", return_value={"problems": ["numpy mismatch"]}), \
                mock.patch("tools.dog_engine.__main__.subprocess.call") as run, \
                redirect_stdout(io.StringIO()):
            self.assertEqual(main(["verify"]), 1)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
