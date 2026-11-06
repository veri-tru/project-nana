# 엔진 구조와 현재 기준

기준일: 2026-11-06. `8671571`은 정리 전 전체 작업의 보존 커밋이다. 현재 변경은 실행 코드 분리와 상충 기준 정리이며, 새 형상·작화·사용자 승인을 만들지 않는다. PR 생성과 main 머지는 보류한다.

## 실행 경로

| 구분 | 현재 경로 | 역할과 경계 |
|---|---|---|
| 통합 명령 | `python -m tools.dog_engine` | 상태·환경 확인, 머리 렌더, 전신 CLI, 회귀 검사 |
| 머리 설정·검증 | `tools/dog_engine/head.py` | 체급 → 품종 → 개체 설정. 체급은 표시 배율이며 얼굴형이나 실측 cm가 아니다. |
| 머리 투영 | `tools/dog_engine/renderer.py`, `raster.py` | 검토된 저장 메시를 5시점으로 그린다. `outputs` 생성 코드를 실행하지 않는다. |
| 모델 카탈로그 | `tools/head_engine/catalog.json` | 5품종·9프리셋과 원본 해시를 보존한다. 현재와 과거 엔진이 같은 검토 모델을 읽는다. |
| 전신 제작기 | `tools/static_maker/render_v03.py`, `standing64.py`, `standing_parts.py` | 2D 작화 프로필·관찰 DB로 출력한다. 머리 메시에서 전신을 생성하지 않는다. |
| native64 머리 진단 | `tools/dog_engine/pixel.py` | 골든 P1/P2/P3 재현용. 명시적인 진단 호출만 허용하며 전달 상태는 BLOCKED다. |
| 보존 엔진·실험 | `tools/head_engine`, 기존 `outputs/*` | 모델·원본 코드·검토·실패 이력의 바이트를 유지한다. 신규 개발의 실행 진입점이 아니다. |

기존 `outputs`에는 모델과 검토 증거도 있으므로 결과 폴더라는 이유로 삭제하거나 이동하지 않는다. 활성 엔진은 그 데이터와 원본 코드의 해시를 확인하지만 과거 생성 코드는 import하지 않는다. 카탈로그와 리뷰에 기록된 비공개 입력도 검증 대상이므로, 실행 코드 분리가 곧 공개 저장소만으로 재현 가능한 배포 패키지 완성을 뜻하지는 않는다.

## 상충 항목과 적용 기준

| 기존 혼선 | 현재 적용 |
|---|---|
| 일부 문서·설정의 B2/C2 미선택 | 머리 화풍은 `breed-head-soft-B2-v1`. C2는 과거 비교 이력. 전체 전신/제품 실행 자산의 화풍 승인은 별도다. |
| A 선택과 B 기본 모델이 충돌하는 것처럼 보임 | 골든·잭 러셀의 **시안 첫 행 A** 선택과 **형상 B** 작업 기본값은 서로 다른 항목이다. 선택 JSON의 범위를 유지한다. |
| 기술 PASS면 픽셀 화풍도 승인된 것으로 해석 | 골든 native64 P1/P2/P3는 USER REJECTED / DELIVERY BLOCKED. 새 진단 출력도 자동 후보로 승격하지 않는다. |
| 귀 3종 시안이 귀 변형 기능처럼 보임 | 고해상도 선택 시안이며 선택은 PENDING. 엔진의 귀 교체·접힘·각도 조절은 미구현이다. |
| 머리와 전신을 하나의 연결된 엔진으로 해석 | 머리는 3D 메시 투영, 전신은 별도의 2D 작화. 자동 연결·전신 3D·연속 애니메이션은 미구현이다. |
| 96px 출력과 64px 정본 혼용 | 기존 정면 제작기는 96px 참고 출력, 자세별 작화는 실제 64px. 제품 목표는 64×64이며 고해상도 시안은 실행 자산이 아니다. |
| 당시 ‘현재’, ‘미구현’, ‘방법론 PASS’ 문구 | 날짜별 문서는 이력이다. 최신 범위는 이 문서와 현재 사양, 선택·거절의 원본 JSON을 따른다. 후보 전달에는 독립 외형·기술 PASS가 모두 필요하다. |
| requirements의 Pillow 12.3과 실제 검사 환경 불일치 | 이 체크포인트는 Pillow 12.2.0에서 검증했다. 현재 요구 버전을 실측 환경과 맞추고 과거 검토 보고서는 그대로 둔다. |

