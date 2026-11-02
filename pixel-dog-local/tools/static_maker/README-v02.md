# Nana 정적 제작기 0.2

96×96 정면 얼굴·앉은 전신을 만드는 로컬 제작기와 내부 편집 화면이다. 사진·이전 시안·이미지 모델·네트워크를 렌더 입력으로 사용하지 않는다. 정본 B2/C2를 목표로 한 **작화 프로토타입**이며 닮음·정본 미감·보호자 승인은 아직 없다.

## 실행

Python 3.11+와 Pillow 12.3.0을 사용한다. 아래는 실제 개체와 무관한 합성 예제다. 이 폴더에서 실행한다.

```sh
python -m pip install -r requirements.txt
mkdir -p private
python maker.py --db private/profiles.sqlite save example.json --expected 0 --reason initial
python render_v02.py --db private/profiles.sqlite migrate synthetic-example
python render_v02.py --db private/profiles.sqlite render synthetic-example --out output/v02
python editor_v02.py --db private/profiles.sqlite --dog synthetic-example --port 8765
```

마지막 명령을 실행한 컴퓨터에서 http://127.0.0.1:8765 를 연다. 외부 공개 서버가 아니며 종료는 Ctrl+C다. 편집 화면은 파일로 직접 열면 작동하지 않는다. 정적 결과는 output/v02/index.html을 별도로 열 수 있다.

이미 등록한 dog_id에 save --expected 0을 반복하지 않는다. 먼저 maker.py의 history로 프로필 revision을 확인한다. migrate도 최초 제작 상태가 없을 때 사용한다. 새 프로필 버전으로 옮기려면 --profile-revision과 현재 제작 상태의 --expected를 명시한다. 지원 밖 조합은 변환·저장 전에 거절한다.

## 관찰 프로필과 제작 상태

- maker.py/기존 SQLite revisions: 원래 관찰·근거·미확인·행동과 v0.1 제작값을 보존한다.
- state_v02.py/render_states: source_profile의 revision·해시를 참조하는 별도 불변 제작 상태다. 눈 가로/세로·기울기·코·주둥이·턱·부위별 털·색·패키지 버전을 저장한다.
- v0.1에서 옮긴 좌표·색은 **제작값**으로 기록한다. 관찰 사실로 승격하지 않는다. 추가한 기본값과 화면 좌우 기준을 migration에 기록한다.
- 기존 프로필과 제작 상태는 revision 번호가 독립적이다. 제작 상태를 수정·복원해도 기존 프로필 내용과 head는 바뀌지 않는다.
- 저장 시 source dog/revision/hash와 패키지 해시를 확인한다. expected와 현재 제작 상태 head가 다르면 충돌로 거절한다.
- 현재 기능은 초안 저장이다. owner/style/identity 승인값을 편집 API로 올릴 수 없고 활성 release를 자동 교체하지 않는다.

```sh
python render_v02.py --db private/profiles.sqlite state synthetic-example > private/state.json
python render_v02.py --db private/profiles.sqlite save private/state.json --expected 1 --reason adjustment
python render_v02.py --db private/profiles.sqlite history synthetic-example
python render_v02.py --db private/profiles.sqlite restore synthetic-example --target 1 --expected 2
python render_v02.py --db private/profiles.sqlite render synthetic-example --revision 1 --out output/revision-1
```

지원하지 않는 값을 조용히 보정하지 않는다. 범위·가림·화면 경계 오류를 확인한 뒤 사용자가 해당 값을 수정한다. 숨은 부위를 실제로 확인한 것처럼 저장하지 않는다.

## 0.2의 변경

- 턱·목·가슴·귀·눈·주둥이·발·꼬리 연결점 공유. 목줄은 목 영역에 클리핑하고 꺼도 목/가슴이 연결된다.
- 몸/다리/목의 합친 실루엣에 외곽선을 적용한다. 다리 상단의 닫힌 직사각형 테두리를 제거하고 필요한 겹침선만 남긴다.
- 눈 가로/세로·기울기·좌우 높이, 코 폭/높이, 주둥이 위치, 아래 얼굴 폭을 추가했다. 눈꺼풀·앞털 마스크를 빼서 눈 노출 영역을 만든 뒤 홍채·동공·반짝임을 그 안에 제한한다.
- 정수리·귀 끝·볼/턱·가슴·발 둘레의 short/medium/long 제작 옵션을 각각 지원한다. 골격 연결점은 털 길이와 별도다.
- packages/v02/shapes.json에 얼굴·귀·귀 음영·꼬리의 정규화된 형상과 기준값을, styles.json에 외곽선/겹침선 역할을 분리했다. 몸·다리·마스크 구성은 연결점 기반 코드가 담당한다.
- B2/C2는 같은 개체 형상·마스크·큰 색 배치를 유지하고 선 색 역할만 바뀐다. 눈·코의 핵심색은 개체 팔레트를 사용한다.

