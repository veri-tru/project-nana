# 독립 기술 검토 — B2 정본화와 골든 재작화 1차

판정: **TECHNICAL=FAIL**. 출처·정본 복사·해시·원본 보존은 확인했지만, 새 이미지의 성견 B 형상 보존 요구가 충족되지 않았다. 이 기록의 판정은 아래 SHA256의 첫 출력에 한정한다.

검토자: `/root/b2_canonical_technical`. 제작자와 별도의 에이전트. 실제 PNG를 열고 정본, 엔진 참조, 품종 사진과 비교했으며 코드나 이미지를 변경하지 않았다.

## 범위와 확인 결과

- `comparison.png`: RGB 1536×1024, A/B/C 세 행 × SIDE/3-4/FRONT/BACK/TOP 전 15셀을 직접 확인했다. 누락 없음.
- `evidence.json`의 출력 1개와 입력 7개를 실제 디스크에서 SHA256 재계산해 전부 일치를 확인했다. 정본 1536×1024 PNG와 기존 `B2-soft.png`는 파일 크기와 SHA256이 동일하다. manifest의 상대 source 경로도 실제 원본으로 해석된다.
- 생성기 원본 `exec-a00e468c-2486-456c-8689-82d616c3817d.png`가 원래 generated_images 위치에 남아 있으며 `comparison.png`와 SHA256이 같다. 출력 원본을 보존한 복사다.
- 참조 역할은 정본 B2=화풍, engine-reference=adult-B 형상, golden-reference 왼쪽 사진=품종/털로 기록되어 있다. 실제 generation.json에는 세 PNG의 절대 경로와 전체 프롬프트가 있다. model-B.pkl은 도구에 직접 전달한 이미지가 아니라 형상 참조의 상위 근거다.
- model-B.pkl의 현재 SHA256은 이전 engine-render.json의 source_model_sha256 및 이전 리뷰 입력 기록과 일치한다. 이번 작업으로 모델이 변했다는 증거는 없다. 기존 엔진 참조 및 모델의 생성 코드를 이번 작업에서 재실행하거나 전 모델의 기하를 다시 검증한 것은 아니다.
- 이전 native64 후보의 review-status.json은 user_decision=REJECTED, delivery=BLOCKED이며 USER_REJECTED 이벤트에 당시 이미지 해시를 남겼다. 과거 기술 PASS를 새 후보의 승인으로 승계하지 않는다.
- generation.json/후보 README는 새 출력이 고해상도 화풍 시안임을 명시한다. 64×64 실행 자산, 정확한 메시 투영, 정수격자, 5색, 이진알파, 실측 치수, 재생성 바이트 동일성 또는 애니메이션 검증을 주장하지 않는다. 참조와 프롬프트가 남아 있어 생성 의도는 추적 가능하지만 확률적 이미지 모델을 바이트 단위로 재현했다고 볼 수 없다.
- 새 이미지의 5시점은 이미지 모델의 개별 그림이다. 실제 동일 메시의 다섯 렌더임을 검증한 것이 아니다. 관절·닫힌 표면·관통은 기존 모델의 해시 보존과 별개이며 이 PNG만으로 새롭게 보증하지 않는다.

## 발견 사항

### T1_ADULT_B_SHAPE_DRIFT — MAJOR, 미해결

파일/개체/시점/부위: `comparison.png` / 골든 A·B·C / 측면 및 사선 / 주둥이·이마·두개부 비율.

직접 관찰: adult-B 엔진 참조에는 길고 두툼하게 앞으로 뻗은 주둥이와 상대적으로 낮은 이마가 있다. 새 세 행은 코에서 이마 꺾임까지의 돌출이 짧아지고, 머리 전체 폭에 대한 이마 높이가 커져 높은 둥근 두개부로 보인다. 이 특징은 화풍 정본의 이전 골든 얼굴에 더 가깝다. 음영이나 픽셀 계단만 바뀐 결과로 설명할 수 없는 실루엣 차이다. 정면과 후면은 넓은 머리 및 늘어진 귀를 유지하지만 측면 회귀를 상쇄하지 못한다. 이 비교는 화면상 비율 판단이며 실제 길이 실측이 아니다.

