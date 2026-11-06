# Nana 정적 제작기 0.3

휘핏(guide-054), 닥스훈트(guide-016), 골든 리트리버(guide-002)는 앉기 수정 후보를 별도로 등록했다. 이 디렉터리에서 `python render_v03.py render-standing guide-054 --pose seated-candidate --out ../../private-data/whippet-seated-preview`로 새 폴더에 출력한다. B 프로필은 `seated_limbs`에서 어깨·팔꿈치·앞발목·발가락 뿌리·발끝 또는 고관절·무릎·비절·발가락 뿌리·발끝의 (x, y, 반경)을 지정한다. 64×64에서 분절의 반경을 보간한 면이 다리와 발을 그린다. [세 개체 비교](../../private-data/seated-rebuild-r1/comparison.png).

### 나나의 갸웃한 앉기 · 중간 음영

이 폴더에서 아래 명령을 실행하면 등록된 나나 관찰 DB와 선택 프로필로 64×64 PNG를 재생성한다. 출력에는 새 경로를 사용한다.

```sh
python render_v03.py render-standing nana-review-20261103 --pose seated --stages --out ../../private-data/nana-seated-check
```

`standing.png`는 기존 CLI의 공통 파일명이다. `review.json`에 실제 자세 `seated`, 선택 상태, 관찰 revision, 작화 및 출력 해시를 남긴다. `--pose`를 생략하면 나나의 서기 기준본을 출력한다. `render-roster`는 나나 폴더에 기존 기본 자세와 `seated/`를 함께 발행한다.

**두 털색과 전용 음영 두 색.** 64×64 v2 프로필에서 `coat_lighting`을 선택하면 부위 채움·무늬·얼굴 털색은 `white`와 `grey`를 쓴다. 실제 RGB는 개체 팔레트에서 지정한다. 각 음영 영역은 `part`, `base`, `runs`로 작성한다. 예를 들어 `{"part":"haunch","base":"grey","runs":[[48,43,45],[49,42,45]]}`는 최종 격자의 y=48에서 x=43~45, 다음 줄에서 x=42~45에 이어지는 면이다. 엔진은 상하좌우로 연결됐는지 검사하고 보이는 부위와 해당 털색 안에서만 `white → light`, `grey → dark`를 적용한다. 눈·코·입 픽셀은 보호한다. 이 방식에서는 기존 `shadows`를 비우고, 눈·코·입의 추가 세부 표현은 head의 `details.feature`로 지정한다.

**작화 기준.** `coat_lighting.direction`에 화면 기준 `upper-left` 또는 `upper-right` 중 하나를 지정하고 그 방향에 맞게 영역을 그린다. 나나의 ②는 왼쪽 위 광원, 중간 깊이 옆구리 그늘, 짧은 눈가 음영, 턱을 따라 이어지는 목털과 흰 가슴 경계를 사용한다. 넓은 털무늬는 사진 속 양쪽 몸통을 대조하고, 떨어진 밝은 점은 눈 반사인지 털무늬인지 구분한다. 귀와 정수리의 붙은 털끝은 원본 1배에서 확인한다. 머리 비율과 구체적인 음영 좌표는 자세별 작화값이다.

가이드 25개체의 현재 얼굴 후보는 `private-data/face-recheck-v4`에 있다. 사진에서 관찰된 눈·코·입을 최종 격자에 투영한 뒤 실제 어두운 눈동자와 코·입선이 각각 표시되는지 검사한다. 가려진 눈과 확인하기 어려운 입선은 생략한다. 기존 개체와 복구 선택본은 이전 등록을 사용한다.

전신 윤곽 재등록 실험은 다음 명령으로 재출력한다. 사진과 관찰 DB가 포함된 가이드 등록 폴더를 입력하고 새 출력 폴더를 지정한다. 세 머리 배율에서 같은 개체의 몸통·다리 입력과 팔레트가 유지된다.

```sh
python body_pilot.py ../../private-data/face-recheck-v4 ../../private-data/body-pilot-repeat
python body_pilot.py ../../private-data/face-recheck-v4 ../../private-data/face-tone-repeat --face-shading
python body_pilot.py ../../private-data/face-recheck-v4 ../../private-data/face-details-repeat --face-details
python body_pilot.py ../../private-data/face-recheck-v4 ../../private-data/ear-fold-repeat --ear-fold
```

