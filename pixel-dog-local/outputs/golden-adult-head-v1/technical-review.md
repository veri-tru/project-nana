# 골든 성견 머리 후보 독립 기술 검토

2026-11-06 / 검토자 `pixel_technical_review` / **TECHNICAL=PASS**.

최종 2차 A/B/C 모델과 PNG 3장을 검토했다. 1차 B/C의 귀뿌리 관통 틈은 MAJOR 실패로 보존했고, 수정한 메시와 보드를 새로 검사했다. 현재 미해결 기술 BLOCKER/MAJOR/MINOR는 없다. 외형·최종 선택은 별도 판정을 따른다.

## 검토 대상과 실제 확인 범위

| 파일 | 크기·형식 | 직접 확인한 범위 |
| --- | --- | --- |
| exterior-comparison.png | 2400×1480 RGB PNG | 기존/A/B/C × 측면·사선·정면·후면·윗면, 20셀 |
| skeleton-comparison.png | 2400×1480 RGB PNG | 기존/A/B/C × 같은 5시점, 20셀 |
| jaw-check.png | 2000×1260 RGB PNG | 기존/A/B/C × 0·10·20도, 12셀 |

실제 저장 파일 3장을 열어 총 52셀 전체를 확인했다. 외피의 수정된 귀뿌리는 정면·후면·윗면에서 다시 확인했다. 골든 사진 자료와 측면·윗면·정면 해부 참고 이미지도 직접 열었다. 사진/해부 자료의 역할은 형태 방향과 연결 관계의 참고이며 치수 실측 자료로 판정하지 않았다.

코드는 각 행의 동일 저장 3D 모델을 실제 투영한다. 외피/골격 비교판의 배율은 3.65, 턱 회전판의 배율은 4.0이다. 원근이나 셀마다의 크기 맞춤으로 A/B/C 차이를 숨기지 않는다. 골격 회전판은 실제 아래턱 정점을 같은 hinge [-16,10,0] 주위로 회전시킨다. 피부의 입 벌림 애니메이션을 만든 것은 아니다.

## 실제 메시 검사

`review_geometry.py`와 `review_saved_bc.py`에서 기존 검사 파일의 필요한 함수만 AST로 읽었다. 이전 전체 검사 스크립트나 이전 생성기를 main 경로로 실행하지 않았다. 검사는 최종 PKL의 실제 정점과 면을 대상으로 했으며, 원래 음함수의 값만으로 피부 포함을 판정하지 않았다.

세 후보의 upper·jaw·cartilage·skin·양쪽 eye 총 18개 부분 메시 모두 다음을 충족한다.

- 모든 수치 배열은 유한하다.
- 부분별 연결 성분은 1개이며 열린 경계와 비다양체 경계는 0이다.
- 영면적 및 double-area < 1e-10 퇴화면은 0이다.
- upper·jaw·skin의 인접하지 않은 삼각형 자기교차는 후보별 모두 0이다.

skin은 A/B/C 모두 Euler=2인 닫힌 단일 표면이다. upper는 비강·관자부 통로가 있는 골격 표면이므로 skin과 같은 Euler=2 조건을 적용하지 않았다.

### 뼈와 실제 피부 포함·교차

각 뼈의 모든 정점과 모든 면 중심을 실제 피부에 대해 ray parity로 검사했다. 거리 계산은 실제 삼각형과의 거리이며 검색 밖 삼각형의 거리 하한도 확인했다. 삼각형 교차는 AABB 후보를 빠짐없이 찾은 뒤 양방향 교차와 동일 평면 겹침까지 검사했다.

| 후보 | upper 샘플 | jaw 샘플 | 피부 외부 샘플 | 뼈–피부 삼각형 교차 | upper 최소 샘플 거리 | jaw 최소 샘플 거리 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 97,674 | 33,944 | 0 | 0 | 0.5393 | 0.3766 |
| B | 100,068 | 34,592 | 0 | 0 | 0.5357 | 0.4039 |
| C | 102,498 | 35,648 | 0 | 0 | 0.5151 | 0.4436 |

거리는 제작 좌표 단위다. 최소 거리는 위 샘플 집합의 인증된 최소값이며 전체 연속 표면 간 최단거리의 수학적 증명이나 mm 단위 조직 두께로 설명하지 않는다. 포함 검사와 전체 삼각형 교차 검사를 함께 사용해 국소 관통을 확인했다.

### 턱 회전 간섭

A/B/C 각각 0·10·20도의 실제 jaw 정점과 면 중심을 upper에 검사했다. 9상태 모두 upper 내부 샘플 0, jaw–upper 삼각형 교차 0이다. 관절 부근을 검사에서 제외하지 않았다. 세 각도 사이의 연속 동작 전 구간, 연골의 역학, 치아 교합이나 피부 표정은 이번 검사 대상이 아니며 검증 완료로 표시하지 않는다.

## 수정 범위와 출처

