from pathlib import Path
import json,sys
sys.stdout.reconfigure(encoding="utf-8")
root=Path(__file__).resolve().parents[1]
p=root/"data/behavior-db/catalog.seed.json"
d=json.loads(p.read_text(encoding="utf-8"))
a=json.loads((root/"exa-results/dog-neutral-behavior-2026-10-17/additions.json").read_text(encoding="utf-8"))
assert d["version"]=="1.2.0", "One-time integration already applied or baseline changed"
for key in ["sources","taxonomy","situations","records","relations","findings"]:
 d[key].extend(a[key])
d["neutral_assessments"]=a["neutral_assessments"]
d["version"]=a["version"]
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
# Update active project authority before hashing the source documents.
p=root/"docs/decisions.md"
s=p.read_text(encoding="utf-8")
anchor="| AI 모델 |"
row="| 중립적인 일상 행동 조사 | 사용자 요청 반영 | 긍정·부정 조사와 같은 방식으로 일상 동작을 조사하고 DB에 추가. 중립은 감정가를 미리 부여하지 않는 조사 범위이며 정상성 판정이 아님 | 2026-10-17 사용자 지시, [조사 결과](../exa-results/dog-neutral-behavior-2026-10-17/report.md) |\n"
assert anchor in s
s=s.replace(anchor,row+anchor,1)
p.write_text(s,encoding="utf-8")
print(json.dumps({"new_records":len(a["records"]),"new_sources":len(a["sources"]),"neutral_annotations":len(a["neutral_assessments"])},ensure_ascii=False))

