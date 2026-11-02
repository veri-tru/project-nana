# Nana 정적 제작기 0.1

Python 3.11+ / Pillow 12.3.0. 사진이나 이전 PNG를 입력으로 받지 않는 로컬 제작기 프로토타입이다. SQLite에 불변 프로필 revision을 저장하고 코드로 정의한 픽셀 부품·가림 마스크·팔레트 역할을 조립한다. 모델 호출·네트워크·난수를 사용하지 않는다.

## 실행

이 폴더에서 실행한다. example.json은 실제 개체와 무관한 합성 입력이다.

```sh
python -m pip install -r requirements.txt
python maker.py --db profiles.sqlite save example.json --expected 0 --reason initial
python maker.py --db profiles.sqlite render synthetic-example --out output/demo-1
python -m unittest discover -s tests -v
```

output/demo-1/index.html을 브라우저로 연다. 얼굴·앉은 전신 각각 B2/C2의 실제 96×96 투명 PNG, 최근접 6배 확대본, 의미별 마스크 PNG와 생성 메타데이터를 출력한다. 출력 폴더가 이미 있으면 덮어쓰지 않고 실패한다. 입력 사진·정본은 렌더 실행에 필요하지 않다.

## 저장·수정·복구

JSON 사본에서 원하는 값을 바꾸고 현재 revision을 명시해 save한다. revision 0은 최초 등록에만 사용한다. 동시 수정의 expected 값이 현재 head와 다르면 저장하지 않는다. 전체 스냅샷이 새 revision으로 추가되고 기존 스냅샷은 유지된다.

```sh
python maker.py --db profiles.sqlite save edited.json --expected 1 --reason ear-length-correction
python maker.py --db profiles.sqlite history synthetic-example
python maker.py --db profiles.sqlite rollback synthetic-example --target 1 --expected 2
python maker.py --db profiles.sqlite render synthetic-example --revision 1 --out output/old-revision
```

rollback은 과거 기록을 수정하지 않고 복원한 내용으로 새 revision을 추가한다. 모든 출력은 초안이다. 활성 release 자동 교체·보호자 승인 기능은 제공하지 않는다. 개인 프로필·DB·사진·출력은 Git에 올리지 않는다. 삭제/사용 묶음 전환 UI는 후속 작업이다.

## 입력 계약

- appearance.geometry의 정수는 96 격자용 제작값이다. 사진 실측값이 아니며 근거·미확인은 evidence/unresolved에 따로 기록한다. 지원 범위는 maker.py의 RANGES를 따른다. 범위 안이라고 모든 조합의 미감이 검증된 것은 아니다.
- appearance.colors는 의미별 색 역할이다. 눈·코·털은 구분하며 기본색과 음영을 별도로 지정한다. 렌더러는 지정한 색과 outline만 사용한다.
- render.coat_length는 short/medium/long이고 현재 정수리 실루엣만 바꾼다. 전신 털 길이 지원으로 표시하지 않는다. collar_visible은 목줄 표시 설정이다.
- left/right_occlusion은 캐릭터를 보는 화면 좌우다. 이 시제품은 정면만 지원하므로 해부학적 좌우 무늬 시스템으로 일반화하지 않는다.
- behavior는 저장·복구만 한다. 행동을 분석하거나 동작을 출력하지 않는다.
- evidence는 photo_observation/owner_report/design_default/synthetic를 구분한다. 미확인값을 실제 습관·눈꺼풀 형태로 확정하지 않는다.
- unknown 필드, 잘못된 색·자료형, 지원 밖 치수/화풍/방향을 거절한다. 가려진 외형이 미확인이어도 제작값으로 그림을 출력할 수 있지만 결과 수락을 실제 해부학 확인으로 취급하지 않는다.

## 제작 패키지와 검증

maker.py가 형상·레이어·가림 정의를, styles.json이 B2/C2의 윤곽색을 담당한다. 두 파일 해시, Pillow 버전, 프로필 해시/revision, RGBA 픽셀 해시와 geometry 해시를 결과 JSON에 기록한다. 외부 이미지가 필요한 템플릿은 없다. 패키지 수정 시 새 버전과 해시를 남겨야 한다.

5개 테스트에서 불변 revision·복구·충돌, 두 개체 분리/미확인 보존, 지원 밖 입력, B2/C2 마스크·알파 동일성과 색 차이, 국소 눈 가림 수정, 색 수≤24·알파 0/255, 이미지 읽기 금지, 소스 코드/스타일/합성 프로필만 복사한 새 프로세스 3회 동일 출력, 출력 덮어쓰기 거절을 검증한다. PNG 파일 부가 메타데이터가 아닌 RGBA 버퍼를 비교한다.

## 현재 한계와 판정

기술 프로토타입 구현 완료. 정본 B2/C2의 시각적 재현과 실제 개체 닮음은 부분 충족/검토 대기이며 보호자 승인은 없다. 외곽선 색만 바꾸는 현재 패키지가 정본 화풍 전체를 구현했다고 주장하지 않는다. 형상이 도식적이고 몸·다리 연결과 귀/얼굴 비율의 작화 보완이 필요하다.

지원은 긴 처진 귀 계열의 정면 얼굴·앉은 전신·96 격자로 제한한다. 반점·비대칭 무늬, 선 귀, 측면/후면, 64 격자 전용 작화, 개체 확장 검증, 애니메이션, 자동 사진 추출, 앱/웹 편집 UI는 없다. 이 도구의 HTML은 결과 보기용이며 사용자 등록 앱이 아니다. 실제 관찰값 자동 추출 없이 사람이 내부 제작값을 입력했다.

로드맵 단계 1의 저장 핵심과 단계 2의 정적 출력 구현은 실행했다. 단계 0의 실기기 확보, 단계 1의 제품 UI/사용 묶음, 단계 2의 정본 미감·닮음·표시 크기 최종 검수를 완료 처리하지 않는다.

## 후속 보완 계획

[0.2 기획](../../docs/static-maker-v02-plan.md)은 연결점·얼굴/가림·부위별 털·작화 패키지·내부 수정 도구와 검수 기준을 정리한다. 기획만 완료됐으며 이 폴더의 실행 버전은 여전히 0.1이다.

