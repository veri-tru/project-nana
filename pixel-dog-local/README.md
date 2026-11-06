# 반려견 픽셀 캐릭터 앱

새 개체 표현: [잭 러셀 귀 3종 비교](outputs/jack-russell-ear-study-20261106/README.md). 승인된 A를 기준으로 접힌 귀·반쯤 선 귀·선 귀를 비교했으며 선택은 대기 중이다.

새 픽셀 화풍 시안: [잭 러셀 B2 3안](outputs/jack-russell-b2-20261106/README.md). 골격 B를 참조한 3행×5시점 고해상도 비교판이며, A 기준·B 옅은·C 깊은 음영이다. 흰 얼굴과 갈색 귀는 제작 배색이며 사용자 선택은 첫 행 A(기준 음영)다.

새 골격 후보: [잭 러셀 테리어 머리·턱 3안](outputs/jack-russell-head-v1/README.md). 주둥이 길이 -6% / 기준 / +6%를 같은 실제 3D 모델의 다섯 시점과 턱 회전으로 비교한다.

현재 머리 화풍: [기존 B2 품종 시안 정본](references/styles/breed-head-b2/v1/manifest.json). [골든 재작화](outputs/golden-b2-canonical-20261106/README.md)는 수정 adult-B 형상을 이 화풍으로 표현한 고해상도 시안이며, 사용자 선택은 첫 행 A(기준 음영)다. 앞선 native64 골든 3안은 화풍 불일치로 REJECTED/BLOCKED이며 현재 추천안이 아니다.

이전 구현 기록: [체급·품종·개체 계층형 머리 엔진](tools/head_engine/README.md)과 [골든 64×64 픽셀 3안](outputs/golden-pixel-refresh-20261106/README.md). 수정 B 골격을 작업 기준으로 5시점을 직접 출력했다. 머리/짧은 목 범위이며 형상·화풍의 사용자 선택은 대기 중이다.

엔진 저장 지점: [머리 엔진 v2/13 체크포인트](docs/head-engine-checkpoint.md) — 2026-11-06, 현재 B안과 A/C 비교안·재생성 입력·검토 기록 보존.

2026-11-06 현재: `skull-based-heads-v2` 13의 A/B/C가 독립 외형·기술 PASS와 전달 검사 READY를 통과했다. 검은 코는 v1 B의 실제 정점을 보존하고, 얼굴 연결은 피부 정점을 다듬었으며 귀는 품종별로 구성했다. 사용자 선택은 PENDING이다. 이전 `skull-based-heads-v1`은 사용자가 거절한 REJECTED / BLOCKED 이력으로 유지한다.

현재 작업: [검은 코 복구·얼굴 연결·품종별 귀 A/B/C](outputs/skull-based-heads-v2/README.md). 60셀 외형 검토, 12개 실제 메시 검증, 전체 재생성 및 전달 검사 완료. 골든·닥스 귀뿌리의 작은 캡 형태는 MINOR로 기록했다. 이 체크포인트 당시 실제 모델 학습과 픽셀 간략화는 미실행이었다. 이후 골든 native64 출력은 화풍 불일치로 거절됐으며 현재 B2 재작화는 위 안내를 따른다.

기반 골격: [공통 머리 골격의 입체 구조 후보 06](outputs/head-skeleton-volume-v2/README.md)이 독립 외형·기술 검토와 전달 검사를 통과했다. 사용자 선택은 대기 중이다. 학습 참고 기반을 먼저 잡고 픽셀 간략화는 이후 진행한다. 실제 모델 학습은 아직 실행하지 않았다. 이전 선 도해 `head-skeleton-v1`은 구조 FAIL / 전달 BLOCKED 이력으로 보존한다.

이전 머리 외피 후보: [네 개체의 머리·턱·짧은 목 v2](outputs/head-neck-volume-v2/README.md). 독립 외형·기술 리뷰와 재생성 검사를 통과한 정적 후보이며 사용자 최종 승인은 대기 중입니다.

