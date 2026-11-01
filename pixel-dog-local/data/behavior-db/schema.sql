PRAGMA foreign_keys = ON;
CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE behavior_nodes (
 node_id TEXT PRIMARY KEY, parent_id TEXT REFERENCES behavior_nodes(node_id),
 level INTEGER NOT NULL CHECK(level BETWEEN 1 AND 4), name_ko TEXT NOT NULL,
 definition TEXT NOT NULL, recordable INTEGER NOT NULL CHECK(recordable IN(0,1)),
 UNIQUE(parent_id,name_ko)
);
CREATE TABLE situations (situation_id TEXT PRIMARY KEY, name_ko TEXT NOT NULL UNIQUE);
CREATE TABLE documents (document_id TEXT PRIMARY KEY, local_file TEXT NOT NULL UNIQUE, sha256 TEXT NOT NULL, scope TEXT NOT NULL);
CREATE TABLE sources (
 source_id TEXT PRIMARY KEY, source_type TEXT NOT NULL CHECK(source_type IN('literature','community','design_proposal','user_requirement')),
 citation TEXT NOT NULL, title TEXT NOT NULL, url TEXT, year INTEGER, published_date TEXT,
 access_scope TEXT NOT NULL, sample TEXT, local_file TEXT NOT NULL, locator TEXT NOT NULL, verification_note TEXT NOT NULL
);
CREATE UNIQUE INDEX source_url_unique ON sources(url) WHERE url IS NOT NULL;
CREATE TABLE raw_reports (
 report_id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(source_id),
 segment TEXT, context_text TEXT, owner_report TEXT, owner_frequency TEXT,
 original_status TEXT NOT NULL, caveat TEXT, original_json TEXT NOT NULL
);
CREATE TABLE records (
 record_id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(source_id),
 behavior_id TEXT NOT NULL REFERENCES behavior_nodes(node_id), situation_id TEXT NOT NULL REFERENCES situations(situation_id),
 context_text TEXT, trigger_text TEXT, target_text TEXT, body_part TEXT, laterality TEXT, posture_detail TEXT,
 frequency_text TEXT, duration_s REAL CHECK(duration_s>=0), latency_s REAL CHECK(latency_s>=0),
 repeat_count INTEGER CHECK(repeat_count>=0), duration_text TEXT, speed_text TEXT,
 measurement_status TEXT NOT NULL CHECK(measurement_status IN('NOT_REPORTED','AGGREGATE_ONLY','MEASURED','OWNER_ESTIMATE')),
 claim_type TEXT NOT NULL CHECK(claim_type IN('literature_observation','literature_definition','literature_mention','published_owner_report','owner_report','design_proposal','user_requirement','reported_learned_behavior')),
 observation_unit TEXT NOT NULL, occurrence_status TEXT NOT NULL,
 inclusion_status TEXT NOT NULL CHECK(inclusion_status IN('candidate','proposal_only','health_context_excluded','problem_context_separate','insufficient_detail','owner_status_unclear')),
 source_report_id TEXT REFERENCES raw_reports(report_id), source_locator TEXT NOT NULL,
 summary TEXT NOT NULL, limitation TEXT NOT NULL, subject_key TEXT,
 created_date TEXT NOT NULL
);
CREATE TABLE relations (
 relation_id TEXT PRIMARY KEY, record_id TEXT NOT NULL REFERENCES records(record_id),
 related_behavior_id TEXT NOT NULL REFERENCES behavior_nodes(node_id),
 related_record_id TEXT REFERENCES records(record_id),
 relation_type TEXT NOT NULL CHECK(relation_type IN('next','concurrent','alternative')),
 basis TEXT NOT NULL CHECK(basis IN('reported_sequence','reported_cooccurrence','reported_alternative','study_sequence','study_cooccurrence','design_proposal')),
 note TEXT NOT NULL,
 UNIQUE(record_id,related_behavior_id,related_record_id,relation_type)
);
CREATE TABLE findings (
 finding_id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(source_id),
 behavior_id TEXT REFERENCES behavior_nodes(node_id), summary TEXT NOT NULL, limitation TEXT NOT NULL
);
CREATE TABLE context_assessments (
 record_id TEXT NOT NULL REFERENCES records(record_id),
 theme TEXT NOT NULL CHECK(theme IN('positive','negative','neutral')),
 domain TEXT NOT NULL, evidence_type TEXT NOT NULL,
 interpretation_status TEXT NOT NULL,
 evidence_summary TEXT NOT NULL, confounds TEXT NOT NULL, implementation_note TEXT NOT NULL,
 PRIMARY KEY(record_id,theme),
 CHECK((theme='positive' AND interpretation_status IN('contextual_support','indirect_support','owner_attribution','behavior_only','not_specific','negative_comparison')) OR
       (theme='negative' AND interpretation_status IN('contextual_support','not_specific','not_supported_here','owner_reported_pattern','definition_only')) OR
       (theme='neutral' AND interpretation_status IN('routine_observation','elicited_observation','owner_reported','definition_only','mixed_context')))
);
CREATE VIEW positive_assessments AS SELECT record_id,domain AS positive_domain,evidence_type,interpretation_status,evidence_summary,confounds,implementation_note FROM context_assessments WHERE theme='positive';
CREATE TABLE field_dictionary (
 table_name TEXT NOT NULL, field_name TEXT NOT NULL, label_ko TEXT NOT NULL,
 description TEXT NOT NULL, missing_rule TEXT NOT NULL,
 PRIMARY KEY(table_name,field_name)
);
CREATE VIEW negative_assessments AS SELECT record_id,domain AS negative_domain,evidence_type,interpretation_status,evidence_summary,confounds,implementation_note FROM context_assessments WHERE theme='negative';
CREATE INDEX records_behavior_idx ON records(behavior_id);
CREATE VIEW neutral_assessments AS SELECT record_id,domain AS neutral_domain,evidence_type,interpretation_status,evidence_summary,confounds,implementation_note FROM context_assessments WHERE theme='neutral';
CREATE INDEX records_situation_idx ON records(situation_id);
CREATE INDEX records_source_idx ON records(source_id);
CREATE INDEX records_status_idx ON records(inclusion_status);
CREATE INDEX relations_record_idx ON relations(record_id);
CREATE TRIGGER recordable_insert BEFORE INSERT ON records
 WHEN (SELECT recordable FROM behavior_nodes WHERE node_id=NEW.behavior_id)=0
 BEGIN SELECT RAISE(ABORT,'records must reference a recordable behavior'); END;
