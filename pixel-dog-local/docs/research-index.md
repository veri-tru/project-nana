# 기획과 조사 문서 목록

기준일: 2026-10-18. 현재 기획, 누적 조사와 과거 보존 문서를 구분한 자료 목록입니다. 전체 내용은 [기획 종합 정리](planning-summary.md)에서 시작합니다.

## 현재 작업에 사용하는 문서

| 목적 | 문서 |
| --- | --- |
| 제품·고객·개인화·개발 단계 전체 파악 | [기획 종합 정리](planning-summary.md) |
| 목표 사용자 경험과 주차별 실행 계획 | [세부 로드맵](roadmap.md) |
| 확정 방향과 가설 구분 | [결정 기록](decisions.md), [프로젝트 개요](project-brief.md) |
| 현재 사양의 확정 상태 | [현재 사양](current-spec.md) |
| 개체 외형·부품·동작 연결 | [개체 개인화 설계](personalization-spec.md), [한 마리 검수 양식](../templates/pet-likeness-review.md) |
| 사용자 니즈와 입력·구매 검증 | [고객 가설과 니즈 조사](customer-needs-2026-10-17.md) |
| 구현 순서와 현재 상태 | [작업 목록](backlog.md), [인수인계](handoff.md) |
| 픽셀·프레임·접지·자산 메타데이터 | [자산 규격 초안](asset-spec.md) |
| 안면근육·입술·턱·혀와 동작 조합 | [얼굴·시선 움직임 정책 반영안](facial-motion-policy.md). 2026-11-01 제작 정본 v1.0, 자산 승인 별도 |
| 상황에 맞는 시선·표정 선택과 전환 | [상황별 연결 정책](contextual-motion-policy.md). 제작 정본 v1.0. 9개 상황, 동작 묶음, 중단·복귀 기준 |
| 눈·머리·몸·이동 분리의 근거 | [시선 문헌과 SNS·공개 보고](gaze-motion-research-20261101.md). 눈추적과 머리 방향 코딩, 원영상 미검증을 구분 |
| 행동 후보와 원근거 | [행동 DB 2.0.0](../data/behavior-db/README.md) |
| 품종별 외형 자료의 활용 | [외형 자료 검토](../reviews/appearance-assets-2026-10-17/report.md) |

## 기존 프로젝트 문서 보존본

아래 10개 문서는 가져온 당시의 조사와 설계입니다. 현재 입력 방식은 사진·응답 중심 방향을 우선하며, 공급자·모델·가격·OS 정책은 도입 시 다시 확인합니다.

| 문서 | 로컬 사본 | 원본 시퀀스 |
| --- | --- | --- |
| 반려견 디지털 트윈 앱 개발 지침과 첫 시제품 범위 | [열기](archive/00_project_guidance.md) | 7 |
| 반려견 데이터 수집 목록과 위계 및 우선순위 | [열기](archive/01_data_hierarchy.md) | 0 |
| 개의 개체 인식을 위한 행동과 습관 문헌검토 | [열기](archive/02_dog_identity_literature.md) | 1 |
| 반려견 2D 3D 움직임 구현 문헌과 적용안 | [열기](archive/03_animation_literature.md) | 0 |
| Jev와 스마트폰 데이터 기반 반려견 개인화 구현 검토 | [열기](archive/04_jev_feasibility.md) | 0 |
| Claude Haiku 5.5 기반 반려견 앱 상세 기획과 설계 | [열기](archive/05_detailed_design.md) | 2 |
| 반려견 개인화 앱 목표 사용자와 시장 및 경쟁사 분석 | [열기](archive/06_market_competitors.md) | 1 |
| 반려견 앱 경쟁사의 매출 구조와 사업 현황 | [열기](archive/07_competitor_revenue.md) | 0 |
| Pixel Pals 벤치마킹과 반려견 앱 적용안 | [열기](archive/08_pixel_pals_benchmark.md) | 0 |
| 픽셀 반려견 외형과 움직임 구현을 위한 GitHub 조사 | [열기](archive/09_github_research.md) | 0 |

현재 개발 기준은 [프로젝트 개요](project-brief.md)와 [결정 기록](decisions.md)를 확인합니다. 시퀀스는 원본 문서 수정 번호로 앱 버전이 아닙니다.

## 누적 조사와 검토

| 자료 | 내용과 현재 해석 |
| --- | --- |
| [시각적 습관 요소](../exa-results/dog-behavior-2026-10-17/report.md) | 행동 정의·개체차, 우선 개인화 후보와 사진·응답 기반 fitting. 몸 털기·기지개를 별도 포함 |
| [커뮤니티 일상 행동](../exa-results/dog-community-habits-2026-10-17/report.md) | 19개 게시글·원수집 23행. 보호자 보고와 건강·교정·보류 맥락 분리, 네이버 카페 본문 미확보 |
| [신뢰 관련 행동](../exa-results/dog-trust-2026-10-17/report.md) | 문헌 9편의 애착·안전기지·사회적 참조·정보 신뢰. 개별 자세를 신뢰 점수로 사용하지 않음 |
| [긍정적 행동 확장](../exa-results/dog-positive-behavior-2026-10-17/report.md) | 놀이·접촉·탐색·휴식·기대의 맥락과 해석 한계 |
| [부정적 행동](../exa-results/dog-negative-behavior-2026-10-17/report.md) | 공포·불편·좌절·경계·분리·반복·자원 통제와 문제·건강 맥락 분리 |
| [중립적인 일상 행동](../exa-results/dog-neutral-behavior-2026-10-17/report.md) | 자세·이동·탐색·먹기·배설·몸 관리 등. 일상 분류를 감정·정상성 판정으로 해석하지 않음 |
| [추가 후보 전체 포함](../exa-results/dog-additional-behaviors-2026-10-17/report.md) | 제안 목록 28항목을 근거 확보·기존 자료 재사용·확인 대기로 연결 |
| [행동 DB 2.0.0](../data/behavior-db/README.md) | 현재 307개 기록·121개 대표 행동·91개 출처. 누적 기록 수와 구현 동작 수는 다름 |
| [중복·통합 검토](../reviews/behavior-db-2026-10-17/report.md) | 보완 전 1.3.1 검토 기록. 현재 적용 상태는 아래 반영 결과 참조 |
| [DB 보완 반영](../reviews/behavior-db-2026-10-17/implementation.md) | 원기록 보존, 대표 행동·속성·상황 분리, 관계 43개·연쇄 8개, DB·Excel 검증 |
| [외형 자료 활용](../reviews/appearance-assets-2026-10-17/report.md) | 첨부 322종·9개 몸통 계열의 활용 검토. 별도 외형 사전과 개체·행동 프로필 연결은 제안 |

개별 조사 보고서의 당시 누적 건수는 역사적 기록입니다. 현재 총계는 DB 안내를 기준으로 확인합니다. 문헌·커뮤니티 근거, 제작 제안, 구현 완료와 고객 검증 결과를 구분합니다.