`--face-details`는 위 사진에서 R4 C의 프로필을 재생성하고 저장한 해시가 맞는지 확인한다. 등록된 두 개체에만 입·눈썹 비교를 적용한다. 새 A·B·C는 각 개체의 입 안쪽 너비 또는 눈썹 한쪽의 색 픽셀 수를 1·2·3칸으로 달리한다.

`--ear-fold`는 골든 리트리버의 입 B를 재생성해 등록 해시를 확인한 뒤, 가까운 귀를 머리에 붙은 독립 부위로 추가한다. 세 안에서 귀의 위치와 면적을 고정하고 볼과 맞닿은 진한 선의 길이만 바꾼다.


골든 입 벌림 비교는 귀 B 프로필을 입력으로 사용한다. 등록 자료의 입꼬리와 아래턱을 고정하고 입 앞쪽의 틈을 1·2·3칸으로 달리한다.

```sh
python mouth_study.py ../../private-data/golden-ear-r2/002/B.json ../../private-data/face-recheck-v4/profiles.sqlite ../../private-data/mouth-opening-repeat
```

## 등록 개체의 64×64 서기 출력

골든 측면의 단순화 실험은 선택한 입 C를 입력으로 사용한다. 등록 자료에서 꼬리·가슴에 공통으로 남길 면과 단계별로 생략할 털 음영을 나누고, 실루엣·구강 틈과 지정된 식별 부위의 픽셀이 기준과 같은지 검사한다.

```sh
python coat_study.py ../../private-data/golden-mouth-open-r3/C.json ../../private-data/face-recheck-v4/profiles.sqlite guide_registration/golden-coat-budget.json ../../private-data/coat-budget-repeat
```

등록된 30개체는 관찰 DB와 작업 프로필을 개체 ID로 찾는다. 다음 명령은 이 폴더에서 실행하며 출력 위치는 새 폴더로 지정한다.

```sh
python render_v03.py render-standing guide-008 --out ../../private-data/preview-008
python render_v03.py render-roster --out ../../private-data/preview-all
```

전체 출력은 각 개체의 관찰 기록, 작화 파일, 완성 픽셀 해시를 검사하고 30건이 모두 맞으면 저장한다. `index.json`과 개별 `review.json`에 사진 자세와 선택 상태를 기록한다. 가이드 신규 25개체는 후보 B를 작업 기준으로 쓴다. 나나·실개체 02·03과 기존 가이드 016·054는 각자의 기존 DB를 사용한다. `render-standing`은 기존 명령 이름이며 출력 자세는 프로필의 `pose`를 따른다.

가이드 25개체의 비공개 입력을 다시 만들 때는 제공받은 가이드 PDF와 322종 표가 든 보조 ZIP을 사용한다. 사진은 캡션 ID와 지면 위치로 연결한다. `guide_registration/landmarks.json`은 사진을 보고 수동 등록한 부위별 윤곽, 눈·코·입, 귀 안쪽 선과 팔레트다. 좌표 범위 0~64는 사진 가로·세로 전체에 각각 대응한다. 실제 픽셀로 옮길 때 사진의 종횡비를 복원한다. 윤곽 안의 명암을 네 내부색으로 묶으며, A·B·C는 귀 안쪽 선의 색만 바꾼다. 각 후보에서 표시하는 눈과 코가 최종 픽셀에 실제로 남는지 검사한다.

```sh
python register_guide.py --pdf <가이드PDF> --tables <보조ZIP> --out ../../private-data/guide-poses-final
python guide_gallery.py ../../private-data/guide-poses-final
```

PDF를 읽는 등록 단계는 PyMuPDF 1.28.0에서 검증했다. 비교판은 기존 휘핏·닥스훈트 작업 폴더도 사용한다. 일반 재출력에는 등록된 비공개 프로필과 SQLite 파일이 필요하다.

이 폴더에서 등록된 관찰 DB와 해당 개체의 서기 작화 JSON으로 실행한다.

```sh
python render_v03.py --db <관찰DB> render-standing <개체ID> --profile <서기작화JSON> --out <새폴더>
```

`render-standing`은 개체 ID, 관찰 revision과 SHA-256을 확인한 뒤 64×64 `standing.png`를 출력한다. `review.json`에 포맷 버전, DB 출처와 작화 데이터·RGBA·PNG 해시를 기록한다. 관찰 DB는 읽기 전용으로 연다. `format`이 `standing64-v1`인 기존 프로필은 기존 출력 방식을 사용한다.

