# 머리 엔진의 체급·품종·개체 설정

2026-11-06 화풍 상태: 계층 해석과 모델 코드는 유지한다. 아래 `pixel.py` 출력 P1/P2/P3는 사용자에게 기존 품종 시안과 화풍이 다르다는 지적을 받아 REJECTED/BLOCKED다. 현재 표현 정본은 [breed-head-soft-B2-v1](../../references/styles/breed-head-b2/v1/manifest.json)이며, 이 정본과 일치하는 native64 변환은 아직 검증하지 않았다. 코드 규격 통과를 제품 화풍 승인으로 해석하지 않는다.

체급 → 품종 → 개체 설정을 해석한 JSON을 실제 저장 모델 선택과 5시점 렌더에 사용한다. 기존 검토 모델을 다시 만들거나 수정하지 않는다. 현재는 머리와 짧은 목만 지원한다.

| 계층 | 실제 적용 항목 | 근거와 한계 |
| --- | --- | --- |
| `size_class` | relative 표시의 기본 상대배율 | small=0.85, medium=1.00, large=1.15는 제작 기본값이다. 체중 경계나 cm 치수가 아니다. 얼굴형 선택에 관여하지 않는다. |
| `breed` | 검토된 `geometry_preset` 선택 | 골든은 `golden-adult-head-v1/model-B.pkl` 작업 기본값이다. 휘핏·닥스훈트·말티푸는 `skull-based-heads-v2`의 기존 B 모델이다. |
| `individual` | 상대배율·같은 품종의 모델 선택을 우선 적용 | 변경한 항목마다 `kind`, `source`, `note`를 기록한다. 지원하지 않는 정점·색·골격 편집은 거절한다. 근거 문자열의 사실성을 자동 인증하지 않는다. |

골든의 A/B/C는 검토된 작업 후보이며 최종 사용자 선택은 PENDING이다. 기본값 B를 사용자 승인으로 기록하지 않는다. 품종이 같아도 `size_class`를 따로 지정할 수 있다. 체급에 따라 얼굴을 둥글거나 넓게 만드는 규칙은 없다.

## 잭 러셀 머리 모델

