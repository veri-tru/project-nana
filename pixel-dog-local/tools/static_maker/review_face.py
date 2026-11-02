"""Build a portable, read-only face review from a private JSON manifest.

Image bytes are embedded unchanged. A viewport crops/scales display only;
native pixel inspection is separate from equal-head-width comparisons.
This tool cannot approve assets or modify profiles.
"""
import argparse
import base64
import hashlib
import html
import json
import math
from pathlib import Path

from PIL import Image


def build(manifest_path):
    manifest_path = Path(manifest_path).resolve()
    spec = json.loads(manifest_path.read_text())
    assets = {}
    cards = []
    evidence = []
    for entry in spec['images']:
        path = (manifest_path.parent / entry['path']).resolve()
        raw = path.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        with Image.open(path) as im:
            width, height = im.size
            mime = Image.MIME.get(im.format)
            if im.format not in ('PNG', 'JPEG', 'WEBP'):
                raise ValueError('Only static PNG/JPEG/WebP references are supported')
            if getattr(im, 'n_frames', 1) != 1:
                raise ValueError('Animated references require a separate motion review')
        roi = entry['roi']
        if len(roi) != 4 or any(isinstance(v, bool) or not isinstance(v, (int, float))
                                or not math.isfinite(v) for v in roi):
            raise ValueError('roi must be four finite pixel coordinates: x, y, width, height')
        x, y, w, h = roi
        if min(x, y) < 0 or min(w, h) <= 0 or x + w > width or y + h > height:
            raise ValueError('Head display region lies outside the original image')
        native = entry.get('native', False)
        if not isinstance(native, bool):
            raise ValueError('native must be a boolean')
        if native and (im.format != 'PNG' or max(width, height) > 512):
            raise ValueError('Native preview requires a small original PNG, not a generated study')
        assets.setdefault(sha, {'url': 'data:' + mime + ';base64,' + base64.b64encode(raw).decode(),
                                'width': width, 'height': height})
        cards.append({'label': entry['label'], 'role': entry['role'], 'asset': sha,
                      'roi': roi, 'native': native, 'candidate': entry.get('candidate', False)})
        evidence.append({'path': str(path), 'sha256': sha, 'size': [width, height],
                         'display_roi': roi, 'role': entry['role'], 'native': native})
    data = json.dumps({'assets': assets, 'cards': cards}, ensure_ascii=False).replace('<', '\\u003c')
    title = html.escape(spec['title'])
    status = html.escape(spec['status'])
    notes = ''.join('<li>' + html.escape(s) + '</li>' for s in spec['notes'])
    document = '''<!doctype html><html lang="ko"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title><style>
*{box-sizing:border-box}body{margin:0;background:#f5f1e8;color:#322c27;font:15px/1.6 system-ui,sans-serif}
main{max-width:1140px;margin:0 auto;padding:28px 20px 60px}h1{font-size:26px;margin:0 0 8px}h2{font-size:20px;margin-top:34px}
p{max-width:900px}.status{border-left:4px solid #ac6754;padding:10px 14px;background:#fff9ef}
.controls{display:flex;flex-wrap:wrap;align-items:center;gap:14px;margin:18px 0}button,select{font:inherit;padding:5px 10px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:18px}
figure{margin:0;background:#fffcf5;border:1px solid #dfd5c6;border-radius:10px;padding:14px;min-width:0}
figcaption{font-weight:650}small{display:block;font-weight:400;color:#756a5f}
.stage{height:280px;display:flex;align-items:center;justify-content:center;overflow:auto;margin-top:10px;background:#f0e9dc;border-radius:5px}
.stage svg{display:block;flex-shrink:0}.native-stage{min-height:125px;display:flex;align-items:center;justify-content:center;overflow:auto;background:#f0e9dc;margin-top:12px;padding:12px}
.native-stage img{image-rendering:pixelated;flex-shrink:0}body.dark .stage,body.dark .native-stage{background:#393b3b}
li{margin:7px 0}.hint{color:#756a5f;font-size:13px}.hash{font:11px monospace;overflow-wrap:anywhere}
</style><main><h1>__TITLE__</h1><p class="status">__STATUS__</p>
<ul>__NOTES__</ul>
<h2>동일한 머리 폭으로 비교</h2>
<p class="hint">머리 전체가 들어오는 영역을 수동 지정해 같은 폭으로 표시합니다. 사진의 영역은 검토용 근사값이며 해부학적 실측이 아닙니다. 비율은 유지하고 원본 이미지 바이트는 바꾸지 않습니다. 이 보기의 비정수 확대는 픽셀 검사가 아닙니다.</p>
<div class="controls"><label>머리 표시 폭 <select id="headWidth"><option>192</option><option selected>256</option></select> px</label><button id="background" type="button">배경 전환</button></div>
<div class="grid" id="heads"></div>
<h2>새 후보의 실제 원본 격자</h2>
<p class="hint">96×96 원본 전체를 1배 또는 정수 배율로 표시합니다. 실제 제품의 해상도·표시 크기 확정은 아닙니다.</p>
<div class="controls"><label>원본 배율 <select id="nativeScale"><option value="1" selected>1배</option><option value="2">2배</option><option value="4">4배</option></select></label></div>
<div class="grid" id="native"></div>
<p class="hint">이 문서는 읽기 전용 검토본입니다. 자산 승인·프로필 저장·배포 기능은 없습니다.</p>
</main><script id="assets" type="application/json">__DATA__</script><script>
const data=JSON.parse(document.getElementById('assets').textContent),ns='http://www.w3.org/2000/svg';
function figure(card){const f=document.createElement('figure'),c=document.createElement('figcaption'),s=document.createElement('small');
 c.textContent=card.label;s.textContent=card.role;c.append(s);f.append(c);return f;}
function heads(){const target=document.getElementById('heads'),size=Number(document.getElementById('headWidth').value);target.replaceChildren();
 for(const card of data.cards){const a=data.assets[card.asset],f=figure(card),stage=document.createElement('div'),svg=document.createElementNS(ns,'svg'),im=document.createElementNS(ns,'image');
 stage.className='stage';svg.setAttribute('viewBox',card.roi.join(' '));svg.setAttribute('width',size);svg.setAttribute('height',size*card.roi[3]/card.roi[2]);
 svg.setAttribute('role','img');svg.setAttribute('aria-label',card.label);im.setAttribute('href',a.url);im.setAttribute('width',a.width);im.setAttribute('height',a.height);
 if(card.native)im.style.imageRendering='pixelated';svg.append(im);stage.append(svg);f.append(stage);target.append(f);}}
function native(){const target=document.getElementById('native'),scale=Number(document.getElementById('nativeScale').value);target.replaceChildren();
 for(const card of data.cards.filter(c=>c.native&&c.candidate)){const a=data.assets[card.asset],f=figure(card),stage=document.createElement('div'),im=document.createElement('img'),hash=document.createElement('p');
 stage.className='native-stage';im.src=a.url;im.alt=card.label;im.width=a.width*scale;im.height=a.height*scale;stage.append(im);f.append(stage);hash.className='hash';hash.textContent='PNG SHA-256 '+card.asset;f.append(hash);target.append(f);}}
document.getElementById('headWidth').onchange=heads;document.getElementById('nativeScale').onchange=native;
document.getElementById('background').onclick=()=>document.body.classList.toggle('dark');heads();native();
</script></html>'''
    # Replace the JSON placeholder last so ordinary text cannot alter embedded assets.
    for token, value in [('__TITLE__', title), ('__STATUS__', status), ('__NOTES__', notes), ('__DATA__', data)]:
        document = document.replace(token, value)
    return document, evidence


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', help='Private JSON manifest; image paths relative to it')
    parser.add_argument('output', help='New self-contained HTML file; existing files are preserved')
    args = parser.parse_args()
    document, evidence = build(args.manifest)
    with Path(args.output).open('x') as output:
        output.write(document)
    print(json.dumps({'output': str(Path(args.output).resolve()), 'images': len(evidence),
                      'unique_files': len({x['sha256'] for x in evidence}),
                      'html_sha256': hashlib.sha256(document.encode()).hexdigest()}, ensure_ascii=False))
