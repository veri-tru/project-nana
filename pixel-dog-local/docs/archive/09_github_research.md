# 픽셀 반려견 외형과 움직임 구현을 위한 GitHub 조사

원본: [ChatGPT 문서](https://chatgpt.com/space/page_e4ad0a22e6b08191b29b495970da71f8)  
문서 시퀀스: 0  
내보낸 날짜: 2026-10-17 (Asia/Seoul)

이 파일은 이전 조사·설계의 보존본입니다. 현재 개발 기준은 [결정 기록](../decisions.md)과 [프로젝트 개요](../project-brief.md)를 우선 확인하세요. 내부 프로젝트 링크는 같은 폴더의 문서로 연결했습니다.

조사 기준일 2026-10-17. 대상은 실제 반려견의 외형과 관찰된 행동을 반영하는 2D 픽셀 캐릭터다. 시제품의 기본 재생 속도는 8fps이며, 64×64px는 원본 해상도 후보로 검토 중이다. 이번 평가는 저장소의 README·선택 소스 파일·라이선스·공식 문서에 기반한 적용 가능성 검토이며, 설치나 실기기 성능 시험 결과는 아니다.

우선 조합은 Pixelorama 또는 Aseprite로 외형과 동작을 제작하고, vscode-pets의 강아지 상태 전환 구조를 참고해 개인별 행동 프로필을 연결하는 방식이다. Flame은 공통 앱의 재생 계층 후보로 비교한다. PixelOE는 픽셀화 보조, sprite-gen은 생성·정리 자동화 실험에 배치한다. Android 네이티브로 표시를 먼저 검증하는 기존 G0 방향을 유지한다.

# 우선 검토할 저장소

| 우선순위 | 저장소 | 확인한 기능 | 프로젝트 적용과 한계 |
| --- | --- | --- | --- |
| 1 | [Orama-Interactive/Pixelorama](https://github.com/Orama-Interactive/Pixelorama) | 레이어·프레임 타임라인, 어니언 스킨, 팔레트, 스프라이트 시트·PNG·GIF 내보내기 | 자체 강아지 외형과 8fps 동작을 편집할 기본 도구 후보. MIT |
| 1 | [aseprite/aseprite](https://github.com/aseprite/aseprite) | 레이어·프레임, 참고 레이어, 어니언 스킨, Lua·CLI, 시트 내보내기 | 첫 개체를 직접 다듬고 반복 내보내기를 자동화할 후보. 프로그램은 EULA 적용 |
| 1 | [tonybaloney/vscode-pets](https://github.com/tonybaloney/vscode-pets) | 강아지의 앉기·눕기·좌우 걷기·달리기·공 쫓기 상태 | 행동 엔진의 구조를 참고. VS Code용이며 모바일로 그대로 실행하는 패키지는 아님 |
| 1 | [flame-engine/flame](https://github.com/flame-engine/flame) | 스프라이트 애니메이션, 상태별 애니메이션 그룹, 입력 처리 | Flutter 공통 앱을 선택할 경우 재생 계층 후보. MIT. 플로팅 표시는 별도 문제 |
| 2 | [KohakuBlueleaf/PixelOE](https://github.com/KohakuBlueleaf/PixelOE) | 윤곽 확장, 대비 기반 축소, 색상 수 조정 | 승인된 외형 시안을 작은 픽셀로 정리하는 보조 도구. 동작 생성 기능으로 보지 않음. Apache-2.0 |
| 2 | [aldegad/sprite-gen](https://github.com/aldegad/sprite-gen) | 상태별 생성, 배경 제거, 프레임 추출·정렬, 아틀라스·메타데이터, 동작 검사 | 제작 자동화 실험 후보. README도 걷기·달리기를 동작 검사 통과 전 실험 대상으로 명시. Apache-2.0 |
| 조건부 | [X-SLAYER/flutter_overlay_window](https://github.com/X-SLAYER/flutter_overlay_window) | Android 오버레이 창, 드래그, 위치·크기 변경, 권한·서비스 설정 | Flutter 채택 시 G0와 비교할 참고 구현. 배터리·터치·서비스 동작은 실기기 검증 필요. MIT |

# 외형 제작에 적용할 방법

[Pixelorama](https://github.com/Orama-Interactive/Pixelorama)와 [Aseprite](https://github.com/aseprite/aseprite)는 개체별 무늬와 비율을 사람이 수정할 수 있는 편집 도구다. 사진을 자동으로 분석해 같은 개의 모든 동작을 만들어 주는 시스템으로 분류하지 않는다. 첫 캐릭터에서는 머리·몸통·귀·꼬리·앞다리·뒷다리·주요 무늬를 편집 가능한 단위로 관리하는 방안을 제안한다.

[PixelOE](https://github.com/KohakuBlueleaf/PixelOE)는 신경망 없이 영상 처리로 윤곽을 확장한 뒤 축소하고 색상을 정리한다. Python API와 CLI가 있으며 README는 CLI가 기존 API를 사용한다고 설명한다. 도입 시 사용 버전과 API를 고정해야 한다. 우리 앱에서는 사진 원본에 일괄 적용하기보다, 배경과 자세를 정리한 승인 시안에 적용해 직접 그린 픽셀 외형과 비교하는 용도로 제안한다.

외형 평가에서는 귀·꼬리 형태, 몸통과 다리 비율, 얼굴의 큰 무늬, 좌우 비대칭 표시를 따로 확인한다. 해상도 변경은 같은 최종 표시 크기에서 비교하고, 사진을 잘 축소했는지와 보호자가 자기 개로 인식하는지를 별도로 평가한다. 8fps 선택만으로 외형 식별이나 프레임 일관성이 보장되지는 않는다.

# 강아지 움직임과 상태 전환

[vscode-pets의 dog.ts](https://github.com/tonybaloney/vscode-pets/blob/main/src/panel/pets/dog.ts)에는 시작 상태와 다음에 갈 수 있는 상태가 명시돼 있다. 앉은 상태에서 걷기·달리기·눕기로, 공 쫓기에서 공을 가진 상태로 연결하는 구조를 직접 확인했다. 이 구조를 참고하되 개체별 대기시간·반복 횟수·반응 순서는 보호자가 확인한 자료로 채우는 것이 적합하다.

[states.ts](https://github.com/tonybaloney/vscode-pets/blob/main/src/panel/states.ts)는 정적 상태의 체류 시간을 호출 횟수로 세고, 이동도 nextFrame 호출마다 속도값을 더하는 부분이 있다. 따라서 숫자를 그대로 8fps 엔진에 옮기면 원래와 다른 체류 시간과 이동 속도가 될 수 있다. 우리 구현에서는 상태 지속 시간을 밀리초, 이동 속도를 초당 거리로 관리하고, 그림 교체 주기 125ms와 분리하는 방안을 권고한다. 이는 소스 구조를 바탕으로 한 이식 설계 판단이다.

강아지 고유의 움직임에는 별도의 제작이 필요하다. 예를 들어 짧은 다리와 긴 몸통을 가진 개에 기존 긴 다리 캐릭터의 프레임을 단순 확대·축소하는 방식이 적절한지는 시안에서 확인해야 한다. 기본 상태 전환 코드가 있다는 사실은 실제 개체의 보행이나 습관을 재현했다는 근거가 아니다.

# 강아지 동작 원본 자산

GitHub 검색에서 연결된 원작자 자산 중에는 [LuizMelo의 Pet Dogs Pack](https://luizmelo.itch.io/pet-dogs-pack)이 직접적인 동작 참고자료다. GitHub 저장소는 아니지만, 원작자가 6견종에 각 11개 애니메이션을 제공하며 CC0와 상업 이용 가능을 명시하고 있다.

| 동작 | 원작자가 명시한 프레임 수 |
| --- | --- |
| 대기 | 10 |
| 걷기 | 8 |
| 달리기 | 8 |
| 짖기 | 3 |
| 눕기 | 7 |
| 긁기 | 2 |
| 잠든 자세 | 1 |
| 앉은 자세 | 1 |
| 핥기 1 | 4 |
| 핥기 2 | 4 |
| 기지개 | 10 |

견종은 골든 리트리버·아키타·그레이트데인·슈나우저·세인트버나드·시베리안 허스키다. 명시된 캐릭터 크기는 견종별로 19×15px부터 43×29px까지 다르다. 이 숫자는 각 이미지 파일의 셀 규격이 모두 같다는 뜻이 아니므로 내려받은 자산에서 여백·프레임 기준점·시트 배열을 확인해야 한다.

이 팩의 활용 우선순위는 발의 순서와 몸통 움직임을 비교하는 기준, G0의 임시 동작, 자체 제작 시 필요한 동작 목록이다. 걷기 8프레임을 각각 125ms씩 표시하면 한 주기는 1초가 된다. 이것이 실제 반려견에게 맞는 보행 주기인지는 영상과 비교해야 한다. 잠든 자세·앉은 자세는 1프레임이므로 자세로 들어가는 전환이나 호흡 움직임은 별도 제작 대상이다.

# 자동화 실험과 후순위 후보

| 저장소 | 확인한 내용 | 판단 |
| --- | --- | --- |
| [aldegad/sprite-gen](https://github.com/aldegad/sprite-gen) | 한 외형에서 상태별 시트 또는 영상 루프를 만들고 투명 프레임·아틀라스·상태별 fps·반복 정보를 구성. 수동 선택·정렬 도구도 제공 | 가장 먼저 비교할 자동화 후보. 외부 생성 모델과 계정·환경이 필요하며, 강아지 동작 품질은 별도 평가 |
| [Olafs-World/sprite-animator](https://github.com/Olafs-World/sprite-animator) | 사진을 픽셀 외형으로 바꾼 뒤 승인된 외형으로 4×4 시트를 생성·분할. 프레임 시간과 출력 크기 설정. MIT | 외형 승인과 동작 생성을 나누는 공정 참고. 기본 동작이 idle·wave·bounce·dance이므로 개의 보행에 바로 대응하지 않음 |
| [dakotacsk/code-as-pixelart](https://github.com/dakotacsk/code-as-pixelart) | 색·부위·방향·프레임을 JSON으로 관리하고 CLI·MCP로 수정·내보내기. MIT | 개체별 무늬와 부위 수정 자동화의 연구 후보. README의 부위 분리 설명만으로 개 사진에 대한 정확도를 확정할 수 없음 |
| [sprited-ai/sprute](https://github.com/sprited-ai/sprute) | 참고 이미지로 다방향 외형 생성, 배경 제거, 프레임 추출. 기본 공정에 좌우 반전 포함 | 방향별 외형 시안용 후보. 개의 비대칭 무늬를 별도로 처리해야 하며, 다방향 외형은 보행 주기와 구분 |
| [JatCool/AI-Sprite-Animation](https://github.com/JatCool/AI-Sprite-Animation) | Unity에서 부위 리깅과 선택적 AI 자세 생성. 코드 MIT | README가 측면 사람형 스프라이트를 입력으로 명시. 네발 강아지용 즉시 도입 후보에서는 제외 |
| [Sopiro/Unity-Procedural-Animation](https://github.com/Sopiro/Unity-Procedural-Animation) | 역기구학을 이용한 다리 위치 제어와 네발 동물 예제. MIT | 발 접지·다리 제어 개념의 후속 참고. 픽셀 프레임 제작 공정을 바로 대체하지 않음 |
| [systemcrash92/DogSprite](https://github.com/systemcrash92/DogSprite) | 브라우저 픽셀 편집기, 레이어·프레임 시간, Aseprite 호환 JSON 내보내기. MIT | 이름과 달리 강아지 전용 동작 생성기라는 근거는 없음. 웹 편집 기능이 필요할 때 비교 |
| [nklbdev/godot-4-importality](https://github.com/nklbdev/godot-4-importality) | Aseprite·LibreSprite·Pixelorama 등에서 Godot의 SpriteFrames·AnimatedSprite2D·AnimationPlayer로 가져오기. MIT | Godot를 채택할 경우의 연결 도구. 현재 모바일 표시 계층 결정과 별도로 보류 |
| [LibreSprite/LibreSprite](https://github.com/LibreSprite/LibreSprite) | 레이어·프레임·어니언 스킨을 갖춘 픽셀 편집기. GPLv2 | 제작 도구 대안. 현재 Aseprite와 라이선스 및 기능을 동일하게 취급하지 않음 |

자동 생성 후보의 일관성·속도 설명은 각 저장소 작성자의 보고다. [sprite-gen](https://github.com/aldegad/sprite-gen)은 발 접촉이 모호하면 측정 결과를 미검증으로 남기고, 걷기·달리기는 동작 검사 통과 전까지 실험 영역으로 둔다. 이번 프로젝트에서도 생성 성공과 사용 가능한 애니메이션을 구분하고, 고정된 발 기준점·몸통 크기·무늬·루프 연결을 직접 확인한다.

# 8fps 재생과 모바일 적용

[Flame 공식 예제](https://github.com/flame-engine/flame/blob/main/examples/lib/stories/sprites/sprite_sheet_example.dart)는 동일한 간격의 시트 재생과 프레임별로 다른 유지 시간을 모두 보여 준다. [SpriteAnimationGroupComponent 문서](https://docs.flame-engine.org/latest/flame/components/sprite_components.html)는 상태에 따라 현재 애니메이션을 바꾸는 기능을 설명한다. 기본 간격을 0.125초로 설정하고, 쉬는 자세는 더 오래 유지하는 구현이 가능하다. 적용 시에는 선택한 릴리스의 API와 예제를 맞춘다.

제안 자산 규격은 투명 PNG 시트와 JSON 메타데이터다. 각 동작에 clip_id, 프레임 영역, frame_duration_ms, loop, 방향, 공통 기준점, 진입·종료 자세, 자산 버전을 기록한다. 위치 이동과 발 접지를 맞추기 위해 필요하면 프레임별 이동량도 별도로 둔다. 이는 프로젝트 제안 규격이며 모든 조사 저장소가 같은 형식을 지원한다는 뜻은 아니다.

[flutter_overlay_window](https://github.com/X-SLAYER/flutter_overlay_window)의 README에는 Android의 SYSTEM_ALERT_WINDOW 권한과 foreground service 설정, 드래그·위치 이동·크기 변경·터치 통과 옵션이 있다. 이 저장소는 Flutter를 선택할 때 비교할 오버레이 구현 참고자료이며, iOS 자유 플로팅이나 양 플랫폼 홈 위젯의 연속 재생을 성립시키는 근거로 삼지 않는다. 기존 G0에서는 작은 창의 터치 영역, 표시 중지, 화면 꺼짐, 권한 철회와 자원 사용을 먼저 확인한다.

# 라이선스와 버전 선택

[Aseprite 공식 FAQ](https://www.aseprite.org/faq/)는 자신의 제작물을 상업 제품에 사용하는 것을 허용한다. 한편 Aseprite 프로그램과 소스는 현재 EULA 적용 대상으로, 앱에 편집기 코드를 포함하거나 프로그램을 재배포하는 판단은 제작물 이용과 구분해야 한다.

[vscode-pets](https://github.com/tonybaloney/vscode-pets)의 코드 라이선스는 MIT이고, README는 강아지 자산의 제작자를 NVPH Studio와 Akita 제작자 Kevin Huang 등으로 따로 표시한다. 이번 검토에서는 해당 그림의 별도 재사용 조건을 확정하지 않았으므로 코드 구조 참고 대상으로 두고, 실제 배포용 그림은 자체 제작 또는 조건을 확인한 원작자 자산을 사용한다. [sprute](https://github.com/sprited-ai/sprute)도 코드 MIT와 별개로 Monet 예제 캐릭터는 데모용이라고 명시한다.

유지 현황은 별 수보다 배포 이력과 해당 기능의 상태를 확인한다. [Pixelorama 릴리스](https://github.com/Orama-Interactive/Pixelorama/releases)에서 v1.2.3과 2026-09-15 날짜를 확인했으며, [Aseprite 릴리스](https://github.com/aseprite/aseprite/releases)에는 v1.3.18.6 및 시트 JSON 관련 수정이 게시돼 있다. [Flame 릴리스](https://github.com/flame-engine/flame/releases)는 여러 패키지와 개발 버전을 함께 나열하므로 목록 맨 위 항목을 Flame 본체의 안정 버전으로 취급하지 않는다. [sprite-gen 릴리스](https://github.com/aldegad/sprite-gen/releases)에는 루프·프레임 검사 관련 변경이 다수 있지만, 변경량이 강아지용 결과의 검증을 대신하지는 않는다.

# 첫 비교 제작 범위

첫 비교는 반려견 한 마리의 외형 한 방향과 걷기·쉬기·잠든 자세로 제한한다. 제작 경로는 직접 편집한 기준 자산과 PixelOE 또는 sprite-gen을 보조로 사용한 자산을 비교한다. 두 경로 모두 같은 해상도·표시 크기·8fps 조건에서 확인한다.

| 비교 항목 | 기록할 내용 |
| --- | --- |
| 외형 | 귀·꼬리·다리 비율, 큰 무늬, 보호자의 자기 개다움 평가 |
| 프레임 일관성 | 몸통·머리 크기 변화, 무늬 이동, 여분의 다리·사라지는 부위 |
| 움직임 | 발 접지, 화면 이동과 발 움직임의 일치, 첫·마지막 프레임 연결 |
| 상호작용 | 탭·드래그 지연, 전환 중 끊김, 화면 경계 처리 |
| 제작 부담 | 최초 제작 시간, 수정 시간, 재생성 횟수, 외부 호출 비용 |
| 모바일 | 동일 조건에서 CPU·메모리·배터리·발열과 표시 종료 동작 |

이 비교가 끝나면 외형 제작 도구, 생성 보조의 사용 범위, 자산 명세를 선택한다. 실제 습관을 반영하는 대기·지속·반복·순서 값은 기존 데이터 수집 및 보호자 확인 흐름과 연결한다.

검색 범위: 외형 편집·강아지 동작과 자산·모바일 재생·생성 자동화의 네 축에서 Exa 검색 응답 59건을 검토했다. URL 정규화 후 56개 주소, 검색에 포함된 서로 다른 GitHub 저장소 37개였으며, 이후 공식 저장소와 문서 주소를 직접 추가 확인했다. 이 수치는 중복을 포함한 검색 응답과 고유 주소를 구분한 것으로, 전체 GitHub를 망라했다는 뜻은 아니다.

[기존 개발 지침](./00_project_guidance.md) · [상세 기획과 설계](./05_detailed_design.md) · [개의 움직임 구현 문헌](./03_animation_literature.md)
