# 현재 엔진 실행 안내

머리 3D 투영과 전신 2D 작화의 공통 진입점이다. 두 경로가 하나의 전신 모델로 연결된 것은 아니다. 구조·선택 범위·이력은 [엔진 정리 문서](../../docs/engine-organization.md)를 따른다.

프로젝트 루트 `pixel-dog-local`에서 실행한다.

```powershell
python -m tools.dog_engine status
python -m tools.dog_engine doctor
python -m tools.dog_engine verify
```

- `status`: 머리 정본·형상 기본값·시안 선택·native64 거절·미구현 항목을 구분한다.
- `doctor`: Python/라이브러리 버전, 폰트·저장 모델·검토 입력의 현재 해시를 검사한다. 이미지 승인이나 배포 검증은 아니다.
- `verify`: 기존 머리 엔진, 전신 제작기, 새 패키지의 회귀 테스트를 각각 별도 프로세스에서 실행한다.
- `head resolve ...`, `head render ...`: 기존 요청 JSON·카탈로그를 그대로 읽고 분리한 현재 렌더러를 사용한다.
- `body -- ...`: 기존 `render_v03.py` 인수를 전달한다. `--db`는 하위 명령 앞에 둔다.
- `pixel-diagnostic <resolved.json> --out <새 폴더>`: 거절된 골든 native64 재현 전용. 생성 recipe는 전달 BLOCKED이며 비교판에도 진단 상태를 표시한다.

현재 Python 3.12 환경의 버전은 `requirements.txt`, 과거 구현과의 비교 검사 추가 의존성은 `verification-requirements.txt`에 있다. 맑은 고딕과 검토 기록의 비공개 입력은 별도 필요하다. 현재 환경의 `doctor` PASS를 다른 컴퓨터나 공개 clone의 실행 보증으로 해석하지 않는다.

`tools/head_engine`은 원본 검토 해시를 유지하는 보존본이다. 새 변경은 이 패키지에서 수행한다. `renderer.py` 또는 `raster.py`를 바꾸면 원본과 회귀 비교 후 `runtime-inputs.json`을 갱신해야 한다. 새 이미지의 외형·기술 검토는 별도다.
