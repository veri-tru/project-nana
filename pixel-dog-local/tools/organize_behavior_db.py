"""Apply versioned corrections and build normalized research views without losing claims."""
from collections import Counter
from copy import deepcopy
import json, re

TABLES=['original_records','record_changes','behavior_concepts','node_concept_map',
        'record_organization','record_facets','evidence_units','record_evidence',
        'personalization_requirements','requirement_records','sequence_templates',
        'sequences','sequence_steps','relation_aliases','context_assessments',
        'catalog_events','source_access_events','concept_links','review_resolutions']
VIEWS=['v_relations_expanded','v_organized_records','v_concept_catalog','v_sequence_steps']

def pack(value): return json.dumps(value,ensure_ascii=False,sort_keys=True)

def organize(root,d,srcs,records,relations):
    cfg=json.loads((root/'data/behavior-db/organization.seed.json').read_text(encoding='utf-8'))
    before=deepcopy(records)
    baseline=json.loads((root/'data/behavior-db/archive/1.3.1/catalog.json').read_text(encoding='utf-8'))
    assert {r['record_id']:r for r in before}=={r['record_id']:r for r in baseline['records']},'Original claims drifted'
    result={k:[] for k in TABLES}
    result['original_records']=[dict(record_id=r['record_id'],version='1.3.1',original_json=pack(r)) for r in before]
    by_id={r['record_id']:r for r in records}
    def update_record(rid,changes,reason):
        row=by_id[rid]
        for field,value in changes.items():
            if row[field]!=value:
                result['record_changes'].append(dict(change_id=f'CH{len(result["record_changes"])+1:03d}',record_id=rid,field_name=field,before_json=pack(row[field]),after_json=pack(value),reason=reason,version=cfg['version']))
                row[field]=value
    for rid,changes in cfg['record_updates'].items():
        update_record(rid,changes,'2026-10-17 중복·분류 검토 R01–R04/R08 반영')
    for i in range(66,72):
        rid=f'E{i:03d}'
        update_record(rid,{
            'source_locator':'L32 Methods; Results 3.1.4; 당시 추출과 이후 Table 1 확인 이력은 source_access_events 참조',
            'limitation':'생후 3–7주 새끼 42마리·3품종. 성견의 보편성·감정·개인화 확률로 일반화하지 않음. 초기 추출 당시 원표 미확인 이력은 보존했으며 후속 원표 대조를 반영함.'},'R14 과거 추출 범위와 현재 확인 범위 분리')
    for node in d['taxonomy']:
        node.update(cfg['node_updates'].get(node['node_id'],{}))
    d['taxonomy'].extend(cfg['new_nodes'])
    for s in d['situations']:
        if s['situation_id']=='S_WALK':s['name_ko']='산책 중 활동'
    d['situations'].append(dict(situation_id='S_WALK_CUE',name_ko='산책하자는 말·제안'))
    nodes={n['node_id']:n for n in d['taxonomy']}
    kinds={code:kind for kind,codes in cfg['kind_sets'].items() for code in codes}
    concept_of={n['node_id']:cfg['concept_aliases'].get(n['node_id'],n['node_id']) for n in nodes.values() if n['recordable']}
    for cid in dict.fromkeys(concept_of.values()):
        n=nodes[cid]
        result['behavior_concepts'].append(dict(concept_id=cid,name_ko=cfg['concept_labels'].get(cid,n['name_ko']),kind=kinds.get(cid,'action'),definition=n['definition'],status='project_working_definition'))
    for bid,cid in concept_of.items():
        direct=any(r['behavior_id']==bid for r in records)
        lifecycle='active' if direct else ('parent_only' if any(n['parent_id']==bid for n in nodes.values()) else 'candidate_unlinked')
        result['node_concept_map'].append(dict(node_id=bid,concept_id=cid,mapping_type='variant_with_facets' if bid!=cid else 'same_project_definition',lifecycle=lifecycle,note='대표 행동과 세부형의 대응. 원문 정의와 정확히 일치한다는 판정은 아님.'))
    method={'literature_observation':'연구 관찰·집단 결과','literature_definition':'문헌 행동 정의','literature_mention':'문헌 본문 언급','published_owner_report':'논문 내 보호자 보고','owner_report':'공개 보호자 진술','reported_learned_behavior':'학습 가능 보고','design_proposal':'설계 제안','user_requirement':'사용자 요구'}
    for r in records:
        rid=r['record_id']; bid=r['behavior_id']
        review='근거 재검토' if rid=='E019' else ('제안·확인 대기' if r['inclusion_status']=='proposal_only' else '기록의 근거 유형 참조')
        result['record_organization'].append(dict(record_id=rid,concept_id=concept_of[bid],context_domain=cfg['contexts'][r['situation_id']],collection_method=method[r['claim_type']],subject_stage='생후 3–7주 새끼' if r['source_id']=='L32' else None,mapping_scope='review_required' if rid=='E019' else ('source_aggregate' if rid in ('E070','E071','E131') else 'project_classification'),mapping_note=cfg['mapping_notes'].get(rid,'원기록의 분류 범위를 유지함. 새 발생·빈도·감정을 추정하지 않음.'),review_status=review))
        facets={**cfg['node_facets'].get(bid,{}),**cfg['record_facets'].get(rid,{})}
        for key,value in facets.items():
            result['record_facets'].append(dict(record_id=rid,facet_key=key,value_text=value,basis='기존 기록의 제안' if r['inclusion_status']=='proposal_only' else ('기존 기록의 명시 내용' if key in cfg['record_facets'].get(rid,{}) else '기존 행동 분류의 정의'),source_locator=r['source_locator']))
    unit_owner={rid:g[0] for g in cfg['unit_groups'] for rid in g}
    made=set()
    for r in records:
        rid=r['record_id']; owner=unit_owner.get(rid,rid); uid='EU_'+owner
        if uid not in made:
            origin=by_id[owner]
            grouping='confirmed_shared_source_item' if owner=='E183' else ('reused_design_definition' if owner in ('P017','P023','P036') else 'record_scoped_not_independent_sample')
            result['evidence_units'].append(dict(unit_id=uid,source_id=origin['source_id'],source_locator=origin['source_locator'],source_term=cfg['source_terms'].get(owner),unit_kind=origin['claim_type'],grouping_status=grouping))
            made.add(uid)
        result['record_evidence'].append(dict(record_id=rid,unit_id=uid,mapping_note=cfg['mapping_notes'].get(rid,'기록 단위 대응. 독립 표본으로 집계하지 않음.')))
    for req in cfg['requirements']:
        result['personalization_requirements'].append(dict(requirement_id=req['id'],name_ko=req['name'],concept_id=req['concept'],status=req.get('status','제안·확인 대기'),note=req['note'],source_id=req.get('source')))
        for rid in req['records']:
            result['requirement_records'].append(dict(requirement_id=req['id'],record_id=rid,role='부분 관련 근거' if rid=='E192' else '요구·설계 이력'))
    templates={}
    for seq in cfg['sequences']:
        prefix=seq.get('shared_prefix',len(seq['records']))
        pattern=[concept_of[by_id[rid]['behavior_id']] for rid in seq['records'][:prefix]]
        tid=seq['template']
        if tid in templates: assert templates[tid]['pattern_json']==pack(pattern)
        else: templates[tid]=dict(template_id=tid,pattern_json=pack(pattern),basis='design_proposal',note='관찰된 고정 연쇄가 아닌 설계 재사용 틀')
        result['sequences'].append(dict(sequence_id=seq['id'],template_id=tid,name_ko=seq['name'],basis='design_proposal',note='단계의 순서와 반복을 보존. 속도·확률·시간은 미설정.'))
        for index,rid in enumerate(seq['records'],1):
            result['sequence_steps'].append(dict(step_id=f'{seq["id"]}_{index:02d}',sequence_id=seq['id'],position=index,record_id=rid,concept_id=concept_of[by_id[rid]['behavior_id']]))
    result['sequence_templates']=list(templates.values())
    for left,right,relation,note in [
        ('DIG','SCRATCH_SURFACE','conditional_overlap','파기는 앞발의 교대 펴기·굽히기 형태로 좁힘. 표면 긁기와 일괄 통합하지 않음.'),
        ('WAIT','RESPONSE_WAIT','behavior_and_measure','정지·반응 보류의 행동과 보상 대기 과제 지표를 각각 유지.'),
        ('PAW_TOUCH','PAW_OBJECT','target_and_action_overlap','접촉 대상과 조작 범위를 구별. 접촉·비접촉 합산은 PAW_OBJECT_AGG로 따로 수정.'),
        ('HEAD_TURN','LOOK_AWAY','form_and_context_overlap','머리 방향 전환과 외면 보고를 구별. 눈만 움직이는 경우를 머리 회전으로 추정하지 않음.')]:
        result['concept_links'].append(dict(left_concept=left,right_concept=right,relation=relation,note=note))
    # Store only one direction, while preserving every original relation ID as an alias.
    unique={};canonical=[]
    for rel in relations:
        left=rel['record_id']; right=rel['related_record_id']; kind=rel['relation_type']; reverse=False
        if kind=='previous':left,right,kind=right,left,'next';reverse=True
        if right and kind in ('concurrent','alternative') and left>right:left,right=right,left;reverse=True
        target=by_id[right]['behavior_id'] if right else rel['related_behavior_id']
        key=(left,right or 'behavior:'+target,kind,rel['basis'])
        if key not in unique:
            new={**rel,'record_id':left,'related_record_id':right,'related_behavior_id':target,'relation_type':kind}
            unique[key]=new['relation_id'];canonical.append(new)
        result['relation_aliases'].append(dict(legacy_relation_id=rel['relation_id'],relation_id=unique[key],reverse_direction=int(reverse),original_note=rel['note'],original_json=pack(rel)))
    for theme in ('positive','negative','neutral'):
        for assessment in d[theme+'_assessments']:
            a=deepcopy(assessment)
            if a['record_id']=='E019':
                a.update(evidence_type='본문의 자세 언급',interpretation_status='mixed_context',evidence_summary='옆눕기를 기존 분류의 한계 설명에서 언급. 독립 정의 항목이 아님.',confounds='E019는 직접 정의 근거에서 제외하고 재검토 상태로 분리.',implementation_note='별도 정의 근거를 확인한 E174 등과 구별해서 사용.')
            result['context_assessments'].append(dict(record_id=a['record_id'],theme=theme,domain=a[theme+'_domain'],**{k:a[k] for k in ('evidence_type','interpretation_status','evidence_summary','confounds','implementation_note')}))
    for f in list(d['findings']):
        if f['finding_id'] in ('F17','F19'):
            result['catalog_events'].append(dict(event_id=f['finding_id'],source_id=f['source_id'],event_type='prior_collection_note',summary=f['summary'],note=f['limitation']))
    d['findings']=[f for f in d['findings'] if f['finding_id'] not in ('F17','F19')]
    result['catalog_events'].append(dict(event_id='ORG2',source_id=None,event_type='organization_migration',summary='R01–R14 분류·속성·근거 단위·요구·연쇄·평가 구조 보완',note='307개 원기록 ID와 원문 스냅샷 유지. 조건부 통합은 구별 상태로 보존.'))
    source_checks=json.loads((root/'reviews/behavior-db-2026-10-17/source-checks.json').read_text(encoding='utf-8'))
    for check in source_checks['urls']:
        result['source_access_events'].append(dict(event_id='ACCESS_'+check['source_id'],source_id=check['source_id'],as_of='2026-10-17',scope=check['scope'],url=check['url'],note='검토 단계의 확인 이력. 과거 추출 범위는 archive/1.3.1/catalog.json에 보존.'))
    review=json.loads((root/'reviews/behavior-db-2026-10-17/findings.json').read_text(encoding='utf-8'))
    resolutions={
      'R01':'산책 제안 기록을 S_WALK_CUE로 이동하고 산책 중 5기록은 S_WALK에 유지.',
      'R02':'휴식 대표 행동에 머리 지지·위치 속성을 연결하고 E017/E018과 분류 정의를 정정.',
      'R03':'E070과 E071을 각각 접촉/비접촉 앞발 합산과 입 조작 합산으로 재분류.',
      'R04':'E019를 문헌 본문 언급·자료 부족으로 정정하고 기본 근거 후보에서 제외.',
      'R05':'중복 개인화 요구 3묶음과 관련 근거만 확보한 얼굴 문지름 요구를 별도 관리. 호출 연쇄의 공통 틀 재사용.',
      'R06':'8개 설계 연쇄에 27개 단계 ID·순번을 부여하고 반복 6단계를 유지.',
      'R07':'조건부 통합 4묶음은 concept_links에 경계를 기록하고 서로 다른 코드를 유지.',
      'R08':'자기 몸 핥기 세부 코드, 뒷다리 뻗기 속성, 얼굴 긁기와 미확인 문지름 구분을 반영.',
      'R09':'대표 행동 121개와 세부 코드 대응, 행동 종류, 기록 속성을 추가.',
      'R10':'307개 기록에 통합 상황과 수집 방식을 별도 부여하고 L32 연령 조건을 분리.',
      'R11':'모든 기록의 근거 단위를 연결. E183/E184의 같은 표 정의와 반복 설계 정의 공유를 명시.',
      'R12':'관계 원본 43개와 기존 ID 83개의 대응을 저장해 양방향 조회를 재구성.',
      'R13':'146개 평가를 공통 테이블로 통합하고 기존 3개 조사 분야는 호환 조회로 제공.',
      'R14':'F17/F19를 작업 이력으로 옮기고 원문 확인 이력·정정 전후·미사용 분류 상태를 보존.'}
    for finding in review['findings']:
        result['review_resolutions'].append(dict(review_id=finding['id'],title=finding['title'],status='applied_with_boundaries' if finding['id']=='R07' else 'applied',resolution=resolutions[finding['id']]))
    d['version']=cfg['version']
    return result,canonical

