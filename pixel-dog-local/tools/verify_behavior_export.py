from pathlib import Path
import json, zipfile, xml.etree.ElementTree as ET, sqlite3, hashlib
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"outputs/behavior-db-20261017"
DB=ROOT/"data/behavior-db"
catalog=json.loads((DB/"catalog.json").read_text(encoding="utf-8"))
ns={"m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
z=zipfile.ZipFile(OUT/"behavior-catalog.xlsx")
assert z.testzip() is None
shared=[]
if "xl/sharedStrings.xml" in z.namelist():
    shared=["".join(x.itertext()) for x in ET.fromstring(z.read("xl/sharedStrings.xml"))]
def value(cell):
    typ=cell.attrib.get("t")
    if typ=="inlineStr":
        return "".join(cell.find("m:is",ns).itertext())
    v=cell.find("m:v",ns)
    if v is None or v.text is None:return None
    return shared[int(v.text)] if typ=="s" else v.text
def read_sheet(number):
    tree=ET.fromstring(z.read(f"xl/worksheets/sheet{number}.xml"))
    rows=[]
    for row in tree.findall("m:sheetData/m:row",ns):
        cells={''.join(c for c in cell.attrib["r"] if c.isalpha()):value(cell) for cell in row.findall("m:c",ns)}
        rows.append(cells)
    headers=rows[0]
    return [{headers[k]:r.get(k) for k in headers} for r in rows[1:]],tree
checks={}
sheet_names=[s.attrib['name'] for s in ET.fromstring(z.read('xl/workbook.xml')).findall('m:sheets/m:sheet',ns)]
sheet_numbers={name:i+1 for i,name in enumerate(sheet_names)}
main,tree=read_sheet(sheet_numbers['행동기록'])
main_by_id={r["기록 ID"]:r for r in main}
assert len(main)==len(main_by_id)==len(catalog["records"])
assert set(main_by_id)=={r["record_id"] for r in catalog["records"]}
claims={"literature_observation":"문헌 관찰","literature_definition":"문헌 행동 정의","published_owner_report":"논문 내 보호자 보고","owner_report":"커뮤니티 보호자 보고","design_proposal":"설계 제안","user_requirement":"사용자 요구","reported_learned_behavior":"학습행동 보고"}
claims['literature_mention']='문헌 본문 언급'
kind_labels={'posture_state':'자세·상태','action':'동작','transition':'전환','composite_activity':'복합 활동','aggregate_measure':'종합 지표','aggregate_behavior':'합산 행동','task_outcome':'과제 결과'}
statuses={"candidate":"근거 후보","proposal_only":"설계·요구 후보","health_context_excluded":"건강 맥락 제외","problem_context_separate":"문제행동 맥락 분리","insufficient_detail":"자료 부족","owner_status_unclear":"보호자 여부 미확인"}
for r in catalog["v_organized_records"]:
    x=main_by_id[r["record_id"]]
    for excel,db in [("대분류","domain"),("중분류","family"),("행동","behavior"),("관찰 또는 제안 내용","summary"),("해석 주의점","limitation"),("출처 ID","source_id")]:
        assert x[excel]==r[db],(r["record_id"],excel)
    for excel,db in [("이전 행동","previous_behavior"),("후속 행동","next_behavior"),("동시 행동","concurrent_behavior"),("대안 행동","alternative_behavior")]:
        assert x[excel]==(r[db] or "미기재"),(r["record_id"],excel)
    assert x["근거 유형"]==claims[r["claim_type"]]
    assert x["채택 상태"]==statuses[r["inclusion_status"]]
    assert all(x[k] is None for k in ["지속시간 초","반응 지연 초","반복 횟수"])
    assert x["출처 URL"]==(r["source_url"] or "로컬 기록")
    for label,key in [('대표 행동','concept_name'),('통합 상황','context_domain'),('수집 방식','collection_method'),('근거 단위','unit_id'),('분류 대응 주의','mapping_note')]:
        assert x[label]==r[key],(r['record_id'],label)
    assert x['행동 종류']==kind_labels[r['concept_kind']]
    assert x['자세·동작 속성']==(r['facets_text'] or '미기재')
    for excel,db in [("긍정 맥락 영역","positive_domain"),("긍정 맥락 근거 내용","positive_evidence_summary"),("긍정 맥락 혼동 요인","positive_confounds"),("개인화 적용 주의","positive_implementation_note")]:
        default="이번 확장 평가 없음" if db=="positive_domain" else "해당 없음"
        assert x[excel]==(r[db] or default),(r["record_id"],excel)
    positive_status={"contextual_support":"맥락 관련","indirect_support":"간접 지지","owner_attribution":"보호자 해석","behavior_only":"행동 보고만","not_specific":"긍정성 비특이","negative_comparison":"부정 조건 비교"}
    assert x["긍정 맥락 해석"]==positive_status.get(r["positive_interpretation"],"이번 확장 평가 없음")
    for excel,db in [("부정 맥락 영역","negative_domain"),("부정 맥락 근거 내용","negative_evidence_summary"),("부정 맥락 혼동 요인","negative_confounds"),("부정 맥락 적용 주의","negative_implementation_note")]:
        default="부정 맥락 평가 없음" if db=="negative_domain" else "해당 없음"
        assert x[excel]==(r[db] or default),(r["record_id"],excel)
    negative_status={"contextual_support":"맥락 관련","not_specific":"부정성 비특이","not_supported_here":"해당 비교에서 미확인","owner_reported_pattern":"보호자 보고 패턴","definition_only":"정의만 제시"}
    assert x["부정 맥락 해석"]==negative_status.get(r["negative_interpretation"],"부정 맥락 평가 없음")
    for excel,db in [("일상 맥락 영역","neutral_domain"),("일상 맥락 근거 방식","neutral_evidence_type"),("일상 맥락 근거 내용","neutral_evidence_summary"),("일상 맥락 혼동 요인","neutral_confounds"),("일상 맥락 적용 주의","neutral_implementation_note")]:
        default="일상 맥락 평가 없음" if db in ("neutral_domain","neutral_evidence_type") else "해당 없음"
        assert x[excel]==(r[db] or default),(r["record_id"],excel)
    neutral_status={"routine_observation":"일상 형태 관찰","elicited_observation":"유도 동작 관찰","owner_reported":"보호자 보고","definition_only":"정의만 제시","mixed_context":"혼합 맥락 형태 참고"}
    assert x["일상 맥락 해석"]==neutral_status.get(r["neutral_interpretation"],"일상 맥락 평가 없음")
checks["all_records_match_database"]=len(main)
checks["positive_context_annotations_match"]=len(catalog["positive_assessments"])
checks["negative_context_annotations_match"]=len(catalog["negative_assessments"])
checks["neutral_context_annotations_match"]=len(catalog["neutral_assessments"])
checks["missing_numeric_values_remain_blank"]=True
expected={name:len(catalog[key]) for name,key in [('대표행동','behavior_concepts'),('행동기록','records'),('행동위계','behavior_nodes'),('행동관계','relations'),('출처','sources'),('원수집','raw_reports'),('개인화항목','personalization_requirements'),('행동연쇄','sequence_steps')]}
expected['필드설명']=4+sum(len(catalog[k]) for k in ['field_dictionary','findings','situations','record_changes','catalog_events','review_resolutions','concept_links'])
assert set(sheet_numbers)==set(expected)
for name,expected_rows in expected.items():
    rows,tree=read_sheet(sheet_numbers[name])
    assert len(rows)==expected_rows,(name,len(rows))
    pane=tree.find(".//m:pane",ns)
    assert pane is not None and pane.attrib.get("ySplit")=="1"
    assert tree.find("m:sheetViews/m:sheetView",ns).attrib.get("showGridLines")=="0"
tables=[n for n in z.namelist() if n.startswith("xl/tables/table") and n.endswith(".xml")]
assert len(tables)==9
assert all(ET.fromstring(z.read(n)).find("m:autoFilter",ns) is not None for n in tables)
raw,_=read_sheet(sheet_numbers['원수집'])
by_report={r["원수집 ID"]:r for r in raw}
for r in catalog["raw_reports"]:
    o=json.loads(r["original_json"])
    assert by_report[r["report_id"]]["보호자 진술 요약 원기록"]==(o["owner_report"] or "미기재")
checks["all_23_original_report_summaries_preserved"]=True
concepts,_=read_sheet(sheet_numbers['대표행동'])
concepts={r['대표 ID']:r for r in concepts}
for r in catalog['v_concept_catalog']:
    row=concepts[r['concept_id']]
    assert row['대표 행동']==r['name_ko'] and row['행동 종류']==kind_labels[r['kind']]
    for label,key in [('기록 수','record_count'),('출처 수','source_count'),('근거 후보 기록','candidate_records'),('제안 기록','proposal_records'),('재검토 기록','review_records')]:
        assert int(row[label])==r[key],(r['concept_id'],label)
sequence_rows,_=read_sheet(sheet_numbers['행동연쇄'])
steps={r['단계 ID']:r for r in sequence_rows}
for r in catalog['v_sequence_steps']:
    row=steps[r['step_id']]
    assert (row['기록 ID'],row['대표 행동'],int(row['단계']),row['공통 틀'])==(r['record_id'],r['concept_name'],r['position'],r['template_id'])
checks['representative_behaviors_match']=len(concepts)
checks['sequence_steps_and_repeats_preserved']=len(steps)
checks["nine_sheets_tables_filters_frozen_headers"]=True
con=sqlite3.connect(DB/"nana-behaviors.sqlite")
assert con.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
assert con.execute("PRAGMA foreign_key_check").fetchall()==[]
con.close()
assert all(hashlib.sha256((ROOT/r["local_file"]).read_bytes()).hexdigest()==r["sha256"] for r in catalog["documents"])
checks["all_source_document_hashes_match"]=len(catalog["documents"])
checks["sqlite_integrity"]="ok"
checks["source_date"]= "2026-10-17"
(OUT/"xlsx-validation.json").write_text(json.dumps(checks,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(checks,ensure_ascii=False,indent=2))

