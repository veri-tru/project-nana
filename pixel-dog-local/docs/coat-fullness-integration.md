# 길이와 독립된 풍성함 v2

최신 음영 출력은 [가슴 음영점 수정](coat-chest-tone-fix.md)을 따른다. 아래 출력·READY·음영점 MINOR는 연결 구현 당시의 이력이며 새 렌더 코드에 승계하지 않는다.

사용자 “후속 계속진행”에 따라 등록 말티푸의 머리·목·상흉부에 풍성함 제어를 추가했다. 형상은 제작용 외피이며 실제 털 길이·숱·밀도·미용 결과의 측정값이 아니다.

## 현재 지원 범위

| 설정 | head-3d | native64 |
|---|---|---|
| 길이 short/medium/long | 정수리·볼·양쪽 귀·가슴 | 동일 |
| 풍성함 flat/moderate/full | 정수리·가슴 | 가슴만 |
| 볼·귀 풍성함, 결·피모 층·미용 이름 | 미지원 | 미지원 |

미지원 항목이 섞이면 요청 전체를 거절한다. 3D에서 검토된 정수리 풍성함을 native64로 내보내는 우회도 거절한다. 기본 short/flat은 원본 외피에 추가 변위가 없는 상태이며 실제 짧은 미용이나 몸에 붙는 피모를 뜻하지 않는다.

길이는 정수리를 위로, 볼·귀·가슴을 아래로 늘린다. 풍성함은 정수리의 위·수평 복합 방향과 상흉부의 수평 방향으로 펼친다. 두 제어는 같은 변위의 배수가 아니다. v1의 평평한 정수리·앞가슴 국소 돌출을 둥근 분포와 가슴 길이의 아래 방향 변위로 보정했다.

눈·코 주변, 귀뿌리, 원본 턱–목 높이 구간 전체, topology와 색을 보호한다. r3에서 시도한 낮은 외측 볼털 예외는 제거했다. 원본 음영 법선을 실제 표면 회전에 맞춰 이동하며 면 방향·면적·귀 표본 간격을 검사한다. 정점 간격만으로 전역 표면 충돌 부재를 증명하지 않으며 별도 기술 검토에서 실제 표면도 확인한다.

## 실행과 재현