### standing64-v2 작화 프로필

휘핏(`guide-054`)과 닥스훈트(`guide-016`)의 작업 기준본은 위 명령에서 `--profile <서기작화JSON>`을 생략해 출력한다. 관찰 DB는 `private-data/breed-standing-pair-v1/profiles.sqlite`를 쓴다. `standing-baselines.json`은 개체별 작화 파일과 기대 해시를 지정한다. 원본 파일을 찾지 못하거나 작화 데이터 또는 출력 픽셀이 달라지면 저장 전에 중단한다. 두 기준본은 머리 ③이 적용된 코·입 수정본이며 입선의 중간 농도는 작업용이다. 다음 시안을 만들 때에는 이 프로필의 사본에서 수정하고 기준 출력과 직접 대조한다.

`render-standing`에 `--stages`를 추가하면 같은 원본 실행에서 S1(단색 외곽), S2(부위·고유 무늬·눈코입·겹침선), shade(음영까지), S3(코 표면과 최종 세부 표현까지)를 PNG로 저장한다. S3는 standing.png와 같다. 모든 단계가 털 사이 틈까지 같은 투명 영역을 쓴다. ownership.png는 각 픽셀에서 앞에 보이는 부위의 번호를 담으며 배경은 0이다. review.json에 부위 번호와 단계별 파일 해시를 기록한다.

**공통 몸통 부품.** v2의 parts 항목에서 기존 shape 대신 component를 지정한다. 지원값은 trunk(몸통), chest(가슴), near_foreleg·far_foreleg(가까운·먼 앞다리)다. parts의 순서는 뒤에서 앞으로 쓴다. morphology에 trunk_length, chest_depth, belly_tuck, foreleg_width를 64 격자의 픽셀 단위로 둔다. stance에는 withers(등 앞쪽 기준점), facing(화면 오른쪽 1, 왼쪽 −1), feet(각 앞다리 component 이름별 접지점)를 둔다. 머리·몸통은 기존 head_anchor에서 연결한다. 부품의 mark와 음영은 markings·shadows에 uv 다각형으로 지정할 수 있다. u는 해당 부위의 앞끝에서 뒤끝까지, v는 위에서 아래까지 0~1 범위다. seam_over에 뒤쪽 부위 이름을 넣으면 실제로 겹치면서 뒤쪽 부위가 보이는 경계만 그린다. 뒷다리·꼬리는 기존 명시 좌표를 사용하므로 몸길이를 크게 바꿀 때 연결 상태를 별도로 확인한다.

**얼굴 가림.** head_view는 이미 자세에 맞게 배치된 얼굴에 적용한다. angle은 front·oblique·profile이고, 돌아간 얼굴에는 near_eye에 개체 기준 left 혹은 right를 지정한다. 각 눈에도 side를 붙인다. oblique는 far_visible을 직접 지정하고 profile은 먼쪽 눈을 숨긴다. foreground에는 눈·코·입을 덮는 털 영역의 머리 좌표를, jaw_over에는 턱 아래와 맞닿는 몸 부위 이름을 넣는다. 얼굴의 그림자와 details에는 feature를 coat·nose·mouth·left_eye·right_eye 중 하나로 표시한다. 눈은 i(윤곽색)·d(어두운색)·w(밝은색)로 표현한다. 기존 눈이 털무늬에 찍혀 있다면 먼저 털과 분리한다. stages를 켜면 눈별로 최종 화면에서 실제 달라지는 픽셀 수(eye_contribution_px)가 기록된다. 이 값은 눈으로 읽히는지에 대한 원본 1배 검수와 함께 사용한다. head_view는 얼굴을 새 각도로 자동 회전시키지 않는다.

같은 CLI에서 `format`을 `standing64-v2`로 지정한다. 기존 부위 다각형·팔레트·눈·코·입 형식에 다음 항목을 사용할 수 있다.