CREATE TRIGGER recordable_update BEFORE UPDATE OF behavior_id ON records
 WHEN (SELECT recordable FROM behavior_nodes WHERE node_id=NEW.behavior_id)=0
 BEGIN SELECT RAISE(ABORT,'records must reference a recordable behavior'); END;
CREATE VIEW v_taxonomy AS
 WITH RECURSIVE tree AS (
 SELECT node_id,parent_id,level,name_ko,definition,recordable,name_ko AS path,
 name_ko AS domain,NULL AS family,NULL AS behavior,NULL AS variant
 FROM behavior_nodes WHERE parent_id IS NULL
 UNION ALL
 SELECT n.node_id,n.parent_id,n.level,n.name_ko,n.definition,n.recordable,
 t.path||' > '||n.name_ko,t.domain,
 CASE WHEN n.level=2 THEN n.name_ko ELSE t.family END,
 CASE WHEN n.level=3 THEN n.name_ko ELSE t.behavior END,
 CASE WHEN n.level=4 THEN n.name_ko ELSE t.variant END
 FROM behavior_nodes n JOIN tree t ON n.parent_id=t.node_id
 ) SELECT * FROM tree;
CREATE VIEW v_record_relations AS
 SELECT x.*,b.name_ko AS related_behavior,s.source_id
 FROM v_relations_expanded x JOIN behavior_nodes b ON b.node_id=x.related_behavior_id
 JOIN records s ON s.record_id=x.record_id;
