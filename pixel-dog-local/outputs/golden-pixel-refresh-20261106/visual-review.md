# 골든 픽셀 재작화 독립 외형 검토 — 수정 2

- 검토일: 2026-11-06
- 검토자: `/root/golden_native_visual`
- 판정: **PASS**. 기존 V01 MAJOR와 V02 MINOR는 이번 직접 재검토에서 해소됐다. 미해결 BLOCKER/MAJOR/MINOR는 없다.
- 본 검토자는 제작에 참여하지 않은 외형 리뷰어다. 첫 검토는 제작자의 성공 평가 및 기술 PASS 없이 시작했다. 이번 재검토는 같은 독립 리뷰어가 수정 범위를 전달받고 실제 파일을 다시 열어 수행했다. 이번 파일의 기술 PASS는 판정 근거로 받거나 사용하지 않았다.
- 이전 FAIL 보고서와 결과는 `iterations/01/`에 보존돼 있다. 이전 판정을 덮어 통과시킨 것이 아니라 바뀐 해시의 그림을 다시 판정했다.
- 골든 B는 작업 기본안이며 사용자 최종 선택이 아니다. PASS는 정적 외형 후보 전달 가능 상태이고 사용자 승인, 실측 해부학 정확도 또는 기술 검증 완료를 뜻하지 않는다.

## 직접 확인 범위

| 파일 | 이번에 직접 연 범위 |
|---|---|
| pixel-comparison.png | 세 스타일 × 측면·사선·정면·후면·윗면의 15개 6배 셀과 동일 15개 원본 1배 셀 전부 |
| P1-soft-atlas.png | 320×64 원본의 다섯 64×64 프레임 전부 |
| P2-depth-atlas.png | 320×64 원본의 다섯 64×64 프레임 전부 |
| P3-contrast-atlas.png | 320×64 원본의 다섯 64×64 프레임 전부 |
| engine-reference.png | 측면·사선·정면·후면·윗면 5셀 전부 |

픽셀 네 파일을 먼저 `view_image(detail=original)`로 열고 원본 atlas, 비교판의 1배 셀, 비교판의 6배 셀을 관찰했다. 그 뒤 engine-reference를 다시 열었다. 이 검토에서 그림이나 생성 코드를 수정하지 않았다.

engine-reference의 SHA-256은 첫 검토와 같은 `45c75c02ff081898fb7532bc200c4acd3fbd609d289ae2fc0cfa31b792f88741`이며 이번에도 직접 열었다. 첫 검토에서 직접 확인한 원본 `../golden-adult-head-v1/exterior-comparison.png` B행, `../deformation-b-face-v2/golden-reference.png` 왼쪽 실제 골든 사진 및 `../../references/styles/b2-c2/v1/reference-sheet.png` B2/C2 양쪽의 관찰을 참고 근거로 재사용했다. 수정 범위가 픽셀 코·눈이고 source 3D와 참조가 유지됐다는 전달 내용을 전제로 하며, 입력 불변 및 재현성의 포괄 검증은 기술 리뷰의 책임이다.

## 수정 사항 재판정

### V01 — 해소: 측면 코의 원본 1배 가독성

- 대상: 세 atlas의 첫 프레임과 비교판 세 행의 측면 코끝. 윗면과 사선·정면도 함께 확인했다.
- 이전 관찰: 검은 코가 극소수 끝 픽셀에 머물러 털 외곽선에 묻혔다.
- 이번 관찰: 검은 면이 주둥이 안쪽으로 두께를 가져 끝 윤곽의 단순한 한 점과 구분된다. 세 안 모두 원본 1배에서 어두운 코끝으로 판독되며, 6배에서는 검은 영역이 주둥이에 붙어 있는 것을 확인했다. P3에서도 외곽선과 같은 방향으로 길게 번지거나 코가 분리된 덩어리가 되지 않았다.
- 연관 시점: 사선·정면은 기존 넓은 코를 유지한다. 윗면의 검은 코도 주둥이 끝에 연속적으로 붙어 있다. 측면 코는 여전히 작은 투영이나, 이전의 사실상 소실 상태는 해소됐다.
- 판정: RESOLVED. 원시 3D의 형상 변경을 요구하거나 승인한 판정이 아니다.

