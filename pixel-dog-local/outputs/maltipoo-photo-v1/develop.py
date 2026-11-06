"""Reuse untouched v2 dogs while iterating Maltipoo; final audit rebuilds all."""
import pickle
import json
import sys
import preview as m

heads,evidence,rigs=m.build(['maltipoo'])
with (m.HERE.parent/'head-neck-volume-v2/geometry.pkl').open('rb') as f:
    saved=pickle.load(f)
saved['heads']['maltipoo']=heads['maltipoo']
saved['rigs']=rigs
ev=evidence['maltipoo']
saved['evidence']['maltipoo']={'jaw':{k:v for k,v in ev['jaw'].items() if k!='field'},'head':ev['head']}
with (m.HERE/'geometry.pkl').open('wb') as f:pickle.dump(saved,f)
(m.HERE/'rigs.json').write_text(json.dumps(rigs,ensure_ascii=False,indent=2),encoding='utf-8')
for name,rows in m.BOARDS.items():
    if '--detail' in sys.argv and name!='maltipoo-detail.png':continue
    m.board(saved['heads'],rows,'머리·턱·목 · 볼륨 재구성').save(m.HERE/name)
    print('Saved',name,flush=True)
