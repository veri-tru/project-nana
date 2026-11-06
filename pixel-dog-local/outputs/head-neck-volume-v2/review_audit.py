"""Independent read-only render reproduction and transitive runtime input audit.

Writes only reviewer-prefixed JSON and images under review-reproduction/. The
candidate generator and saved candidate outputs are never overwritten.
"""
import argparse
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import types

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reproduce', action='store_true')
    args = parser.parse_args()
    opened = set()
    active = True

    def observe(event, data):
        if not active or event != 'open' or not isinstance(data[0], (str, bytes)):
            return
        path = Path(os.fsdecode(data[0])).resolve()
        mode, flags = data[1:3]
        if isinstance(mode, str) and any(c in mode for c in 'wax+'):
            return
        if mode is None and flags & (os.O_WRONLY | os.O_RDWR):
            return
        if path.suffix == '.pyc':
            try:
                path = Path(importlib.util.source_from_cache(str(path)))
            except ValueError:
                return
        if path.is_relative_to(ROOT) or path.parent == Path('C:/Windows/Fonts'):
            opened.add(path)

    sys.addaudithook(observe)
    from PIL import ImageFont
    original_font = ImageFont.truetype

    def font(*a, **kw):
        result = original_font(*a, **kw)
        if isinstance(result.path, (str, bytes)):
            opened.add(Path(os.fsdecode(result.path)).resolve())
        return result

    ImageFont.truetype = font
    source = HERE / 'preview.py'
    source_start = digest(source)
    spec = importlib.util.spec_from_file_location('review_volume_candidate', source)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    seen = set()

    def modules(value):
        if not isinstance(value, types.ModuleType) or id(value) in seen:
            return
        seen.add(id(value))
        file = getattr(value, '__file__', None)
        if not file:
            return
        path = Path(file).resolve()
        if not path.is_relative_to(ROOT):
            return
        opened.add(path)
        for child in vars(value).values():
            modules(child)

    modules(m)
    if args.reproduce:
        heads, evidence, rigs = m.build()
    else:
        m.inputs()
        m.model.label(__import__('PIL.Image', fromlist=['Image']).new('RGB', (100, 50)), 0, 0, 'Audit', 12)
        m.model.label(__import__('PIL.Image', fromlist=['Image']).new('RGB', (100, 50)), 0, 0, 'Audit', 12, bold=True)
    results = {}
    if args.reproduce:
        out = HERE / 'review-reproduction'
        out.mkdir(exist_ok=True)
        for name, rows in m.BOARDS.items():
            im = m.board(heads, rows, '머리·턱·목 · 볼륨 재구성')
            buf = io.BytesIO()
            im.save(buf, format='PNG')
            actual = hashlib.sha256(buf.getvalue()).hexdigest()
            target = HERE / name
            results[name] = dict(sha256=actual, candidate_sha256=digest(target), bytes_equal=buf.getvalue() == target.read_bytes(), size=list(im.size))
            (out / name).write_bytes(buf.getvalue())
    active = False
    checks = None
    if args.reproduce:
        cspec = importlib.util.spec_from_file_location('independent_final_checks', HERE / 'review_final_checks.py')
        cm = importlib.util.module_from_spec(cspec)
        cspec.loader.exec_module(cm)
        checks = cm.run(m, heads, evidence, rigs)
    # Candidate output files are comparisons, not generation inputs.
    excluded = {HERE / name for name in m.BOARDS} | {Path(__file__).resolve()}
    inputs = {os.path.relpath(p, HERE).replace('\\', '/'): digest(p) for p in sorted(opened) if p.exists() and p not in excluded and not p.is_relative_to(HERE / 'review-reproduction')}
    report = dict(reviewer='/root/volume_technical_review', mode='reproduce' if args.reproduce else 'input-audit-only', source_unchanged=source_start == digest(source), inputs=inputs, libraries={name: importlib.metadata.version(name) for name in ['numpy', 'scipy', 'scikit-image', 'Pillow', 'numba']}, python=sys.version, images=results, checks=checks)
    path = HERE / ('review-reproduction.json' if args.reproduce else 'review-input-audit.json')
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(report=str(path), inputs=len(inputs), source_unchanged=report['source_unchanged'], images=results), indent=2))


if __name__ == '__main__':
    main()