CREATE VIEW v_behavior_records AS
 SELECT r.*,t.domain,t.family,t.behavior,t.variant,t.path AS behavior_path,
 s.citation,s.url AS source_url,s.source_type,s.access_scope,s.sample,s.local_file,
 c.name_ko AS situation_name,
 a.positive_domain,a.evidence_type AS positive_evidence_type,a.interpretation_status AS positive_interpretation,
 a.evidence_summary AS positive_evidence_summary,a.confounds AS positive_confounds,a.implementation_note AS positive_implementation_note,
 n.negative_domain,n.evidence_type AS negative_evidence_type,n.interpretation_status AS negative_interpretation,
 n.evidence_summary AS negative_evidence_summary,n.confounds AS negative_confounds,n.implementation_note AS negative_implementation_note,
 u.neutral_domain,u.evidence_type AS neutral_evidence_type,u.interpretation_status AS neutral_interpretation,
 u.evidence_summary AS neutral_evidence_summary,u.confounds AS neutral_confounds,u.implementation_note AS neutral_implementation_note,
 (SELECT group_concat(DISTINCT b.name_ko) FROM v_relations_expanded x JOIN behavior_nodes b ON b.node_id=x.related_behavior_id WHERE x.record_id=r.record_id AND x.relation_type='previous') AS previous_behavior,
 (SELECT group_concat(DISTINCT b.name_ko) FROM v_relations_expanded x JOIN behavior_nodes b ON b.node_id=x.related_behavior_id WHERE x.record_id=r.record_id AND x.relation_type='next') AS next_behavior,
 (SELECT group_concat(DISTINCT b.name_ko) FROM v_relations_expanded x JOIN behavior_nodes b ON b.node_id=x.related_behavior_id WHERE x.record_id=r.record_id AND x.relation_type='concurrent') AS concurrent_behavior,
 (SELECT group_concat(DISTINCT b.name_ko) FROM v_relations_expanded x JOIN behavior_nodes b ON b.node_id=x.related_behavior_id WHERE x.record_id=r.record_id AND x.relation_type='alternative') AS alternative_behavior,
 (SELECT group_concat(DISTINCT x.basis) FROM v_relations_expanded x WHERE x.record_id=r.record_id) AS relation_basis
 FROM records r JOIN v_taxonomy t ON t.node_id=r.behavior_id
 JOIN sources s ON s.source_id=r.source_id JOIN situations c ON c.situation_id=r.situation_id
 LEFT JOIN positive_assessments a ON a.record_id=r.record_id
 LEFT JOIN negative_assessments n ON n.record_id=r.record_id
 LEFT JOIN neutral_assessments u ON u.record_id=r.record_id;
CREATE VIEW v_neutral_contexts AS SELECT * FROM v_behavior_records WHERE neutral_interpretation IS NOT NULL;
CREATE VIEW v_positive_contexts AS SELECT * FROM v_behavior_records WHERE positive_interpretation IS NOT NULL;
CREATE VIEW v_negative_contexts AS SELECT * FROM v_behavior_records WHERE negative_interpretation IS NOT NULL;
CREATE VIEW v_evidence_candidates AS SELECT * FROM v_behavior_records
 WHERE inclusion_status='candidate' AND claim_type NOT IN('design_proposal','user_requirement');
CREATE VIEW v_proposals AS SELECT * FROM v_behavior_records
 WHERE inclusion_status='proposal_only';
CREATE VIEW v_review_required AS SELECT * FROM v_behavior_records
 WHERE inclusion_status IN('health_context_excluded','problem_context_separate','insufficient_detail','owner_status_unclear');