- `head_parts`에 머리와 함께 움직일 부위 이름을 넣는다. 기본값은 `["head"]`다. 먼 쪽 귀가 별도 부위이면 `["head", "far ear"]`를 사용한다. `head_anchor`를 기준으로 `head_scale`을 적용해 털무늬의 면을 함께 확대하고 눈 중심·코·입 위치를 옮긴다. 눈의 반사점은 원래 픽셀 크기를 유지한다. 이미 확대된 좌표로 저장한 프로필에는 배율 1을 사용한다.
- 가는 다리에는 해당 부위에 `"outline_neighbors": 4`를 지정할 수 있다. 대각선 모서리만 투명 영역과 닿은 칸에는 털색이 남는다. 기본값 8은 기존 외곽선을 사용한다.
- `nose_surface`는 기존 `nose` 다각형에서 실제로 보이는 부분에 칠한다. 예를 들어 `{"color":"dark","reflection":{"at":[60,16],"color":"white"}}`는 해당 코 안에 반사점 한 칸을 찍는다. `reflection`은 선택 항목이다. 닫힌 입선은 `mouth`로 따로 지정하며 빈 배열이면 생략한다.
- `details`는 팔레트 안에서 눈꺼풀·줄무늬·귀의 그늘·다리 겹침선을 지정하는 배열이다. 예를 들어 `{"part":"near front","color":"outline","polygon":[[22,39],[22,44]]}`는 가까운 앞다리의 보이는 부분에만 선을 그린다. 한 좌표는 점, 두 좌표는 선, 세 좌표 이상은 면이다. 기본 음영과 코 표면을 그린 뒤 배열 순서대로 적용하며 마지막 색이 남는다.

좌표는 프로필 입력 격자를 기준으로 한다. 사진 비율로 등록한 새 v2 프로필에서 `head_scale`을 생략하면 머리·귀의 길이와 높이를 기본 1.55배로 그린다. 엔진은 `head_anchor`와 확대 그룹의 모든 외곽점을 확인하고, 한 칸 여백이 부족하면 자동 배율을 낮춘다. 원래 외곽을 줄이지는 않는다. `review.json`의 `applied_head_scale`에서 적용값을 확인할 수 있다.

배율을 명시한 프로필은 그 값을 사용한다. 휘핏과 닥스훈트의 기존 ③은 1.42배이며, 이미 머리를 확대해 저장한 좌표는 1이 원래 시안의 표시 배율이다. 수동 배율을 지정할 때는 코끝과 귀 끝 여백을 전신에서 확인한다.

## 같은 얼굴을 두 시점에서 확인하기

`face_views.render_view(body, registered_head, pivot, radius_ratio, profile, depth, view, colors)`는 등록된 RGBA 머리와 몸 레이어 위에 공통 주둥이 부품을 투영한다. `MuzzleProfile`은 콧등 시작점(x, y, z), 양 볼의 총폭·높이, 코 폭·높이를 담는다. `depth`는 코끝의 작화 깊이이며 실측값이 아니다. 같은 후보의 두 호출에는 동일한 레이어·프로필·깊이·팔레트를 쓰고 `View(yaw, pitch)`의 각도(도)만 바꾼다. 시점마다 머리도 함께 회전한다. 정면에서 등록하지 못한 뒤쪽 털은 주변의 털색으로 근사한다.

코·입·턱·콧등·볼은 각 픽셀에서 카메라에 가장 가까운 표면을 골라 표시한다. 반환값은 완성 RGBA, 실제 보이는 부위별 마스크, 두 볼의 투영 영역이다. 투영 영역이 서로 겹치는 픽셀 수와, 가까운 볼을 제거했을 때 먼 볼이 실제로 드러나는 픽셀 수는 서로 다른 지표다. 이 실험은 지정한 시점과 프로필의 비교용이며, 사진에서 카메라 각도나 해부학적 길이를 자동 복원하지 않는다.

## 개체 명세에서 주둥이 비교 라운드 만들기

`appearance_round.py`는 같은 얼굴에서 주둥이 폭을 고정하고 돌출 파라미터 세 값만 바꿔 A·B·C를 병렬 출력한다. 돌출은 실측 길이가 아니라 제작 비율이다. 턱, 먼 볼, 가까운 볼, 콧등과 코끝을 별도 면으로 계산한다. 비스듬한 얼굴에서는 코와 가까운 볼이 먼 볼을 덮고 입의 먼 끝이 짧아진다. 좌우를 돌리면 가림 방향도 바뀐다. 사진은 사람이 읽고 관찰과 자료 출처를 명세에 적는다.

