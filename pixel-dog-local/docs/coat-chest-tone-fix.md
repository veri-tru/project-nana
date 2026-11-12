# 가슴의 고립된 음영점 수정

2026-11-07 사용자 “가슴음영점처리”에 따른 수정이다. 말티푸 풍성함 진단 출력의 moderate/full 사선 가슴 밝은 원반과 full의 작은 어두운 점을 대상으로 한다. 메시·법선·카메라·길이·풍성함 입력은 수정하지 않는다.

## 처리 규칙

`coat_native64.py`에서 조명을 3단계 톤으로 양자화한 뒤 RGB 팔레트를 배정하기 전에 처리한다. 가장 밝거나 어두운 작은 영역이 8방향으로 완전히 중간 톤에 둘러싸인 경우에만 중간 톤으로 합친다. 한 번의 원본 톤 지도를 기준으로 평가하며 연쇄 보정하지 않는다.

픽셀 중심·깊이·직교 카메라로 모델 좌표를 복원한다. 등록 템플릿의 y<−25 영역과 후방 상흉부 x>20, y<−10 영역만 대상으로 하고 머리 부품 의미 ID를 함께 검사한다. 후방 확장은 y=−25 경계에 걸린 어두운 점을 포함하면서 목 앞쪽을 제외한다. 원본 상흉부/어깨 제작 범위에 따른 상수이며 다른 품종의 해부학 기준이 아니다.

고립 영역의 크기는 화면에 보이는 해당 가슴 영역의 10% 이하여야 한다. 이 값은 제작용 톤 규칙이다. 윤곽·재질/처리 영역 경계·화면 경계에 닿거나, 여러 톤에 둘러싸인 영역은 유지한다. 큰 어깨/등 하이라이트와 하단 그림자 띠를 삭제하지 않는다.

이는 렌더링 톤 정리이며 원래 법선이나 해부 구조가 잘못됐다고 확정하거나 교정한 것은 아니다. 생성 기록에 `tone_policy`와 새 renderer ID를 남긴다.

## 검증

합성 사례와 실제 pinned 모델의 flat/moderate/full × 5시점 × 64/480 해상도를 검사한다. 메시·법선·카메라·alpha·depth·semantic과 처리 영역 밖 색의 불변, 실제 문제 위치의 어두운 점 회귀, 경계에 붙은 밝은 면 보존이 대상이다.

첫 수정은 밝은 원반만 처리했고, 다음 수정에서도 어두운 점이 y=−25 경계에 걸려 남았다. 중간 출력과 독립 기술 근거는 원래 폴더에 보존하고 전달본으로 사용하지 않는다. 현재 r3는 후방 상흉부 처리 범위를 보완한 출력이다.

현재 구조 출력은 `private-data/coat-chest-tone-20261107/{head,chest}-{flat,moderate,full}-r3`에 있다. 구조 6건과 `native64-{flat,moderate,full}-r3` 3건 모두 독립 외형·기술 PASS, 전달 검사 9/9 READY를 확인했다. 사용자 선택은 PENDING이다. 구조 54 PNG와 native 21 PNG를 실제 검토했고 native는 1배와 6배를 확인했다. 이전 `coat-fullness-20261107`의 READY는 당시 코드 해시의 이력이며 현재 코드에 자동 승계하지 않는다.

3D 정수리·가슴 / native64 가슴 풍성함 지원 경계, 볼 및 native 정수리 풍성함 거절, C/B2·개체 닮음·실기기 미승인 상태는 [기존 연결 규격](coat-fullness-integration.md)을 따른다.


## 결과

관련 검사 18개 통과(새 음영 규칙/실제 출력 검사 4개 + native 연결 14개). 독립 기술 재생에서 75개 PNG가 정확히 일치했고 메시·법선·카메라·alpha·depth·semantic·처리 영역 밖 색이 보존됐다. 구조 형상이 동일하므로 기존 정밀 표면/접촉 검사는 바이트 동일 근거를 명시해 재사용했다.

실제 64px의 사선에서 moderate는 밝은 점 6픽셀, full은 밝은 점 23픽셀과 어두운 점 1픽셀이 주변 중간 톤으로 바뀌었다. flat의 7개 native 파일은 이전과 바이트가 같다. 가슴 단계별 외곽 차이는 그대로다. 3D에는 경계 근처의 작은 옅은 명암 세부가 MINOR로 남지만, 대상이던 중앙 원반과 full의 어두운 점은 해결됐다. native 검토의 미해결 사항은 없다.

| 수준 | 수정된 3D | 수정된 64px의 6배 보기 |
|---|---|---|
| flat | [3D](../private-data/coat-chest-tone-20261107/chest-flat-r3/structure-sheet.png) | [64px](../private-data/coat-chest-tone-20261107/native64-flat-r3/native64-preview.png) |
| moderate | [3D](../private-data/coat-chest-tone-20261107/chest-moderate-r3/structure-sheet.png) | [64px](../private-data/coat-chest-tone-20261107/native64-moderate-r3/native64-preview.png) |
| full | [3D](../private-data/coat-chest-tone-20261107/chest-full-r3/structure-sheet.png) | [64px](../private-data/coat-chest-tone-20261107/native64-full-r3/native64-preview.png) |

구현 /root, 독립 외형 /root/chest_tone_visual, 독립 기술 /root/chest_tone_technical. 각 폴더의 두 보고서와 review-status.json에 최종 해시·판정·범위를 기록했다. 형상·화풍 선택이나 실제 미용 재현의 새 승인은 아니다.