개체별 귀: 같은 품종이라도 서거나 접히는 귀, 좌우 비대칭을 구분해야 한다. [개체 귀 요구사항](../../docs/profile-generation-spec.md#개체별-귀-형태와-자세)을 따른다. 현재 엔진은 저장 모델 선택만 지원하며 개체별 귀 교체·접힘·각도 변경은 아직 구현하지 않았다. 품종 기본 귀를 개체의 확정 특징으로 취급하지 않는다.

`jack_russell`은 검토를 통과한 `jack-russell-A/B/C` 외피 모델을 선택한다. 작업 기본값은 B이며 사용자 최종 선택은 PENDING이다. [예제](examples/jack-russell-working.json)는 `small` 체급을 사용한다. A/B/C의 주둥이 앞뒤 길이는 기준의 94%/100%/106%다. 기존 품종과 마찬가지로 체급은 표시배율이며 얼굴형을 결정하지 않는다.

```powershell
python tools/head_engine/engine.py resolve --profile tools/head_engine/examples/jack-russell-working.json --output outputs/jack-russell-next/resolved-profile.json
python tools/head_engine/engine.py render --resolved outputs/jack-russell-next/resolved-profile.json --output-dir outputs/jack-russell-next
```

골격·중립 외피 원본과 비교판은 [jack-russell-head-v1](../../outputs/jack-russell-head-v1/README.md)에 있다. native64 색상 어댑터는 아직 골든 전용이며 잭 러셀 픽셀 자산은 생성하지 않았다. catalog가 갱신되면 이전 resolved JSON을 수정하지 말고 원래 요청을 새 폴더에서 다시 resolve한다.

## 표시 방식

- `normalized`: 해당 모델의 5시점 전체에서 가장 큰 투영 길이를 320px에 맞춘다. 다섯 시점은 한 배율을 공유한다. 모델 간 비율 비교를 위한 최대 bbox 정규화이며 `relative_scale`과 `scene_scale`을 화면 크기에 적용하지 않는다.
- `relative`: `scene_scale × relative_scale`을 그대로 pixels/model-unit 배율로 사용한다. 여러 개체를 비교하려면 같은 `scene_scale`을 지정한다. 기존 모델 단위는 실측 cm로 보정되어 있지 않으므로 이 모드를 실제 크기 비교라고 부르지 않는다.
- 상대 표시가 셀을 넘으면 오류로 중단한다. 잘리지 않게 몰래 축소하지 않으며, 호출자가 공통 `scene_scale`을 낮춰야 한다.

후속 실측 크기 경로에는 단위·측정 부위·측정 근거·모델 좌표와 실제 단위의 변환을 따로 정의해야 한다. 현재 `actual-size` 모드나 체중 기반 자동 체급 분류는 지원하지 않는다.

## 실행

프로젝트 루트에서 실행한다. 이미 파일이 있거나 검토 기록이 있는 출력 폴더에는 덮어쓰지 않는다. 새 작업 폴더를 사용한다.

```powershell
python tools/head_engine/engine.py resolve --profile tools/head_engine/examples/golden-working.json --output outputs/golden-pixel-next/resolved-profile.json
python tools/head_engine/engine.py render --resolved outputs/golden-pixel-next/resolved-profile.json --output-dir outputs/golden-pixel-next
python -m unittest discover -s tools/head_engine/tests -v
```

첫 명령은 체급 기본값, 품종 모델, 개체 override를 순서대로 반영해 최종 값과 항목별 provenance를 저장한다. 두 번째 명령은 그 **저장된 JSON을 읽어** 모델을 선택하고 실제 정점·면을 투영한다. `resolved-profile.json`을 수동 수정하면 실행을 거절한다. 요청 JSON을 고친 뒤 새 폴더로 다시 resolve한다.

`examples/golden-working.json`은 기본 비율 비교용이다. 개체 override 예시는 다음과 같다.

```json
{
  "schema_version": 1,
  "size_class": "large",
  "breed": "golden",
  "individual": {
    "id": "example-golden",
    "overrides": {
      "geometry_preset": "golden-adult-A",
      "relative_scale": 1.05
    },
    "evidence": {
      "geometry_preset": {
        "kind": "authored_default",
        "source": "example-comparison-01",
        "note": "약한 비율 조정 후보를 비교하는 예시이며 사용자 선택이 아니다."
      },
      "relative_scale": {
        "kind": "authored_default",
        "source": "example-comparison-01",
        "note": "표시배율 예시이며 실제 몸길이나 체중 측정값이 아니다."
      }
    }
  },
  "display": {
    "mode": "relative",
    "scene_scale": 3.2
  }
}
```

근거 종류는 `authored_default`, `owner_report`, `observed_input`만 받는다. `owner_report`나 `observed_input`을 선택했다고 사용자 승인이나 실측 크기로 승격하지 않는다. 다른 품종의 preset 선택, 알 수 없는 키, 누락된 근거, bool을 포함한 잘못된 숫자 타입, NaN·Infinity·범위 밖 배율을 거절한다.

## API

- `resolve_profile(request)`: 최종 설정과 provenance를 반환한다.
- `validate_resolved(resolved)`: 요청과 catalog에서 재해석한 값과 같은지 확인한다.
- `verify_source(resolved)`: 선택 모델·원본 검토·렌더 의존성의 해시와 기존 전달 검사를 확인한다.
- `load_model(resolved)`: 검증 후 선택한 저장 외피 모델을 읽는다. 원본에 쓰지 않는다.
- `projection_plan(resolved, bounds)`: 5×2 투영 bbox로 실제 배율과 픽셀 크기를 계산한다.
- `render_resolved(resolved)`: 실제 5시점 이미지와 배율 기록을 메모리에서 반환한다.
- `render_file(resolved_path, output_dir)`: 저장된 JSON을 소비해 새 참조 이미지와 입력 기록을 쓴다.

`catalog.json`에 등록된 원본만 읽는다. 사용자가 입력한 임의 파일 경로를 pickle로 역직렬화하지 않는다. 원본 모델·검토 상태·원본 코드의 해시가 바뀌면 실행을 중단한다. 새 원본 채택은 별도 검토 후 catalog를 갱신해야 한다.

## 출력과 검증

- `engine-reference.png`: 실제 저장 메시에서 그린 2400×650 RGB 5시점 참조. 부드러운 3D 렌더이며 native 픽셀 자산이 아니다.
- `engine-render.json`: 선택 모델 해시, 모드, 실제 pixels/model-unit 배율, 시점별 투영 bbox, source/output 사용자 상태.
- `engine-inputs.json`: 원본 모델·코드·검토 보고서·간접 입력·폰트·resolved JSON과 참조 이미지의 SHA-256. 최종 독립 리뷰용 입력 기록이다.

새 출력은 독립 외형/기술 검토 전까지 전달 승인 상태가 아니다. 원본의 검토 PASS를 새 참조 그림의 PASS로 자동 승계하지 않는다. 최종 `review-status.json`은 구현 호출자가 관리하며 엔진이 생성하거나 덮지 않는다.

테스트는 계층 우선순위, 체급과 얼굴형 분리, 잘못된 입력, 근거 누락, 같은 품종 내 모델 선택, resolved 변조, 다른 세 품종 원본 배열 보존, 골든 B 실제 투영 배열 일치, normalized/relative 배율 차이와 원본 출력 보호를 확인한다. 실행 환경은 기존 Python·NumPy·Pillow·SciPy·scikit-image·Numba 설치를 사용하며 환경 전체를 잠근 배포 패키지는 아니다.

## 실제 64×64 픽셀 출력

`pixel.py`는 위 계층에서 해석된 모델을 실제 64×64 깊이 버퍼에 직접 투영한다. 기존 3D 생성기와 저장 형상은 바꾸지 않는다. 이미지 생성 모델·고해상도 축소·안티앨리어싱을 사용하지 않는 기존 코드 기반 엔진의 출력 단계다. 초기 색상 어댑터는 골든 머리/짧은 목만 지원한다.

```powershell
python tools/head_engine/pixel.py outputs/golden-pixel-next/resolved-profile.json --out outputs/golden-pixel-next
```

세 스타일은 같은 형상·눈/코 픽셀·알파를 공유한다. P1/P2는 B2 계열의 같은 윤곽과 팔레트에서 음영 경계만 다르고, P3는 P2의 윤곽색만 C2 계열로 바꾼다. 외곽/귀 겹침 윤곽 1색과 눈·코/털 기본/밝음/그늘의 내부 4색을 사용한다. 기본 표정의 입선을 새로 만들어 넣지 않는다. 코와 눈을 별도 의미 마스크로 투영한 뒤, 폭 2칸 이하의 보이는 코만 기존 실루엣 안쪽으로 한 칸 확장한다. 눈은 투영 중심에 맞춘 3칸/4칸 클러스터로 정리하고 가려진 눈은 만들지 않는다. 이는 원본 크기에서 특징을 보존하기 위한 픽셀 단계 보정이며 3D 부착점 변경이 아니다.

각 atlas는 320×64 투명 PNG이며 왼쪽부터 측면·사선·정면·후면·윗면의 64×64 프레임 다섯 개를 담는다. `pixel-comparison.png`는 6배 최근접 보기와 1배 원본을 함께 보여준다. 20개 관련 테스트는 15개 프레임의 팔레트·이진 알파·여백, 모든 확대 블록/원본 영역, 윤곽만 변경한 P3, 직접 재출력 일치, 상대 크기와 형상 분리를 포함한다.

픽셀 CLI의 `--mode`를 생략하면 resolved profile의 표시 모드를 따른다. `--native-scene-scale` 기본값 0.4는 native 격자의 모델 단위당 px이며 고해상도 참조의 scene_scale과 구분한다. `relative`는 여기에 최종 relative_scale을 곱하고, 넘치면 오류를 낸다. `normalized`는 다섯 시점의 최대 길이를 54칸에 맞춘다. 실제 cm 보정·전신·애니메이션·실기기 표시는 아직 지원하거나 검증한 결과가 아니다.