요구/근거: manifest는 옛 골든의 형상을 정본 범위에서 제외하고 현재 adult-B 형상을 권위로 둔다. 생성 프롬프트도 높은 어린 골든 이마/짧은 주둥이를 피하고 adult-B의 긴 전방 돌출을 보존하도록 요구한다.

수정 후 확인: 같은 B2 화풍을 유지하면서 측면/사선의 성견 B 주둥이 돌출과 두개부 높이를 회복한 새 파일을 직접 검토해야 한다. 문서상 '정확한 투영이 아님'이라는 제한만 추가해서 해결할 수 없다.

### T2_VARIANT_CONTOUR_DRIFT — MINOR, 미해결

파일/개체/시점/부위: 같은 파일 A/B/C / 측면·정면·윗면 / 귀끝·목밑·정수리 외곽.

직접 관찰: B의 측면 귀끝은 A/C와 완전히 같지 않고, 정수리와 목밑 계단 및 윗면 귀 돌출에도 작은 차이가 있다. B가 옅고 C가 진한 음영 변화는 확인되지만 세 행이 '음영 이외 형상까지 동일'한 통제 실험은 아니다. 현재 README는 음영만 바꾸려던 의도와 실제 일치 검토를 구분해 과장하지 않는다.

수정 후 확인: 새 세 행에서도 외곽과 특징 위치를 대조하고 작은 변동이 남으면 공개한다. 형상 전체 보존이라고 단정하지 않는다. 이 작은 행 간 차이는 T1의 공통 형상 회귀와 별도다.

## 간접 의존성과 한계

정본 원본, 형상 참조 PNG, 실제 모델, 품종 사진 및 생성 기록을 범위에 포함했다. 이전 engine-render.json/리뷰 상태는 모델 해시와 거절 이력의 대조 근거로 읽었다. 과거 전체 모델 생성 의존성을 이번 image_gen 생성 코드라고 오인하지 않았으며, 별도 모델 수정·훈련·앱 출력 검수는 이번 결과에 포함하지 않는다. 후보 README 및 활성 문서의 정본화 갱신은 출처/범위 기록과 대조했지만 T1 때문에 전달 차단이다.

<!-- review-verdict: {"status": "FAIL", "reviewer": "/root/b2_canonical_technical", "artifacts": {"comparison.png": "201306cc1ba82859cdf0f927634295451c4cd16c166ccfd4e4c5d5ac38512752"}, "inputs": {"../../references/styles/breed-head-b2/v1/reference-sheet.png": "e15a82616528b4f05c51acc369ae4cbc25f6ffc781f1b1e11b1aea3f7fb1a3d6", "../../references/styles/breed-head-b2/v1/manifest.json": "b4b663e1bdc45968d34e50a7e5035f6b826e9400e165f29942e4e11d25938c86", "../skeleton-pixel-concepts-20261106/B2-soft.png": "e15a82616528b4f05c51acc369ae4cbc25f6ffc781f1b1e11b1aea3f7fb1a3d6", "../golden-pixel-refresh-20261106/engine-reference.png": "45c75c02ff081898fb7532bc200c4acd3fbd609d289ae2fc0cfa31b792f88741", "../golden-adult-head-v1/model-B.pkl": "9ccdb84a4d3f03604b3f49195a1b919224e92641c04640781fde535c10dbf122", "../deformation-b-face-v2/golden-reference.png": "2be4a6076f6730adbbab58d68536181bf15b528898084adae17b5f49f1b032ef", "generation.json": "110fc67b76bbbddc7467e88a6041ae42d2b816bfe616825d6377f6d7deab5c4d"}, "coverage_complete": true, "unresolved": {"T1_ADULT_B_SHAPE_DRIFT": "MAJOR", "T2_VARIANT_CONTOUR_DRIFT": "MINOR"}} -->