### V02 — 해소: 둥근 눈 방향

- 대상: 세 안의 측면·사선·정면·윗면 눈. 후면의 눈 부재도 확인했다.
- 이전 관찰: 대각으로 꺾인 작은 갈고리 모양이 둥근 눈 인상을 약화했다.
- 이번 관찰: 눈에 중심이 있는 작고 조밀한 어두운 덩어리가 생겼다. 6배에서는 격자 때문에 십자형에 가까운 부분이 보이지만 1배에서는 짧은 선이나 갈고리보다 작은 둥근 점으로 읽힌다. 눈의 위치와 얼굴 방향은 유지되고 불필요한 반사점은 보이지 않는다.
- 판정: RESOLVED. 64격자 단순화를 허용한 현재 요구에서 충족하며, 매끄러운 원이나 사진 수준의 눈 묘사를 뜻하지 않는다.

## 모든 시점의 회귀 관찰

| 시점 | 세 스타일 모두에서 확인한 결과 |
|---|---|
| 측면 | 코끝·깊은 주둥이 아래 면·눈·처진 귀를 1배에서 구별할 수 있다. 코가 부리처럼 길게 돌출하거나 분리되지 않았다. 귀와 목의 큰 관계가 유지된다. |
| 사선 | 검은 코와 가까운 눈, 귀 앞 경계를 판독할 수 있다. 먼 눈의 제한된 노출은 가장자리 가림 안에 머무른다. 코 밑에 새로 분리된 구형 덩어리가 없다. |
| 정면 | 양 눈·코·양 귀가 구별되고 넓은 아래 얼굴이 유지된다. 둥근 두개부는 남지만 아래 얼굴 폭을 잃어 과도하게 어린 강아지 비율이 된 변화는 없다. |
| 후면 | 눈·코를 추가하지 않았고 양 귀·뒤통수·중앙 목이 이어진다. 귀뿌리 구멍, 단절 또는 새 판형 목은 관찰되지 않는다. |
| 윗면 | 주둥이가 넓고 끝으로 뾰족하게 수렴하지 않는다. 양 눈과 양 귀 뿌리가 구별된다. 엔진에서도 보이는 귀의 작은 캡 같은 단면이 남지만 새 부착 단절이나 구멍은 보이지 않는다. |

P1은 밝은 면이 넓고 P2는 아래 그늘이 넓으며 P3는 P2의 음영 배치에 짙은 윤곽을 사용한 것으로 읽힌다. 세 안 사이 머리 실루엣이나 귀·목 위치가 달라졌다는 시각적 증거는 없었다. 이는 눈으로 본 관찰이며 픽셀 단위 동일성 또는 메시 불변을 검사한 기술 결론은 아니다.

실제 골든 사진의 넓고 깊은 주둥이와 처진 귀를 판단 근거로 삼았다. 사진은 입을 벌린 측면이므로 닫힌 입 또는 다른 방향의 개체 닮음을 실증하지 않는다. B2/C2 참고는 윤곽 대비와 큰 색면의 역할에 사용했으며 그 캐릭터의 품종·무늬·눈 크기를 골든에 이식하는 기준으로 삼지 않았다.

## 한계와 기록

원본 atlas를 직접 열고 비교판의 원본 1배를 확인한 결과다. 실제 기기, 움직임, 전신, 체급 간 상대 크기는 검토하지 않았다. 작은 코·눈은 64격자의 제한된 표현이며 모든 화면 환경의 가독성을 보증하지 않는다. 명백한 구조 결함을 사용자 취향으로 넘긴 미해결 항목은 없다.

