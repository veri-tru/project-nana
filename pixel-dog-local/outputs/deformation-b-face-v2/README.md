# B 압축형의 얼굴 수정

후속 피드백에서 사용자가 세 품종의 귀와 주둥이를 모두 거절했다. 현재 후보는 [사진 윤곽 기반 v3](../deformation-b-face-v3/README.md)다.

서기 데포르메는 B 압축형이다. [세 품종의 수정 골격](B.json)은 이전 B와 같은 76개 기준점·관절, 몸통·다리·꼬리를 사용한다. 목에 연결된 머리 안에서 기준점의 깊이와 너비를 바꿨다.

[골든 원사진과 얼굴 기준점](golden-reference.png) · [기존 B와 수정 B의 얼굴 비교](faces.png) · [서기 전신에서 확인](standing.png)

| 품종 | 확인한 형태 | 골격에 적용한 부분 |
| --- | --- | --- |
| 휘핏 | 옆으로 길고 가늘어지는 얼굴, 약한 이마 단차, 작게 뒤로 접히는 귀 | 눈 아래 볼과 아래턱의 두께를 살리고, 코끝을 앞으로 빼 콧등의 완만한 경사를 남겼다. [영국 로열 켄넬 클럽](https://www.royalkennelclub.com/breed-standards/hound/whippet) · [개체 사진](../../private-data/breed-standing-pair-v1/whippet-source.png) |
| 닥스훈트 | 위에서 보면 길고 코 쪽으로 고르게 좁아진다. 원사진에서 둥근 귓불은 턱 아래까지 닿는다. | 주둥이의 앞뒤 길이와 코 폭을 늘리고, 옆으로 늘어진 귀가 턱보다 낮게 오도록 했다. [FCI 품종 표준](https://www.fci.be/en/nomenclature/DACHSHUND-148.html) · [개체 사진](../../private-data/breed-standing-pair-v1/dachshund-source.png) |
| 골든 리트리버 | 넓고 완만하게 굽은 두상, 머리 뒤쪽 길이에 가까운 넓고 깊은 주둥이, 눈 바로 위·뒤에서 시작해 볼에 붙는 귀. 원사진에서도 넓은 귓면과 두툼한 윗주둥이가 보인다. | 뒤통수를 뒤로 옮기고 이마와 콧등의 단차를 분리했다. 콧방울·윗입술·턱을 따로 배치하고 귀가 볼 뒤를 덮도록 귀뿌리와 접힘점을 옮겼다. [미국 골든 리트리버 클럽 품종 표준](https://grca.org/about-the-breed/akc-breed-standard/) · [머리 도해, 인쇄 20쪽](https://grca.org/wp-content/uploads/2017/09/Final-GRCA-Study-Guide-2017-rev.pdf) · [개체 사진](../../private-data/guide-roster/002/source.jpg) |

골든 골격의 측면에서 이마 단차부터 코까지와 뒤통수부터 이마 단차까지의 수평 길이는 22 대 23이다. 측면 콧등 경사는 기존 약 28도에서 약 4도로 줄였다. 이 수치는 품종 표준의 서술을 그림으로 옮긴 작화값이다. 사진 속 골든은 입을 벌리고 있고, 세 골격의 기본 자세는 닫힌 입이다. 반대편 얼굴의 너비와 깊이도 사진 한 장으로 실측할 수 없어 좌우 대칭으로 잡았다.

볼륨 비교판의 눈·입선은 표면에 붙여 그렸으며 그림의 색과 조명은 형태 판독용이다. 골든의 측면 눈 노출과 두상 표면에는 추가 조형 여지가 있다. 개체 닮음은 사용자 검토 대기다.

재생성은 이 폴더에서 `python build.py`, `python preview.py`, `python golden_reference.py` 순서로 한다. 생성기는 네 발 접지, 목 연결, 아래턱의 독립 회전과 꼬리 길이를 검사한다. 사진 대조판은 [원본 및 저작자 정보](https://commons.wikimedia.org/wiki/File:Golden_Retriever_Dukedestiny01_drvd.jpg)에 기재된 퍼블릭 도메인 사진을 확대하여 사용했다.
