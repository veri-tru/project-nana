"""Evidence-gate regression tests. Synthetic bytes are not visual test images."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from tools.dog_engine import head, structure_gate as gate


class StructureGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.status_path = self.root / 'review-status.json'
        self.contract_path = self.root / 'structure-contract.json'
        Image.new('RGB', (32, 32), (100, 120, 140)).save(self.root / 'render.png')
        (self.root / 'model.npz').write_bytes(b'synthetic saved model')
        self.contract = {
            'schema_version': 1, 'scope': gate.SCOPE, 'geometry_kind': 'actual_mesh',
            'models': {'model.npz': head.sha(self.root / 'model.npz')},
            'appearance_reference_artifacts': ['render.png'],
            'view_sets': [{'model': 'model.npz', 'model_sha256': head.sha(self.root / 'model.npz'),
                'views': sorted(gate.REQUIRED_VIEWS), 'frame': 'head_neck_upper_thorax',
                'ears_hidden_diagnostic': True, 'same_mesh_same_camera_crop_comparison': True,
                'artifacts': ['render.png']}],
        }
        self.status = {'schema_version': 1, 'implementer': 'fixture-maker',
            'artifacts': [{'path': 'render.png', 'sha256': head.sha(self.root / 'render.png')}],
            'inputs': {}, 'reviews': {}, 'findings': [], 'history': [],
            'user_decision': 'PENDING', 'delivery': 'READY'}
        row = self.contract['view_sets'][0]
        row['renders'] = []
        row['ears_hidden_renders'] = []
        for index, (view, camera) in enumerate(gate.CAMERAS.items()):
            name = view + '.png'
            Image.new('RGB', (32, 32), (index * 30, 110, 130)).save(self.root / name)
            record = {'view': view, 'model_sha256': row['model_sha256'], 'camera': list(camera),
                      'scale': 2.0, 'center': [16, 16], 'canvas': [32, 32], 'artifact': name}
            record['projection_id'] = gate.projection_id(record)
            row['renders'].append(record)
            if view in ('side', 'back'):
                name = view + '-hidden.png'
                Image.new('RGB', (32, 32), (index * 30, 10, 130)).save(self.root / name)
                row['ears_hidden_renders'].append({**record, 'artifact': name})
        side = next(r for r in row['renders'] if r['view'] == 'side')
        with Image.open(self.root / side['artifact']) as image:
            image.crop((0, 0, 16, 16)).save(self.root / 'side-crop.png')
        row['crop_comparison'] = {'artifact': 'side-crop.png', 'source_artifact': side['artifact'],
            'source_rect': [0, 0, 16, 16], 'model_sha256': row['model_sha256'], 'projection_id': side['projection_id']}
        self.status['artifacts'] = [{'path': p.name, 'sha256': head.sha(p)} for p in sorted(self.root.glob('*.png'))]
        row['artifacts'] = [a['path'] for a in self.status['artifacts']]
        self.refresh()

    def refresh(self, missing_scope_role=None):
        head.write_json(self.contract_path, self.contract)
        self.status['inputs'] = {p: head.sha(self.root / p) for p in ('model.npz', 'structure-contract.json')}
        for role in ('visual', 'technical'):
            v = {'reviewer': 'fixture-' + role, 'status': 'PASS',
                 'artifacts': {item['path']: item['sha256'] for item in self.status['artifacts']},
                 'coverage_complete': True, 'unresolved': {},
                 'structure_review': {'scope': gate.SCOPE, 'contract_sha256': head.sha(self.contract_path),
                                      'checks': {check: 'PASS' for check in gate.REQUIRED_CHECKS}}}
            if role == 'technical':
                v['inputs'] = self.status['inputs']
            if role == missing_scope_role:
                del v['structure_review']
            report = self.root / (role + '.md')
            report.write_text('Synthetic test verdict only.\n<!-- review-verdict: ' + json.dumps(v) + ' -->\n', 'utf-8')
            self.status['reviews'][role] = {**v, 'report': report.name, 'report_sha256': head.sha(report), 'coverage': ['fixture']}
        head.write_json(self.status_path, self.status)

    def errors(self):
        return gate.check(self.status_path, self.contract_path)

    def plan_and_generation(self):
        plan = self.root / 'appearance-plan.json'
        gate.prepare(self.status_path, self.contract_path, plan)
        generation = self.root / 'generation.json'
        head.write_json(generation, {'referenced_image_paths': [str(self.root / 'render.png')]})
        return plan, generation

    def test_complete_current_evidence_can_prepare_inputs_but_not_approve_art(self):
        self.assertEqual(self.errors(), [])
        plan, generation = self.plan_and_generation()
        self.assertEqual(gate.check_art_inputs(plan, generation), [])
        self.assertEqual(head.read_json(plan)['status'], 'STRUCTURE_INPUTS_VERIFIED_ONLY')
        self.assertTrue(gate.check_art_delivery(self.status_path, plan, generation))

    def test_ear_only_pass_cannot_be_promoted(self):
        self.contract['scope'] = 'ears_only'
        self.refresh()
        self.assertTrue(any('ear-only PASS' in error for error in self.errors()))

    def test_partial_reviewer_scope_cannot_be_promoted(self):
        self.refresh(missing_scope_role='visual')
        self.assertTrue(any('visual: full structural scope' in error for error in self.errors()))

    def test_missing_side_view_hidden_ears_or_crop_comparison_blocks(self):
        for key, value, expected in [('views', ['front'], 'all required'),
                ('ears_hidden_diagnostic', False, 'Ears-hidden'),
                ('same_mesh_same_camera_crop_comparison', False, 'crop comparison'),
                ('frame', 'head_only', 'Short neck crop')]:
            old = copy.deepcopy(self.contract['view_sets'][0])
            self.contract['view_sets'][0][key] = value
            self.refresh()
            self.assertTrue(any(expected in error for error in self.errors()))
            self.contract['view_sets'][0] = old

    def test_mixed_model_views_and_imagegen_geometry_block(self):
        self.contract['view_sets'][0]['model_sha256'] = 'different-model'
        self.contract['geometry_kind'] = 'imagegen'
        self.refresh()
        self.assertTrue(any('Mixed/stale' in e for e in self.errors()))
        self.assertTrue(any('same-mesh' in e for e in self.errors()))

    def test_empty_plan_reference_list_does_not_bypass_inputs(self):
        plan, generation = self.plan_and_generation()
        value = head.read_json(plan)
        value['required_structure_images'] = {}
        head.write_json(plan, value)
        head.write_json(generation, {'referenced_image_paths': []})
        errors = gate.check_art_inputs(plan, generation)
        self.assertTrue(any('differ from original' in e for e in errors))
        self.assertTrue(any('Missing/changed' in e for e in errors))

    def test_new_rejection_invalidates_already_prepared_plan(self):
        plan, generation = self.plan_and_generation()
        self.status['user_decision'] = 'REJECTED'
        self.refresh()
        errors = gate.check_art_inputs(plan, generation)
        self.assertTrue(any('Changed structure_status' in e for e in errors))
        self.assertTrue(any('User rejected' in e for e in errors))

    def test_renamed_rejected_image_and_added_artifacts_cannot_evade_history(self):
        digest = self.status['artifacts'][0]['sha256']
        (self.root / 'extra.png').write_bytes(b'new additional artifact')
        self.status['artifacts'].append({'path': 'extra.png', 'sha256': head.sha(self.root / 'extra.png')})
        self.status['history'] = [{'event': 'USER_REJECTED', 'artifacts': {'old-name.png': digest}}]
        self.refresh()
        self.assertTrue(any('Blocked artifact content reused' in e for e in self.errors()))

    def test_new_status_without_history_cannot_reuse_registered_hash(self):
        digest = self.status['artifacts'][0]['sha256']
        with patch.object(gate, 'rejected_hashes', return_value={digest}):
            self.assertTrue(any('Blocked artifact content reused' in e for e in self.errors()))

    def test_boolean_only_crop_claim_is_insufficient(self):
        del self.contract['view_sets'][0]['renders']
        self.refresh()
        self.assertTrue(any('booleans are insufficient' in e for e in self.errors()))

    def test_crop_from_different_camera_or_model_is_blocked(self):
        crop = self.contract['view_sets'][0]['crop_comparison']
        crop['projection_id'] = 'different-camera'
        crop['model_sha256'] = 'different-model'
        self.refresh()
        self.assertTrue(any('same side-view' in e for e in self.errors()))
        self.assertTrue(any('another model' in e for e in self.errors()))

    def test_recropped_or_rescaled_image_is_blocked_even_with_fresh_review_hashes(self):
        Image.new('RGB', (16, 16), (99, 99, 99)).save(self.root / 'side-crop.png')
        for artifact in self.status['artifacts']:
            artifact['sha256'] = head.sha(self.root / artifact['path'])
        self.refresh()
        self.assertTrue(any('not the exact saved full image region' in e for e in self.errors()))

    def test_metadata_only_change_does_not_fake_hidden_ear_pixels(self):
        hidden = self.contract['view_sets'][0]['ears_hidden_renders'][0]
        visible = next(r for r in self.contract['view_sets'][0]['renders'] if r['view'] == hidden['view'])
        info = PngInfo()
        info.add_text('changed-metadata', 'same pixels')
        with Image.open(self.root / visible['artifact']) as image:
            image.save(self.root / hidden['artifact'], pnginfo=info)
        for artifact in self.status['artifacts']:
            artifact['sha256'] = head.sha(self.root / artifact['path'])
        self.refresh()
        self.assertTrue(any('Hidden-ear pixels are identical' in e for e in self.errors()))

    def test_forged_projection_id_does_not_allow_invalid_numeric_center(self):
        row = self.contract['view_sets'][0]
        for record in row['renders'] + row['ears_hidden_renders']:
            record['center'] = 'not coordinates'
            record['projection_id'] = gate.projection_id(record)
        row['crop_comparison']['projection_id'] = next(r for r in row['renders'] if r['view'] == 'side')['projection_id']
        self.refresh()
        self.assertTrue(any('two finite numbers' in e for e in self.errors()))

    def test_final_review_covers_all_actual_photo_and_style_inputs(self):
        plan, generation = self.plan_and_generation()
        photo = self.root / 'photo.png'
        Image.new('RGB', (8, 8), 'red').save(photo)
        head.write_json(generation, {'referenced_image_paths': [str(self.root / 'render.png'), str(photo)]})
        art = self.root / 'art.png'
        Image.new('RGB', (16, 16), 'blue').save(art)
        status = {'schema_version': 1, 'implementer': 'fixture-artist',
            'artifacts': [{'path': art.name, 'sha256': head.sha(art)}],
            'inputs': {p.name: head.sha(p) for p in (plan, generation, self.root / 'render.png', photo)},
            'reviews': {}, 'findings': [], 'history': [], 'user_decision': 'PENDING', 'delivery': 'READY'}
        def write_reviews():
            for role in ('visual', 'technical'):
                v = {'reviewer': 'art-' + role, 'status': 'PASS', 'artifacts': {art.name: head.sha(art)},
                     'coverage_complete': True, 'unresolved': {},
                     'appearance_review': {'scope': gate.SCOPE, 'plan_sha256': head.sha(plan),
                        'checks': {name: 'PASS' for name in gate.REQUIRED_CHECKS}}}
                if role == 'technical':
                    v['inputs'] = status['inputs']
                report = self.root / ('art-' + role + '.md')
                report.write_text('Synthetic fixture\n<!-- review-verdict: ' + json.dumps(v) + ' -->\n', 'utf-8')
                status['reviews'][role] = {**v, 'report': report.name, 'report_sha256': head.sha(report), 'coverage': ['fixture']}
            head.write_json(self.root / 'art-status.json', status)
        write_reviews()
        self.assertEqual(gate.check_art_delivery(self.root / 'art-status.json', plan, generation), [])
        del status['inputs'][photo.name]
        write_reviews()
        self.assertTrue(any('stale actual generation input' in e for e in gate.check_art_delivery(self.root / 'art-status.json', plan, generation)))
        status['inputs'][photo.name] = head.sha(photo)
        write_reviews()
        Image.new('RGB', (8, 8), 'green').save(photo)
        self.assertTrue(any('stale actual generation input' in e for e in gate.check_art_delivery(self.root / 'art-status.json', plan, generation)))

    def test_changed_model_and_reference_are_not_covered_by_old_pass(self):
        plan, generation = self.plan_and_generation()
        (self.root / 'model.npz').write_bytes(b'changed geometry')
        (self.root / 'render.png').write_bytes(b'changed render')
        self.assertTrue(gate.check_art_inputs(plan, generation))

    def test_failed_structure_cannot_write_output_plan(self):
        self.contract['scope'] = 'ears_only'
        self.refresh()
        out = self.root / 'blocked-plan.json'
        with self.assertRaisesRegex(ValueError, 'Appearance work blocked'):
            gate.prepare(self.status_path, self.contract_path, out)
        self.assertFalse(out.exists())

    def test_missing_or_malformed_evidence_fails_closed(self):
        self.contract_path.write_text('{}', 'utf-8')
        self.assertTrue(self.errors())
        self.assertTrue(gate.check_art_inputs(self.root / 'missing.json', self.root / 'missing-generation.json'))


if __name__ == '__main__':
    unittest.main()
