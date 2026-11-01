"""Verify v2 organization against the frozen, previously reviewed v1.3.1 catalog."""
from pathlib import Path
import json,hashlib,sqlite3,sys
sys.stdout.reconfigure(encoding='utf-8')
root=Path(__file__).resolve().parents[1]
read=lambda p:json.loads((root/p).read_text(encoding='utf-8'))
old=read('data/behavior-db/archive/1.3.1/catalog.json')
new=read('data/behavior-db/catalog.json')
audit=read('reviews/behavior-db-2026-10-17/audit.json')
for path,digest in audit['protected_artifact_sha256'].items():
    backup=root/'data/behavior-db/archive/1.3.1'/Path(path).name
    assert hashlib.sha256(backup.read_bytes()).hexdigest()==digest,path
before={r['record_id']:r for r in old['records']};after={r['record_id']:r for r in new['records']}
assert set(before)==set(after)
assert {r['record_id']:json.loads(r['original_json']) for r in new['original_records']}==before
patches={(r['record_id'],r['field_name']):r for r in new['record_changes']}
assert len(patches)==len(new['record_changes'])
changes=[]
for rid,record in before.items():
    for key,value in record.items():
        if after[rid][key]!=value:
            patch=patches[(rid,key)]
            assert json.loads(patch['before_json'])==value
            assert json.loads(patch['after_json'])==after[rid][key]
            changes.append((rid,key))
assert set(changes)==set(patches)
for table in ['sources','raw_reports','positive_assessments','negative_assessments']:
    assert old[table]==new[table],table
neutral={r['record_id']:r for r in new['neutral_assessments']}
assert all(neutral[r['record_id']]==r for r in old['neutral_assessments'] if r['record_id']!='E019')
assert {r['legacy_relation_id']:json.loads(r['original_json']) for r in new['relation_aliases']}=={r['relation_id']:r for r in old['relations']}
expanded={r['relation_id']:r for r in new['v_relations_expanded']}
for old_rel in old['relations']:
    expected=dict(old_rel)
    if expected['related_record_id']:expected['related_behavior_id']=after[expected['related_record_id']]['behavior_id']
    assert expanded[expected['relation_id']]==expected,expected['relation_id']
assert len(new['relations'])==43 and len(expanded)==83
assert all(r['relation_type']!='previous' for r in new['relations'])
for key in ['duration_s','latency_s','repeat_count','subject_key']:
    assert all(r[key] is None for r in new['records'])
organized={r['record_id']:r for r in new['v_organized_records']}
assert organized['E017']['concept_id']==organized['E018']['concept_id']=='REST'
facets={(r['record_id'],r['facet_key']):r['value_text'] for r in new['record_facets']}
assert facets['E017','머리_지지']=='목으로 유지' and facets['E018','머리_지지']=='외부 지지'
assert facets['E171','뒷다리_배치']=='뻗음' and organized['E171']['concept_id']=='LIE'
assert after['E019']['claim_type']=='literature_mention' and after['E019']['inclusion_status']=='insufficient_detail'
assert after['C_KQ01_01']['situation_id']=='S_WALK_CUE'
assert all(after[f'E{i}']['situation_id']=='S_WALK' for i in range(150,155))
assert after['C_KQ03_03']['behavior_id']=='SELF_LICK' and after['C_KQ03_03']['inclusion_status']=='health_context_excluded'
assert organized['E070']['concept_kind']==organized['E071']['concept_kind']=='aggregate_behavior'
for a,b in [('P017','P019'),('P023','P025'),('P036','P038')]:
    steps=[r for r in new['sequence_steps'] if r['record_id'] in (a,b)]
    assert len(steps)==2 and steps[0]['position']!=steps[1]['position'] and steps[0]['sequence_id']==steps[1]['sequence_id']
assert organized['E183']['unit_id']==organized['E184']['unit_id']
assert len(new['context_assessments'])==146
# A live planning document may evolve after the research DB was frozen.
# Only a version with the exact hash pinned by that DB can satisfy this check.
source_versions=read('data/behavior-db/source-snapshots/index.json')
source_snapshots_used=[]
for r in new['documents']:
    current=root/r['local_file']
    if hashlib.sha256(current.read_bytes()).hexdigest()==r['sha256']:
        continue
    version=source_versions.get(r['local_file'])
    assert version and version['sha256']==r['sha256'],r['local_file']
    snapshot=root/version['snapshot']
    assert hashlib.sha256(snapshot.read_bytes()).hexdigest()==r['sha256'],version['snapshot']
    source_snapshots_used.append({'document':r['local_file'],'snapshot':version['snapshot'],'sha256':r['sha256']})
db=sqlite3.connect((root/'data/behavior-db/nana-behaviors.sqlite').as_uri()+'?mode=ro',uri=True)
assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
assert not db.execute('PRAGMA foreign_key_check').fetchall()
assert db.execute("SELECT count(*) FROM v_evidence_candidates WHERE record_id='E019'").fetchone()[0]==0
db.close()
result={'status':'passed','frozen_artifact_hashes_verified':5,'original_record_ids_preserved':len(before),'changed_records':len({r for r,k in changes}),'field_changes_with_exact_history':len(changes),'all_sources_and_raw_reports_preserved':True,'positive_negative_assessments_preserved':True,'neutral_assessment_corrected_only':'E019','canonical_relations':43,'legacy_relations_exactly_reconstructed_with_current_behavior_codes':83,'sequence_repeat_pairs_preserved':3,'source_document_hashes_match':len(new['documents']),'no_individual_measurements_inferred':True}
result['source_snapshots_used']=source_snapshots_used
report_path=Path(sys.argv[1]) if len(sys.argv)>1 else root/'reviews/behavior-db-2026-10-17/implementation-check.json'
report_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