기존 정면·앉기 제작 상태를 사용할 때는 이관된 DB의 개체 ID와 제작 revision을 명시한다. 아래는 합성 입력 예시다.

```json
{
  "dog_id": "synthetic-example",
  "revision": 2,
  "photo_observations": ["합성 예제. 실제 사용 시 사진 번호와 관찰 부위를 기록한다."],
  "table_reference": "합성 예제. 실제 사용 시 외형표 행과 채택한 항목을 기록한다.",
  "design_choice": "주둥이 폭과 코 크기를 유지한 채 코끝 돌출을 비교",
  "unknowns": ["실제 주둥이 길이"],
  "turn": 0,
  "projection": [0, 0.15, 0.30]
}
```

```sh
python appearance_round.py concept.json --db private/profiles.sqlite --out output/round-1
python appearance_round.py concept.json --template private/template.json --out output/standing-round-1
```

두 번째 명령은 다른 자세와 실제 격자를 지원한다. 한 개체·자세·해상도에 대해 코와 입이 아직 그려지지 않은 `base` PNG와 주둥이 부품을 그릴 수 있는 이진 `slot` PNG를 준비한다. 템플릿 JSON에는 `dog_id`, `revision`, 두 파일의 상대 경로 `base`·`slot`, 픽셀 단위 `center: [x,y]`·`span: [폭,높이]`·`nose_size: [폭,높이]`, 색상 객체 `colors`를 넣는다. 색 키는 `outline, coat, muzzle, muzzle_shadow, nose`이고 값은 `#RRGGBB`다. 선택 항목 `lobe_depth`는 0~0.3의 양 볼 부피값이다. 등록한 개체가 바뀌면 데이터와 레이어를 교체한다. 좌우 방향 `turn`은 -1~1의 제작값이며 라운드 중 고정된다.

결과는 PNG 세 장과 `round.json`이다. 명세·원본 revision 또는 등록 레이어 해시·각 파일 해시를 남긴다. 알파, 팔레트, 주둥이 밖 픽셀 불변, 세 출력의 실제 차이를 검사하고 실패한 라운드는 발행하지 않는다. 기존 출력 폴더는 덮어쓰지 않는다. 적대적 리뷰는 규칙과 방법론만 검토하며 미감·개체 닮음·최종 선택은 자동 승인하지 않는다.

비스듬한 시점에서는 인접한 두 후보 사이에 먼 볼의 노출 픽셀 수가 줄어야 한다. 또한 앞 후보의 먼 볼이 다음 후보의 가까운 볼로 바뀐 위치 중 실제 RGB가 달라진 픽셀이 하나 이상 있어야 한다. 코·입·콧등이 지나간 픽셀은 이 수에서 제외한다. 명세의 `exposed_far_pad_px`와 `visible_far_to_near_transfer_px`에 두 값을 기록한다. 정면에서는 한쪽 볼을 더 가리도록 강제하지 않는다.

한 개체의 96×96 정면 얼굴·앉은 전신을 출력하고 조절하는 로컬 제작 도구다. 사진·이전 시안·이미지 모델 호출 없이 저장된 제작 상태와 버전 패키지로 재출력한다. **닮음·B2/C2 정본 미감은 아직 검수 중**이며 동작·자동 사진 분석·제품 앱은 후속 범위다.

## 실행

Python 3.11+, Pillow 12.3.0. 이 폴더에서 실행한다. example.json은 실제 개체와 무관한 합성 입력이다.

```sh
python -m pip install -r requirements.txt
mkdir -p private
python maker.py --db private/profiles.sqlite save example.json --expected 0 --reason initial
python render_v02.py --db private/profiles.sqlite migrate synthetic-example
python render_v03.py --db private/profiles.sqlite migrate synthetic-example --expected 1
python editor_v03.py --db private/profiles.sqlite --dog synthetic-example --port 8765
```

실행한 컴퓨터에서 http://127.0.0.1:8765 를 연다. 종료는 Ctrl+C다. 이미 등록한 DB에 최초 등록 명령을 반복하지 않는다. 기존 0.2 사용자는 render_v03.py의 history로 현재 제작 revision을 확인하고 migrate --expected에 그 값을 전달한다. 이관은 새 revision을 추가하며 원본 관찰 프로필·0.2 기록을 보존한다.

