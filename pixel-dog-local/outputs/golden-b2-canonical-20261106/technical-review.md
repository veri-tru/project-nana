# 독립 기술 검토 — B2 정본화와 골든 재작화 2차

판정: **TECHNICAL=PASS**. 1차의 성견 B 형상 회귀는 2차 이미지에서 수정됐다. 미해결 BLOCKER/MAJOR는 없고 행 간 미세한 외곽 차이 1건은 MINOR로 남는다. 사용자 선택·정확한 메시 투영·실행 자산 승인을 뜻하지 않는다.

검토자: `/root/b2_canonical_technical`. 제작자 및 외형 리뷰어와 별도 에이전트. 이미지/코드는 변경하지 않았다. 아래 최종 해시에만 이 판정을 적용한다. 1차 FAIL 보고서는 `iterations/01/technical-review.md`에 원바이트로 보존되어 있다(SHA256 `a6a44d5bf95dc3f1913dc2d565cacf4582a2c62e87b7c88ee458def714563017`).

## 실제 확인 범위

- 최종 `comparison.png`를 직접 열었다. RGB 1536×1024, 골든 A/B/C × SIDE/3-4/FRONT/BACK/TOP의 전 15셀을 확인했다. 같은 정본과 엔진 참조 및 품종 사진은 1차 검토에서 직접 열었고 해시가 변하지 않아 해당 출처 검토를 재사용했다. 최종 이미지 직접 검토는 생략하지 않았다.
- `evidence.json`의 최종 출력 1개와 입력 9개를 SHA256으로 다시 검증했다. 전부 일치한다. 정본 PNG와 기존 `B2-soft.png`는 동일 바이트이며 manifest의 상대 source는 실제 원본에 도달한다. 정본은 화풍 권위이고 과거 골든 형상 승인을 뜻하지 않는다.
- 2차 생성 원본 `exec-4ee2fe99-f8bf-46ac-9588-797df487abbc.png`가 generated_images 원래 위치에 남아 있고 최종 PNG와 동일 해시다. 1차 PNG는 `iterations/01/comparison.png`에 원래 해시 `201306cc1ba82859cdf0f927634295451c4cd16c166ccfd4e4c5d5ac38512752`로 보존됐다. 1차 evidence와 실패 보고서도 확인했다.
- `generation-02.json`의 실제 첫 입력은 편집 당시 루트 `comparison.png`다. 현재는 다른 바이트지만 기록된 edit_target_snapshot과 evidence가 당시 바이트를 보존본에 연결한다. 원본 경로를 사후 보존 경로였다고 바꾸지 않았다. 첫 생성의 `generation.json` 및 품종 사진은 2차의 간접 입력 계보로 유지한다.
- 2차 직접 입력은 1차 그림, 실제 adult-B 엔진 참조, 현재 정본 PNG다. model-B.pkl은 도구가 읽은 이미지 자체가 아니라 형상 참조의 상위 근거다. 현재 모델 해시는 이전 engine-render.json의 source_model_sha256/리뷰 기록 및 1차 입력과 같다. 이번 작업의 실제 모델 수정 또는 모델 훈련을 주장하지 않는다.
- 이전 native64 출력 review-status.json은 REJECTED/BLOCKED를 유지한다. 현재 AGENTS, 화풍 규격, README의 현재 기준/표, 엔진 README, 인계·백로그 및 결정기록은 새 B2 정본을 연결한다. 검토 중 발견한 README의 옛 B2/C2 현재 기준과 인계·백로그의 native64 READY/PENDING 문장은 현재 정본 및 당시 PASS/현재 거절 상태로 정정됐음을 재확인했다.

## 변경 격리와 시각적 기술 확인

측면 세 행 모두 1차보다 코에서 이마까지의 수평 돌출이 길어지고 정수리 높이가 낮아졌다. 사선에서도 넓고 깊은 주둥이가 앞쪽으로 충분히 이어지며, 정면·후면의 전체 비율은 둥근 세로 공 형태에서 넓고 낮은 형태로 바뀌었다. 윗면은 넓은 뒤 두개부와 앞 주둥이 연결을 유지한다. 옛 B2 골든의 높은 이마·짧은 주둥이를 그대로 복사했던 1차 실패를 반복하지 않는다. 이것은 참조와의 화면상 형상 비교이며 실측·투영 오차 수치가 아니다.

코는 주둥이 끝에 붙어 있고, 다문 입의 턱밑에서 짧은 목으로 이어진다. 귀는 세 행의 측면/사선/정면/후면에서 두개부 옆에 연결되어 보이며 뚜렷한 부착 단절이나 관통은 보이지 않는다. 피부 속 관절·폐곡면이나 가려진 부착부의 수치적 기하 검사를 이 PNG로 새롭게 완료한 것은 아니다.