나나의 64×64 갸웃한 앉기는 중간 음영 ②를 선택했다. [엔진 재출력과 4색 음영 규격](tools/static_maker/README.md) · [선택된 앉기 원본](private-data/nana-seated-medium-v1/export/standing.png)

핵심 개발 목표는 여러 강아지에 같은 제작 절차를 적용하면서 각자의 특징을 살리는 **공통 픽셀 캐릭터 제작 엔진**이다. 나나는 첫 검증 개체다. [프로젝트 개요](docs/project-brief.md) · [재사용 검증 로드맵](docs/roadmap.md)

[한 개체 정적 제작기 0.3](tools/static_maker/README.md): 목·어깨·골반·앞발과 얼굴 구조를 보완하고, 0.2/0.3 복원·로컬 편집·자체 이미지 포함 전후 비교를 구현했습니다. 자동 검사 22개와 기존/신규 브라우저 검증을 통과했습니다. 닮음·정본 화풍·실기기 검수는 남아 있으며 사진 자동 분석·동작·앱은 미구현입니다.

실제 반려견의 외형과 관찰된 습관을 작은 2D 픽셀 캐릭터에 반영하는 모바일 앱의 로컬 개발 준비 패키지입니다. 작업용 폴더명은 `pixel-dog-local`이며 서비스명은 미정입니다.

현재는 로컬 정적 제작기 구현과 시각 검수 단계입니다. Android/iOS 앱, 분석 서버, 배포 설정은 아직 구현하지 않았습니다.

전체 기획은 [기획 종합 정리](docs/planning-summary.md)에서 먼저 확인합니다. 고객 가설, 사진·응답 기반 행동 개인화, 행동 DB 2.0.0, 외형 자료 활용안, 중간점검 A/B와 개발 순서를 한 문서에 정리했습니다.

해상도·입력 방식 등 사양의 확정 상태는 [현재 사양](docs/current-spec.md), 품종 자료를 실제 개체와 동작 자산에 연결하는 규칙은 [개체 개인화 설계](docs/personalization-spec.md)를 봅니다. 2026-10-18 보완안은 설계 초안이며 실제 자산 지원과 검증 완료를 뜻하지 않습니다.

현재 [세부 로드맵](docs/roadmap.md)은 프로필 저장 → 정적 제작기 → 다른 개체 재사용 → 동작 → 사진 입력·사용자 3단계 → Android 통합 순서입니다. 시안 첨부 의존을 줄이는 제작기와 G0 병행 검증, 8–12주 배치안·첫 10영업일·단계별 통과 조건을 담았습니다. 인력·기간·표본은 제안입니다. 정적 제작기 핵심은 구현했으며 닮음·정본 미감·실기기 검수와 후속 동작·제품 통합은 진행 전입니다. [이전 로드맵](docs/roadmap-20261019.md)은 이력으로 보존합니다.

## 시작 순서

1. 이 폴더 전체를 원하는 작업 위치에 압축 해제합니다.
2. Codex 또는 사용하는 코드 편집기에서 이 폴더를 프로젝트 루트로 엽니다.
3. [AGENTS.md](AGENTS.md), [프로젝트 개요](docs/project-brief.md), [현재 결정 기록](docs/decisions.md), [개발 인수인계](docs/handoff.md)를 읽습니다.
4. [로컬 시작 프롬프트](prompts/start-local.md)를 사용해 Android G0 개발 환경 점검부터 진행합니다.
5. 시안은 [참고 시안 목록](references/previews/index.html)을 브라우저로 열어 확인합니다. 별도 서버나 설치가 필요 없는 복사본입니다.

## 이번 패키지에 포함한 것

- 기획·문헌·시장·경쟁사·GitHub 조사 문서 10개와 원문 스냅샷
- 확정 사항, 개발 기본안, 미결정 사항을 구분한 결정 기록
- Android G0 작업 목록과 수동 검증 기록 양식
- 8fps 애니메이션 자산 규격 초안과 기계가 읽을 수 있는 프로젝트 설정
- 기존 해상도·96×96 움직임·fps 비교 HTML 시안 4개
- Git 제외 규칙과 문서·자산 출처 기록