```sh
python render_v03.py --db private/profiles.sqlite history synthetic-example
python render_v03.py --db private/profiles.sqlite state synthetic-example > private/state.json
python render_v03.py --db private/profiles.sqlite save private/state.json --expected 2 --reason adjustment
python render_v03.py --db private/profiles.sqlite render synthetic-example --out output/review-1
python render_v03.py --db private/profiles.sqlite restore synthetic-example --target 1 --expected 3
```

위 revision 값은 최초 등록→0.2 이관→0.3 이관→조절 저장 순서의 예다. 실제 현재 값과 맞지 않으면 충돌로 거절한다. 과거 revision을 선택해 migrate하려면 --from-authoring을 추가한다. 지원하지 않는 치수 조합은 자동 보정하지 않으므로 원본 revision을 보존한 채 편집하거나 이관을 보류한다.

## 0.3에서 바뀐 것

- 머리 내림·목 폭·어깨 폭·골반 폭·앞발 간격을 개체 제작값으로 분리했다. 긴 목과 과도한 골반 팽창을 줄이고 앞발 사이의 여백과 배 아래 색면을 구성한다.
- 큰 털 덩어리의 정수리/귀 실루엣, 턱 연결과 두 볼로 구분되는 주둥이를 보완했다. 주둥이 두 볼의 구분 정도와 동공 비율도 저장한다.
- 0.2의 얼굴 치수·개체 팔레트·5부위 털은 유지한다. 0.3 이관 기본값은 사진 실측이나 모든 강아지의 공통 체형이 아닌 미검수 제작 시작값이다.
- B2/C2는 동일 개체 기하·마스크·큰 색 배치를 공유하고 외곽/겹침선 색 역할만 달리한다. 해당 역할 차이가 정본 화풍 전체의 재현을 뜻하지 않는다.
- 관찰 프로필은 schema 1, 이전 제작 상태는 schema 2, 새 제작 상태는 schema 3이다. 0.3은 출처 0.2 revision/해시와 사진 관찰 프로필 revision/해시를 함께 검증한다.

정면 처진 귀 계열·96px·얼굴과 앉은 전신만 지원한다. 복잡한 무늬·선 귀·다른 방향·64px 재작화·다른 개체 지원 검증·동작은 아직 없다. 사진은 사람이 보고 제작값을 조정했으며 자동 추출 성능으로 보고하지 않는다.

## 편집과 복원

편집 화면에서 4개 보기, 전후 비교, 연결점/눈 가림, 치수·털·색 조절, 초안 저장·재접속·버전 복원을 제공한다. 0.2 상태에서는 “0.3 제작 구조로 이관”을 명시적으로 실행한다. 미저장 수정이 있으면 먼저 저장/복원해야 하며 이관이 수정을 조용히 버리지 않는다.

0.2로 복원하면 0.2 치수·렌더러·비교 기준으로 바뀌고, 0.3으로 복원하면 새 구조로 돌아온다. 복원도 새 revision이며 원래 기록은 바뀌지 않는다. maker.py, state_v02.py, render_v02.py, 기존 형상/색 패키지는 그대로 보존했다. 공동 편집 화면과 HTTP 서버만 여러 버전을 표시하도록 확장했다.

상태는 모두 초안이다. 보호자/화풍/닮음 승인, 활성 사용 묶음 전환, 삭제 UI는 없다. 편집기는 내부 제작자 도구이며 제품의 사진→털 선택→행동/결과 3단계를 늘리는 설문이 아니다. 서버는 127.0.0.1에만 연결하고 세션 토큰·Host/Origin 검사를 사용한다. 공개 서비스용 계정/인증은 없다.

## 결과와 비교

render 명령은 네 개의 투명 PNG, 최근접 6배 확대본, 의미별 마스크, 버전/해시/연결점/팔레트 메타데이터, review.json과 index.html을 생성한다.

HTML에는 **0.2 원본 / 0.3 구조 변경 / 0.3 현재 제작값**의 이미지 12개를 직접 포함한다. HTML만 옮겨도 다른 PNG 경로를 참조하지 않는다. 1·2·4배와 밝은/어두운 배경을 선택할 수 있다. 비교 출처와 구조 기본값에서 달라진 치수·색·털을 기록해 패키지 효과와 수동 보정 효과를 구분한다.