골든만 새 모델로 생성했다. 세 강도는 0.75/1.00/1.25이며, 선언한 폭·정수리·주둥이 길이·하악체 깊이·외피 주둥이 폭/높이 제어가 코드와 저장 설정에 일치한다. 실제 upper의 x 길이는 기존 76.1305에서 A/B/C 79.1839/80.0358/81.1878로 늘고, z 폭은 56.4461에서 62.1615/64.0632/65.9706으로 늘었다. 정수리 최대 y는 33.9941에서 32.4956/31.9943/31.4968로 낮아졌다. 이것은 실제 모델 변화 확인이며 성견의 생물학적 실측 기준이 아니다.

코 배율 5.4와 양쪽 눈 반경 3.7은 모두 유지한다. `exterior_seed.py`와 기존 v1 코드의 차이는 골든 주둥이 폭·높이를 상수로 분리한 부분뿐이며 공통 코 함수는 동일하다. 코·눈 위치는 새 골격에 맞춰 계산되므로 원래 검은 코 정점이나 눈 정점의 절대 좌표 불변을 주장하지 않는다. 귀·목도 폭 입력의 영향을 받으며 전체 정점 보존 대상이 아니다.

2차 수정은 귀 배치용 폭을 21+(새 폭-21)×0.55로 바꿨다. 실제 2차 A/B/C skeleton의 모든 배열은 각각 1차와 정확히 일치한다. 귀 수정으로 골격이 달라지지 않았음을 확인했다.

이전 `skull-based-heads-v2/review-status.json`에 고정된 소스·모델·파라미터·간접 JSON 12개의 현재 해시가 모두 당시 기록과 일치한다. 기존 골격/외피 전체 모델 파일이 같으므로 휘핏·닥스훈트·말티푸의 저장 모델도 바뀌지 않았다. 새 분기의 생성 경로는 golden만 호출한다. 기존 파일을 덮는 main 경로는 호출하지 않는다. 전체 저장소의 다른 기존 수정까지 이번 작업의 불변 대상으로 주장하지 않는다.

`evidence.json`의 입력 27개와 출력 3개의 현재 SHA-256을 모두 재계산했고 일치했다. 입력에는 새 코드·모델·설정, 재사용 골격/외피 코드·기준 모델, 사진·해부 참고와 폰트가 포함된다. 간접 실행 의존성인 골격 build/raster, v2 build가 import하는 v1 build, 폰트까지 검사했다. Python·NumPy·SciPy·scikit-image·Pillow·Numba 등 설치 환경 자체를 패키지 잠금으로 고정한 재현성 보증은 아니다. 동일 로컬 환경에서 아래 반복 검증을 수행했다.

## 반복 생성 검증

- A는 새 골격과 외피를 메모리에서 전체 재생성했다. 모든 정점·면·법선·색·영역 배열과 설정/metadata가 저장본과 정확히 같다.
- B/C는 최종 저장된 모든 부분 메시의 위상, 포함, 삼각형 교차, 자기교차, 턱 3각도를 직접 검사했다. 추가 전체 생성 반복은 하지 않았다.
- 세 PNG는 최종 저장 모델을 사용해 메모리에서 다시 렌더했다. 세 파일 모두 픽셀과 PNG 바이트가 저장본과 정확히 같다.
- 입력 소스/모델 해시는 검사 전후 안정적이다. 검사 과정은 기존 모델과 PNG를 덮지 않았다.

전체 재생성은 A 대표 1개, 전 보드 렌더는 3개, 저장 메시 검사는 A/B/C 전체라는 범위를 구분한다. PKL의 직렬화 바이트 재생성이나 모든 환경에서의 동일성까지 확대하지 않는다.

## 실패와 수정 확인

TG01 / MAJOR / **해결됨**: 1차 B/C의 정면·후면 귀뿌리에 작은 배경색 구멍이 보였다. 단일 닫힌 skin이었지만 Euler=-2였고 양쪽에 실제 관통 통로가 생겨 있었다. 귀 부착 연속성을 요구하는 검토 정책을 충족하지 못하므로 FAIL로 기록했다. `iterations/01/technical-findings.md`와 당시 모델/보드를 보존했다.

수정 후 A/B/C 모두 skin Euler=2, 열린/비다양체 경계 0, 자기교차 0이고 정면·후면·윗면에서 구멍이 사라졌다. 이전 검사 결과를 승계하지 않고 새 skin에 포함·교차·위상 검사를 다시 수행했다. 이 문제는 최종 후보에서 해결됐다.

## 근거 파일과 판정 한계

주요 수치 근거는 `technical-final-measurements.json`, `technical-render-check.json`, `technical-iteration-check.json`, `technical-source-preservation.json`, `technical-dimensions.json`, `technical-hash-check.json`이다. 실행 스크립트는 `review_geometry.py`, `review_saved_bc.py`, `review_render.py`다. `technical-measurements.json`의 A 재생성 완료와 B 검사 중간 기록을 보존하고, B/C 최종 저장 메시 검사는 `technical-saved-BC.json`에서 합쳐 최종 수치 파일을 만들었다.

