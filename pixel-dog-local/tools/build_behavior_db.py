"""Build a local research catalog from curated seed data and preserved reports.
The JSON seed and original community file own the data; SQLite/XLSX are exports.
Uses only Python's standard library. Rebuild into a temporary DB before replace.
"""
from pathlib import Path
import json, sqlite3, hashlib, os
from collections import Counter
from organize_behavior_db import organize, validate as validate_organization, TABLES as ORGANIZATION_TABLES, VIEWS as ORGANIZATION_VIEWS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "behavior-db"
SEED = OUT / "catalog.seed.json"
COMMUNITY = ROOT / "exa-results/dog-community-habits-2026-10-17/observations.json"
DATE = "2026-10-17"

def read_json(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))

def write_json(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

def build():
    d = read_json(SEED)
    raw = read_json(COMMUNITY)["rows"]
    nodes = {r["node_id"]: r for r in d["taxonomy"]}
    srcs = {s["source_id"]:s for s in d["sources"]}
    records = d["records"]
    relations = d["relations"]
    mappings = {r["source_report_id"]:r for r in d["community_maps"]}
    assert len(mappings)==len(raw)==23
    assert set(mappings)=={r["source_id"] for r in raw}
    url_sources = {}
    raw_reports = []
    for old in raw:
        key=old["source_id"]
        if old["url"] not in url_sources:
            sid=f"C{len(url_sources)+1:03d}"
            url_sources[old["url"]]=sid
            srcs[sid]=dict(source_id=sid,source_type="community",
                citation=old["community"]+" / "+old["title"],title=old["title"],url=old["url"],
                year=int(old["posted_date"][:4]) if old["posted_date"] else None,
                published_date=old["posted_date"] if old["segment"]=="본문" else None,access_scope=old["access"],
                sample="공개 게시글·댓글; 실제 개체 수와 동일 개체 여부 미확인",
                local_file=str(COMMUNITY.relative_to(ROOT)).replace("\\","/"),
                locator="원수집 ID "+key, verification_note="기존 본문 수집 기록을 이관. 이미지·영상 미판독; 이번 DB화에서 웹 재조회 없음.")
        sid=url_sources[old["url"]]
        raw_reports.append(dict(report_id=key,source_id=sid,segment=old["segment"],
            context_text=old["context"],owner_report=old["owner_report"],
            owner_frequency=old["owner_frequency"],original_status=old["status"],
            caveat=old["caveat"],original_json=json.dumps(old,ensure_ascii=False)))
        mapping=mappings[key]
        ids=[]
        for j, atom in enumerate(mapping["behaviors"],1):
            beh,summary,scene,ctx=atom[:4]
            opts=atom[4] if len(atom)>4 else {}
            rid=f"C_{key}_{j:02d}"; ids.append(rid)
            # A paper's behavioral definition is not an inferred individual habit.
            row=dict(record_id=rid,source_id=sid,behavior_id=beh,situation_id=scene,
                context_text=ctx,trigger_text=None,target_text=None,body_part=None,
                laterality=None,posture_detail=None,frequency_text=None,
                duration_s=None,latency_s=None,repeat_count=None,duration_text=None,speed_text=None,
                measurement_status="NOT_REPORTED",claim_type="owner_report",
                observation_unit="anonymous_owner_report",occurrence_status="PRESENT_REPORTED",
                inclusion_status=old["status"],source_report_id=key,
                source_locator=key+" / "+old["segment"],summary=summary,
                limitation=old["caveat"],subject_key=None,created_date=DATE)
            row.update(opts)
            if key=="DC01" and beh in ("REST_HEAD_DOWN","HEAD_TILT"):
                row["frequency_text"]="항상 한다고 서술; 수치 없음"
            elif key in ("DC05","MN01","DC06"):
                row["frequency_text"]=old["owner_frequency"]
            if key=="KQ03" and j==1:
                row["duration_text"]="한두 시간; 보호자 보고의 범위값"
                row["measurement_status"]="OWNER_ESTIMATE"
            if key=="KQ02" and beh=="APPROACH":
                row["speed_text"]="천천히; 보호자 표현"
            if key in ("DC03","MN02") and not (key=="MN02" and j==1):
                row["claim_type"]="reported_learned_behavior"
                row["occurrence_status"]="ABILITY_REPORTED"
                row["limitation"]+=" 명령명에서 대응한 행동 후보이며 실제 자세·성공률은 미확인."
            if key=="KD02":
                row["situation_id"]="S_UNSPEC"
                row["context_text"]="보호자에게 엉덩이를 들이밀거나 비빔; 직전 자극 미기재"
            records.append(row)
        for a,b,kind in mapping.get("relations",[]):
            basis={"next":"reported_sequence","concurrent":"reported_cooccurrence","alternative":"reported_alternative"}[kind]
            note="보호자 진술의 상대적 순서; 지연·지속 실측 없음." if kind=="next" else ("같이 나타난다는 진술; 선후관계로 처리하지 않음." if kind=="concurrent" else "선택적 또는 서로 다른 결과; 연속 순서로 처리하지 않음.")
            relations.append(dict(record_id=ids[a],related_behavior_id=mapping["behaviors"][b][0],
                related_record_id=ids[b],relation_type=kind,basis=basis,note=note))
            reverse="previous" if kind=="next" else kind
            relations.append(dict(record_id=ids[b],related_behavior_id=mapping["behaviors"][a][0],
                related_record_id=ids[a],relation_type=reverse,basis=basis,note=note))
    for r in records:
        for field in ("duration_text","speed_text","subject_key"):
            r.setdefault(field,None)
        r.setdefault("created_date",DATE)
        r.setdefault("occurrence_status","PROPOSED" if r["inclusion_status"]=="proposal_only" else ("DEFINITION_ONLY" if r["claim_type"]=="literature_definition" else "PRESENT_REPORTED"))
        assert r["behavior_id"] in nodes and nodes[r["behavior_id"]]["recordable"]==1
        assert r["source_id"] in srcs
    # Explicit new IDs must not renumber the pre-existing community relations.
    legacy_relation_index=0
    for r in relations:
        if not r.get("relation_id"):
            legacy_relation_index+=1
            r["relation_id"]=f"REL{legacy_relation_index:04d}"
    organized,relations=organize(ROOT,d,srcs,records,relations)
    nodes={r['node_id']:r for r in d['taxonomy']}
    document_paths=sorted(set(s["local_file"] for s in srcs.values()) | {
        "docs/archive/01_data_hierarchy.md",
        "exa-results/dog-community-habits-2026-10-17/report.md",
        "data/behavior-db/organization.seed.json",
        "reviews/behavior-db-2026-10-17/report.md",
        "reviews/behavior-db-2026-10-17/source-checks.json"})
    docs=[]
    for i,relative in enumerate(document_paths,1):
        path=ROOT/relative
        assert path.exists(),relative
        docs.append(dict(document_id=f"DOC{i:02d}",local_file=relative,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),scope="이 빌드가 구조화한 누적·확장 조사 자료"))
    dictionary=[
        ("records","record_id","기록 ID","행동·상황·출처를 구분하는 안정 ID. 개체 수가 아님","필수"),
        ("behavior_nodes","level","분류 단계","1 영역, 2 동작군, 3 구체 행동, 4 세부 변형","세부 변형이 없으면 3단계에 기록"),
        ("behavior_nodes","parent_id","상위 행동 분류","한 노드의 직접 상위 분류 ID","1단계만 NULL"),
        ("records","behavior_id","행동 코드","기록 가능한 3·4단계 노드. 형태가 미상일 때 세부 변형을 추정하지 않음","필수"),
        ("records","situation_id","상황 분류","행동 위계와 독립. 같은 행동이 여러 상황에 존재 가능","미기재는 S_UNSPEC"),
        ("records","context_text","상황 상세","출처에 기재된 환경과 상호작용 조건","NULL=미기재"),
        ("records","trigger_text","직전 자극","보호자 말·접촉·다른 개 행동 등 외부 사건","NULL=미기재; 이전 개 행동과 구분"),
        ("relations","relation_type","이전·후속·동시·대안","previous/next/concurrent/alternative. 시간 순서와 동시 발생·대안 구분","관계 행 없음=미기재; 행동 없음이 아님"),
        ("relations","basis","관계 근거","보호자 순서·동시·대안 보고, 연구 순서·동시 발생, 설계 제안","필수; 공동 발생을 순서로 변환하지 않음"),
        ("relations","related_record_id","연결 기록","같은 출처 장면의 구체 상대 기록","연구 요약에서 행동 유형만 있으면 NULL"),
        ("records","target_text","행동 대상","보호자·다른 개·물체 등","NULL=미기재"),
        ("records","body_part","신체 부위","출처에 명시된 움직임·접촉 부위","NULL=미기재"),
        ("records","laterality","좌우 방향","출처에서 확인한 좌·우·양쪽","NULL=미기재; 방향 선호 추정 금지"),
        ("records","posture_detail","자세 특징","앞발·몸통·머리 위치 등 보이는 형태 또는 보고","NULL=미기재"),
        ("records","frequency_text","빈도 표현","항상·종종 등 원보고 표현 또는 집단 연구 비율","NULL=미기재; 집단 비율을 개인 확률로 변환 금지"),
        ("records","duration_s","지속시간 초","단일 사건의 확인된 정확한 지속시간","NULL=수치 없음; 0으로 대체 금지"),
        ("records","latency_s","반응 지연 초","자극 시작부터 첫 반응까지 확인된 시간","NULL=수치 없음; 0으로 대체 금지"),
        ("records","repeat_count","반복 횟수","단일 관찰 장면의 확인된 반복 수","NULL=미측정"),
        ("records","duration_text","지속시간 표현","범위·정성·보호자 추정 표현","NULL=미기재; 정확한 duration_s와 구분"),
        ("records","speed_text","속도 표현","천천히 등 보호자 표현","NULL=미기재; 정량 속도 아님"),
        ("records","claim_type","근거 유형","문헌 정의·문헌 관찰·논문 내 보호자 보고·커뮤니티 보고·학습행동 보고·설계·사용자 요구","필수"),
        ("records","observation_unit","관찰 단위","연구 요약·익명 보고·다수 개 보고·제안 등","연구 요약을 개별 개로 세지 않음"),
        ("records","occurrence_status","발생 상태","PRESENT_REPORTED/DEFINITION_ONLY/PROPOSED/ABILITY_REPORTED/NO_CHANGE_REPORTED/DIFFICULTY_REPORTED","미발생·어려움·미확인을 정상 발생과 구분"),
        ("records","inclusion_status","채택 상태","candidate/proposal_only/health_context_excluded/problem_context_separate/insufficient_detail/owner_status_unclear","candidate도 개인화 확정 또는 정상성 진단이 아님"),
        ("records","source_report_id","원수집 ID","23개 커뮤니티 수집 행으로 추적; 여러 원자 기록이 같은 행에서 나올 수 있음","비커뮤니티는 NULL"),
        ("sources","source_id","출처 ID","한 논문 또는 한 게시글당 1개. 같은 글의 댓글은 원수집 ID로 구분","필수"),
        ("sources","access_scope","출처 확인 범위","관련 본문·초록·보존본 요약을 구분. 출처별 확인 이력 참조","기존 누적 자료와 이번 신규 조사의 확인 범위를 구분"),
        ("records","source_locator","근거 위치","기존 문서의 절/R번호 또는 원수집 ID·댓글 위치","필수"),
        ("records","summary","관찰·제안 내용","간결한 출처 요약; 직접 인용이나 영상 판독값 아님","필수"),
        ("records","limitation","해석 주의점","표본·맥락·관찰 범위·설계 여부","필수"),
        ("records","subject_key","실제 개체 식별자","실제 동일 개체가 확인됐을 때 사용. 현재 모두 NULL","익명 계정·게시글 ID를 개체 ID로 쓰지 않음"),
        ("findings","summary","종합 연구 결과","생리·메타분석·성격 요인 결과처럼 원자 동작으로 억지 변환하지 않은 내용","행동 ID가 없을 수 있음"),
        ("raw_reports","original_json","원수집 자료","이전 커뮤니티 수집 행 전체를 무손실 보존","원문 전체 또는 미디어 원본은 아님"),
        ("positive_assessments","positive_domain","긍정 맥락 검색 영역","함께 놀기·물체 놀이·접촉·탐색·휴식·기대 등의 검색 묶음","행동 위계와 독립; 평가 행 없음은 이번 확장 평가 없음"),
        ("positive_assessments","evidence_type","긍정 맥락 근거 방식","실험·관찰·인지 편향·평정·설문을 구분","연구 설계 구분이며 개인 감정의 확률값이 아님"),
        ("positive_assessments","interpretation_status","긍정 맥락 해석 상태","맥락 관련·간접 지지·보호자 해석·행동 보고만·비특이·부정 조건 비교","미평가를 부정으로 바꾸지 않으며 긍정 점수를 만들지 않음"),
        ("positive_assessments","evidence_summary","긍정 맥락 근거 내용","해당 기록과 연결된 문헌 결과","출처·상황을 함께 읽음"),
        ("positive_assessments","confounds","긍정 맥락 혼동 요인","각성·보상 차단·발달·관찰자 해석 등 일반화 제약","관계가 있다는 사실을 확정 감정으로 바꾸지 않음"),
        ("positive_assessments","implementation_note","개인화 적용 주의","실제 동작·상황 확인 및 추정 금지 항목","애니메이션 구현·효과 검증 결과가 아님"),
        ("negative_assessments","negative_domain","부정 맥락 검색 영역","공포·급성 불편·좌절·회피·경계·분리·반복·자원 접근 통제","나쁜 행동 또는 성격을 뜻하는 분류가 아님"),
        ("negative_assessments","evidence_type","부정 맥락 근거 방식","실험·준실험·관찰·설문·전문가 정의를 구분","실험 조건과 자연 발생·정의를 혼합하지 않음"),
        ("negative_assessments","interpretation_status","부정 맥락 해석 상태","맥락 관련·비특이·해당 비교에서 미확인·보호자 보고 패턴·정의만 제시","유의하지 않음을 행동·감정의 부재로 해석하지 않음"),
        ("negative_assessments","evidence_summary","부정 맥락 근거 내용","해당 기록과 연결한 결과 또는 명시적 정의","기존 기록 재사용은 새 관찰로 세지 않음"),
        ("negative_assessments","confounds","부정 맥락 혼동 요인","자극·각성·표본·통계·임상 해석의 한계","진단·원인·위험 확률·필수 경고 순서로 변환하지 않음"),
        ("negative_assessments","implementation_note","부정 맥락 적용 주의","기본 행동 후보와 문제·건강 맥락의 표현 검토를 구분","문제 맥락 분리는 개체의 질환 진단 또는 자산 제작 승인과 다름")
    ]
    dictionary.extend([
        ("neutral_assessments","neutral_domain","일상 맥락 검색 영역","휴식·이동·섭취·몸단장·탐색·배설을 감정가와 독립적으로 검색","중립 감정 또는 정상성 판정이 아님"),
        ("neutral_assessments","evidence_type","일상 맥락 근거 방식","자연 관찰·유도 과제·설문·정의·혼합 자료를 구분","연구 전체 표본과 행동별 표본은 다를 수 있음"),
        ("neutral_assessments","interpretation_status","일상 맥락 해석 상태","routine_observation/elicited_observation/owner_reported/definition_only/mixed_context","평가 없음은 긍정·부정 또는 행동 부재의 뜻이 아님"),
        ("neutral_assessments","evidence_summary","일상 맥락 근거 내용","기록에 연결된 관찰·보고·정의 또는 기존 출처 재확인","과제 시간·집단 사건 수·설문 비율을 개별 수치로 넣지 않음"),
        ("neutral_assessments","confounds","일상 맥락 혼동 요인","표본·유도·건강 혼합·보호자 인지 수면 등의 해석 한계","무활동·머리 높이만으로 수면이나 편안함을 판정하지 않음"),
        ("neutral_assessments","implementation_note","일상 맥락 적용 주의","사진·응답으로 확인할 동작 형태와 상황","구현 승인·감정 진단·개인 행동 확률과 별도")
    ])
    dictionary.extend([
      ('behavior_concepts','concept_id','대표 행동 ID','세부형을 속성으로 연결한 공통 행동. 독립 검증된 습관 수가 아님','필수'),
      ('behavior_concepts','kind','행동 종류','자세·상태 / 동작 / 전환 / 복합 활동 / 종합 지표 / 합산 행동 / 과제 결과','프로젝트 분류'),
      ('record_organization','context_domain','통합 상황','연구 방법·보고 방식과 분리한 활동 맥락','미상은 원문 정의의 맥락 또는 상황 미기재'),
      ('record_organization','collection_method','수집 방식','관찰·정의·본문 언급·보호자 보고·제안의 구분','발생 사실과 구별'),
      ('record_organization','mapping_scope','분류 대응 범위','원문 합산 범주·프로젝트 대응·재검토를 구분','정확한 원문 일치로 자동 해석하지 않음'),
      ('record_facets','value_text','자세·동작 속성','기존 분류 또는 명시 내용에서 분리한 몸통·앞발·뒷다리·머리·접촉 등의 특성','미기재 속성은 추정하지 않음'),
      ('evidence_units','unit_id','원문 근거 단위','같은 표 항목에서 분리된 기록의 공통 출처 연결','독립 표본·발생 횟수가 아님'),
      ('sequence_steps','position','연쇄 단계','동일 행동이 반복돼도 별도 단계와 순번을 보존','현재 설계 연쇄이며 시간·확률 미설정'),
      ('personalization_requirements','requirement_id','대표 개인화 요구','겹치는 제안·사용자 요구를 원기록과 연결','관련 정의만으로 실제 습관을 확정하지 않음'),
      ('record_changes','before_json','정정 이전 값','모든 기록 정정의 전후 값과 이유를 보존','원본은 original_records에도 보존'),
      ('context_assessments','theme','평가 조사 분야','긍정·부정·일상 평가의 공통 구조. 한 기록에 복수 분야 가능','감정의 배타적 라벨이 아님'),
      ('relation_aliases','legacy_relation_id','기존 관계 ID','원본 방향 하나에서 예전 양방향 관계 조회를 재구성','역방향을 별도 독립 관계로 집계하지 않음')
    ])
    fields=[dict(table_name=x[0],field_name=x[1],label_ko=x[2],description=x[3],missing_rule=x[4]) for x in dictionary]
    dbtemp=OUT/"nana-behaviors.building.sqlite"
    if dbtemp.exists(): dbtemp.unlink()
    con=sqlite3.connect(dbtemp)
    con.row_factory=sqlite3.Row
    con.executescript((OUT/"schema.sql").read_text(encoding="utf-8"))
    con.executescript((OUT/"organization.sql").read_text(encoding="utf-8"))
    def insert(table, rows):
        if not rows:return
        columns=[x[1] for x in con.execute(f"PRAGMA table_info({table})")]
        names=",".join(columns); marks=",".join("?" for _ in columns)
        con.executemany(f"INSERT INTO {table} ({names}) VALUES ({marks})",
            [[r.get(k) for k in columns] for r in rows])
    insert("metadata",[dict(key=k,value=str(v)) for k,v in {
        "schema_version":d["version"],"as_of":DATE,"taxonomy":"project_observation_taxonomy_not_validated_ethogram",
        "scope":"반려견 행동의 누적 문헌·공개 보고·설계 후보",
        "unknown_policy":"NULL=미기재 또는 미측정. 미발생은 별도 상태.",
        "authoritative_data":"catalog.seed.json + 원수집 observations.json + organization.seed.json",
        "row_unit":"출처·상황별 행동 주장. 개체 또는 실제 발생 사건 수가 아님"}.items()])
    for table,rows in [("behavior_nodes",d["taxonomy"]),("situations",d["situations"]),
        ("documents",docs),("sources",list(srcs.values())),("raw_reports",raw_reports),
        ("records",records),("relations",relations),("findings",d["findings"]),("field_dictionary",fields)]:
        insert(table,rows)
    for table in ORGANIZATION_TABLES:insert(table,organized[table])
    con.commit()
    checks={}
    checks["sqlite_integrity"]=con.execute("PRAGMA integrity_check").fetchone()[0]
    checks["foreign_key_errors"]=[list(x) for x in con.execute("PRAGMA foreign_key_check")]
    assert checks["sqlite_integrity"]=="ok" and not checks["foreign_key_errors"]
    assert len({r["record_id"] for r in records})==len(records)
    assert len({s["url"] for s in srcs.values() if s["url"]})==sum(bool(s["url"]) for s in srcs.values())
    assert all(n["level"]==1 if n["parent_id"] is None else n["level"]==nodes[n["parent_id"]]["level"]+1 for n in nodes.values())
    assert con.execute("SELECT count(*) FROM v_taxonomy").fetchone()[0]==len(nodes)
    for rel in relations:
        if rel["related_record_id"]:
            linked=next(r for r in records if r["record_id"]==rel["related_record_id"])
            current=next(r for r in records if r["record_id"]==rel["record_id"])
            assert linked["behavior_id"]==rel["related_behavior_id"]
            assert linked["source_id"]==current["source_id"]
            if current["source_report_id"]:assert linked["source_report_id"]==current["source_report_id"]
    checks["raw_reports_preserved"]=len(raw_reports)
    checks["community_records"]=sum(r["source_report_id"] is not None for r in records)
    checks["source_posts_deduplicated"]=len(url_sources)
    checks["no_individual_ids_inferred"]=all(r["subject_key"] is None for r in records)
    checks["no_unmeasured_numeric_times"]=all(r["duration_s"] is None and r["latency_s"] is None and r["repeat_count"] is None for r in records)
    checks["excluded_rows_in_candidate_view"]=con.execute("SELECT count(*) FROM v_evidence_candidates WHERE inclusion_status!='candidate'").fetchone()[0]
    for mapping in d["community_maps"]:
        for a,b,kind in mapping.get("relations",[]):
            if kind not in ("concurrent","alternative"): continue
            left=f'C_{mapping["source_report_id"]}_{a+1:02d}'
            right=f'C_{mapping["source_report_id"]}_{b+1:02d}'
            assert con.execute("SELECT count(*) FROM relations WHERE ((record_id=? AND related_record_id=?) OR (record_id=? AND related_record_id=?)) AND relation_type IN('previous','next')",(left,right,right,left)).fetchone()[0]==0
    checks["no_order_from_cooccurrence"]=True
    # Source-specific checks prevent the most consequential conversion mistakes.
    assert con.execute("SELECT previous_behavior FROM v_behavior_records WHERE record_id='C_DC05_02'").fetchone()[0]=="잠자기"
    assert con.execute("SELECT next_behavior FROM v_behavior_records WHERE record_id='C_DC05_02'").fetchone()[0]=="바라보기"
    assert con.execute("SELECT count(*) FROM relations WHERE record_id='C_KQ02_04' AND relation_type='next'").fetchone()[0]==0
    assert con.execute("SELECT count(*) FROM v_evidence_candidates WHERE source_report_id IN('DC06','MN04','KQ03','KQ04')").fetchone()[0]==0
    checks["sequence_spot_checks"]="passed"
    checks["positive_contexts"]=con.execute("SELECT count(*) FROM v_positive_contexts").fetchone()[0]
    if d.get("positive_assessments"):
        assert con.execute("SELECT positive_interpretation FROM v_behavior_records WHERE record_id='E072'").fetchone()[0]=="behavior_only"
        assert con.execute("SELECT positive_interpretation FROM v_behavior_records WHERE record_id='E057'").fetchone()[0]=="not_specific"
        assert con.execute("SELECT count(*) FROM relations WHERE record_id IN('E064','E065') AND relation_type IN('next','previous')").fetchone()[0]==0
        assert con.execute("SELECT count(*) FROM positive_assessments WHERE record_id<'E057'").fetchone()[0]==0
    checks["negative_contexts"]=con.execute("SELECT count(*) FROM v_negative_contexts").fetchone()[0]
    if d.get("negative_assessments"):
        assert con.execute("SELECT negative_interpretation FROM v_behavior_records WHERE record_id='E092'").fetchone()[0]=="definition_only"
        assert con.execute("SELECT negative_interpretation FROM v_behavior_records WHERE record_id='E101'").fetchone()[0]=="not_supported_here"
        assert con.execute("SELECT count(*) FROM v_evidence_candidates WHERE record_id BETWEEN 'E111' AND 'E126'").fetchone()[0]==0
        assert con.execute("SELECT count(*) FROM relations WHERE record_id BETWEEN 'E111' AND 'E115'").fetchone()[0]==0
        assert con.execute("SELECT count(*) FROM v_behavior_records WHERE positive_interpretation IS NOT NULL AND negative_interpretation IS NOT NULL").fetchone()[0]==4
    checks["neutral_contexts"]=con.execute("SELECT count(*) FROM v_neutral_contexts").fetchone()[0]
    if d.get("neutral_assessments"):
        assert con.execute("SELECT occurrence_status FROM records WHERE record_id='E138'").fetchone()[0]=="DEFINITION_ONLY"
        assert con.execute("SELECT neutral_interpretation FROM v_behavior_records WHERE record_id='E148'").fetchone()[0]=="mixed_context"
        assert con.execute("SELECT claim_type FROM records WHERE record_id='E165'").fetchone()[0]=="published_owner_report"
        assert con.execute("SELECT count(*) FROM relations WHERE record_id IN('E137','E177')").fetchone()[0]==0
        assert con.execute("SELECT next_behavior FROM v_behavior_records WHERE record_id='E155'").fetchone()[0]=="발로 땅을 뒤로 긁기"
        assert con.execute("SELECT count(*) FROM neutral_assessments WHERE record_id<'E130'").fetchone()[0]==3
        checks["neutral_definition_report_sequence_checks"]="passed"
    if any(r['record_id']=='U017' for r in records):
        coverage=read_json(ROOT/'exa-results/dog-additional-behaviors-2026-10-17/additions.json')['coverage']
        assert len(coverage)==len({r['item_id'] for r in coverage})==28
        by_id={r['record_id']:r for r in records}
        assert all(r['record_id'] in by_id for r in coverage)
        pending=[by_id[r['record_id']] for r in coverage if r['status']=='evidence_pending']
        assert len(pending)==9
        assert all(r['claim_type']=='user_requirement' and r['inclusion_status']=='proposal_only' and r['occurrence_status']=='PROPOSED' for r in pending)
        assert con.execute("SELECT count(*) FROM v_evidence_candidates WHERE record_id BETWEEN 'U009' AND 'U017'").fetchone()[0]==0
        assert all(by_id[f'E{i}']['claim_type']=='literature_definition' and by_id[f'E{i}']['occurrence_status']=='DEFINITION_ONLY' for i in range(178,193))
        assert all(by_id[f'E{i}']['claim_type']=='literature_observation' for i in range(193,196))
        assert by_id['E171']['claim_type']=='published_owner_report'
        assert con.execute("SELECT count(*) FROM relations WHERE relation_id LIKE 'ADD_REL%' AND basis='design_proposal'").fetchone()[0]==2
        checks['additional_candidates_covered']=len(coverage)
        checks['pending_candidates_separate_from_evidence']=len(pending)
        checks['additional_definition_observation_sequence_checks']='passed'
    checks['organization']=validate_organization(con,organized)
    tables={}
    for table in ["metadata","behavior_nodes","situations","documents","sources","raw_reports","records","relations","findings","positive_assessments","negative_assessments","neutral_assessments","field_dictionary","v_taxonomy","v_behavior_records"]+ORGANIZATION_TABLES+ORGANIZATION_VIEWS:
        tables[table]=[dict(r) for r in con.execute(f"SELECT * FROM {table}")]
    counts={table:len(rows) for table,rows in tables.items() if not table.startswith("v_")}
    counts["domains"]=sum(n["level"]==1 for n in nodes.values())
    counts["recordable_behavior_nodes"]=sum(n["recordable"] for n in nodes.values())
    counts["behavior_types_in_records"]=len(set(r["behavior_id"] for r in records))
    counts["evidence_candidates"]=con.execute("SELECT count(*) FROM v_evidence_candidates").fetchone()[0]
    counts["proposal_records"]=con.execute("SELECT count(*) FROM v_proposals").fetchone()[0]
    counts["review_records"]=con.execute("SELECT count(*) FROM v_review_required").fetchone()[0]
    counts["next_relations"]=con.execute("SELECT count(*) FROM relations WHERE relation_type='next'").fetchone()[0]
    counts['expanded_relations']=con.execute('SELECT count(*) FROM v_relations_expanded').fetchone()[0]
    counts["records_by_claim_type"]=dict(Counter(r["claim_type"] for r in records))
    checks["counts"]=counts
    con.close()
    os.replace(dbtemp,OUT/"nana-behaviors.sqlite")
    write_json(OUT/"catalog.json",tables)
    write_json(OUT/"validation.json",checks)
    write_json(OUT/"manifest.json",dict(as_of=DATE,schema_version=d["version"],counts=counts,
        note="행 수는 독립 개체 수 또는 행동 발생 횟수가 아님",documents=docs))
    print(json.dumps(checks,ensure_ascii=False,indent=2))

if __name__=="__main__":
    build()

