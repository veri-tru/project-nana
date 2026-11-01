"""Record the authorized policy v1.0 and frame-candidate delivery; no research DB rebuild."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[2]
out=Path(__file__).resolve().parent
protected=list((root/'outputs/dog-crayon-p1-policy-20261101').glob('*.png'))+list((root/'outputs/dog-crayon-outline-levels-20261101').glob('*.png'))+[root/'data/behavior-db'/f for f in ['catalog.json','manifest.json','nana-behaviors.sqlite']]
before={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
def edit(rel,old,new):
 p=root/rel;s=p.read_text(encoding='utf-8');assert old in s,(rel,old);p.write_text(s.replace(old,new,1),encoding='utf-8')
def insert(rel,text):
 p=root/rel;s=p.read_text(encoding='utf-8');head,tail=s.split('\n',1);p.write_text(head+'\n\n'+text.strip()+'\n'+tail,encoding='utf-8')
def append(rel,text):
 p=root/rel;s=p.read_text(encoding='utf-8');p.write_text(s.rstrip()+'\n\n'+text.strip()+'\n',encoding='utf-8')
edit('docs/facial-motion-policy.md','상태: **정책 연결 초안 / 자산·재생 검증 전**.','상태: **제작 정책 정본 v1.0 / 2026-11-01 정본화 / 자산·재생 승인 별도**.\n\n사용자의 ‘2번까지’ 지시에 따라 정책 정본화와 P1 세 장면 연속 프레임 후보 제작을 진행했다. 이 문서의 부위별 정의·접촉·충돌·점눈 표현·복귀 규칙을 현재 제작 기준으로 사용한다. 문헌의 관찰 범위와 제작 규칙을 구분하며, 후순위 후보·미정 값은 확정값으로 승격하지 않는다. 세부 상황 규칙은 [상황 정책 v1.0](contextual-motion-policy.md), 변경 결정은 [결정 기록](decisions.md)을 따른다.')
edit('docs/contextual-motion-policy.md','상태: **사용자 요청에 따른 정책 정비 / 세부 연결 규칙은 설계안 / 런타임·자산 검수 전**.','상태: **제작 정책 정본 v1.0 / 2026-11-01 정본화 / 런타임·자산 승인 별도**.\n\n사용자의 ‘2번까지’ 지시에 따라 9개 상황 ID·선택 조건·부위 조합·충돌·중단·현재 상태 복귀·필수 기록 항목을 제작 기준으로 확정한다. 정본화는 이 문서를 후속 제작의 기준으로 삼는다는 뜻이다. 개체 습관, 자연적인 행동 순서·지연, 자산 품질, 런타임 구현을 승인한 것은 아니다. 아래 선택 후보와 미정 수치는 계속 그 상태로 남긴다.')
edit('docs/contextual-motion-policy.md','이번 정비는 문서 설계이며 실제 반응 엔진이나 새로운 입력 기능을 구현한 것은 아니다.','실제 반응 엔진이나 새로운 입력 기능은 미구현이다. [P1 연속 프레임 후보](../outputs/dog-crayon-p1-sequences-20261101/README.md)는 이 규칙을 시각화한 제작물이며 실행 준비 자산과 구분한다.')
edit('docs/contextual-motion-policy.md','이 표는 구현 전 데이터 계약안이다.','이 표는 v1.0의 필수 기록 계약이다. 구현은 아직 수행하지 않았다.')
edit('docs/contextual-motion-policy.md','현재는 설계 문서만 있으며 해당 상태의 규칙이나 실행 자산이 없다.','현재 P1 세 장면은 제작 프레임과 미리보기 시간표만 있다. 실행 준비 상태의 규칙·앱 자산은 없으며 나머지 6개 상황도 자산 미제작 상태다.')
append('docs/contextual-motion-policy.md','''## 11. v1.0 적용과 P1 제작값

- 정본의 범위: 9개 CTX 상황, 공유 사건·대상·반응 ID, 부위 소유와 충돌, 같은 대상 갱신 시 재시작 금지, 유효성·만료·취소, 현재 상태 재평가 복귀, 미정 값의 실행 금지.
- 자산 기준: 작은 점눈과 개체 무늬·비율을 유지하며, 최신 [약한 외곽선 A](../outputs/dog-crayon-outline-levels-20261101/README.md)를 후속 화풍 기준으로 쓴다. 눈동자 방향은 독립적으로 표현하지 않고 머리 방향으로 대상 확인을 전달한다.
- [제작 후보 v0.1](../outputs/dog-crayon-p1-sequences-20261101/README.md): A 쉬면서 옆 확인 12장/2.5초, B 걷는 중 후측방 확인 12장/1.5초, C 장난감↔사람 확인 12장/3초. 기본 간격 125ms이며 A·C의 정지 구간에는 같은 프레임을 더 오래 표시한다.
- 이번 세 장면은 열린 입·짧은 혀 보임을 진입 전부터 가진 제작 변형이다. 대상 등장 때문에 입이 열리거나 헐떡이는 규칙이 아니다. A에만 1프레임의 닫힌 눈을 넣는다. 코 핥기·입술 쓸기·AU101은 이번 산출물에 포함하지 않는다.
- 미리보기 사건은 버튼으로 한 번 시작하고 마지막 프레임에서 끝난다. 입력 지연 0ms, 반복 상한 1회, 자동 재실행 없음, 대상은 장면 종료까지 유효한 가상 대상이다. 일반 런타임의 재실행 대기·만료값을 이 값으로 고정하지 않는다.
- 모든 수치는 제작 기본값이다. 문헌 실측이나 이 개의 반응 지연·빈도가 아니다. 프레임 시퀀스는 합쳐진 그림이며 독립 부위 제어 엔진이 구현된 것은 아니다.
- 3단계: 8fps 재생 자연스러움, 목·귀·무늬·발 접지와 프레임 경계, 실제 표시 크기, 중단/대상 갱신과 복귀를 검수한다. 최종 해상도·개체 닮음·사용자 승인은 별도다.
''')
edit('docs/facial-motion-policy.md','현재 [P1 내부 기준 수정안](../outputs/dog-crayon-p1-policy-20261101/README.md)은 1254×1254 크레용풍 정적 후보다.','자세 참고는 [P1 내부 기준 수정안](../outputs/dog-crayon-p1-policy-20261101/README.md), 최신 선·채움 참고는 [약한 외곽선 A](../outputs/dog-crayon-outline-levels-20261101/README.md)다. 1254×1254 참고 원본과 별도로 [세 장면의 362×362 연속 프레임 후보](../outputs/dog-crayon-p1-sequences-20261101/README.md)를 만들었다. 이 크기는 생성 시트의 셀 크기이며 최종 자산 해상도를 확정하지 않는다.')
append('docs/decisions.md','''## 2026년 11월 1일 상황·얼굴 동작 정책 정본화

- 사용자 지시: 다음 단계 중 ‘2번까지’ 수행. 1단계 정책 정본화, 2단계 P1 세 장면의 시작·반응·복귀 연속 프레임 후보 제작.
- 이전: 부위별 얼굴 정책과 9개 상황 연결 규칙은 문서 초안. P1 장면 3개는 제작 계획.
- 현재: [얼굴·시선 정책](facial-motion-policy.md)과 [상황별 연결 정책](contextual-motion-policy.md)을 제작 정본 v1.0으로 관리한다. 사건·대상·진행 단계를 공유하고 시선/머리/몸/이동과 입술/턱/혀는 구분한다. 부위 충돌·중단·현재 상태 복귀·미정 값 실행 금지를 필수로 적용한다.
- 제작 기준: 수정된 점눈·개체 특징과 현재 선택된 약한 외곽선 A. 8fps·125ms 기준을 유지하며 최종 원본 해상도와 표시 크기는 미정이다.
- 결과: [P1 세 장면 후보 v0.1](../outputs/dog-crayon-p1-sequences-20261101/README.md), 12장씩 총 36장과 단계별 시간표. 정지/유지 시간은 제작값이고 개체 관찰값이 아니다.
- 승인 경계: 정책을 제작 기준으로 정본화한 것이며 생성 그림의 최종 닮음·연속성·실기기·사용자 승인은 아니다. 3단계 재생 검수와 실제 앱 구현은 미실시다.
- 조사 DB 2.0.0의 DOC05가 참조한 이 문서의 이전 바이트는 [출처 스냅샷](../data/behavior-db/source-snapshots/decisions-20261017.md)에 보존한다. 조사 DB·SQLite·Excel은 재빌드하지 않고 이번 결정과 제작 프레임을 기존 관찰 근거에 소급 편입하지 않는다.
- 영향: 이 결정 기록, 얼굴/상황 정책, 현재 사양, 자산 규격, 연구 색인, 작업 목록과 인계, 세 장면 제작 폴더.
''')
edit('docs/current-spec.md','2026-11-01 정책 반영안 작성. 자산·재생·개체 검수 전','제작 정책 정본 v1.0. P1 세 장면 후보 제작, 자산·재생·개체 승인 전')
edit('docs/current-spec.md','사용자 방향 반영, 세부 규칙 설계안·런타임 미구현','9개 상황의 제작 정책 정본 v1.0·런타임 미구현')
edit('docs/asset-spec.md','문서 연결 단계이며 새 프레임·실행 자산·눈 방향 표현·실기기 검수는 미실시입니다.','정책은 제작 정본 v1.0이며 [세 장면 연속 프레임 후보](../outputs/dog-crayon-p1-sequences-20261101/README.md) 36장을 제작했습니다. 눈동자만의 방향 표현·앱 실행 자산·3단계 재생 및 실기기 검수는 미실시입니다.')
edit('docs/research-index.md','2026-11-01 작성, 자산 검수 전','2026-11-01 제작 정본 v1.0, 자산 승인 별도')
edit('docs/research-index.md','사건·대상·활동, 동작 묶음, 중단·복귀의 설계안','제작 정본 v1.0. 9개 상황, 동작 묶음, 중단·복귀 기준')
insert('docs/backlog.md','''## 2026-11-01 정책 정본화와 P1 연속 프레임

- [x] 얼굴·상황 정책을 제작 정본 v1.0으로 정리하고 결정 기록에 반영.
- [x] P1 세 장면 12장씩 36개 프레임 후보와 시간표·미리보기 제작. [산출물](../outputs/dog-crayon-p1-sequences-20261101/README.md)
- [x] 현재 선택된 약한 외곽선 A를 생성 참조로 적용. 전체 닮음·선 강도 정합성 최종 승인은 별도.
- [ ] 3단계: 재생 자연스러움·몸 고정과 보행 접지·실제 표시 크기·복귀 경계 검수 및 보완.
- [ ] 실제 반응 엔진 구현과 대상 갱신/소멸/중단/현재 상태 복귀의 실행 검증.
- [ ] 생성 자산의 사용자 승인과 개체별 습관 확인.
''')
insert('docs/handoff.md','''## 최신 인계: 2026-11-01 정책 v1.0 + 세 장면 후보

사용자가 요청한 ‘2번까지’ 범위로 [얼굴 정책](facial-motion-policy.md)과 [9개 상황 정책](contextual-motion-policy.md)을 제작 정본 v1.0으로 정리했다. [연속 프레임 후보](../outputs/dog-crayon-p1-sequences-20261101/README.md)는 각 12장, 총 36장이다. 최신 약한 외곽선 A를 참조했고 시작·확인·복귀 시간표와 재생/프레임 보기 화면을 함께 저장했다. 정책 정본과 그림 후보 승인은 별개다.

다음은 3단계 재생 검수다. 쉬기/앉기 몸통의 미세한 변화, 걷기 발 접지와 머리 회전 폭, 귀·무늬 유지, 마지막→첫 프레임 경계를 중점 확인한다. 현재 미리보기는 고정 가상 대상·제자리 걷기이며 실제 이동·동적 취소 엔진은 없다. 최종 해상도, 실기기, 사용자 닮음·동작 승인은 미정이다.

decisions.md 변경 전 DOC05 출처는 별도 바이트 스냅샷으로 보존했다. DB 검증기는 현재 파일 해시가 다르면 DB에 기록된 해시와 정확히 같은 지정 스냅샷만 허용한다. 조사 DB/SQLite/Excel과 기존 P1/P2 원본은 이번 작업에서 변경하지 않는다. 아래 이전 작업 내역의 ‘초안/미제작’ 표기는 당시 이력이다.
''')
append('data/behavior-db/README.md','''## 활성 문서와 조사 당시 출처 버전

2026-11-01 동작 정책 정본화로 활성 docs/decisions.md에 새 결정이 추가됐다. DB 2.0.0의 DOC05 해시에 해당하는 원문은 [바이트 스냅샷](source-snapshots/decisions-20261017.md)과 [버전 매핑](source-snapshots/index.json)으로 보존한다. 새 정책은 기존 연구 결과로 소급하지 않는다. verify_behavior_organization.py는 DB에 고정된 해시가 현재 파일 또는 지정된 과거 스냅샷과 정확히 일치해야 통과한다. 보고서 경로를 첫 인자로 주면 과거 검증 보고서를 덮어쓰지 않는다. 향후 DB 재빌드의 문서 해시는 재빌드 시점의 출처를 기록하므로 버전 차이를 별도 검토한다.
''')
assert before=={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
(out/'preservation.json').write_text(json.dumps({'unchanged':before},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('policy v1.0 recorded; protected assets unchanged:',len(before))
