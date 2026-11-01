import fs from "node:fs/promises";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {Workbook,SpreadsheetFile} from "@oai/artifact-tool";
const out=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(out,"../..");
const d=JSON.parse(await fs.readFile(path.join(root,"data/behavior-db/catalog.json"),"utf8"));
const wb=Workbook.create();
const status={candidate:"근거 후보",proposal_only:"설계·요구 후보",health_context_excluded:"건강 맥락 제외",problem_context_separate:"문제행동 맥락 분리",insufficient_detail:"자료 부족",owner_status_unclear:"보호자 여부 미확인"};
const claim={literature_observation:"문헌 관찰",literature_definition:"문헌 행동 정의",published_owner_report:"논문 내 보호자 보고",owner_report:"커뮤니티 보호자 보고",design_proposal:"설계 제안",user_requirement:"사용자 요구",reported_learned_behavior:"학습행동 보고"};
const basis={reported_sequence:"보고된 순서",reported_cooccurrence:"보고된 동시 발생",reported_alternative:"보고된 대안",study_sequence:"연구의 순서 관계",study_cooccurrence:"연구의 공동 발생",design_proposal:"설계 제안 순서"};
const positiveStatus={contextual_support:"맥락 관련",indirect_support:"간접 지지",owner_attribution:"보호자 해석",behavior_only:"행동 보고만",not_specific:"긍정성 비특이",negative_comparison:"부정 조건 비교"};
const positiveEvidence={controlled_comparison:"통제 조건 비교",observational_play_context:"놀이 맥락 관찰",acoustic_pilot:"음향 예비 연구",developmental_ethogram:"발달 행동 관찰",owner_survey:"보호자 행동 설문",preference_experiment:"선호 선택 실험",controlled_reunion:"재회 조건 비교",judgment_bias_intervention:"개입 후 인지 편향",observer_rating_experiment:"실험의 관찰자 평정",owner_perception_survey:"보호자 해석 설문"};
const negativeStatus={contextual_support:"맥락 관련",not_specific:"부정성 비특이",not_supported_here:"해당 비교에서 미확인",owner_reported_pattern:"보호자 보고 패턴",definition_only:"정의만 제시"};
const negativeEvidence={within_dog_video_comparison:"같은 개의 영상 비교",ethogram_definition:"행동 코딩 정의",acute_stimulus_experiment:"급성 자극 실험",quasi_experimental_training:"훈련 방식 준실험",reward_extinction_experiment:"보상 중단 실험",human_approach_experiment:"사람 접근 조건 비교",selected_video_observation:"선택된 영상의 관찰",separation_test_and_survey:"분리 시험·설문 연관",owner_behavior_survey:"보호자 행동 설문",expert_definition_study:"전문가 정의 연구",noise_playback_experiment:"소음 녹음 실험",existing_context_comparison:"기존 상황 비교 재사용"};
const kind={previous:"이전",next:"후속",concurrent:"동시",alternative:"대안"};
const neutralStatus={routine_observation:"일상 형태 관찰",elicited_observation:"유도 동작 관찰",owner_reported:"보호자 보고",definition_only:"정의만 제시",mixed_context:"혼합 맥락 형태 참고"};
const sourceKind={literature:"문헌",community:"커뮤니티",design_proposal:"설계 제안",user_requirement:"사용자 요구"};
const occ={PRESENT_REPORTED:"발생 보고",DEFINITION_ONLY:"정의만 제시",PROPOSED:"제안",ABILITY_REPORTED:"학습·수행 가능 보고",NO_CHANGE_REPORTED:"변화 없음 보고",DIFFICULTY_REPORTED:"어려움 보고"};
claim.literature_mention="문헌 본문 언급";occ.MENTION_ONLY="언급만 확인";
const conceptKind={posture_state:"자세·상태",action:"동작",transition:"전환",composite_activity:"복합 활동",aggregate_measure:"종합 지표",aggregate_behavior:"합산 행동",task_outcome:"과제 결과"};
const unit={study_summary:"연구 집단 요약",qualitative_user_report:"논문 질적 보고",survey_summary:"설문 집단 요약",proposed_scene:"제안 장면",feature_requirement:"기능 요구",anonymous_owner_report:"익명 보호자 보고",owner_report_multiple_dogs:"여러 개에 대한 보고"};
unit.expert_definition="전문가 정의 제안";
const text=v=>v===null||v===undefined?"미기재":String(v);
const displayBasis=v=>v? v.split(",").map(x=>basis[x]||x).join(", "):"미기재";
const sheets=[];
const taxonomyMap=Object.fromEntries(d.v_taxonomy.map(x=>[x.node_id,x]));
const orderedTaxonomy=[];
function visit(parent){for(const n of d.behavior_nodes.filter(x=>x.parent_id===parent)){orderedTaxonomy.push(taxonomyMap[n.node_id]);visit(n.node_id);}}
visit(null);
const taxonomyOrder=Object.fromEntries(orderedTaxonomy.map((n,i)=>[n.node_id,i]));
function col(n){let s="";for(n++;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;}
function tableSheet(name,headers,rows,widths,freeze=1){
 const s=wb.worksheets.add(name);s.showGridLines=false;
 const n=rows.length+1,last=col(headers.length-1),area=s.getRange(`A1:${last}${n}`);
 area.values=[headers,...rows].map(row=>row.map(v=>typeof v==="string"&&v.startsWith("=")?"'"+v:v));
 area.format.font={name:"Malgun Gothic",size:10,color:"#253047"};
 area.format.wrapText=true;area.format.verticalAlignment="top";
 for(let j=0;j<headers.length;j++)s.getRange(`${col(j)}1:${col(j)}${n}`).format.columnWidthPx=widths[j]||210;
 const tab=s.tables.add(`A1:${last}${n}`,true,"Data_"+(sheets.length+1));tab.showFilterButton=true;tab.style="TableStyleLight1";
 s.getRange(`A1:${last}1`).format={fill:"#28364D",font:{name:"Malgun Gothic",size:10,bold:true,color:"#FFFFFF"},rowHeightPx:44,verticalAlignment:"center",horizontalAlignment:"center",wrapText:true};
 for(let i=0;i<rows.length;i++){
  const lines=Math.max(...rows[i].map((v,j)=>{const st=v===null?"":String(v);const units=[...st].reduce((a,c)=>a+(c.charCodeAt(0)>255?1.8:1),0);return Math.ceil(units/((widths[j]||210)/7-2));}));
  s.getRange(`A${i+2}:${last}${i+2}`).format.rowHeightPx=Math.max(38,lines*19+12);
 }
 s.freezePanes.freezeRows(1);if(freeze)s.freezePanes.freezeColumns(freeze);
 sheets.push({s,name,headers,rows,last});
 return s;
}
const conceptMap=Object.fromEntries(d.behavior_concepts.map(x=>[x.concept_id,x]));
const nodeMapping=Object.fromEntries(d.node_concept_map.map(x=>[x.node_id,x]));
const organizedMap=Object.fromEntries(d.v_organized_records.map(x=>[x.record_id,x]));
tableSheet("대표행동",["대표 ID","대분류","대표 행동","행동 종류","연결된 세부 코드","기록 수","출처 수","근거 후보 기록","제안 기록","재검토 기록","정의","집계 주의"],
 [...d.v_concept_catalog].sort((a,b)=>taxonomyOrder[a.concept_id]-taxonomyOrder[b.concept_id]).map(r=>[r.concept_id,taxonomyMap[r.concept_id].domain,r.name_ko,conceptKind[r.kind],r.legacy_codes,r.record_count,r.source_count,r.candidate_records,r.proposal_records,r.review_records,r.definition,"기록 수는 발생 빈도·독립 개체 수가 아닙니다. 세부 자세와 상황은 행동기록에서 확인합니다."]),
 [190,160,260,160,410,95,95,125,105,120,500,380],2);
const rank=r=>r.inclusion_status==="candidate"?0:r.inclusion_status==="proposal_only"?1:2;
const rows=[...d.v_organized_records].sort((a,b)=>taxonomyOrder[a.behavior_id]-taxonomyOrder[b.behavior_id]||rank(a)-rank(b)||a.record_id.localeCompare(b.record_id)).map(r=>[
 r.record_id,r.domain,r.family,r.behavior,r.variant||"세부형 미지정",r.context_text||r.situation_name,
 text(r.trigger_text),text(r.previous_behavior),text(r.next_behavior),text(r.concurrent_behavior),text(r.alternative_behavior),
 text(r.target_text),text(r.body_part),text(r.laterality),text(r.posture_detail),text(r.frequency_text),
 r.duration_s,r.latency_s,r.repeat_count,text(r.duration_text),text(r.speed_text),
 claim[r.claim_type],unit[r.observation_unit]||r.observation_unit,occ[r.occurrence_status],
 status[r.inclusion_status],displayBasis(r.relation_basis),r.summary,r.limitation,
 r.source_report_id||"해당 없음",r.source_id,r.source_url||"로컬 기록",r.source_locator,
 r.positive_domain||"이번 확장 평가 없음",positiveEvidence[r.positive_evidence_type]||"이번 확장 평가 없음",
 positiveStatus[r.positive_interpretation]||"이번 확장 평가 없음",r.positive_evidence_summary||"해당 없음",
 r.positive_confounds||"해당 없음",r.positive_implementation_note||"해당 없음",
 r.negative_domain||"부정 맥락 평가 없음",negativeEvidence[r.negative_evidence_type]||"부정 맥락 평가 없음",
 negativeStatus[r.negative_interpretation]||"부정 맥락 평가 없음",r.negative_evidence_summary||"해당 없음",
 r.negative_confounds||"해당 없음",r.negative_implementation_note||"해당 없음",
 r.neutral_domain||"일상 맥락 평가 없음",r.neutral_evidence_type||"일상 맥락 평가 없음",
 neutralStatus[r.neutral_interpretation]||"일상 맥락 평가 없음",r.neutral_evidence_summary||"해당 없음",
 r.neutral_confounds||"해당 없음",r.neutral_implementation_note||"해당 없음",
 r.concept_name,conceptKind[r.concept_kind],r.context_domain,r.collection_method,r.facets_text||"미기재",r.unit_id,r.mapping_note
]);
const mainHeaders=["기록 ID","대분류","중분류","행동","세부 변형","상황","직전 자극","이전 행동","후속 행동","동시 행동","대안 행동","대상","신체 부위","좌우 방향","자세 특징","빈도 표현","지속시간 초","반응 지연 초","반복 횟수","지속시간 표현","속도 표현","근거 유형","관찰 단위","발생 상태","채택 상태","관계 근거","관찰 또는 제안 내용","해석 주의점","원수집 ID","출처 ID","출처 URL","근거 위치"];
const mainWidths=[140,160,170,190,195,280,210,190,190,190,190,200,145,120,300,310,115,115,110,260,200,205,200,205,215,250,410,460,135,110,440,270];
mainHeaders.push("긍정 맥락 영역","긍정 맥락 근거 방식","긍정 맥락 해석","긍정 맥락 근거 내용","긍정 맥락 혼동 요인","개인화 적용 주의");
mainWidths.push(205,225,210,420,470,420);
mainHeaders.push("부정 맥락 영역","부정 맥락 근거 방식","부정 맥락 해석","부정 맥락 근거 내용","부정 맥락 혼동 요인","부정 맥락 적용 주의");
mainWidths.push(215,235,225,430,490,440);
mainHeaders.push("일상 맥락 영역","일상 맥락 근거 방식","일상 맥락 해석","일상 맥락 근거 내용","일상 맥락 혼동 요인","일상 맥락 적용 주의");
mainWidths.push(215,235,225,430,490,440);
mainHeaders.push("대표 행동","행동 종류","통합 상황","수집 방식","자세·동작 속성","근거 단위","분류 대응 주의");
mainWidths.push(255,160,245,230,430,160,430);
const order=[0,1,2,3,4,5,7,8,21,24,50,51,52,53,54,55,56,6,9,10,11,12,13,14,15,16,17,18,19,20,22,23,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49];
const main=tableSheet("행동기록",order.map(i=>mainHeaders[i]),rows.map(r=>order.map(i=>r[i])),order.map(i=>mainWidths[i]),2);
main.tabColor="#28364D";
const displayColumn=i=>col(order.indexOf(i));
main.getRange(`${displayColumn(16)}2:${displayColumn(17)}${rows.length+1}`).setNumberFormat("0.00");
main.getRange(`${displayColumn(18)}2:${displayColumn(18)}${rows.length+1}`).setNumberFormat("0");
main.getRange(`J2:J${rows.length+1}`).conditionalFormats.add("containsText",{text:"제외",format:{fill:"#FDE9E7",font:{color:"#9A3028"}}});
main.getRange(`J2:J${rows.length+1}`).conditionalFormats.add("containsText",{text:"설계",format:{fill:"#FFF3D8",font:{color:"#76551D"}}});
const nodeMap=Object.fromEntries(d.behavior_nodes.map(x=>[x.node_id,x]));
tableSheet("행동위계",["분류 ID","상위 분류 ID","단계","대분류","중분류","행동","세부 변형","기록 가능","정의","대표 행동 ID","대표 행동","사용 상태"],
 orderedTaxonomy.map(r=>{const m=nodeMapping[r.node_id];return [r.node_id,r.parent_id||"없음",r.level,r.domain,r.family||"",r.behavior||"",r.variant||"",r.recordable?"가능":"분류 묶음",r.definition,m?.concept_id||"분류 묶음",m?conceptMap[m.concept_id].name_ko:"분류 묶음",({active:"기록 연결",parent_only:"하위형 묶음",candidate_unlinked:"기록 없는 후보"})[m?.lifecycle]||"분류 묶음"];}),
 [170,170,80,180,190,205,230,135,510,180,250,165],1);
const recordMap=Object.fromEntries(d.records.map(x=>[x.record_id,x]));
tableSheet("행동관계",["관계 ID","기준 기록 ID","기준 행동","관계","연결 행동","연결 기록 ID","관계 근거","설명","출처 ID"],
 d.relations.map(r=>[r.relation_id,r.record_id,nodeMap[recordMap[r.record_id].behavior_id].name_ko,kind[r.relation_type],nodeMap[r.related_behavior_id].name_ko,r.related_record_id||"행동 유형만 연결",basis[r.basis],r.note,recordMap[r.record_id].source_id]),
 [130,170,210,100,210,190,210,470,110],2);
const accessMap=Object.fromEntries(d.source_access_events.map(x=>[x.source_id,x]));
const source=tableSheet("출처",["출처 ID","출처 유형","인용 정보","제목","URL","발행연도","구간 날짜","확인 범위","표본 또는 단위","근거 위치","확인 이력","검토 시 재확인 범위","과거 이력 보존"],
 d.sources.map(r=>[r.source_id,sourceKind[r.source_type],r.citation,r.title,r.url||"로컬 기록",r.year,r.published_date?new Date(r.published_date+"T00:00:00Z"):null,r.access_scope,r.sample||"해당 없음",r.locator,r.verification_note,accessMap[r.source_id]?.scope||"이번 선택 재확인 대상 아님",accessMap[r.source_id]?.note||"기존 출처 정보 유지"]),
 [105,145,410,560,470,110,135,210,360,290,480,440,440],1);
source.getRange(`G2:G${d.sources.length+1}`).setNumberFormat("yyyy-mm-dd");
const raws=d.raw_reports.map(r=>{const o=JSON.parse(r.original_json);return [r.report_id,r.source_id,o.community,o.title,o.url,o.posted_date?new Date(o.posted_date+"T00:00:00Z"):null,o.segment,text(o.context),text(o.owner_report),text(o.owner_frequency),o.proposed_feature,status[o.status],o.access,o.caveat];});
const rawSheet=tableSheet("원수집",["원수집 ID","출처 ID","커뮤니티","제목","URL","기재 날짜","구간","상황 원기록","보호자 진술 요약 원기록","빈도 원기록","제안 요소 원기록","기존 분류","접근 범위","주의점 원기록"],
 raws,[135,110,190,390,470,135,240,330,480,360,350,220,160,480],2);
rawSheet.getRange(`F2:F${raws.length+1}`).setNumberFormat("yyyy-mm-dd");
const guides=[
 ["읽는 법","기록 단위","행동·상황·출처별 주장 1건","행 수는 실제 발생 횟수나 독립 개체 수가 아닙니다."],
 ["읽는 법","빈칸과 미기재","수치 빈칸 및 텍스트 미기재는 자료 없음","행동이 없다는 뜻이나 0초가 아닙니다."],
 ["읽는 법","위계 기준","1 영역 / 2 동작군 / 3 행동 / 4 변형","상황과 신뢰·행복 등의 해석은 행동 위계와 분리합니다."],
 ["읽는 법","원본과 편집","DB와 Excel은 누적 자료의 내보내기 결과","Excel 수정 사항은 SQLite에 자동 반영되지 않습니다."],
 ...d.field_dictionary.map(r=>[r.table_name,r.label_ko,r.description,r.missing_rule]),
 ...d.findings.map(r=>["종합 근거",r.finding_id+" / "+r.source_id,r.summary,r.limitation]),
 ...d.situations.map(r=>["상황 사전",r.situation_id,r.name_ko,"통합 상황·수집 방식은 행동기록에서 별도 확인"]),
 ...d.record_changes.map(r=>["기록 정정",r.record_id+" / "+r.field_name,`${r.before_json} → ${r.after_json}`,r.reason]),
 ...d.catalog_events.map(r=>["작업 이력",r.event_id,r.summary,r.note]),
 ...d.review_resolutions.map(r=>["검토 반영",r.review_id+" / "+r.title,r.resolution,r.status==="applied_with_boundaries"?"경계를 명시하고 별도 코드 유지":"반영"]),
 ...d.concept_links.map(r=>["통합 경계",r.left_concept+" / "+r.right_concept,r.note,"조건부 관계. 동의어로 합치지 않음"])
];
tableSheet("필드설명",["구분","항목","뜻 또는 내용","해석과 결측 기준"],guides,[175,245,640,580],1);
tableSheet("개인화항목",["항목 ID","개인화 항목","대표 행동","연결 기록","확인 상태","내용과 범위"],
 d.personalization_requirements.map(r=>[r.requirement_id,r.name_ko,conceptMap[r.concept_id].name_ko,d.requirement_records.filter(x=>x.requirement_id===r.requirement_id).map(x=>x.record_id+" ("+x.role+")").join(", "),r.status,r.note]),
 [210,260,240,460,195,580],2);
tableSheet("행동연쇄",["연쇄 ID","연쇄 이름","공통 틀","단계","단계 ID","기록 ID","대표 행동","단계 내용","근거"],
 d.v_sequence_steps.map(r=>[r.sequence_id,r.sequence_name,r.template_id,r.position,r.step_id,r.record_id,r.concept_name,r.summary,"설계 제안. 관찰된 고정 순서가 아님."]),
 [135,235,270,85,160,140,240,500,330],2);
wb.recalculate();
const inspection=await wb.inspect({kind:"table",range:"행동기록!A1:J6",include:"values",tableMaxRows:6,tableMaxCols:10,maxChars:2200});
await fs.writeFile(path.join(out,"inspection.txt"),inspection.ndjson);
const errors=await wb.inspect({kind:"match",searchTerm:"#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!",options:{useRegex:true,maxResults:20},maxChars:1800});
await fs.writeFile(path.join(out,"formula-check.txt"),errors.ndjson);
await fs.mkdir(path.join(out,"previews"),{recursive:true});
for(const {name,last}of sheets){
 const range=name==="필드설명"?"A1:D7":name==="행동위계"?"A1:I8":name==="행동관계"?"A1:I6":name==="출처"?"A1:D5":name==="원수집"?"A1:D5":name==="대표행동"?"A1:D7":name==="개인화항목"?"A1:F5":name==="행동연쇄"?"A1:G9":"A1:J7";
 const preview=await wb.render({sheetName:name,range,scale:1,format:"png"});
 await fs.writeFile(path.join(out,"previews",name+".png"),new Uint8Array(await preview.arrayBuffer()));
}
const output=await SpreadsheetFile.exportXlsx(wb);
const newRecordRow=order.length&&rows.findIndex(r=>r[0]==="E078")+2;
const positivePreview=await wb.render({sheetName:"행동기록",range:`${displayColumn(32)}${newRecordRow}:${displayColumn(37)}${newRecordRow+3}`,scale:1,format:"png"});
await fs.writeFile(path.join(out,"previews","긍정맥락.png"),new Uint8Array(await positivePreview.arrayBuffer()));
const negativeRow=rows.findIndex(r=>r[0]==="E127")+2;
const negativePreview=await wb.render({sheetName:"행동기록",range:`${displayColumn(38)}${negativeRow}:${displayColumn(43)}${negativeRow+2}`,scale:1,format:"png"});
await fs.writeFile(path.join(out,"previews","부정맥락.png"),new Uint8Array(await negativePreview.arrayBuffer()));
const negativeHeader=await wb.render({sheetName:"행동기록",range:`${displayColumn(38)}1:${displayColumn(43)}3`,scale:1,format:"png"});
await fs.writeFile(path.join(out,"previews","부정맥락머리글.png"),new Uint8Array(await negativeHeader.arrayBuffer()));
const neutralRow=rows.findIndex(r=>r[0]==="E168")+2;
const neutralPreview=await wb.render({sheetName:"행동기록",range:`${displayColumn(44)}${neutralRow}:${displayColumn(49)}${neutralRow+2}`,scale:1,format:"png"});
await fs.writeFile(path.join(out,"previews","일상맥락.png"),new Uint8Array(await neutralPreview.arrayBuffer()));
const neutralHeader=await wb.render({sheetName:"행동기록",range:`${displayColumn(44)}1:${displayColumn(49)}3`,scale:1,format:"png"});
await fs.writeFile(path.join(out,"previews","일상맥락머리글.png"),new Uint8Array(await neutralHeader.arrayBuffer()));
for(const [id,label] of [["E019","근거정정"],["E171","자세속성"],["U015","확인대기후보"]]){
 const start=rows.findIndex(r=>r[0]===id)+2;
 if(start<2)throw new Error(`Missing requested preview record ${id}`);
 for(const [left,right,suffix] of [["A","J","분류"],["K","Q","속성"]]){
  const preview=await wb.render({sheetName:"행동기록",range:`${left}${start}:${right}${start+1}`,scale:1,format:"png"});
  await fs.writeFile(path.join(out,"previews",`${label}-${suffix}.png`),new Uint8Array(await preview.arrayBuffer()));
 }
}
await output.save(path.join(out,"behavior-catalog.xlsx"));
console.log(JSON.stringify({file:path.join(out,"behavior-catalog.xlsx"),sheets:sheets.map(x=>({name:x.name,records:x.rows.length,columns:x.headers.length}))}));

