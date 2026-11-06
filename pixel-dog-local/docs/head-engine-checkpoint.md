이 문서는 2026-11-06 11:02 저장본의 이력이다. 현재 실행은 [엔진 정리 문서](engine-organization.md)와 `tools/dog_engine`을 따른다. 아래 재생성 명령은 해당 저장본 복원용이다.

# 머리 엔진 체크포인트

저장 시각: 2026-11-06T11:02:26+09:00 (Asia/Seoul)
체크포인트: `20261106-110226-head-engine-v2-13`

사용자 요청 “일단 여기까지 엔진저장”에 따라 현재 작업을 여기서 보존한다. 기준은 `outputs/skull-based-heads-v2` 13이며 B를 이어서 작업할 기본 비교안으로 기록하고 A/C도 함께 저장한다. 저장 요청을 새 외형 승인이나 실제 모델 학습으로 확대하지 않는다. 기존 사용자 선택 상태 PENDING과 개발 실패 이력은 그대로 유지한다.

- [압축 체크포인트](../private-data/engine-checkpoints/20261106-110226-head-engine-v2-13/engine-checkpoint.zip)
- [파일·해시 목록](../private-data/engine-checkpoints/20261106-110226-head-engine-v2-13/checkpoint.json)
- [무결성 검사](../private-data/engine-checkpoints/20261106-110226-head-engine-v2-13/verification.json)
- [현재 엔진 설명](../outputs/skull-based-heads-v2/README.md)

포함: 생성 코드, 설정, 최종 메시·세 이미지, 골격과 코 복구 기준, 실제 참조 이미지, 기술·외형 검토, 개발 기록, 재생성 환경 정보. 로컬 보관용이며 기존 저장소의 다른 작업이나 Git 이력은 변경하지 않는다.

## 재개

현재 작업 폴더 `pixel-dog-local`에서 `python outputs/skull-based-heads-v2/build.py B`로 B를 생성한다. 세 안은 끝 인수를 `A B C`로 지정한다. 저장본을 복원할 때는 압축의 `workspace/`를 별도 작업 폴더에 풀고, 그 안의 `pixel-dog-local`에서 실행한다. Windows 글꼴과 Python 라이브러리는 `checkpoint.json`의 환경 정보를 맞춘다. `external/`은 외부 입력의 보존본이며 시스템 파일에 자동 덮어쓰지 않는다. 생성 후에는 변경된 결과를 새로 검토한다.

현재 상태: 독립 외형·기술 PASS, 전달 게이트 READY, 12개 모델·메타데이터·세 PNG 재생성 일치. 남은 경미한 항목은 골든·닥스 귀뿌리의 캡 형태다. 픽셀 간략화·표정 재적용·학습은 후속이다.