`status`는 기존 선택 JSON과 해시가 일치하는 이미지를 읽는다. 상태는 `config/project.json`, 원본 모델 카탈로그, 선택·거절 기록을 합쳐 보여 주며 사용자 승인을 새로 추정하지 않는다.

## 실행과 검증

프로젝트의 `pixel-dog-local` 폴더에서 실행한다.

```powershell
python -m tools.dog_engine status
python -m tools.dog_engine doctor
python -m tools.dog_engine verify
python -m tools.dog_engine head resolve --profile tools/head_engine/examples/golden-working.json --output outputs/new-head/resolved-profile.json
python -m tools.dog_engine head render --resolved outputs/new-head/resolved-profile.json --output-dir outputs/new-head
python -m tools.dog_engine body -- render-standing guide-054 --out private-data/new-body
```

새 출력은 기존 파일이나 검토 기록을 덮어쓰지 않는 폴더를 지정한다. 새 참조 그림은 검토 전 PENDING이며 원본 PASS를 승계하지 않는다. `pixel-diagnostic`은 거절된 화풍을 분석하기 위한 명시적 진단 명령이다. `pixel.export()` 직접 호출도 `diagnostic=True` 없이는 거절한다. 진단 비교판에는 거절 상태를 표시하고 recipe에는 BLOCKED와 NOT_VALIDATED를 남긴다.

환경은 Windows / Python 3.12이며 `tools/dog_engine/requirements.txt`에 실제 사용 버전을 기록했다. 과거 생성 코드와의 비교 검사는 `verification-requirements.txt`의 scikit-image도 필요하다. 한글 참조 보드는 맑은 고딕 두 파일의 기존 해시를 요구한다. 글꼴을 자동 대체하거나 비공개 입력 검사를 생략하지 않는다. 라이브러리 설치나 폰트 배포는 이번 정리에서 수행하지 않았다.

## 보존과 회귀 기준

- 정리 전 원본 `outputs`, 머리 카탈로그·엔진, B2 참조, 전달 검사 도구는 수정하지 않는다. 새 패키지에는 해시 보존용 `.gitattributes` 규칙을 추가한다.
- 9개 프리셋 × 5시점의 투영 좌표·색 배열을 기존 구현과 비교한다.
- 골든 5시점 참조 PNG와 native64 3개 atlas는 저장된 파일과 바이트 단위로 비교한다. 진단 비교판의 상태 문구 변경은 픽셀 형상 동일성 검사와 구분한다.
- 원본 73개 테스트와 새 패키지 회귀 검사를 함께 실행한다. 환경·원본 해시·선택/형상 구분·변조 차단도 확인한다.
- 실제 이미지 후보를 새로 전달하지 않는 코드 정리다. 새 형상이나 작화를 만들 때는 기존 독립 외형·기술 리뷰 규칙을 적용한다.

## 이번 정리의 실제 검증 결과

2026-11-06 로컬 검사에서 기존 머리 21개·전신 52개·새 패키지 10개, 총 83개 테스트가 통과했다. 9프리셋 × 5시점 투영값, 골든 참조 PNG와 native64 atlas 3개의 바이트 동일성을 확인했다. 진단 출력의 BLOCKED 기록과 덮어쓰기 차단도 임시 폴더에서 확인하고 해당 파일은 정리했다.

`doctor`는 환경과 9개 모델의 입력 검증을 통과했다. 머리 v2/13, 골든 adult, 잭 러셀 머리, 골든 B2, 잭 러셀 B2, 잭 러셀 귀 비교의 기존 전달 기록 6개는 READY를 유지한다. `8671571` 대비 원본 outputs·head_engine·review 도구·B2 참조의 변경은 없다. 이 결과는 새 이미지 후보 승인이나 공개 clone 검증을 뜻하지 않는다. 기존 테스트의 Pillow getdata 사용 중단 예정 경고는 남아 있으며 실행 실패는 없었다.

## 남은 작업

B2 정본과 일치하는 native64 머리 화풍, 개체별 귀 변형, 머리/전신 연결, 동작과 모바일 앱은 후속이다. 저장 모델의 pickle 형식, 비공개 원본 의존성, Windows 폰트 의존성도 남아 있다. 이번 정리를 완성된 공통 캐릭터 생성 엔진이나 배포 패키지로 표시하지 않는다.
