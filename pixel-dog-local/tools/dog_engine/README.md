# 현재 엔진 실행 안내

털 표현의 조사 근거와 전체 설계는 [털·미용 표현 기준](../../docs/coat-grooming-reference.md), 실제 사진 4건은 [관찰 기록](../../docs/coat-reference-observations.md)을 따른다. `coat` 명령은 기존 96px 길이 초안과 등록된 말티푸 구조의 **털 설정 → 3D 외피 → 직접 native64 진단 출력**을 지원한다. v2는 3D에서 정수리·가슴, native64에서 가슴 풍성함을 길이와 독립 조절한다. 곱슬·미용 형태와 B2 native64 화풍은 후속이다.

머리 3D 투영과 전신 2D 작화의 공통 진입점이다. 두 경로가 하나의 전신 모델로 연결된 것은 아니다. 구조·선택 범위·이력은 [엔진 정리 문서](../../docs/engine-organization.md)를 따른다.

프로젝트 루트 `pixel-dog-local`에서 실행한다.

```powershell
./engine.ps1 -Setup
./engine.ps1 status
./engine.ps1 doctor
./engine.ps1 verify
```

`-Setup`은 Python 3.12의 프로젝트 전용 `.venv`를 만들고 `verification-lock.txt`의 전체 의존성을 설치한다. 다른 프로젝트의 전역 설치를 변경하지 않는다. 아래 상세 예제의 `python`은 이 환경의 `.venv/Scripts/python.exe`를 뜻한다. 일반 `python`을 사용할 때는 먼저 해당 환경을 활성화해야 한다.

- `status`: 머리 정본·형상 기본값·시안 선택·native64 거절·털 지원 범위·미구현 항목을 구분한다. 두 개체 C의 이미지·선택 기록·검토 근거가 바뀌면 오류를 반환한다.
- `doctor`: Python/전체 고정 의존성 버전, 폰트·저장 모델·검토 입력의 현재 해시를 검사한다. 이미지 승인이나 배포 검증은 아니다.
- `verify`: 환경·입력 검사 통과 후 기존 머리 엔진, 전신 제작기, 새 패키지의 회귀 테스트를 각각 별도 프로세스에서 실행한다. 환경이 다르면 렌더 전에 중단하고 복원 명령을 안내한다.
- `head resolve ...`, `head render ...`: 기존 요청 JSON·카탈로그를 그대로 읽고 분리한 현재 렌더러를 사용한다.
- `body -- ...`: 기존 `render_v03.py` 인수를 전달한다. `--db`는 하위 명령 앞에 둔다.
- `pixel-diagnostic <resolved.json> --out <새 폴더>`: 거절된 골든 native64 재현 전용. 생성 recipe는 전달 BLOCKED이며 비교판에도 진단 상태를 표시한다.
- `ear-structure --output <새 폴더>`: 분리된 귀·머리 진단 실험. 카탈로그 형상/개체 귀 기능 승인과 별개다.
- `neck-structure --output <새 폴더>`: 머리–목–상흉부 연결 실험. 현재 미승인으로, 작화 입력에 바로 사용하지 않는다.
- `structure-gate`: 전체 구조 검토→실제 작화 입력→최종 작화 검토를 확인한다. [명령·필수 계약](../../docs/anatomy-regression-policy.md). 같은 귀 전용 PASS, 짧은 crop, 거절 내용 해시를 재사용해 통과할 수 없다. 자동 형상 판정기는 아니다.

Python 3.12의 실행 의존성은 `requirements.txt`, 과거 구현과의 비교 검사 추가 의존성은 `verification-requirements.txt`, 간접 의존성을 포함한 고정 설치 파일은 `verification-lock.txt`다. 맑은 고딕과 검토 기록의 비공개 입력은 별도 필요하다. 현재 환경의 `doctor` PASS를 다른 컴퓨터나 공개 clone의 실행 보증으로 해석하지 않는다.

`tools/head_engine`은 원본 검토 해시를 유지하는 보존본이다. 새 변경은 이 패키지에서 수행한다. `renderer.py` 또는 `raster.py`를 바꾸면 원본과 회귀 비교 후 `runtime-inputs.json`을 갱신해야 한다. 새 이미지의 외형·기술 검토는 별도다.

## 털 참조와 길이 초안

```powershell
python -m tools.dog_engine coat references
python -m tools.dog_engine coat describe --request tools/dog_engine/examples/coat-lengths.json
python -m tools.dog_engine coat describe --request tools/dog_engine/examples/coat-unsupported.json
```

