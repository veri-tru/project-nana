"""Isolated v03 validation worker. JSON in/out; no files, DB writes or saved art."""
from copy import deepcopy
import json
import sys

from PIL import __version__ as PIL_VERSION

from render_v03 import build
from state_v03 import COAT_PARTS, validate


def prepare(state, patch):
    validate(state)
    if not isinstance(patch, dict) or not patch or set(patch) - set(COAT_PARTS):
        raise ValueError('Expected a nonempty supported coat patch')
    if any(not isinstance(value, str) or value not in ('short', 'medium', 'long') for value in patch.values()):
        raise ValueError('Unsupported coat length')
    draft = deepcopy(state)
    draft['coat'].update(patch)
    validate(draft)
    checks = {}
    for view in ('face', 'full'):
        before = build(state, 'B2', view)[2]
        after = build(draft, 'B2', view)[2]
        if before['anchors'] != after['anchors'] or before['display_anchors'] != after['display_anchors']:
            raise ValueError('Coat modification changed structural anchors')
        checks[view] = dict(before_rgba_sha256=before['rgba_sha256'],
                            after_rgba_sha256=after['rgba_sha256'],
                            anchors_unchanged=True, canvas_px=after['canvas_px'])
    return dict(state=draft, validation=dict(views=checks, style='B2',
                scope='schema_and_in_memory_render_only', visual_review='NOT_REVIEWED',
                runtime=dict(python=sys.version.split()[0], pillow=PIL_VERSION)))


if __name__ == '__main__':
    try:
        payload = json.load(sys.stdin)
        print(json.dumps(prepare(payload['state'], payload['patch']), ensure_ascii=False, allow_nan=False))
    except (ValueError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
