"""Coat adapter boundaries, real v03 pixel effects, and non-destructive CLI."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools/static_maker'))
from tools.dog_engine import coat
import state_v02
import state_v03
from coat_bridge import prepare


class CoatTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.request = coat.read_json(ROOT / 'tools/dog_engine/examples/coat-lengths.json')[0]
        self.profile = coat.read_json(ROOT / 'tools/static_maker/example.json')[0]
        self.state = state_v03.migrate(state_v02.migrate(self.profile, 1), 1)
        self.state_path = self.folder / 'state.json'
        self.state_path.write_bytes(coat.encode(self.state))
        self.request_path = self.folder / 'request.json'
        self.request_path.write_bytes(coat.encode(self.request))
        self.source_hash = coat.digest(self.state_path.read_bytes())
        self.out = self.folder / 'result'

    def tearDown(self):
        self.temp.cleanup()

    def apply(self):
        return coat.apply_file(self.request_path, self.state_path, self.source_hash, self.out)

    def test_each_supported_region_changes_pixels_without_moving_anchors(self):
        original = deepcopy(self.state)
        for region in coat.SUPPORTED:
            with self.subTest(region=region):
                short = prepare(self.state, {region: 'short'})
                long = prepare(self.state, {region: 'long'})
                self.assertNotEqual(short['validation']['views']['full']['after_rgba_sha256'],
                                    long['validation']['views']['full']['after_rgba_sha256'])
                for view in ('face', 'full'):
                    self.assertTrue(long['validation']['views'][view]['anchors_unchanged'])
                for field in set(self.state) - {'coat'}:
                    self.assertEqual(long['state'][field], self.state[field])
        self.assertEqual(self.state, original)

    def test_apply_is_reproducible_and_preserves_inputs_and_observation_binding(self):
        inputs = (self.state_path.read_bytes(), self.request_path.read_bytes())
        record = self.apply()
        first = (self.out / 'draft-state.json').read_bytes()
        second_out = self.folder / 'result2'
        second = coat.apply_file(self.request_path, self.state_path, self.source_hash, second_out)
        self.assertEqual(first, (second_out / 'draft-state.json').read_bytes())
        self.assertEqual(record, second)
        draft = json.loads(first)
        for field in set(self.state) - {'coat'}:
            self.assertEqual(draft[field], self.state[field])
        self.assertEqual(draft['review'], {'identity':'unreviewed','style':'unreviewed','owner':'unreviewed'})
        self.assertEqual(record['artifacts']['draft-state.json'], coat.digest(first))
        self.assertEqual(record['saved_images'], 0)
        self.assertFalse(record['database_modified'])
        self.assertEqual({p.name for p in self.out.iterdir()}, {'draft-state.json', 'application.json'})
        self.assertEqual(inputs, (self.state_path.read_bytes(), self.request_path.read_bytes()))

    def test_mixed_unsupported_request_never_partially_applies(self):
        request = coat.read_json(ROOT / 'tools/dog_engine/examples/coat-unsupported.json')[0]
        plan = coat.describe(request)
        self.assertEqual(plan['status'], 'UNSUPPORTED')
        self.assertEqual(plan['applicable_patch'], {'ears': 'long'})
        self.assertEqual(set(plan['unsupported']), {'regions.cheeks.volume', 'regions.body.length_mm', 'texture', 'grooming'})
        self.request_path.write_bytes(coat.encode(request))
        with self.assertRaisesRegex(ValueError, 'No partial'):
            self.apply()
        self.assertFalse(self.out.exists())

    def test_unsupported_axes_and_targets_are_explicit(self):
        for region in ('body', 'neck', 'muzzle', 'tail', 'left_ear', 'right_ear', 'legs'):
            request = deepcopy(self.request)
            request['regions'] = {region: {'length':'short'}}
            self.assertEqual(coat.describe(request)['status'], 'UNSUPPORTED')
        for target in ('head-3d', 'native64'):
            request = deepcopy(self.request)
            request['target'] = target
            self.assertEqual(coat.describe(request)['applicable_patch'], {})
        request = deepcopy(self.request)
        request['coat_layers'] = 'double'
        self.assertIn('coat_layers', coat.describe(request)['unsupported'])

    def test_invalid_types_unknown_keys_and_empty_requests_fail(self):
        edits = [dict(schema_version=True), dict(schema_version=2), dict(dog_id='../dog'),
                 dict(regions={}), dict(regions={'ears':{}}), dict(regions={'ears':{'length':None}}),
                 dict(regions={'ears':{'length':True}}), dict(regions={'ears':{'length':'extra'}}),
                 dict(regions={'ears':{'length_mm':True}}), dict(regions={'ears':{'length_mm':float('inf')}}),
                 dict(regions={'ears':{'density':'high'}}), dict(texture=[]), dict(grooming=''),
                 dict(reference_ids=['bad']), dict(reference_ids=[{}]), dict(unknown='ignored')]
        for edit in edits:
            with self.subTest(edit=edit):
                request = {**deepcopy(self.request), **edit}
                with self.assertRaises(ValueError):
                    coat.describe(request)

    def test_duplicate_keys_and_nonfinite_json_fail(self):
        for raw in ('{"schema_version":1,"schema_version":2}', '{"x":NaN}', '{"x":Infinity}'):
            self.request_path.write_text(raw)
            with self.assertRaises(ValueError):
                coat.read_json(self.request_path)

    def test_cross_dog_stale_hash_and_package_fail_before_output(self):
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            coat.apply_file(self.request_path, self.state_path, '0'*64, self.out)
        self.request['dog_id'] = 'another-dog'
        self.request_path.write_bytes(coat.encode(self.request))
        with self.assertRaisesRegex(ValueError, 'dog_id differ'):
            self.apply()
        self.request['dog_id'] = self.state['dog_id']
        self.request_path.write_bytes(coat.encode(self.request))
        self.state['package']['version'] = 'old'
        self.state_path.write_bytes(coat.encode(self.state))
        self.source_hash = coat.digest(self.state_path.read_bytes())
        with self.assertRaisesRegex(ValueError, 'package'):
            self.apply()
        self.assertFalse(self.out.exists())

    def test_output_and_existing_review_are_protected(self):
        self.out.mkdir()
        marker = self.out / 'keep.txt'
        marker.write_text('keep')
        with self.assertRaisesRegex(ValueError, 'overwrite'):
            self.apply()
        self.assertEqual(marker.read_text(), 'keep')
        (self.folder / 'review-status.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'reviewed artifact'):
            coat.apply_file(self.request_path, self.state_path, self.source_hash, self.folder / 'new')

    def test_late_input_change_leaves_no_partial_output(self):
        run = coat.subprocess.run
        def change_after_worker(*args, **kwargs):
            result = run(*args, **kwargs)
            self.state_path.write_bytes(self.state_path.read_bytes() + b' ')
            return result
        with patch.object(coat.subprocess, 'run', side_effect=change_after_worker):
            with self.assertRaisesRegex(ValueError, 'Input changed'):
                self.apply()
        self.assertFalse(self.out.exists())
        self.assertEqual(list(self.folder.glob('.coat-draft-*')), [])

    def test_reference_ids_are_annotations_not_render_presets(self):
        catalog = coat.read_json(coat.CATALOG)[0]
        self.request['reference_ids'] = [catalog['references'][0]['id']]
        plan = coat.describe(self.request)
        self.assertEqual(plan['applicable_patch'], {'crown':'short', 'ears':'long', 'cheeks':'medium'})
        self.request['reference_ids'] *= 2
        with self.assertRaises(ValueError):
            coat.describe(self.request)

    def test_cli_describe_and_apply_exit_codes(self):
        def cli(*args):
            return subprocess.run([sys.executable, '-m', 'tools.dog_engine', 'coat', *args],
                                  cwd=ROOT, capture_output=True,
                                  env={**os.environ, 'PYTHONIOENCODING':'utf-8'})
        result = cli('describe', '--request', str(self.request_path))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'SUPPORTED_DRAFT_ONLY')
        result = cli('describe', '--request', 'tools/dog_engine/examples/coat-unsupported.json')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['status'], 'UNSUPPORTED')
        result = cli('apply', '--request', str(self.request_path), '--state', str(self.state_path),
                     '--expected-state-sha256', self.source_hash, '--out', str(self.out))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.out / 'draft-state.json').is_file())


if __name__ == '__main__':
    unittest.main()