등록 모델: `maltipoo-neck02-soft-v2`, 기하 버전: `envelope-v2`. 원본은 기존 `neck-reference02/model-B.npz`이며 파일 SHA-256은 `77d56d9ce2454a12d4ac2f9329c1a880414e5cc14da59730816c993213b27133`이다. 기존 v1 기하 코드와 원본 모델은 변경하지 않았다. [실행 안내](../tools/dog_engine/README.md#길이와-독립된-풍성함-v2).

- 3D 예제: `coat-head-structure-fullness-flat/moderate/full.json` — 모든 길이 long 고정, 정수리·가슴 풍성함 변경. 정수리 요청이 있어 native64 출력은 차단된다.
- 64px 예제: `coat-head-fullness-flat/moderate/full.json` — 모든 길이 long, 머리 풍성함 고정, 가슴 풍성함만 변경.
- 순서: prepare → 전체 구조의 독립 외형·기술 검토 → native64 직접 raster → 출력의 독립 검토. 구조와 64px의 승인은 별개다.

카메라·배율·중심은 원본에서 고정하며 후보별 재정규화하지 않는다. registry와 참조 목록을 같은 snapshot으로 읽어 입력 해시에 연결한다. native reader는 전체 요청·기하·의미 라벨·카메라를 다시 계산하고 저장 결과와 대조한다. 코드·입력이 바뀌면 과거 PASS를 승계하지 않는다.

## 검증과 산출물

현재 관련 검사 **37개 통과**: 기하 12개, 털·라우팅·native 25개. 기하 조합·독립 변위·원본 보존·볼 길이 회귀·미지원 전체 거절·registry/catalog snapshot·실제 64px 외곽 변화를 확인했다. 전체 회귀 147개는 초기 r1에서 실행한 이력이며 현재 전체 재실행 수치로 표시하지 않는다.

구조 6건은 `private-data/coat-fullness-20261107/head-{flat,moderate,full}-r5`와 `chest-{flat,moderate,full}-r5`에 있다. 각 9 PNG, 5시점·귀 숨김·같은 카메라 crop·전체 비교판과 실제 메시를 포함한다. head 27 PNG는 r4와 바이트가 같음을 확인해 기존 직접 시각 관찰을 명시적으로 재사용했고, chest 27 PNG는 새로 확인했다. 구조 6건의 외형·기술 검토와 게이트는 통과했다.

현재 코드로 실제 READY head 구조 세 건을 native export에 전달해 정수리 풍성함 거절과 출력 미생성을 확인했다. 근거는 `native-target-rejection.json`이다.

native64 결과는 `chest-{flat,moderate,full}-native64-r2`다. 각 5개 64×64 프레임·320×64 atlas·6배 최근접 미리보기·의미/깊이 배열을 포함한다. 3건 모두 독립 외형·기술 PASS 및 현재 해시 기반 전달 검사 READY를 확인했다. 구조 6건을 포함해 총 9건이며 사용자 선택은 PENDING이다. 구현은 /root와 /root/coat_references, 외형 리뷰는 /root/coat_supported_visual, 기술 리뷰는 /root/coat_review가 담당했다.

| 수준 | 3D 정수리·가슴 | 실제 64px 가슴 예시의 6배 보기 |
|---|---|---|
| flat, 추가 팽창 없음 | [3D 비교판](../private-data/coat-fullness-20261107/head-flat-r5/structure-sheet.png) | [64px 미리보기](../private-data/coat-fullness-20261107/chest-flat-native64-r2/native64-preview.png) |
| moderate | [3D 비교판](../private-data/coat-fullness-20261107/head-moderate-r5/structure-sheet.png) | [64px 미리보기](../private-data/coat-fullness-20261107/chest-moderate-native64-r2/native64-preview.png) |
| full | [3D 비교판](../private-data/coat-fullness-20261107/head-full-r5/structure-sheet.png) | [64px 미리보기](../private-data/coat-fullness-20261107/chest-full-native64-r2/native64-preview.png) |

64px 외곽 alpha 변화는 정면 16/14, 사선 9/9, 측면 4/6, 후면 16/14, 윗면 38/34 픽셀이다(flat→moderate / moderate→full). `native64-chest-differences.json`에 이미지 해시와 RGBA 차이도 기록했다. 수치 차이는 시각 식별성의 대체 증거가 아니다. 실제 1배에서 정면·후면·윗면의 가슴 단계가 구분되지만 모든 단일 시점에서 세 단계를 똑같이 쉽게 구분한다는 보장은 없다.

회색 엔지니어링 진단 출력이다. moderate/full 사선의 작은 가슴 하이라이트는 MINOR로 남아 있다. B2/C 화풍·실제 미용·개체 닮음·실기기·사용자 선택 승인은 아니다. 최종 상태는 각 폴더의 `review-status.json`과 두 보고서의 현재 해시를 검사한다. 생성 기록의 BLOCKED는 생성 당시 미검토 상태이며 최종 상태를 대신하지 않는다.

## 실패 이력과 후속

r1~r3의 볼 풍성함 후보는 실제 윤곽 구분이 부족해 외형 FAIL/BLOCKED로 보존했다. r3 당시 기하 코드는 `failed-r3-geometry.py`에 별도 보관했다. 귀 가까운 중간 볼 외곽의 보호와 제한된 노출 영역 때문에 단순 gain 증가가 해법이 아니었고, 좁은 전방 패치의 메모리 실험도 날개·뿔 같은 형태로 실패했다. 볼은 넓은 털 표면과 접합·귀 충돌·눈 노출을 구분한 새 제작 계약이 필요하다.

r4 구조의 정수리 변화는 480px에서 보였으나 최초 native64의 정수리 단계는 실제 1배에서 구분되지 않아 FAIL이었다. 두 단계로 이름만 줄여도 해결되지 않았다. 이 실패도 원본 파일·보고서·BLOCKED 상태로 보존한다. 정수리는 3D 전용, 볼 풍성함은 미지원으로 명시했으며 과거 실패를 해결됐다고 바꾸지 않는다. 전체 머리·귀·목·상흉부 검토 범위는 줄이지 않았다.
