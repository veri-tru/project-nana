# 털 설정 → 3D 외피 → native64 독립 기술 검토

검토일: 2026-11-07. 검토자: `/root/coat_review`. **기술 판정 PASS**, 미해결 기술 BLOCKER/MAJOR 없음. 이 판정은 중립 진단 출력 연결 범위이며 B2 화풍·개체 닮음·사용자 승인을 뜻하지 않는다.

## 확인한 결과

- 고정된 말티푸 머리·목·상흉부 원본에 정수리/볼/양쪽 귀/가슴 길이 선택을 적용하고, 별도 구조 리뷰 뒤 실제64×64 depth-buffer raster로 연결한다.
- 원본 pin, 별도 파생 모델 저장, 요청/모델/semantic/계약/리뷰 해시 결합, 미지원 요청 전체 거절, 기존 출력 보호가 유지된다.
- short/medium/long r3 구조판27개 PNG와3개 NPZ가 검토한 r2와 바이트 단위로 같고 최신 입력 해시도 일치한다. r2에서는 실제 재생성27PNG·모델 전 채널 재현, 독립 manifold와 귀↔머리 양방향 교차 검사를 수행했다. 자유부 교차와 coplanar 후보는0이며 root 연결만 존재한다.
- 최종 native64-r2의21개 PNG를 재생성해 바이트 일치,15개 semantic/depth 배열 exact, 모든 프레임64×64·alpha0/255·선언 팔레트·고정 카메라를 확인했다. atlas는 원본을 이어 붙이고 preview만 nearest-neighbor로 확대한다.
- 귀 가독성 수정은 기존 native 출력의 alpha/semantic/depth를 유지하고 귀 소유 픽셀 안의 색만 변경한다. 기존 head/눈/코/배경에 변경이 없다.
- 실제 missing-review 거절 및 임시 복사본의 변조 계약/메타데이터/미지원 요청 거절을 확인했다. 내부 reader 검사는 테스트에서만 gate를 명시적으로 mock했으며 실제 native 출력의 구조 게이트는 mock하지 않았다. 실패 시 출력 폴더가 없었다.
- 최신 native64 자동 검사10개를 독립 실행해 통과했다. 전체 저장소 회귀 검사는 구현 담당자의 별도 기록을 따른다.

## 검토 중 해결된 문제

1. 파생 모델을 원본 전용 hash-pinned loader로 읽어 정상 medium/long까지 거절하던 연결을 수정했다. 파생 NPZ는 검토 해시와 exact channel/dtype/array 재현으로 확인하고 렌더에는 다시 생성한 모델을 사용한다. 원본 loader의 pin은 유지한다.
2. native reader가 applicable_patch만 재현하지 않도록 지원 target, unsupported 부재, plan 일치, 원본 identity/hash를 다시 확인한다.
3. 초기 native의 귀 가독성 문제에 대한64px 전용 색상 수정은 구조와 별도로 검토했다. 구조 이미지·메시를 바꾸지 않은 사실을 bytes와 semantic 소유권으로 검증했다.

## 세부 기록

세부 기술 보고서는 `private-data/coat-head-20261107/{short,medium,long}-r3/technical-review.md`와 `{short,medium,long}-native64-r2/technical-review.md`에 있다. 각 보고서는 해당 최종 파일 해시와 입력 집합을 marker로 연결한다. 비공개 모델/이미지는 이 공개 문서에 복제하지 않는다.

구조와 새 native64 외형 판정은 별도 리뷰어가 수행한다. 기술 PASS만으로 전달 상태를 확정하지 않으며, 최종 review-status와 전달 검사 결과를 함께 따른다.

## 최종 검토 코드

| 파일 | SHA-256 |
|---|---|
| `tools/dog_engine/coat.py` | `4fce44b0071fc2bfe00298b2cc67f8ac04db3ea03ad39f84a47f8f7b0bb97530` |
| `tools/dog_engine/coat_head.py` | `c574731e970ba2baf9f5bd23aa058e13bbd22dcf3bd26a60e2928ba4c27bbd34` |
| `tools/dog_engine/coat_head_geometry.py` | `cf56bcc3d557a3b84d7a0217b363e45780999f9f07f987b46a1b5942066fd760` |
| `tools/dog_engine/coat_native64.py` | `70b89ca83ae4ae52396d83695ce8d2880e6ad10457d3a1e99b8c95e4a9314b00` |
| `tools/dog_engine/coat-head-models.json` | `b99e438003e5a2da0dbe0e18c5d4c7b279c7ec91f6bcc616612670ad4a85cbc2` |

## 범위 제한

하나의 검토된 구조 템플릿에 대한 제작용 외피 길이 변형이다. 실측 mm·독립 모량·곱슬·미용 형태·좌우 개별 귀 길이는 미지원이며 전신·동작·앱 연결도 포함하지 않는다. 면 방향/면적·manifold·귀 교차 검사를 모든 표면의 전역 self-intersection 부재 증명으로 확대하지 않는다. 선택된 두 개체 C의 정본이나 거절된 P1/P2/P3 상태는 승계·변경하지 않는다.