A/B/C는 둥근 어두운 눈, 따뜻한 유색 윤곽, 연결된 계단형 음영을 공통으로 유지한다. B는 음영 범위/대비가 작고 C는 크며 A는 그 사이로 보인다. 과거 native64의 십자형 눈과 굵고 거친 띠 음영을 다시 사용하지 않았다. 다섯 시점은 이미지 모델 작화이며 동일 메시를 직접 렌더한 결과는 아니다.

## 발견 사항과 처리

### T1_ADULT_B_SHAPE_DRIFT — 이전 MAJOR, 해결

대상: 1차 `comparison.png`의 골든 A/B/C 측면·사선 주둥이/이마. 성견 B 대비 짧은 주둥이·높은 둥근 두개부가 관찰됐다. 2차의 전 15셀을 직접 재검토했고 위 설명과 같이 주둥이/이마 및 정면 비율이 교정됐다. 해결은 새 파일의 형상 확인에 근거하며 단순 문구 완화나 이전 PASS 승계가 아니다.

### T2_VARIANT_CONTOUR_DRIFT — MINOR, 미해결

대상: 최종 골든 A/B/C의 측면/사선 귀끝과 목밑, 정면/윗면의 외곽 계단. 음영 외에도 작은 외곽/귀끝 계단 차이가 남아 있어 완전히 같은 형상에 음영만 바꾼 통제 실험은 아니다. 다만 머리 비율·주둥이 길이·귀 부착의 큰 관계는 공통이며 성견 비율 회귀나 구조 결함으로 이어지지 않는다. README는 음영만 바꾸려던 의도와 실제 이미지 모델의 변동을 구분하고 정확한 메시 재투영/바이트 통제 실험이 아니라고 명시한다. 후속 실행 자산에서 행 간 형태를 동일하게 고정하려면 실제 렌더 경로나 고정된 픽셀 마스크를 통한 별도 검증이 필요하다. 이번 후보 전달을 막는 심각도는 아니다.

## 재현성과 주장 범위

전체 프롬프트, 실제 참조, 입력 스냅샷, 출력 원본 및 해시가 남아 생성 경로를 추적할 수 있다. 확률적 이미지 모델을 바이트 단위로 재현했다고 주장할 근거는 없다. 고해상도 시안이며 native64, 5색 제한, 정수 격자, 이진알파, 실제 cm, 연속 애니메이션 또는 실기기 검수는 미검증이다. 현재 README 및 생성 기록은 이 한계를 명시한다.

간접 의존성 검토는 첫 생성 입력/출력 계보, 정본 원본, 모델 해시 및 이미지를 생성한 실제 engine-reference의 기존 출처 기록까지다. 과거 전체 모델 생성 코드를 이번 이미지 생성 코드로 오인하지 않았으며, 이 검토는 모델 구현·기하를 다시 승인하는 절차가 아니다. 모든 직접 생성 입력과 이번 편집에 필요한 이전 이미지 바이트가 evidence에 포함된다.

<!-- review-verdict: {"status": "PASS", "reviewer": "/root/b2_canonical_technical", "artifacts": {"comparison.png": "7f3a47af0bcb09237bf2881a1bd5221e8a19eb1c4fa2669e584db5e41575d31f"}, "inputs": {"../../references/styles/breed-head-b2/v1/reference-sheet.png": "e15a82616528b4f05c51acc369ae4cbc25f6ffc781f1b1e11b1aea3f7fb1a3d6", "../../references/styles/breed-head-b2/v1/manifest.json": "b4b663e1bdc45968d34e50a7e5035f6b826e9400e165f29942e4e11d25938c86", "../skeleton-pixel-concepts-20261106/B2-soft.png": "e15a82616528b4f05c51acc369ae4cbc25f6ffc781f1b1e11b1aea3f7fb1a3d6", "../golden-pixel-refresh-20261106/engine-reference.png": "45c75c02ff081898fb7532bc200c4acd3fbd609d289ae2fc0cfa31b792f88741", "../golden-adult-head-v1/model-B.pkl": "9ccdb84a4d3f03604b3f49195a1b919224e92641c04640781fde535c10dbf122", "../deformation-b-face-v2/golden-reference.png": "2be4a6076f6730adbbab58d68536181bf15b528898084adae17b5f49f1b032ef", "generation.json": "110fc67b76bbbddc7467e88a6041ae42d2b816bfe616825d6377f6d7deab5c4d", "generation-02.json": "19d5f91a40e4930648ba4845acc16c4bd96202b0535b5f0cf25a10a74c6e0066", "iterations/01/comparison.png": "201306cc1ba82859cdf0f927634295451c4cd16c166ccfd4e4c5d5ac38512752"}, "coverage_complete": true, "unresolved": {"T2_VARIANT_CONTOUR_DRIFT": "MINOR"}} -->
