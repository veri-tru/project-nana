CREATE TABLE original_records (record_id TEXT PRIMARY KEY REFERENCES records(record_id),version TEXT NOT NULL,original_json TEXT NOT NULL);
CREATE TABLE record_changes (change_id TEXT PRIMARY KEY,record_id TEXT NOT NULL REFERENCES records(record_id),field_name TEXT NOT NULL,before_json TEXT NOT NULL,after_json TEXT NOT NULL,reason TEXT NOT NULL,version TEXT NOT NULL);
CREATE TABLE behavior_concepts (concept_id TEXT PRIMARY KEY,name_ko TEXT NOT NULL,kind TEXT NOT NULL CHECK(kind IN('posture_state','action','transition','composite_activity','aggregate_measure','aggregate_behavior','task_outcome')),definition TEXT NOT NULL,status TEXT NOT NULL);
CREATE TABLE node_concept_map (node_id TEXT PRIMARY KEY REFERENCES behavior_nodes(node_id),concept_id TEXT NOT NULL REFERENCES behavior_concepts(concept_id),mapping_type TEXT NOT NULL,lifecycle TEXT NOT NULL,note TEXT NOT NULL);
CREATE TABLE record_organization (record_id TEXT PRIMARY KEY REFERENCES records(record_id),concept_id TEXT NOT NULL REFERENCES behavior_concepts(concept_id),context_domain TEXT NOT NULL,collection_method TEXT NOT NULL,subject_stage TEXT,mapping_scope TEXT NOT NULL,mapping_note TEXT NOT NULL,review_status TEXT NOT NULL);
CREATE TABLE record_facets (record_id TEXT NOT NULL REFERENCES records(record_id),facet_key TEXT NOT NULL,value_text TEXT NOT NULL,basis TEXT NOT NULL,source_locator TEXT NOT NULL,PRIMARY KEY(record_id,facet_key));
CREATE TABLE evidence_units (unit_id TEXT PRIMARY KEY,source_id TEXT NOT NULL REFERENCES sources(source_id),source_locator TEXT NOT NULL,source_term TEXT,unit_kind TEXT NOT NULL,grouping_status TEXT NOT NULL);
CREATE TABLE record_evidence (record_id TEXT PRIMARY KEY REFERENCES records(record_id),unit_id TEXT NOT NULL REFERENCES evidence_units(unit_id),mapping_note TEXT NOT NULL);
CREATE TABLE personalization_requirements (requirement_id TEXT PRIMARY KEY,name_ko TEXT NOT NULL,concept_id TEXT NOT NULL REFERENCES behavior_concepts(concept_id),status TEXT NOT NULL,note TEXT NOT NULL,source_id TEXT REFERENCES sources(source_id));
CREATE TABLE requirement_records (requirement_id TEXT NOT NULL REFERENCES personalization_requirements(requirement_id),record_id TEXT NOT NULL REFERENCES records(record_id),role TEXT NOT NULL,PRIMARY KEY(requirement_id,record_id));
CREATE TABLE sequence_templates (template_id TEXT PRIMARY KEY,pattern_json TEXT NOT NULL,basis TEXT NOT NULL,note TEXT NOT NULL);
CREATE TABLE sequences (sequence_id TEXT PRIMARY KEY,template_id TEXT NOT NULL REFERENCES sequence_templates(template_id),name_ko TEXT NOT NULL,basis TEXT NOT NULL,note TEXT NOT NULL);
CREATE TABLE sequence_steps (step_id TEXT PRIMARY KEY,sequence_id TEXT NOT NULL REFERENCES sequences(sequence_id),position INTEGER NOT NULL CHECK(position>0),record_id TEXT NOT NULL REFERENCES records(record_id),concept_id TEXT NOT NULL REFERENCES behavior_concepts(concept_id),UNIQUE(sequence_id,position));
CREATE TABLE relation_aliases (legacy_relation_id TEXT PRIMARY KEY,relation_id TEXT NOT NULL REFERENCES relations(relation_id),reverse_direction INTEGER NOT NULL CHECK(reverse_direction IN(0,1)),original_note TEXT NOT NULL,original_json TEXT NOT NULL);
CREATE TABLE catalog_events (event_id TEXT PRIMARY KEY,source_id TEXT REFERENCES sources(source_id),event_type TEXT NOT NULL,summary TEXT NOT NULL,note TEXT NOT NULL);
CREATE TABLE source_access_events (event_id TEXT PRIMARY KEY,source_id TEXT NOT NULL REFERENCES sources(source_id),as_of TEXT NOT NULL,scope TEXT NOT NULL,url TEXT NOT NULL,note TEXT NOT NULL);
CREATE TABLE review_resolutions (review_id TEXT PRIMARY KEY,title TEXT NOT NULL,status TEXT NOT NULL,resolution TEXT NOT NULL);
CREATE TABLE concept_links (left_concept TEXT NOT NULL REFERENCES behavior_concepts(concept_id),right_concept TEXT NOT NULL REFERENCES behavior_concepts(concept_id),relation TEXT NOT NULL,note TEXT NOT NULL,PRIMARY KEY(left_concept,right_concept,relation));
CREATE VIEW v_relations_expanded AS
 SELECT a.legacy_relation_id AS relation_id,
 CASE WHEN a.reverse_direction=1 THEN r.related_record_id ELSE r.record_id END AS record_id,
 CASE WHEN a.reverse_direction=1 THEN origin.behavior_id ELSE r.related_behavior_id END AS related_behavior_id,
 CASE WHEN a.reverse_direction=1 THEN r.record_id ELSE r.related_record_id END AS related_record_id,
 CASE WHEN a.reverse_direction=1 AND r.relation_type='next' THEN 'previous' ELSE r.relation_type END AS relation_type,
 r.basis,a.original_note AS note
 FROM relation_aliases a JOIN relations r ON r.relation_id=a.relation_id JOIN records origin ON origin.record_id=r.record_id;