def validate(con,extra):
    assert con.execute('SELECT count(*) FROM records').fetchone()[0]==307
    assert con.execute('SELECT count(*) FROM original_records').fetchone()[0]==307
    assert con.execute('SELECT count(*) FROM v_organized_records').fetchone()[0]==307
    assert con.execute('SELECT count(*) FROM relations').fetchone()[0]==43
    assert con.execute('SELECT count(*) FROM v_relations_expanded').fetchone()[0]==83
    assert con.execute('SELECT count(*) FROM context_assessments').fetchone()[0]==146
    assert con.execute("SELECT count(*) FROM v_evidence_candidates WHERE record_id='E019'").fetchone()[0]==0
    assert con.execute("SELECT behavior_id FROM records WHERE record_id='E070'").fetchone()[0]=='PAW_OBJECT_AGG'
    assert con.execute("SELECT situation_id FROM records WHERE record_id='C_KQ01_01'").fetchone()[0]=='S_WALK_CUE'
    assert con.execute("SELECT count(*) FROM records WHERE record_id BETWEEN 'E150' AND 'E154' AND situation_id='S_WALK'").fetchone()[0]==5
    assert con.execute("SELECT count(*) FROM sequence_steps WHERE record_id IN ('P017','P019','P023','P025','P036','P038')").fetchone()[0]==6
    assert con.execute("SELECT count(DISTINCT unit_id) FROM record_evidence WHERE record_id IN ('E183','E184')").fetchone()[0]==1
    assert con.execute("SELECT inclusion_status FROM records WHERE record_id='C_KQ03_03'").fetchone()[0]=='health_context_excluded'
    assert con.execute("SELECT count(*) FROM findings WHERE finding_id IN ('F17','F19')").fetchone()[0]==0
    assert con.execute("SELECT count(*) FROM catalog_events WHERE event_id IN ('F17','F19')").fetchone()[0]==2
    # Reconstruct original payloads using the change log, not just row counts.
    original={r['record_id']:json.loads(r['original_json']) for r in extra['original_records']}
    actual={r['record_id']:dict(r) for r in con.execute('SELECT * FROM records')}
    for change in extra['record_changes']:
        assert original[change['record_id']][change['field_name']]==json.loads(change['before_json'])
        original[change['record_id']][change['field_name']]=json.loads(change['after_json'])
    assert actual==original
    return {'original_record_ids_preserved':307,'corrections_have_before_after_history':len(extra['record_changes']),'canonical_relations':43,'legacy_relations_reconstructed':83,'common_assessments':146,'review_items_applied':14}