마지막 명령은 의도적으로 미지원 요청을 보여 주며 exit 2를 반환한다. 지원 요청은 `SUPPORTED_DRAFT_ONLY`, 미지원 항목이 포함되면 `UNSUPPORTED`다. `applicable_patch`는 적용 가능한 부분을 설명할 뿐이며 미지원 항목이 있으면 `apply`는 전체를 거절한다.

가상 개체의 v03 상태와 요청 예제가 함께 제공된다. 프로젝트 루트에서 아래 명령으로 **새 JSON 초안 폴더**를 만든다. 이미 존재하는 출력 폴더에는 쓰지 않는다.

```powershell
$coatState = 'tools/dog_engine/examples/coat-source-state.json'
$coatDigest = (Get-FileHash -LiteralPath $coatState -Algorithm SHA256).Hash.ToLowerInvariant()
python -m tools.dog_engine coat apply --request tools/dog_engine/examples/coat-lengths.json --state $coatState --expected-state-sha256 $coatDigest --out private-data/my-coat-draft
```

- 지원: `target=static-v03`, `regions`의 `crown/ears/cheeks/chest/paws`에 `length=short/medium/long`. 귀는 양쪽 공통이며 이 값은 기존 제작 변위다. mm와 대응하지 않는다.
- 요청의 `intent.kind`는 `authored_example` 또는 `owner_request`다. 입력자가 선언한 출처이며 보호자 확인을 인증하지 않는다. 새 파일의 `review`는 모두 `unreviewed`다.
- 이 v03 경로에서 몸통·목·주둥이·꼬리·다리·좌우 개별 귀 길이, `volume`, `length_mm`, `texture`, `coat_layers`, `grooming`은 미지원이다. `head-3d/native64`는 아래 별도 등록 모델 경로를 사용한다. 알 수 없는 필드·중복 키·잘못된 값은 거절한다.
- `reference_ids`는 `coat references`에 있는 ID 목록이다. 사진 연결 메모이며 사진의 mm·외곽·품종을 실행 값으로 자동 변환하지 않는다.
- 출력: `draft-state.json`과 `application.json`. 원본 상태·요청·코드/패키지 해시, 런타임 버전, 얼굴/전신의 메모리 내 렌더 해시와 anchors 불변 검사를 기록한다. 이미지와 DB는 저장하지 않는다.
- 이 명령은 v03 상태 스키마와 패키지를 확인하지만 DB의 원본 revision·migration 관계를 인증하지 않는다. 실제 DB 저장 시 기존 `body ... save`의 원본·revision 검사를 거쳐야 한다. 정상 종료는 외형·화풍·닮음·native64 승인이 아니다.

## 3D 머리와 실제 64px 연결

등록 모델은 `coat-head-models.json`의 **maltipoo-neck02**(길이 v1)와 **maltipoo-neck02-soft-v2**(길이·풍성함 v2)다. 두 버전은 같은 원본 구조를 사용한다. 머리·목·상흉부의 검토된 원본 NPZ와 계약·보고서 해시가 로컬에 있어야 한다. 원본은 개인 데이터 폴더에 있으며 공개 저장소 복제만으로 재생성할 수 없다. 이 구조는 개체 실측 모델이 아닌 공통 제작 참조다.

요청의 `target`은 `head-3d` 또는 `native64`다. 아래 기존 길이 예제의 `model_id`는 `maltipoo-neck02`다. 두 target 모두 동일 3D 준비 절차를 거친다. 정수리·볼·양쪽 귀·앞가슴의 길이를 적용하며 생략한 부위는 short(기준 외피)를 유지한다. short/medium/long은 추가 변위 0/2/4 제작 단위이고 볼에는 0.4 배율을 적용한다. 실제 mm·모량·미용 명칭을 자동 환산하지 않는다. 눈·코 인접부·턱–목 연결·귀뿌리를 보호하고 원본을 수정하지 않는다.

```powershell
python -m tools.dog_engine coat describe --request tools/dog_engine/examples/coat-head-medium.json
python -m tools.dog_engine coat head-prepare --request tools/dog_engine/examples/coat-head-medium.json --out private-data/my-coat-head
```