CREATE VIEW v_organized_records AS
 SELECT r.*,o.concept_id,c.name_ko AS concept_name,c.kind AS concept_kind,o.context_domain,o.collection_method,o.subject_stage,o.mapping_scope,o.mapping_note,o.review_status,e.unit_id,
 (SELECT group_concat(f.facet_key||': '||f.value_text,'; ') FROM record_facets f WHERE f.record_id=r.record_id) AS facets_text
 FROM v_behavior_records r JOIN record_organization o ON o.record_id=r.record_id
 JOIN behavior_concepts c ON c.concept_id=o.concept_id JOIN record_evidence e ON e.record_id=r.record_id;
CREATE VIEW v_concept_catalog AS
 SELECT c.*,
 (SELECT group_concat(m.node_id,', ') FROM node_concept_map m WHERE m.concept_id=c.concept_id) AS legacy_codes,
 count(r.record_id) AS record_count,count(DISTINCT r.source_id) AS source_count,
 sum(CASE WHEN r.inclusion_status='candidate' AND r.claim_type NOT IN('user_requirement','design_proposal') THEN 1 ELSE 0 END) AS candidate_records,
 sum(CASE WHEN r.inclusion_status='proposal_only' THEN 1 ELSE 0 END) AS proposal_records,
 sum(CASE WHEN r.inclusion_status NOT IN('candidate','proposal_only') THEN 1 ELSE 0 END) AS review_records
 FROM behavior_concepts c LEFT JOIN record_organization o ON o.concept_id=c.concept_id LEFT JOIN records r ON r.record_id=o.record_id GROUP BY c.concept_id;
CREATE VIEW v_sequence_steps AS
 SELECT s.*,q.name_ko AS sequence_name,q.template_id,c.name_ko AS concept_name,r.summary,r.source_id
 FROM sequence_steps s JOIN sequences q ON q.sequence_id=s.sequence_id JOIN behavior_concepts c ON c.concept_id=s.concept_id JOIN records r ON r.record_id=s.record_id;