지원은 정면 처진 귀 계열·96 격자다. 무늬·선 귀·측면·뒷모습·동작·사진 자동 분석·모바일 앱은 없다. 각 값이 개별 범위 안이어도 조합이 잘리거나 겹치면 지원하지 않는다. 64 격자는 아직 지원하지 않는다.

## 편집 화면

얼굴/전신 B2/C2 네 개 보기를 동시에 갱신한다. 연결점·눈 노출/앞털 마스크 오버레이, 0.1과 비교, 원본 1배, 부위별 털·팔레트·세부 치수, 초안 저장·버전 복원·저장본으로 되돌리기를 제공한다. 조정 중/잘못된 조합은 저장을 막고 이유를 표시한다. 오래된 미리보기 응답이 새 조정을 덮어쓰지 않게 처리한다.

로컬 Host/Origin 확인과 페이지 세션 토큰으로 저장 요청을 제한한다. 사용자 계정·외부 접속·공개 배포용 인증은 구현하지 않았다. 기본 바인딩은 127.0.0.1이며 임의 파일 제공 기능은 없다. 관찰 프로필 수정 UI나 제품의 사용자 등록 3단계를 대체하지 않는다.

## 산출물과 재현

출력 폴더에는 네 개의 실제 96×96 투명 PNG, 6배 최근접 확대, 이름 있는 마스크 PNG, 프로필/제작 상태 revision·패키지/코드 해시·Pillow 버전·RGBA/기하 해시·연결점·검수 상태 JSON, 전후 비교 HTML이 들어간다. API 미리보기에는 오버레이가 포함된다.

완성된 결과만 임시 폴더에서 최종 폴더로 이동한다. 실패한 렌더는 최종 산출물로 등록하지 않고 기존 폴더는 덮어쓰지 않는다. 패키지가 수정되면 이전 제작 상태를 조용히 새 패키지로 렌더하지 않고 해시 불일치로 거절한다. 과거 출력을 재현하려면 해당 코드·패키지·Pillow 버전을 복원한다.

maker.py와 styles.json 및 기존 테스트는 0.1 그대로 보존했다. 0.1 명령으로 원래 출력도 재생성할 수 있다. [0.1 안내](README-v01.md).

## 검사

```sh
python -m unittest discover -s tests -v
```

기존 5개와 새 9개, 총 14개 자동 검사가 통과했다. 연결·마스크 가림·변경 범위·동일 B2/C2 기하·지원 밖 조합·원자적 출력·source binding·충돌/복원·새 프로세스 3회 픽셀 재현·편집 API를 검증한다. 실제 개체의 로컬 제작 상태도 별도 프로세스 3회 동일 출력을 확인했다.

브라우저 검사는 선택 개발 의존성인 Playwright와 Chromium이 필요하다.

```sh
python -m pip install playwright
python tests/browser_v02.py --browser /usr/bin/chromium
```

설치된 Chromium 경로를 지정한다. 이 환경에서는 실제 Chromium으로 화면 로드·4개 미리보기·조절·저장·새로고침·복원·지원 밖 조합 거절·초안 초기화·오버레이·모바일 폭을 확인했다. [검수 기록](VERIFY-v02.md).

## 현재 판정

목 연결의 투명한 끊김과 사각 다리 경계는 개선했다. 같은 입력의 재현성과 편집 기능을 검증했지만, 도식적인 몸/얼굴 비율과 정본의 세부 작화 차이는 남아 있다. **정본 미감·개체 닮음·실기기 표시·보호자 검수는 전체 통과가 아니다.** 고해상도 정본을 임의로 재정의하거나 현재 출력으로 교체하지 않는다.

[0.2 보완 기획](../../docs/static-maker-v02-plan.md) · [로드맵](../../docs/roadmap.md)
