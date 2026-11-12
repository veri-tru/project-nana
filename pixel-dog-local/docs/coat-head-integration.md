# 털 설정 → 3D 머리 → native64 연결

> 이 문서는 길이 v1의 당시 검증 이력이다. 후속 v2 연결로 공용 코드·registry 해시가 바뀌었으므로 아래 이전 READY를 현재 코드에 승계하지 않는다. 최신 범위와 새 검토는 [풍성함 v2](coat-fullness-integration.md)를 따른다.

2026-11-07 사용자 확인: “3D 머리·64px 출력까지 연결”. 구현 대상은 등록된 말티푸 머리·목·상흉부 구조 한 종류다.

## 실행 계약

`coat describe` → `coat head-prepare` → 새 구조의 독립 외형·기술 리뷰 → `coat head-native64` → native64 독립 검토 순서로 진행한다. [실행 명령과 예제](../tools/dog_engine/README.md#3d-머리와-실제-64px-연결).

- 원본: `neck-reference02/model-B.npz`, SHA-256 `77d56d9ce2454a12d4ac2f9329c1a880414e5cc14da59730816c993213b27133`. 이전 구조 계약·보고서를 검사하고 변경된 모델은 새 검토를 요구한다.
- 적용: 정수리·볼·귀·앞가슴의 bounded authored envelope. short는 추가 변위가 없는 기준 외피, medium/long은 기본 2/4 제작 단위다. 볼은 gain 0.4다. mm 또는 실제 털 길이 검증값이 아니다.
- 보존: 원본 배열·눈·코 인접부·귀뿌리·턱과 목의 연결, topology와 색. 변경된 표면의 법선은 다시 계산한다.
- 확인: 면 방향/면적·보호 영역·귀 표본 간격. 정점 표본 간격은 전역 표면 교차 부재를 증명하지 않는다.
- 투영: 같은 원본에서 정한 카메라·배율·중심으로 5시점을 직접 64×64 raster한다. 길이마다 bbox를 다시 정규화하거나 96px 이미지를 축소하지 않는다.
- 의미 구분: 머리 피모·좌우 귀·좌우 눈·코 면 ID를 고정한다. 코 경계 혼합 면은 원본 코 정점이 2개 이상이면 코로 분류한다. 광원 값과 categorical ID는 별도 채널이다.
- 출력: 중립 회색 진단 팔레트. C 고해상도 정본 재현이나 B2 native64 승인은 아니다. 전체 몸통·다리·동작·곱슬·독립 풍성함·미용 형태는 포함하지 않는다.

## 실제 검증 자료

최종 구조는 `private-data/coat-head-20261107/{short-r3,medium-r3,long-r3}`, native64는 같은 상위 폴더의 `{short-native64-r2,medium-native64-r2,long-native64-r2}`에 보존한다. 구조 r1→r2는 reader 검증 보완, r2→r3는 native 음영 코드의 출처 갱신이다. 구조 PNG 27개·모델 NPZ 3개는 동일하며 의미 라벨과 구조 계약도 r2/r3에서 동일하다. 원본 모델·개체 C·기존 native64 진단 코드는 변경하지 않았다.

각 구조 후보는 정면·사선·측면·후면·윗면, 귀 숨김 측면/후면, 같은 배율 crop, 전체 비교판을 포함한다. Long은 정수리가 조금 평평하고 앞가슴 외피의 국소 돌출이 보여 자연스러운 털 외형 개선이 남아 있다. 이 연결의 기술 검증을 실제 미용 재현으로 확대하지 않는다.

## 시험과 출력 차이

- 전체 `python -m tools.dog_engine verify`: 135개 통과(기존 머리 21·정적 제작기 52·활성 엔진 62). 새 3D geometry 8개와 native 연결 9개가 포함된다.
- 이후 귀 가독성 보완과 회귀 1개 추가 후 `python -m unittest tools.dog_engine.tests.test_coat_native64 -q`: 10개 통과. 변경 없는 전체 검사를 다시 실행한 수치로 표시하지 않는다.
- 원래 native 윗면의 귀는 투영되어 있었으나 밝은 머리 면과 섞여 읽기 어려웠다. 귀 재질을 한 단계 어둡게 하고 실제 귀–머리 접경의 귀 픽셀 안쪽에 경계를 표시했다. 최종 15프레임의 alpha·semantic ID·depth는 이전과 정확히 같으며 바뀐 색은 귀 소유 픽셀뿐이다.
- 최종 3단계 모두 고정 카메라에서 실제 픽셀 차이가 있다. 아래 수치는 변경된 RGBA 픽셀 수이며 사람이 1배에서 단계 차이를 쉽게 식별한다는 사용성 검증이 아니다.

| 시점 | short→medium | medium→long |
|---|---:|---:|
| 정면 | 36 | 24 |
| 사선 | 30 | 37 |
| 측면 | 34 | 35 |
| 후면 | 12 | 13 |
| 윗면 | 12 | 6 |

생성 기록의 `delivery=BLOCKED`는 생성 당시의 미검토 상태다. 최종 전달 판단은 같은 폴더의 `review-status.json`과 두 독립 보고서의 현재 해시를 `check_delivery.py`로 검사한다. 보고서·파일이 바뀌면 이전 PASS를 승계하지 않는다.

## 최종 검토와 결과

최종 구조 3건과 native64 3건 모두 독립 외형·기술 PASS 및 전달 검사 READY를 확인했다. 구현자는 `/root`, 외형 리뷰어는 `/root/coat_head_visual`, 기술 리뷰어는 `/root/coat_review`다. 구조 PNG 27개와 최종 native PNG 21개가 검토 범위이며 native의 각 원본 프레임은 1배와 6배에서 직접 확인했다. 새 형상·출력의 사용자 선택은 PENDING이다.

| 길이 | 실제 5프레임 atlas | 6배 진단 미리보기 | 검토 기록 |
|---|---|---|---|
| short | [320×64 atlas](../private-data/coat-head-20261107/short-native64-r2/native64-atlas.png) | [미리보기](../private-data/coat-head-20261107/short-native64-r2/native64-preview.png) | [상태](../private-data/coat-head-20261107/short-native64-r2/review-status.json) |
| medium | [320×64 atlas](../private-data/coat-head-20261107/medium-native64-r2/native64-atlas.png) | [미리보기](../private-data/coat-head-20261107/medium-native64-r2/native64-preview.png) | [상태](../private-data/coat-head-20261107/medium-native64-r2/review-status.json) |
| long | [320×64 atlas](../private-data/coat-head-20261107/long-native64-r2/native64-atlas.png) | [미리보기](../private-data/coat-head-20261107/long-native64-r2/native64-preview.png) | [상태](../private-data/coat-head-20261107/long-native64-r2/review-status.json) |

각 native 폴더의 `technical-review.md`에는 7개 PNG의 재현, 의미/깊이 배열 일치, 검토 누락·변조·미지원 혼합 요청 거절을 기록했다. `visual-review.md`에는 귀 경계 가독성 `NATIVE-EAR-01` 해결과 전체 구조 판독 결과를 기록했다. Long의 평평한 정수리·앞가슴 국소 돌출은 `MINOR COAT-LONG-01`로 남긴다. 전달 READY는 **중립 진단 결과**의 검토 통과이며 자연스러운 미용 외형·B2·개체 닮음·실기기 승인은 아니다.