완성된 폴더만 최종 위치로 이동하며 기존 폴더를 덮어쓰지 않는다. 실패한 생성은 최종 결과로 남기지 않는다. 0.2 상태를 render_v03.py로 출력하면 0.2 렌더 경로로 전달한다. 정확한 재현에는 해당 코드·패키지·Pillow 버전이 필요하다. 사진·실제 개체 JSON·DB·결과는 공개 Git에 올리지 않는다.

## 검증과 남은 일

```sh
python -m unittest discover -s tests -v
```

22개 통과: 기존 14개와 새 8개. 0.2 고정 픽셀 해시, 이관/충돌/버전 복원, 관찰 보존, 얼굴에 영향을 주지 않는 몸 조절, 목 연결·발 여백, 눈 가림·홍채·1px 반짝임, 5부위 털, B2/C2 기하, 출력 원자성·비교 출처와 이미지 없는 새 프로세스 3회 재현을 검사한다.

선택 개발 검사에는 Playwright와 설치된 Chromium이 필요하다.

```sh
python -m pip install playwright
python tests/browser_v02.py --browser /usr/bin/chromium
python tests/browser_v03.py --browser /usr/bin/chromium
```

이 환경에서 두 브라우저 검사를 통과했다. 새 편집/저장/재접속과 양쪽 버전 복원, 잘못된 조합 거절, 390px 폭, 독립 HTML 내용의 이미지 12개 로드·배율·배경을 확인했다. 관리 브라우저의 file:// 탐색은 제한되어 HTML 내용을 직접 로드해 검사했으며 실제 기기에서 파일 열기/표시는 별도다.

**다음 과제는 도식적인 얼굴·몸과 정본 작화 차이의 추가 보완, 개체 닮음·목표 표시 크기·보호자 검수다.** 이번 기능/재현 검증으로 이를 완료 처리하지 않는다.

[0.3 검수 기록](VERIFY-v03.md) · [0.2 안내](README-v02.md) · [0.1 안내](README-v01.md) · [로드맵](../../docs/roadmap.md)

## 얼굴 재작업 비교 도구

`review_face.py`는 비공개 JSON 목록에서 원본 사진·화풍 정본·이전/새 후보를 읽어 이미지가 내장된 HTML을 만든다. 각 이미지의 머리 영역을 같은 폭으로 표시하고, 새 네이티브 후보는 원본 전체의 1·2·4배 보기도 제공한다. 영역 지정과 표시 확대만 수행하며 원본 이미지 바이트·프로필·제작 상태를 수정하지 않는다. 승인 기능과 P1 패키지 전환 기능은 없다.

```sh
python review_face.py private/face-review.json output/face-review.html
```

목록에는 `title`, `status`, 문자열 배열 `notes`, 배열 `images`를 넣는다. 각 이미지 항목은 `path`, `label`, `role`, `roi: [x, y, width, height]`가 필수다. 경로는 목록 파일 기준이고 영역은 원본 픽셀 좌표다. 실제 작은 원본 PNG에만 `native: true`를, 새 후보에만 `candidate: true`를 지정한다. 사진의 수동 표시 영역은 해부학적 실측으로 사용하지 않는다. 기존 출력 파일은 덮어쓰지 않는다.

얼굴 재작업에서 6개 머리 보기, 원본 이미지 5개의 독립 로드, 표시 폭 192/256px, 네이티브 1·2·4배, 배경 전환, 390px 화면, 외부 요청/JS 오류 없음과 잘못된 영역 거절을 확인했다. 브라우저 검사는 HTML 내용 로드 방식이며 실제 기기·file:// 탐색 검증은 아니다. 새 얼굴의 96px·14색·공통 기하·재출력 일치는 기술 확인이며, 화풍·닮음은 부분 충족/보호자 미검수로 남았다. 개인 사진·목록·개체 결과는 공개 Git에서 제외한다.

## 사진에서 자세를 추려 64×64에 그리기

골든 측면 예제는 격자에서 직접 그린 전신을 등록한다. 먼 쪽 두 다리의 위쪽을 고정하고 발만 앞으로 0·1·2칸 옮긴 세 프로필과 PNG를 각각 내보낸다. 다음 명령은 이 디렉터리에서 실행하며 출력 경로는 새 이름을 사용한다.

```sh
python native_pose_study.py ../../private-data/face-recheck-v4/profiles.sqlite guide_registration/golden-native-stance.json ../../private-data/native-stance-repeat
```