준비 명령은 새 모델·고정 semantic 면 라벨·다섯 실제 시점·귀 숨김·동일 카메라 crop·구조 계약·입력 해시를 저장한다. 새 구조는 처음에는 `BLOCKED`다. 독립 외형/기술 리뷰가 같은 파일과 전체 구조 범위를 통과한 `review-status.json`을 작성한 뒤 아래 명령을 실행한다. 명령이 리뷰 승인 파일을 만들지 않는다. 누락·오래된 입력·미지원 혼합 요청은 거절한다.

```powershell
python -m tools.dog_engine coat head-native64 --prepared private-data/my-coat-head --out private-data/my-coat-native64
```

실제 64×64 격자에 깊이 버퍼로 직접 투영한다. 96px 축소를 사용하지 않는다. 각 길이와 시점의 카메라·배율·중심은 원본에서 한 번 정한 값을 사용한다. `head/ear_left/ear_right/eye_-1/eye_1`과 코를 명시적으로 분리하고, 원본의 검은 코 정점이 삼각형의 2개 이상인 면을 코로 고정한다. 부품 ID를 색상 보간으로 추정하지 않는다.

출력은 5개 64×64 프레임, 320×64 atlas, 6배 최근접 미리보기, semantic/depth 배열과 해시 기록이다. **회색 기술 진단 팔레트이며 B2 정본 화풍이 아니다.** 기존 P1/P2/P3 거절 상태도 유지한다. 새 native64 파일 자체의 독립 검토가 끝나기 전에는 전달 차단이며, 구조 검토 PASS를 화풍·닮음 승인으로 승계하지 않는다.

생성 JSON의 `BLOCKED`는 생성 시점 기록이다. 검토 후 최종 판단은 같은 폴더의 `review-status.json`과 `check_delivery.py`를 따른다. 귀는 실제 소유 픽셀만 음영·접경을 구분하며 새 실루엣이나 숨겨진 특징을 그려 넣지 않는다.

재현 예제는 `coat-head-short.json`, `coat-head-medium.json`, `coat-head-long.json`이다. 기술 연결 결과와 검토 범위는 [연결 검증 기록](../../docs/coat-head-integration.md)을 따른다.


## 길이와 독립된 풍성함 v2

`model_id=maltipoo-neck02-soft-v2`는 `volume=flat/moderate/full`을 추가한다. `target=head-3d`는 정수리·가슴, `target=native64`는 가슴만 지원한다. 정수리 풍성함은 현재 64px 구도에서 단계가 구분되지 않아 거절한다. 3D 준비본으로 우회해 native64를 출력할 수도 없다. 길이는 정수리를 위로, 볼·귀·가슴을 아래로 늘리고 풍성함은 정수리의 위·수평 방향과 상흉부의 수평 방향으로 펼친다. 볼은 길이만 지원하며 풍성함은 외형 검증 실패로 차단한다. 원래 턱–목 보호 영역 전체를 유지한다. 실제 모량·밀도·mm 환산값은 아니다. 생략한 길이는 `short`, 풍성함은 `flat`이다. 두 값은 원본 외피에 추가 변위가 없다는 뜻이며 실제 짧은 미용이나 몸에 붙는 피모를 보증하지 않는다. 볼·귀 풍성함·곱슬·미용 명칭은 미지원이며 섞인 요청은 전체 거절한다.

```powershell
python -m tools.dog_engine coat describe --request tools/dog_engine/examples/coat-head-fullness-moderate.json
python -m tools.dog_engine coat head-prepare --request tools/dog_engine/examples/coat-head-fullness-moderate.json --out private-data/my-coat-fullness
```

`coat-head-fullness-flat/moderate/full.json` 세 예제는 길이와 머리 풍성함을 고정하고 가슴 풍성함만 바꾼다. 모든 길이는 long이다. 새 구조의 독립 검토 후 같은 `head-native64` 명령으로 출력한다. 버전·요청·참조 목록·코드 해시가 바뀌면 준비부터 새 검토를 거쳐야 한다. [v2 구현과 검증 기록](../../docs/coat-fullness-integration.md).

3D 전용 정수리·가슴 예제는 `coat-head-structure-fullness-flat/moderate/full.json`이다. 준비 후 해당 구조 자체를 검토할 수 있으나, 정수리 풍성함을 지정한 요청은 native64로 내보낼 수 없다.

가슴의 고립된 작은 밝은/어두운 톤은 모델 좌표의 가슴·후방 상흉부 안에서만 주변 중간 톤으로 정리한다. 형상·법선·깊이·부위 구분은 유지한다. [규칙·현재 예시·검증](../../docs/coat-chest-tone-fix.md).