표식의 artifacts는 직접 검토한 최종 5개 PNG의 현재 해시이며 현재 파일과 대조해 일치했다. inputs 42개는 evidence.json의 동일 생성 입력 집합을 검토 버전에 연결하기 위해 포함한다. 이를 포함했다는 사실만으로 입력 코드·재현성·수치 정확도를 외형 리뷰가 기술 승인한 것은 아니다. 전체 입력 검증과 전달 판정은 별도 기술 보고서 및 review-status.json에서 함께 확인해야 한다.

<!-- review-verdict: {"status":"PASS","reviewer":"/root/golden_native_visual","artifacts":{"engine-reference.png":"45c75c02ff081898fb7532bc200c4acd3fbd609d289ae2fc0cfa31b792f88741","pixel-comparison.png":"a5da995e312c3c114b725db3bdd0108dd8e1d442c093b291932a623995c71981","P1-soft-atlas.png":"5dd0e065c927528f3f3b63016db8d8a3f1f5c677b80cde47f77c7a1a5f9ccb9d","P2-depth-atlas.png":"d2283370019bf38dda2b89cd9ee95eaaca289b531a4563e2b50c6b2de936d1b1","P3-contrast-atlas.png":"aab44b7c4c59b3a5fe6d65ae13451ebf2053dcb55d876726adb25889a236dd8e"},"inputs":{"../deformation-b-face-v2/golden-reference.png":"2be4a6076f6730adbbab58d68536181bf15b528898084adae17b5f49f1b032ef","../golden-adult-head-v1/build.py":"885b85b9d9ec1380fe7f1549359b77949dd0ccf6130782042d1c244f70d98898","../golden-adult-head-v1/exterior_seed.py":"1d2dc33999af309e5e3add4885408817c45047ee236ac68286f79189f6701102","../golden-adult-head-v1/model-A.pkl":"e6844a219181cba6e8a62139dd7229e2dc6656e6e40a110cac27dcb66ed099c8","../golden-adult-head-v1/model-B.pkl":"9ccdb84a4d3f03604b3f49195a1b919224e92641c04640781fde535c10dbf122","../golden-adult-head-v1/model-C.pkl":"2aead49c66c118880a21d9d9a1c1129694df49b07c692811b31764697e64f0be","../golden-adult-head-v1/parameters-A.json":"4d1e0bc80b91088a05c4e74086b49d8d72b54e65d5707cc4ff00abb4605f4435","../golden-adult-head-v1/parameters-B.json":"cd1910fce896650a2ef027208f8a1ddf37f36ad00dc5c81311503fc3c9c2d987","../golden-adult-head-v1/parameters-C.json":"a8bc6c3d01d6bef464b28d252123949a92d9c8e7c019f40eaa81d91dc0388a4b","../golden-adult-head-v1/parameters.json":"8444d5c83ae838d303c9683730ef6b85d918e18b3f4d09715316318a53d2c2e3","../golden-adult-head-v1/references.json":"3d20e0b322ed00be58e00f77ffca33a2e41d47800e2795240bd6abf1edea41fd","../golden-adult-head-v1/review-status.json":"a608f16458339098b98f14b30c7ed6709ba3683506acb5b65c8723bd080fcd07","../golden-adult-head-v1/technical-review.md":"fe5aca73eb253fa8cdef9a2d49e365adbc141542f094b504c3ccc583f234d296","../golden-adult-head-v1/visual-review.md":"0cf3e5ca40fd70e6bb18d97950f9d3fe48398f03b9f9c222648714ea5a42d12a","resolved-profile.json":"dbc7809ef0ded534e4132887e27fe2e24b111b6965102c501a36c78c72cd52e7","../head-skeleton-volume-v2/build.py":"734b85527c58a0cf9bf598867dfabbd9bddf2dd91f50b8fef9ec9fbc6733419e","../head-skeleton-volume-v2/geometry.pkl":"eaec7d20d5ea8abbb8a14e728d6120f4f119e2d3ee238d4af5b3836f06e4d154","../head-skeleton-volume-v2/profiles.json":"aab232a82947fe4a81c6785e3c4e54ad458dca82c82a99e1aa9431ce8e29e323","../head-skeleton-volume-v2/raster.py":"f2747b235362f49c94d8a7121784d5d597464723649bd1a4b951396dbb289f15","../head-skeleton-volume-v2/references.json":"ae6dd24467d04a9666b1def48ff3f7cdcbdeb9708011a08940629c6b26a93c3d","../head-skeleton-volume-v2/review-status.json":"5c9d76e0d6c23f260daf3fa4f327d9cbc2b8b4c8204567a19bcf7754a0ff7e1e","../skull-based-heads-v1/build.py":"84ff23798e2d487de2dddaa2302f15eebd292affb4dec0c9ab3690b2df410b2d","../skull-based-heads-v2/build.py":"37e6843526018bec5c1f501f4feb8253b7a097f1905fd4c9b9ae63b5ded3a384","../skull-based-heads-v2/geometry.pkl":"3321e3644b2647bb29238898995646d29b0e1fce64851e672d8267f3b7bc2cf9","../skull-based-heads-v2/parameters.json":"5d534c3ab7008f55d7a2f1523b5ee921ed75f724109d12a6f0fb5e8873139230","../skull-based-heads-v2/review-status.json":"4debc35e3aa60ac15e448d4d57541d933c4cf8b9cce560aa0428fc5285791892","../../private-data/skull-anatomy-v2/dorsal.jpg":"f7c059883e2ca7a9ba17f48385f62485e3c2c40b4189dbfff13052b417167a10","../../private-data/skull-anatomy-v2/lateral.jpg":"df1c09fa01836ce5fc28b5c51ca7ccf1333f9a3ce129d448af866709288e9cfd","../../private-data/skull-anatomy-v2/rostral.jpg":"8d8d140502b12b2fb37cbb19b2620ee9ef03bd504a961a333417d39204192ccb","../../tools/head_engine/catalog.json":"6f31c28416c166a3ebf394b243ff21801f0e8fb9650204b703511fb020741922","../../tools/head_engine/engine.py":"820f1c48fbd7365223375d872efc533dc07f1c8d9b54a21592f6c99530bf14a0","../../tools/review/check_delivery.py":"ad64dc1ed59f386ce5a8e45af14f55d67f29fcb686760232ae1d38e199c8ab4b","../../../../../../../Windows/Fonts/malgun.ttf":"7a183cf1c6c56b9609fcc16eda8b5229fbc11758a21e669ec00343239b02192f","../../../../../../../Windows/Fonts/malgunbd.ttf":"e8cbc0b2afcc14fb45dfb6086d5102c0b23a96e7b6e708f3122acde1b86c9082","../../tools/head_engine/pixel.py":"cd91ee921c47f7c7d4d710581662f2626f3083e4a2753b0611c6b5ffe860bd40","../../tools/head_engine/tests/test_pixel.py":"9d72ec4128d54976436071a0d6391824973c555b15e7ed00d2559008139ff160","../../tools/head_engine/tests/test_engine.py":"1ecfc83ddb5fe3746f2e084a402272cb8ef12d6be5faa076492852f250940459","pixel-recipe.json":"115c9427dc26246ffa1c8f53cab6faf954e4db213358d82ab2b32877fdba733c","pixel-validation.json":"ab7a86af267bac9f05ff465c345222929311bc361044c922b7fde578d2950348","engine-render.json":"1d40e27ff5eecd9a338519145f43d8cf8ac07892f584d52c16675347ceb44ad2","../../references/styles/b2-c2/v1/reference-sheet.png":"654330121aa768fefddfbd0909e6975bb1b8bac539d533325364ba111cd8e744","../../references/styles/b2-c2/v1/manifest.json":"d2433df43d14c06c8798571451fed86e20b440cb2432a2d81f6440456f1f812c"},"coverage_complete":true,"unresolved":{}} -->