## 핵심 기준

| 항목 | 현재 기준 |
| --- | --- |
| 대상 | 개. 고양이는 후속 프로젝트 |
| 표현 | 머리 화풍은 기존 B2 품종 시안 정본 `breed-head-soft-B2-v1`. C2는 이전 비교 이력 |
| 애니메이션 | 기본 8fps, 기본 프레임 유지 125ms |
| 해상도 | 픽셀 정본은 프레임당 64×64px. 96×96은 기존 제작기·시안의 참고 해상도 |
| 개발 순서 | Android 플로팅 G0 → 한 마리 개인화 G1 → 탐색 파일럿 G2 → 양 플랫폼·위젯 G3 |
| 첫 G0 | 걷기·쉬기·잠든 자세, 탭·드래그, 켜기·끄기·권한·종료 |
| 행동 재생 | 기기 내 규칙과 사전 제작 자산. 프레임마다 AI 호출하지 않음 |
| AI 분석 | 후속 G1. 보호자가 확인한 후보만 프로필에 적용 |

현재 머리 작화 기준은 [B2 현재 규격](docs/b2-c2-style-spec.md)과 [품종 시안 정본 manifest](references/styles/breed-head-b2/v1/manifest.json)입니다. 기존 B2의 픽셀 밀도·유색 윤곽·음영을 공통 적용하고 형상은 최신 품종/개체 모델을 따릅니다.

## 폴더 안내

| 경로 | 내용 |
| --- | --- |
| [docs/planning-summary.md](docs/planning-summary.md) | 현재 기획, 결정 상태, 준비 자료와 다음 작업 |
| [docs/roadmap.md](docs/roadmap.md) | 사용자 경험을 구현·검증하는 주차별 계획과 완료 조건 |
| [docs/current-spec.md](docs/current-spec.md) | 공통 사양의 확정값·설계 방향·미결정 항목 |
| [docs/personalization-spec.md](docs/personalization-spec.md) | 개체 외형·행동·부품·클립 연결과 검수 기준 |
| [docs/project-brief.md](docs/project-brief.md) | 제품·기술 범위 |
| [docs/decisions.md](docs/decisions.md) | 결정과 미결정 사항 |
| [docs/handoff.md](docs/handoff.md) | 로컬 개발을 이어갈 방법 |
| [docs/backlog.md](docs/backlog.md) | 단계별 작업과 완료 기준 |
| [docs/asset-spec.md](docs/asset-spec.md) | 픽셀 자산과 시간 규격 초안 |
| [docs/research-index.md](docs/research-index.md) | 보존 문서 10개와 근거 링크 |
| [docs/archive](docs/archive) | 기존 문서의 로컬 Markdown 사본 |
| [references/previews/index.html](references/previews/index.html) | 독립 실행 가능한 참고 시안 |
| [provenance/README.md](provenance/README.md) | 원문·변환 기록과 파일 해시 |
| [config/project.json](config/project.json) | 상태가 명시된 개발 설정 |
| [templates/device-check.md](templates/device-check.md) | G0 기기 확인 기록 |
| [THIRD_PARTY.md](THIRD_PARTY.md) | 외부 코드·자산 도입 시 기록 기준 |

이전 문서는 당시 조사와 설계를 보존한 것입니다. 현재 작업에는 최신 사용자 지시와 `docs/decisions.md`를 적용하고, 변경 가능한 API·모델·가격·OS 정책은 실제 도입 시 공식 자료로 다시 확인합니다.


## 행동 DB 보완

2026-10-17 [중복·분류 검토 후 보완](reviews/behavior-db-2026-10-17/implementation.md)을 반영했습니다. [행동 DB](data/behavior-db/README.md) 2.0.0은 원기록 ID 307개를 유지하며 대표 행동 121개, 자세·동작 속성 70행, 관계 43개, 설계 연쇄 8개로 연결합니다. 기존 긍정·부정·일상 조사와 원수집 자료는 보존하고 정정 전후를 기록했습니다. Excel은 대표행동·개인화항목·행동연쇄를 포함한 9개 시트입니다.
