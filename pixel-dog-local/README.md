# 반려견 픽셀 캐릭터 앱

[한 개체 정적 제작기 0.2](tools/static_maker/README.md): 관찰/제작 상태 분리, 연결점 기반 얼굴·앉은 전신, 5부위 털·눈 가림, B2/C2 비교와 로컬 편집·저장·복원을 구현했습니다. 자동 검사 14개와 실제 브라우저 검증을 통과했습니다. 정본 화풍·닮음은 검토 대기이며 사진 자동 분석·동작·앱은 미구현입니다.

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
| 표현 | B2·C2 비교 정본 v1.0. 최종 단일 화풍은 미선택 |
| 애니메이션 | 기본 8fps, 기본 프레임 유지 125ms |
| 해상도 | 최종 미정. 64×64 검토 기록과 96×96 참고 시안을 함께 보존 |
| 개발 순서 | Android 플로팅 G0 → 한 마리 개인화 G1 → 탐색 파일럿 G2 → 양 플랫폼·위젯 G3 |
| 첫 G0 | 걷기·쉬기·잠든 자세, 탭·드래그, 켜기·끄기·권한·종료 |
| 행동 재생 | 기기 내 규칙과 사전 제작 자산. 프레임마다 AI 호출하지 않음 |
| AI 분석 | 후속 G1. 보호자가 확인한 후보만 프로필에 적용 |

현재 작화 기준은 [B2·C2 세부 규격](docs/b2-c2-style-spec.md)과 [정본 원본·manifest](references/styles/b2-c2/v1/manifest.json)입니다. B2의 부드러운 유색선과 C2의 짙은 윤곽을 동일 개체에 비교하며, 얼굴형·눈꺼풀은 개체별로 유지합니다.

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
