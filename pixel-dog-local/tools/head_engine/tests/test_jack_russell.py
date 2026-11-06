"""Integration: new breed presets consume the reviewed saved meshes."""
import copy
import pickle
import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import engine

class JackRussellIntegrationTests(unittest.TestCase):
    def test_all_jack_presets_resolve_and_load_their_own_reviewed_meshes(self):
        request=engine.read_json(engine.HERE/'examples/jack-russell-working.json')
        base=engine.resolve_profile(request)
        self.assertEqual(base['values']['relative_scale'],.85)
        self.assertEqual(base['values']['geometry_preset'],'jack-russell-B')
        for variant in 'ABC':
            req=copy.deepcopy(request)
            req['individual']['overrides']={'geometry_preset':'jack-russell-'+variant}
            req['individual']['evidence']={'geometry_preset':{'kind':'authored_default','source':'reviewed-jack-study','note':'Test candidate selection; not owner approval.'}}
            resolved=engine.resolve_profile(req);actual=engine.load_model(resolved)
            expected=pickle.loads((engine.ROOT/f'outputs/jack-russell-head-v1/model-{variant}.pkl').read_bytes())['exterior']
            self.assertEqual(actual['breed'],'jack_russell')
            self.assertEqual(actual['metadata']['ear_type'],'forward_button_authored')
            self.assertEqual(set(actual['parts']),set(expected['parts']))
            for part in expected['parts']:
                for array in ('v','f','n','c'):
                    self.assertTrue(np.array_equal(actual['parts'][part][array],expected['parts'][part][array]))

if __name__=='__main__':unittest.main()
