"""Read-only catalog audit. Writes review evidence without changing source data."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib, json, re, sqlite3, sys, unicodedata

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reviews/behavior-db-2026-10-17'
sys.stdout.reconfigure(encoding='utf-8')

def duplicates(rows, key, id_key):
    groups=defaultdict(list)
    for row in rows:
        groups[key(row)].append(row[id_key])
    return [ids for ids in groups.values() if len(ids)>1]

def audit():
    OUT.mkdir(parents=True,exist_ok=True)
    catalog=ROOT/'data/behavior-db/catalog.json'
    d=json.loads(catalog.read_text(encoding='utf-8'))
    records=d['records']; nodes=d['behavior_nodes']; relations=d['relations']
    evidence=[r for r in records if r['claim_type'] not in ('design_proposal','user_requirement')]
    candidates=[r for r in evidence if r['inclusion_status']=='candidate']
    proposal=[r for r in records if r['claim_type'] in ('design_proposal','user_requirement')]
    used={r['behavior_id'] for r in records}
    evidence_codes={r['behavior_id'] for r in evidence}
    proposal_codes={r['behavior_id'] for r in proposal}
    annotation_sets=[{r['record_id'] for r in d[t]} for t in ('positive_assessments','negative_assessments','neutral_assessments')]
    con=sqlite3.connect((ROOT/'data/behavior-db/nana-behaviors.sqlite').as_uri()+'?mode=ro',uri=True)
    con.row_factory=sqlite3.Row
    tables=['behavior_nodes','situations','sources','raw_reports','records','relations','findings','positive_assessments','negative_assessments','neutral_assessments']
    for table in tables:
        rows=[dict(r) for r in con.execute(f'SELECT * FROM {table}')]
        assert rows==d[table],table
    integrity=con.execute('PRAGMA integrity_check').fetchone()[0]
    fk=[list(r) for r in con.execute('PRAGMA foreign_key_check')]
    assert integrity=='ok' and not fk
    con.close()
    canonical=set()
    for rel in relations:
        left=rel['record_id']
        right=rel['related_record_id'] or 'behavior:'+rel['related_behavior_id']
        kind=rel['relation_type']
        if kind=='previous':left,right,kind=right,left,'next'
        if kind in ('concurrent','alternative'):left,right=sorted((left,right))
        canonical.add((left,right,kind,rel['basis']))
    source_norm=lambda s:re.sub(r'[^a-z0-9가-힣]','',unicodedata.normalize('NFKC',s['title']).lower())
    fingerprint_paths=['data/behavior-db/catalog.seed.json','data/behavior-db/catalog.json','data/behavior-db/nana-behaviors.sqlite','data/behavior-db/schema.sql','outputs/behavior-db-20261017/behavior-catalog.xlsx']
    result={
      'as_of':'2026-10-17','mode':'review_only_no_catalog_migration',
      'counts':{t:len(d[t]) for t in tables},
      'claim_counts':dict(Counter(r['claim_type'] for r in records)),
      'source_type_counts':dict(Counter(r['source_type'] for r in d['sources'])),
      'behavior_counts':{'recordable_nodes':sum(r['recordable'] for r in nodes),'used_nodes':len(used),'evidence_linked_nodes_including_review_contexts':len(evidence_codes),'candidate_view_nodes':len({r['behavior_id'] for r in candidates}),'proposal_only_nodes':len(proposal_codes-evidence_codes)},
      'exact_payload_duplicate_groups':duplicates(records,lambda r:json.dumps({k:v for k,v in r.items() if k not in ('record_id','created_date')},sort_keys=True,ensure_ascii=False),'record_id'),
      'same_source_behavior_situation_groups':duplicates(records,lambda r:(r['source_id'],r['behavior_id'],r['situation_id']),'record_id'),
      'duplicate_source_urls':duplicates([s for s in d['sources'] if s['url']],lambda s:s['url'],'source_id'),
      'duplicate_normalized_source_titles':duplicates(d['sources'],source_norm,'source_id'),
      'relation_rows_by_type':dict(Counter(r['relation_type'] for r in relations)),
      'relation_rows_by_basis':dict(Counter(r['basis'] for r in relations)),
      'canonical_relation_count':len(canonical),
      'canonical_relations_by_basis':dict(Counter(x[3] for x in canonical)),
      'assessment_rows':sum(len(d[t]) for t in ('positive_assessments','negative_assessments','neutral_assessments')),
      'assessed_unique_records':len(set.union(*annotation_sets)),
      'positive_negative_overlap':sorted(annotation_sets[0]&annotation_sets[1]),
      'records_with_no_context_assessment':len(set(r['record_id'] for r in records)-set.union(*annotation_sets)),
      'unused_recordable_nodes':[n['node_id'] for n in nodes if n['recordable'] and n['node_id'] not in used],
      'proposal_only_nodes':sorted(proposal_codes-evidence_codes),
      'unused_situations':[s['situation_id'] for s in d['situations'] if not any(r['situation_id']==s['situation_id'] for r in records)],
      'sources_with_no_record':[s['source_id'] for s in d['sources'] if not any(r['source_id']==s['source_id'] for r in records)],
      'source_locator_needs_resolution':[r['record_id'] for r in records if re.fullmatch(r'R\d+',r['source_locator'])],
      'sqlite_integrity':integrity,'foreign_key_errors':fk,'sqlite_json_tables_match':tables,
      'protected_artifact_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in fingerprint_paths},
      'limits':['Exact text/title/URL matching does not prove semantic duplication or study independence.','Canonical relations retain evidence basis and record identity, not only behavior codes.','No rows or codes are removed or rewritten by this review.']
    }
    (OUT/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':audit()
