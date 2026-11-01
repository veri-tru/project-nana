"""One-time integration with preservation checks for the all-candidates request."""
from pathlib import Path
import json, sys
from build_behavior_db import build

sys.stdout.reconfigure(encoding='utf-8')
root=Path(__file__).resolve().parents[1]
research=root/'exa-results/dog-additional-behaviors-2026-10-17'
seed_path=root/'data/behavior-db/catalog.seed.json'
catalog_path=root/'data/behavior-db/catalog.json'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
before=read(catalog_path)
seed=read(seed_path)
addition=read(research/'additions.json')
assert seed['version']=='1.3.0', 'One-time integration already applied or baseline changed'
assert len(before['records'])==280
for key in ['sources','taxonomy','situations','records','relations','findings','neutral_assessments']:
    seed[key].extend(addition[key])
for update in addition['source_updates']:
    source=next(s for s in seed['sources'] if s['source_id']==update['source_id'])
    source.update(update['changes'])
seed['version']=addition['version']
seed_path.write_text(json.dumps(seed,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
decision_path=root/'docs/decisions.md'
decision=decision_path.read_text(encoding='utf-8')
anchor='| AI 모델 |'
assert anchor in decision
row='| 추가 행동 전체 포함 | 사용자 요청 반영 | 제안 목록 28항목을 DB에 모두 연결. 새 문헌 근거 18건·기존 보고 1건·근거 확인 대기 9건을 구분하며 실제 발생·고정 순서·구현 완료로 간주하지 않음 | 2026-10-17 사용자 지시 모두 포함, [반영표와 조사 결과](../exa-results/dog-additional-behaviors-2026-10-17/report.md) |\n'
decision_path.write_text(decision.replace(anchor,row+anchor,1),encoding='utf-8')
build()
after=read(catalog_path)
checks={}
keys={'records':'record_id','relations':'relation_id','raw_reports':'report_id','behavior_nodes':'node_id','situations':'situation_id','findings':'finding_id','positive_assessments':'record_id','negative_assessments':'record_id','neutral_assessments':'record_id','field_dictionary':'field_key'}
for table,key in keys.items():
    # The field dictionary has no single stable ID; compare complete original rows.
    if table=='field_dictionary':
        assert before[table]==after[table]
    else:
        new={r[key]:r for r in after[table]}
        assert all(new[r[key]]==r for r in before[table]), table
    checks[table+'_preserved']=len(before[table])
new_sources={r['source_id']:r for r in after['sources']}
allowed={u['source_id']:u['changes'] for u in addition['source_updates']}
for row in before['sources']:
    expected={**row,**allowed.get(row['source_id'],{})}
    assert new_sources[row['source_id']]==expected,row['source_id']
checks['original_sources_verified']=len(before['sources'])
checks['allowed_source_metadata_updates']=addition['source_updates']
record_map={r['record_id']:r for r in after['records']}
assert len(addition['coverage'])==28
for item in addition['coverage']:
    record=record_map[item['record_id']]
    if item['status']=='evidence_pending':
        assert (record['claim_type'],record['occurrence_status'],record['inclusion_status'])==('user_requirement','PROPOSED','proposal_only')
checks['coverage_items_linked']=28
checks['new_records']=len(after['records'])-len(before['records'])
checks['existing_record_reused']='E171'
checks['status']='passed'
(research/'preservation-check.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(checks,ensure_ascii=False,indent=2))