후보 전달에 필요한 기술 검토 범위는 완료했다. 이는 품종 실측 정확도·사용자 선택·픽셀 실행 자산·표정 애니메이션의 승인이 아니다. 동일 파일 해시의 독립 외형 PASS와 최종 전달 검사가 추가로 필요하다.

<!-- review-verdict: {"status": "PASS", "reviewer": "pixel_technical_review", "artifacts": {"exterior-comparison.png": "74ccb1f736d048a04b4eda1d375cc59b65cec99ecd30c9130cd4af77872e6674", "skeleton-comparison.png": "e325fa606f0a31fe87ac6bf49ba3203577208656fc6a79f4f2a607eb026b5b36", "jaw-check.png": "b990b1d6e813b772cdc8cce415410d281d85e6bc6c784f38533e58cae721dffc"}, "inputs": {"build.py": "885b85b9d9ec1380fe7f1549359b77949dd0ccf6130782042d1c244f70d98898", "exterior_seed.py": "1d2dc33999af309e5e3add4885408817c45047ee236ac68286f79189f6701102", "parameters.json": "8444d5c83ae838d303c9683730ef6b85d918e18b3f4d09715316318a53d2c2e3", "references.json": "3d20e0b322ed00be58e00f77ffca33a2e41d47800e2795240bd6abf1edea41fd", "model-A.pkl": "e6844a219181cba6e8a62139dd7229e2dc6656e6e40a110cac27dcb66ed099c8", "model-B.pkl": "9ccdb84a4d3f03604b3f49195a1b919224e92641c04640781fde535c10dbf122", "model-C.pkl": "2aead49c66c118880a21d9d9a1c1129694df49b07c692811b31764697e64f0be", "parameters-A.json": "4d1e0bc80b91088a05c4e74086b49d8d72b54e65d5707cc4ff00abb4605f4435", "parameters-B.json": "cd1910fce896650a2ef027208f8a1ddf37f36ad00dc5c81311503fc3c9c2d987", "parameters-C.json": "a8bc6c3d01d6bef464b28d252123949a92d9c8e7c019f40eaa81d91dc0388a4b", "../head-skeleton-volume-v2/build.py": "734b85527c58a0cf9bf598867dfabbd9bddf2dd91f50b8fef9ec9fbc6733419e", "../head-skeleton-volume-v2/raster.py": "f2747b235362f49c94d8a7121784d5d597464723649bd1a4b951396dbb289f15", "../head-skeleton-volume-v2/geometry.pkl": "eaec7d20d5ea8abbb8a14e728d6120f4f119e2d3ee238d4af5b3836f06e4d154", "../head-skeleton-volume-v2/profiles.json": "aab232a82947fe4a81c6785e3c4e54ad458dca82c82a99e1aa9431ce8e29e323", "../head-skeleton-volume-v2/references.json": "ae6dd24467d04a9666b1def48ff3f7cdcbdeb9708011a08940629c6b26a93c3d", "../head-skeleton-volume-v2/review-status.json": "5c9d76e0d6c23f260daf3fa4f327d9cbc2b8b4c8204567a19bcf7754a0ff7e1e", "../skull-based-heads-v1/build.py": "84ff23798e2d487de2dddaa2302f15eebd292affb4dec0c9ab3690b2df410b2d", "../skull-based-heads-v2/build.py": "37e6843526018bec5c1f501f4feb8253b7a097f1905fd4c9b9ae63b5ded3a384", "../skull-based-heads-v2/geometry.pkl": "3321e3644b2647bb29238898995646d29b0e1fce64851e672d8267f3b7bc2cf9", "../skull-based-heads-v2/parameters.json": "5d534c3ab7008f55d7a2f1523b5ee921ed75f724109d12a6f0fb5e8873139230", "../skull-based-heads-v2/review-status.json": "4debc35e3aa60ac15e448d4d57541d933c4cf8b9cce560aa0428fc5285791892", "../deformation-b-face-v2/golden-reference.png": "2be4a6076f6730adbbab58d68536181bf15b528898084adae17b5f49f1b032ef", "../../private-data/skull-anatomy-v2/lateral.jpg": "df1c09fa01836ce5fc28b5c51ca7ccf1333f9a3ce129d448af866709288e9cfd", "../../private-data/skull-anatomy-v2/dorsal.jpg": "f7c059883e2ca7a9ba17f48385f62485e3c2c40b4189dbfff13052b417167a10", "../../private-data/skull-anatomy-v2/rostral.jpg": "8d8d140502b12b2fb37cbb19b2620ee9ef03bd504a961a333417d39204192ccb", "../../../../../../../Windows/Fonts/malgun.ttf": "7a183cf1c6c56b9609fcc16eda8b5229fbc11758a21e669ec00343239b02192f", "../../../../../../../Windows/Fonts/malgunbd.ttf": "e8cbc0b2afcc14fb45dfb6086d5102c0b23a96e7b6e708f3122acde1b86c9082"}, "coverage_complete": true, "unresolved": {}} -->
