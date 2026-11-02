# Nana 정적 제작기 0.3

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
