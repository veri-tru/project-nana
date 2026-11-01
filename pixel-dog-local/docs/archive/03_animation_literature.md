# 반려견 2D 3D 움직임 구현 문헌과 적용안

원본: [ChatGPT 문서](https://chatgpt.com/space/page_dbd877cfd4108191ba05974570cbf1bb)  
문서 시퀀스: 0  
내보낸 날짜: 2026-10-17 (Asia/Seoul)

이 파일은 이전 조사·설계의 보존본입니다. 현재 개발 기준은 [결정 기록](../decisions.md)과 [프로젝트 개요](../project-brief.md)를 우선 확인하세요. 내부 프로젝트 링크는 같은 폴더의 문서로 연결했습니다.

검토 기준일: 2026-10-17. 대상은 개의 움직임과 개 캐릭터 구현입니다. 고양이는 후속 프로젝트로 분리합니다.

현재의 2D 우선 개발 방향은 유지할 수 있습니다. 권장 시작점은 실제 반려견 영상에서 동작의 형태와 타이밍을 기록하고, 2D 레이어·골격에 옮긴 뒤 상황별 행동 규칙으로 재생하는 방식입니다. 3D 복원과 생성형 애니메이션은 제작을 보조하거나 후속 단계에서 확장하는 후보입니다. 이 권고는 아래 문헌을 종합한 개발 판단이며, 2D가 3D보다 보호자의 ‘우리 개’ 인식을 높인다는 비교 실험 결과는 아닙니다.

문헌이 잘 뒷받침하는 것은 자세 추적, 외형 복원, 동작 전이와 제어입니다. 외형과 움직임이 자연스럽다는 평가만으로 특정 보호자가 자신의 반려견이라고 인식한다고 결론낼 수 없습니다. 이 효과는 별도 실험으로 확인해야 합니다.

연결 문서: [프로젝트 지침과 시제품 범위](./00_project_guidance.md) · [행동과 습관 문헌검토](./02_dog_identity_literature.md) · [데이터 수집 위계와 우선순위](./01_data_hierarchy.md)

## 1. 검색 범위와 근거의 해석

2D 변형·스프라이트, 개의 자세 추적·모션캡처, 3D 형상 복원, 관절형 아바타, 자동 리깅, 동작 제어·전이, 생성형 모션, 지각 평가와 모바일 구현을 검색했습니다. 27개 검색식에서 199개 결과가 반환되었고, URL 중복을 제거하면 188개였습니다. 같은 논문의 출판사·arXiv·프로젝트 페이지는 한 연구로 묶었습니다.

최종 목록은 54편입니다. 종설 2편, 기반·응용 연구 49편, 적용 경계 또는 제외 후보 3편을 포함합니다. 199편의 원문을 모두 읽었다는 뜻이 아니며, 학술 데이터베이스 전부를 망라한 체계적 문헌고찰의 전수목록도 아닙니다. 직접 관련 연구는 원문 또는 저자 자료로 확인했고, 초록만 확인한 항목은 표에 표시했습니다. 최신 arXiv 자료와 워크숍, 본회의·학술지 논문을 구분했습니다.

문헌의 연도는 확인한 출판 버전을 따릅니다. 예를 들어 Farm3D는 arXiv 초판 2023년, 3DV 발표 2024년입니다. AniClipart는 온라인 공개 2024년으로 표시했습니다.

근거를 다음처럼 읽어야 합니다.

| 근거 종류 | 말할 수 있는 것 | 이 자료만으로 말할 수 없는 것 |
|---|---|---|
| 개의 실제 영상·모션캡처 연구 | 제시된 환경에서 개의 자세나 동작을 추적·복원·제어 | 모든 품종·가정 영상·개인 습관에 동일한 정확도 |
| 여러 동물·범용 캐릭터 연구 | 해당 표현·변형·리깅 기술의 구현 가능성 | 개 전용 정확도와 특정 반려견의 재현 |
| 생성형 이미지·모션 연구 | 그럴듯한 미관측 외형·동작을 생성 | 생성 결과가 실제 그 개의 외형·습관이라는 사실 |
| 지각 연구 | 실험에서 측정한 자연스러움·동작 지각 | 보호자의 자기 반려견 식별과 정서적 유대 |
| 모바일 또는 데스크톱 성능 보고 | 논문에 제시한 기기·조건에서의 실행 | Android·iPhone의 상시 표시, 배터리·발열 성능 |

이 검토에서는 코드 설치, 모델 실행, 모바일 성능 측정을 수행하지 않았습니다.

## 2. 구현 문제를 다섯 단계로 분리

| 단계 | 입력 → 출력 | 대표 문헌 | 프로젝트에서의 역할 |
|---|---|---|---|
| 관찰·추적 | 실제 영상 → 시간별 관절·실루엣·접촉 | [SuperAnimal](https://www.nature.com/articles/s41467-024-48792-2), [RGBD-Dog](https://openaccess.thecvf.com/content_CVPR_2020/papers/Kearney_RGBD-Dog_Predicting_Canine_Pose_from_RGBD_Sensors_CVPR_2020_paper.pdf) | 실제 개가 어떻게 움직였는지 기록 |
| 자산 제작 | 사진·그림·영상 → 레이어 또는 3D 형상과 골격 | [Animato](https://igl.ethz.ch/projects/animato/animato-mgia.pdf), [BITE](https://openaccess.thecvf.com/content/CVPR2023/papers/Ruegg_BITE_Beyond_Priors_for_Improved_Three-D_Dog_Pose_Estimation_CVPR_2023_paper.pdf), [Animal Avatars](https://remysabathier.github.io/animalavatar.github.io/) | 움직일 수 있는 외형 제작 |
| 전이·보정 | 원본 동작 → 캐릭터 체형에 맞춘 동작 | [WalkTheDog](https://arxiv.org/html/2407.18946v1), [How to Train Your Dog](https://mig2021.inria.fr/files/2021/11/mig21_egan.pdf) | 발 미끄러짐·관절 변형을 줄이며 옮기기 |
| 행동·동작 제어 | 상황·사용자 입력 → 동작 선택과 전환 | [MANN](https://www.pure.ed.ac.uk/ws/files/60838109/dog2.pdf), [Local Motion Phases](https://www.pure.ed.ac.uk/ws/portalfiles/portal/157671564/Local_Motion_Phases_STARKE_DOA27042020_AFV.pdf) | 걷기·앉기·눕기 및 반응 순서를 연결 |
| 표시·렌더링 | 자세·외형 → 화면 이미지 | [ARAP](https://cs.brown.edu/people/jhughes/papers/Igarashi-ASM-2005/main.htm), [GART](https://www.jiahuilei.com/projects/gart/), [ARTEMIS](https://arxiv.org/html/2202.05628v3) | 2D 또는 3D 화면 표현 |

행동 선택과 동작 실행은 별도 층으로 둡니다. ‘보호자가 부르면 잠깐 바라본 뒤 다가온다’는 상황·잠복기·순서 데이터가 행동 선택을 결정하고, 다가올 때 다리·몸통·머리·꼬리가 어떻게 움직이는지는 모션 자산이 결정합니다. 움직임 생성 모델 하나로 두 문제를 해결했다고 간주하지 않습니다.

2D 화면을 선택해도 내부 동작까지 반드시 2D여야 하는 것은 아닙니다. 3D 골격을 움직여 2D 이미지나 여러 방향의 스프라이트로 출력할 수도 있습니다. 이는 후속 설계 선택지이며 현재의 2D 우선 범위를 변경하는 결정은 아닙니다.

## 3. 구현 경로 비교와 권장 순서

| 경로 | 필요한 자산 | 장점 | 핵심 한계 | 적용 판단 |
|---|---|---|---|---|
| 2D 레이어·골격·짧은 모션 클립 | 부위별 그림, 관절·제어점, 실제 영상의 동작 타이밍 | 작은 화면의 제작·수정 범위를 관리하기 쉬움 | 몸 회전과 다리 겹침은 별도 레이어·시점 자산 필요 | 현재 시제품의 우선 경로 |
| 3D 골격을 2D로 출력 | 경량 메시·골격·동작, 고정 또는 제한된 카메라 | 여러 시점과 체형 변화에 일관된 골격 활용 | 초기 모델·리깅·전이 작업이 증가 | 반복 제작 비용을 확인한 뒤 비교 |
| 표준 3D 메시·스키닝 | 체형·텍스처·골격·모션 | 자유 시점과 상황별 동작 제어 | 털·귀·꼬리·접지·모바일 최적화 필요 | 후속 3D 시제품 |
| Gaussian·신경 아바타 | 영상 또는 사진, 학습·최적화된 표현과 전용 렌더러 | 외형·털을 풍부하게 표현하는 연구 경로 | 표준 메시와 자산 형식·편집·모바일 비용이 다름 | 연구용 비교 후보 |
| 이미지·텍스트→동영상 | 참조 이미지와 조건 또는 모션 영상 | 동작 초안과 시각적 시연 제작 | 출력 영상만으로 상호작용 리그·연속 제어가 확보되지 않음 | 제작 보조 |

첫 버전은 2D 레이어와 골격, 소수의 검수된 동작, 상황별 타이밍 규칙을 조합합니다. AI 자세 추정은 제작 과정의 보조로 사용하고, 오류가 있는 관절과 접지는 사람이 확인합니다. 클립을 연결하는 과정에서 그 개 특유의 멈춤, 좌우 차이, 반응 지연을 일괄적으로 매끈하게 지우지 않도록 원본과 비교합니다.

이 순위는 실제 관찰자료를 보존하고 구현 범위를 제한하려는 판단입니다. 논문 간 서로 다른 데이터셋의 수치를 한 표에서 직접 순위화한 결과는 아닙니다.

## 4. 먼저 읽을 핵심 문헌 10편

| 순서 | 문헌 | 읽는 목적 |
|---|---|---|
| 1 | [MANN · 2018](https://www.pure.ed.ac.uk/ws/files/60838109/dog2.pdf) | 개의 이동·정지·앉기·눕기를 연속 제어하는 구조 |
| 2 | [Animato · 2016](https://igl.ethz.ch/projects/animato/animato-mgia.pdf) | 2D 그림 변형을 모바일에 구현한 작업 흐름 |
| 3 | [SuperAnimal · 2024](https://www.nature.com/articles/s41467-024-48792-2) | 실제 영상에서 관절을 추적하는 출발점 |
| 4 | [BITE · 2023](https://openaccess.thecvf.com/content/CVPR2023/papers/Ruegg_BITE_Beyond_Priors_for_Improved_Three-D_Dog_Pose_Estimation_CVPR_2023_paper.pdf) | 개의 자세·체형과 지면 접촉 문제 |
| 5 | [Animal Avatars · 2024](https://remysabathier.github.io/animalavatar.github.io/) | 실제 개 영상에서 움직일 수 있는 3D 외형을 복원하는 경로 |
| 6 | [Local Motion Phases · 2020](https://www.pure.ed.ac.uk/ws/portalfiles/portal/157671564/Local_Motion_Phases_STARKE_DOA27042020_AFV.pdf) | 발 접촉과 동작 전환의 시간 구조 |
| 7 | [How to Train Your Dog · 2021](https://mig2021.inria.fr/files/2021/11/mig21_egan.pdf) | 제작한 사족 동작을 신경망으로 보완하는 방법 |
| 8 | [WalkTheDog · 2024](https://arxiv.org/html/2407.18946v1) | 서로 다른 체형·골격으로 동작을 옮기는 문제 |
| 9 | [DogRecon · 2025](https://link.springer.com/article/10.1007/s11263-025-02485-5) | 사진 한 장의 외형 복원 가능성과 미관측 부분 추정의 한계 |
| 10 | [Exploring the Perception of Quadruped Motion Retargeting · 2021](https://mig2021.inria.fr/files/2021/11/mig21_poster_fletcher.pdf) | 자연스러움 평가를 개체 인식 검증과 구분하는 이유 |

MANN은 데스크톱 환경에서 실시간 개 동작 제어를 제시합니다. 이를 스마트폰의 상시 표시 성능 근거로 그대로 사용할 수는 없습니다. Animato는 iPad 구현을 제시하지만, 논문 당시 iPhone 이식은 진행 중이었고 Android 검증은 아닙니다.

Animal Avatars는 실제 개의 영상에 기반한 복원이라는 점에서 직접 관련성이 높습니다. DogRecon처럼 사진 한 장에서 시작하는 방법은 수집 부담을 낮추지만, 보이지 않는 외형과 동작은 사전 지식에 의존합니다. 두 경로는 서로 다른 문제를 해결합니다.

‘Habit-preserved’라는 제목의 [Behave Your Motion](https://arxiv.org/html/2507.07394v1)도 주로 종·범주별 특성을 다룹니다. 보호자와 특정 개 사이의 반복 습관이 보존되었다는 뜻으로 읽어서는 안 됩니다.

## 5. 전체 선정 문헌표

제목을 누르면 논문 또는 저자·공식 자료로 연결됩니다. ‘초록’으로 표시한 문헌은 초록 범위를 넘어 세부 실험을 주장하지 않았습니다. 일반 기술과 개 직접 연구를 적용 열에서 구분했습니다.

### 5.1. 개관 — 2편

| 문헌 | 발표·확인 자료 | 입력과 결과 | 프로젝트 적용과 한계 |
|---|---|---|---|
| [Animating Quadrupeds: Methods and Applications](https://doi.org/10.1111/j.1467-8659.2008.01312.x) | 2009 · Computer Graphics Forum 종설 | 사족 모션 획득·골격·IK·물리·제어를 분류 | 분야 구조 파악용. 현재 알고리즘 성능 근거로 사용하지 않음 |
| [Advances and Trends in the 3D Reconstruction of the Shape and Motion of Animals](https://arxiv.org/html/2508.16062v1) | 2025 · arXiv 종설 | 입력·형상 표현·학습·Gaussian 방식의 분류 | 최근 복원 연구의 지도. 개별 성능은 원논문으로 확인 |

### 5.2. 2D와 그림 기반 제작 — 7편

| 문헌 | 발표·확인 자료 | 입력과 결과 | 프로젝트 적용과 한계 |
|---|---|---|---|
| [Controlled Animation of Video Sprites](https://sites.cc.gatech.edu/gvu/perception/projects/videotexture/SCA02/index.html) | 2002 · SCA 저자 프로젝트 | 실제 영상 프레임을 재배열해 경로·행동 제약을 따르는 스프라이트 생성 | 실제 동작을 활용하는 기반. 공개 예시는 햄스터 등으로 개 전용 검증은 아님 |
| [As-Rigid-As-Possible Shape Manipulation](https://cs.brown.edu/people/jhughes/papers/Igarashi-ASM-2005/main.htm) | 2005 · SIGGRAPH 저자 자료 | 2D 도형과 제어점으로 국소 형태를 유지하는 변형 | 그림의 머리·다리·몸통을 움직이는 기반. 동작 타이밍은 별도로 제공 |
| [Image Deformation Using Moving Least Squares](https://people.engr.tamu.edu/schaefer/research/mls.pdf) | 2006 · SIGGRAPH 저자 원문 | 점·선 제약에 따른 이미지 변형 | 범용 변형법. 가려진 반대쪽 다리나 새로운 시점을 관찰한 것처럼 복원하지 못함 |
| [Animato: 2D Shape Deformation and Animation on Mobile Devices](https://igl.ethz.ch/projects/animato/animato-mgia.pdf) | 2016 · 저자 원문 | 그림 분할·리깅·비선형 변형을 iOS 기기에 구현 | iPad 구현 근거. 논문 당시 iPhone 이식은 진행 중이며 Android 성능 검증은 아님 |
| [Monster Mash: A Single-View Approach to Casual 3D Modeling and Animation](https://igl.ethz.ch/projects/monster-mash/monster-mash-paper.pdf) | 2021 · ACM TOG 저자 원문 | 그림의 윤곽·레이어에서 부풀린 3D 메시와 제어점 애니메이션 생성 | 2D 작업 흐름과 3D 모델 사이의 연결. 실제 개의 해부학·습관을 자동 획득하는 방법은 아님 |
| [AniClipart: Clipart Animation with Text-to-Video Priors](https://link.springer.com/article/10.1007/s11263-024-02306-1) | 2024 온라인 · IJCV 원문 | 클립아트·텍스트로 관절점의 Bézier 궤적과 ARAP 변형 최적화 | 일러스트 외형 유지와 움직임 초안 제작 후보. 실제 개체의 동작을 측정한 결과와 구분 |
| [AnaMoDiff: 2D Analogical Motion Diffusion via Disentangled Denoising](https://arxiv.org/html/2402.03549) | 2024 · arXiv 원문 확인 | 참조 영상의 움직임을 다른 캐릭터 이미지에 전이 | 개 움직임을 다른 동물로 옮기는 예시. 출력 영상과 앱용 편집 가능한 리그는 다름 |

### 5.3. 자세 추적과 데이터 — 9편

| 문헌 | 발표·확인 자료 | 입력과 결과 | 프로젝트 적용과 한계 |
|---|---|---|---|
| [DeepLabCut: Markerless Pose Estimation of User-defined Body Parts with Deep Learning](https://www.nature.com/articles/s41593-018-0209-y) | 2018 · Nature Neuroscience 공식 초록 | 사용자가 정의한 신체 지점의 영상 추적 | 행동 코딩 보조 기반. 원논문의 학습량·정확도를 반려견 가정 영상에 그대로 적용하지 않음 |
| [SLEAP: A Deep Learning System for Multi-animal Pose Tracking](https://www.nature.com/articles/s41592-022-01426-1) | 2022 · Nature Methods 원문 | 여러 개체의 자세·개체 ID를 추적 | 원논문 평가 종은 파리·벌·생쥐·저빌. 개 전용 성능 근거가 아닌 도구 후보 |
| [SuperAnimal Pretrained Pose Estimation Models for Behavioral Analysis](https://www.nature.com/articles/s41467-024-48792-2) | 2024 · Nature Communications 원문 | 사전학습된 동물 자세 추정과 영상 적응·미세조정 | 사족 자세 추적의 시작점. 긴 털·가림·희귀 자세는 해당 영상에서 확인 |
| [AP-10K: A Benchmark for Animal Pose Estimation in the Wild](https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/903ce9225fca3e988c2af215d4e544d3-Abstract-round2.html) | 2021 · NeurIPS Datasets and Benchmarks 공식 초록 | 54종·10,015장 이미지의 키포인트 자료 | 자세 추적 학습·평가용. 연속 동작이나 실제 습관 데이터가 아님 |
| [RGBD-Dog: Predicting Canine Pose from RGBD Sensors](https://openaccess.thecvf.com/content_CVPR_2020/papers/Kearney_RGBD-Dog_Predicting_Canine_Pose_from_RGBD_Sensors_CVPR_2020_paper.pdf) | 2020 · CVPR 원문 | RGB-D와 모션캡처 기반 개의 3D 관절 추정 | 개 직접 연구. 일반 단안 스마트폰 RGB 영상과 입력 조건이 다름 |
| [Who Left the Dogs Out? 3D Animal Reconstruction with Expectation Maximization in the Loop](https://arxiv.org/abs/2007.11110) | 2020 · ECCV 원문·공식 데이터 저장소 | 개 이미지에서 3D 자세·형상, StanfordExtra와 SMBLD 제공 | 개 전용 형상·키포인트 기반. 정지 이미지 자료만으로 개인의 행동 순서를 학습할 수는 없음 |
| [Benchmarking Monocular 3D Dog Pose Estimation Using In-The-Wild Motion Capture Data](https://cvssp.org/data/3DDogs/) | 2024 · CV4Animals 워크숍·3DDogs 공식 자료 | 실내 모션캡처·RGB-D·IMU·압력매트와 가공한 Wild 자료 | 보행 기준 자료. Wild는 실내 자료의 마커 제거·배경 합성본을 포함 |
| [DogMo: A Large-Scale Multi-View RGB-D Dataset for 4D Canine Motion Recovery](https://arxiv.org/abs/2510.24117) | 2025 · arXiv 원문·초록 | 10마리의 약 1,200개 모션 시퀀스와 다중 시점 복원 | 개 전용 시공간 자료. 시퀀스 수와 독립 개체 수를 구분 |
| [InterPet4D: A Multimodal 4D Human-Pet Interaction Dataset for Pet Motion Generation](https://arxiv.org/abs/2607.10287) | 2026 · arXiv 원문 | 개 13마리·사람 23명의 동기화 영상·메시·키포인트·음성 | 사람–개 상호작용과 가까운 후보. 훈련된 상호작용 및 고정 길이 생성 범위를 확인해야 함 |

### 5.4. 3D 형상과 아바타 복원 — 15편

| 문헌 | 발표·확인 자료 | 입력과 결과 | 프로젝트 적용과 한계 |
|---|---|---|---|
| [3D Menagerie: Modeling the 3D Shape and Pose of Animals](https://openaccess.thecvf.com/content_cvpr_2017/papers/Zuffi_3D_Menagerie_Modeling_CVPR_2017_paper.pdf) | 2017 · CVPR 원문 | 장난감 동물 스캔에서 학습한 SMAL 형상·관절 모델 | 많은 후속 연구의 기반. 실제 반려견 스캔으로만 학습한 모델이 아님 |
| [BARC: Learning To Regress 3D Dog Shape From Images by Exploiting Breed Information](https://openaccess.thecvf.com/content/CVPR2022/html/Ruegg_BARC_Learning_To_Regress_3D_Dog_Shape_From_Images_by_CVPR_2022_paper.html) | 2022 · CVPR 공식 초록 | 단일 개 사진에서 품종 정보를 활용한 3D 형상·자세 추정 | 개 체형 초기값 후보. 형상 복원과 행동 개인화는 별도 |
| [BITE: Beyond Priors for Improved Three-D Dog Pose Estimation](https://openaccess.thecvf.com/content/CVPR2023/papers/Ruegg_BITE_Beyond_Priors_for_Improved_Three-D_Dog_Pose_Estimation_CVPR_2023_paper.pdf) | 2023 · CVPR 원문 | D-SMAL과 신체–지면 접촉으로 사진의 개 자세·형상 복원 | 앉기·눕기 등 가림이 많은 자세와 접지 처리에 직접 관련 |
| [LASR: Learning Articulated Shape Reconstruction From a Monocular Video](https://openaccess.thecvf.com/content/CVPR2021/papers/Yang_LASR_Learning_Articulated_Shape_Reconstruction_From_a_Monocular_Video_CVPR_2021_paper.pdf) | 2021 · CVPR 원문 | 단일 영상의 실루엣·광류·색으로 템플릿 없는 형상·움직임 학습 | 개를 포함한 동적 복원 기반. 복원 결과의 골격·제어 품질은 별도 검토 |
| [BANMo: Building Animatable 3D Neural Models From Many Casual Videos](https://openaccess.thecvf.com/content/CVPR2022/html/Yang_BANMo_Building_Animatable_3D_Neural_Models_From_Many_Casual_Videos_CVPR_2022_paper.html) | 2022 · CVPR 공식 초록 | 여러 단안 영상에서 관절·블렌드 스키닝·NeRF 복원 | 많은 영상으로 형상을 구성하는 경로. 단일 사진 방식과 수집 부담이 다름 |
| [Reconstructing Animatable Categories From Videos](https://openaccess.thecvf.com/content/CVPR2023/papers/Yang_Reconstructing_Animatable_Categories_From_Videos_CVPR_2023_paper.pdf) | 2023 · CVPR 원문 | 여러 영상에서 범주 공통 구조와 개체 형상·시간별 움직임 분리 | 개 범주 포함. 개체 외형과 동작 분리를 위한 비교 문헌 |
| [MagicPony: Learning Articulated 3D Animals in the Wild](https://3dmagicpony.github.io/) | 2023 · CVPR 저자 프로젝트 | 한 장의 이미지에서 관절형 메시·텍스처·시점 추정 | 사족 일반 기술. 실제 개체의 습관을 추출하는 연구는 아님 |
| [Farm3D: Learning Articulated 3D Animals by Distilling 2D Diffusion](https://arxiv.org/abs/2304.10535) | 2024 학회 · 3DV; 초판 arXiv 2023 | 확산모델의 합성 이미지와 사전 지식으로 관절형 3D 복원기 학습 | 학습자료 확보의 대안. 합성된 부분을 개체의 관찰 사실로 취급하지 않음 |
| [Learning the 3D Fauna of the Web](https://openaccess.thecvf.com/content/CVPR2024/papers/Li_Learning_the_3D_Fauna_of_the_Web_CVPR_2024_paper.pdf) | 2024 · CVPR 원문 | 100종 이상에 걸친 2D 이미지에서 관절형 3D 모델 학습 | 범용성 참고. 개 전용 정확도와 개인 동작 재현의 증거는 구분 |
| [Animal Avatars: Reconstructing Animatable 3D Animals from Casual Videos](https://remysabathier.github.io/animalavatar.github.io/) | 2024 · ECCV 저자 프로젝트 | 단안 개 영상에서 형상·시간별 자세·텍스처를 함께 복원 | 실제 개의 영상 기반 3D 경로에 직접 관련. 입력 시점·가림과 미관측 영역 문제 남음 |
| [GART: Gaussian Articulated Template Models](https://www.jiahuilei.com/projects/gart/) | 2024 · CVPR 저자 프로젝트 | 단안 영상에서 관절 템플릿과 3D Gaussian 표현 학습 | 동적 외형과 새 자세 렌더링. 표준 메시와 동일한 자산 형식은 아님 |
| [DogRecon: Canine Prior-Guided Animatable 3D Gaussian Dog Reconstruction From A Single Image](https://link.springer.com/article/10.1007/s11263-025-02485-5) | 2025 · IJCV 원문 | 개 사진 한 장에서 생성 시점·D-SMAL·Gaussian 아바타 구성 | 낮은 입력 부담. 보이지 않는 외형과 새로운 동작은 생성·추정이며 관찰 사실이 아님 |
| [ARTEMIS: Articulated Neural Pets with Appearance and Motion Synthesis](https://arxiv.org/html/2202.05628v3) | 2022 · ACM TOG 원문 | 다중 카메라·모션 자료로 털 외형과 골격 제어를 결합 | 동작 제어와 털 렌더링의 통합 참고. 가정용 단일 영상보다 획득 장비가 복잡 |
| [4D-Animal: Freely Reconstructing Animatable 3D Animals from Videos](https://openaccess.thecvf.com/content/WACV2026/papers/Zhong_4D-Animal_Freely_Reconstructing_Animatable_3D_Animals_from_Videos_WACV_2026_paper.pdf) | 2026 · WACV 원문 | 영상의 조밀한 특징과 시공간 정합으로 SMAL 기반 복원 | 개 데이터셋 평가. 희소 키포인트 의존을 줄이지만 입력·형상 제약이 없어지는 것은 아님 |
| [WildAni4D: Towards 4D Animal Mesh Reconstruction](https://openaccess.thecvf.com/content/CVPR2026F/papers/Cho_WildAni4D_Towards_4D_Animal_Mesh_Reconstruction_CVPRF_2026_paper.pdf) | 2026 · CVPR Findings 원문 | 합성 영상 학습과 시퀀스 공통 형상으로 자세·이동 궤적 복원 | 시간적 떨림·형상 변동을 다루는 최신 참고. CVPR 본회의와 Findings를 구분 |

### 5.5. 움직임 제어와 전이 — 9편

| 문헌 | 발표·확인 자료 | 입력과 결과 | 프로젝트 적용과 한계 |
|---|---|---|---|
| [Mode-Adaptive Neural Networks for Quadruped Motion Control](https://www.pure.ed.ac.uk/ws/files/60838109/dog2.pdf) | 2018 · SIGGRAPH ACM TOG 원문 | 개 모션캡처와 사용자 입력에서 걷기·뛰기·앉기·눕기 등 연속 제어 | 앱의 상태 전환과 이동 제어에 직접 관련. 데스크톱 실행 성능과 모바일 성능을 구분 |
| [How to Train Your Dog: Neural Enhancement of Quadruped Animations](https://mig2021.inria.fr/files/2021/11/mig21_egan.pdf) | 2021 · MIG 원문 | 거친 개 골격 애니메이션을 모션캡처에 가까운 자세로 보정 | 수동 초안 뒤 품질 보완 후보. 특정 개체의 습관 보존을 검증한 것은 아님 |
| [Local Motion Phases for Learning Multi-Contact Character Movements](https://www.pure.ed.ac.uk/ws/portalfiles/portal/157671564/Local_Motion_Phases_STARKE_DOA27042020_AFV.pdf) | 2020 · SIGGRAPH ACM TOG 원문 | 부위별 접촉과 동작 위상을 이용한 모션 제어 | 사지 접촉 타이밍·복잡한 전환의 기반. 인간 상호작용도 포함한 범용 연구 |
| [WalkTheDog: Cross-Morphology Motion Alignment via Phase Manifolds](https://arxiv.org/html/2407.18946v1) | 2024 · SIGGRAPH Conference Papers 원문 | 사람·개 등 서로 다른 골격의 동작을 위상·의미로 정렬 | 골격 차이와 속도 정렬에 참고. 실제 개의 타이밍을 보존했는지는 별도 평가 |
| [NeuroDog: Quadruped Embodiment Using Neural Networks](https://doi.org/10.1145/3606936) | 2023 · PACMCGIT 원문 | 사람의 VR 추적 입력을 개의 움직임으로 변환 | 실시간 조종 참고. 보호자 영상에서 그 개의 습관을 학습하는 방식은 아님 |
| [OmniMotionGPT: Animal Motion Generation with Limited Data](https://openaccess.thecvf.com/content/CVPR2024/papers/Yang_OmniMotionGPT_Animal_Motion_Generation_with_Limited_Data_CVPR_2024_paper.pdf) | 2024 · CVPR 원문 | 텍스트에서 동물 모션 생성; AnimalML3D 제시 | 일반 모션 후보 확장. 애니메이션 개체 36개를 실제 개 36마리의 관찰자료로 해석하지 않음 |
| [AniMo: Species-Aware Model for Text-Driven Animal Motion Generation](https://openaccess.thecvf.com/content/CVPR2025/papers/Wang_AniMo_Species-Aware_Model_for_Text-Driven_Animal_Motion_Generation_CVPR_2025_paper.pdf) | 2025 · CVPR 원문 | 종 정보를 포함한 텍스트–모션 생성; AniMo4D 제공 | 종별 움직임 생성. 114종의 자료 규모가 특정 반려견의 재현 정확도를 의미하지 않음 |
| [Behave Your Motion: Habit-preserved Cross-category Animal Motion Transfer](https://arxiv.org/html/2507.07394v1) | 2025 · arXiv 원문 확인 | 범주별 습관 인코더로 동물 종 사이 모션 전이 | 여기서 habit은 주로 종·범주별 특성. 보호자와 한 개 사이의 개인적 습관과 구분 |
| [Two2Four: Generative Quadruped Puppeteering from Human Motion](https://doi.org/10.1111/cgf.70565) | 2026 · Computer Graphics Forum 공식 초록 | 사람 움직임을 조건으로 사족 모션과 머리·다리 제어 | 제작자가 조종하는 애니메이션 도구 후보. 실제 개체 관찰자료의 대체물은 아님 |

### 5.6. 자동 리깅 — 2편

| 문헌 | 발표·확인 자료 | 입력과 결과 | 프로젝트 적용과 한계 |
|---|---|---|---|
| [One Model to Rig Them All: Diverse Skeleton Rigging with UniRig](https://github.com/VAST-AI-Research/UniRig) | 2025 · SIGGRAPH ACM TOG·공식 저장소 | 3D 메시에서 골격과 스키닝 가중치 생성 | 3D 자산 제작 보조. 자동 관절이 개의 해부학·접촉 조건에 적합한지 검수 |
| [RigAnything: Template-Free Autoregressive Rigging for Diverse 3D Assets](https://arxiv.org/html/2502.09615) | 2025 · ACM TOG 원문 | 메시에서 다양한 관절 구조·가중치 생성 | 비인간형 구조의 자동화 후보. 정적인 메시의 리깅은 개체의 움직임 학습과 별도 |

### 5.7. 물리와 지각 평가 참고 — 3편

| 문헌 | 발표·확인 자료 | 입력과 결과 | 프로젝트 적용과 한계 |
|---|---|---|---|
| [DeepMimic: Example-Guided Deep Reinforcement Learning of Physics-Based Character Skills](https://arxiv.org/abs/1804.02717) | 2018 · SIGGRAPH ACM TOG 원문 | 참조 모션을 물리 시뮬레이션에서 모방하는 제어 정책 | 기술 기반으로만 참고. 원논문 캐릭터는 사람·로봇·공룡·용으로 개 직접 검증이 아님 |
| [Exploring the Perception of Quadruped Motion Retargeting](https://mig2021.inria.fr/files/2021/11/mig21_poster_fletcher.pdf) | 2021 · MIG 포스터 원문 | 20명이 원래 개 모션과 다른 개에서 전이한 모션의 자연스러움 평가 | 원본·전이 간 유의한 주효과 미확인, 전반적 평정도 낮음. 등가성이나 자기 개 식별의 증거가 아님 |
| [Human Perception of Quadruped Motion](https://doi.org/10.1145/1620993.1621024) | 2009 · APGV 공식 초록 | 농장 동물의 점광원·3D 모델을 통한 움직임 지각 연구 | 지각 검증의 배경. 개 보호자의 개체 식별 결과로 사용하지 않음 |

### 5.8. 최신 확장 후보 — 4편

| 문헌 | 발표·확인 자료 | 입력과 결과 | 프로젝트 적용과 한계 |
|---|---|---|---|
| [SMAL-pets: SMAL Based Avatars of Pets from Single Image](https://arxiv.org/abs/2603.17131) | 2026 · arXiv 초록 | 사진·SMAL·Gaussian과 텍스트 편집을 결합한 아바타 | 개 아바타와 직접 관련. 초록 수준 확인이며 재현성·모바일 성능 미검증 |
| [AniGauss: Toward Animatable Animal Reconstruction from Single In-the-Wild Images via Topology-Aware Gaussians](https://vision3d-lab.github.io/anigauss/) | 2026 · CV4Animals 워크숍 저자 프로젝트 | 한 사진에서 정규 시점 생성과 SMAL 정합 Gaussian 복원 | 워크숍 단계. 확인 시 프로젝트에 코드 미공개로 표시 |
| [AnimalLift: Reconstructing Animatable 3D Animals from a Single Image by Learning Canonical Shape, Texture, and Fur Maps](https://arxiv.org/abs/2609.09513) | 2026 · arXiv 초록 | 일관된 메시·UV·털 표현을 가진 동물 자산 생성 | 편집 가능한 털 자산에 주목. 개 개인의 행동 재현 근거는 아님 |
| [CORGI: Consistency-Aware 3D Dog Reconstruction from a Single Image in the Wild](https://arxiv.org/abs/2607.00321) | 2026 · arXiv 원문 확인 | 개 사진에서 일관성 보정·D-SMAL 기반 Gaussian 생성 | 새 시점·형상 보완 후보. 확인 원문에 최종 DOI 자리표시자가 있어 확정 학술지 게재로 표기하지 않음 |

### 5.9. 적용 경계와 제외 후보 — 3편

| 문헌 | 발표·확인 자료 | 입력과 결과 | 프로젝트 적용과 한계 |
|---|---|---|---|
| [QuadFM: Foundational Text-Driven Quadruped Motion Dataset for Generation and Control](https://arxiv.org/abs/2603.24021) | 2026 · arXiv 로봇 연구 초록 | 텍스트–모션과 사족 로봇 제어 | 주요 검증 대상은 로봇. 로봇의 엣지 지연을 스마트폰 개 캐릭터 성능으로 해석하지 않음 |
| [Bunraku: Turning a Single Illustration into an Editable Live2D Character](https://arxiv.org/abs/2607.27348) | 2026 · arXiv·저자 프로젝트 | 한 일러스트에서 RGBA 레이어·메시·파라미터별 키포즈 생성 | 편집 가능한 2D 자산 생성이라는 점에서 참고. 개의 전신 보행 검증은 확인하지 못함 |
| [Animating Childlike Drawings with 2.5D Character Rigs](https://arxiv.org/html/2502.17866v1) | 2025 · ACM TOG 표기 원문 | 3D 골격 모션을 시점 의존 2.5D 그림으로 전이 | 입력 조건이 직립한 인간형 그림. 사족 개에 바로 적용되는 근거로 제외 |

## 6. 수집 데이터에 추가할 움직임 정보

기존 행동 데이터의 우선순위는 유지합니다. 아래는 애니메이션 제작에 필요한 추가 필드입니다. 원본 수집과 사람의 간단한 확인을 먼저 하고, 프레임 전체의 정밀 라벨링이나 고가 장비는 검증 결과에 따라 확대합니다. 다음 우선순위·촬영 범위는 문헌을 종합한 제안이며, 논문이 제시한 보편적인 최소 촬영량은 아닙니다.

| 우선순위 | 수집·파생 항목 | 2D에서 쓰는 곳 | 3D에서 추가되는 요구 | 근거·이유 |
|---|---|---|---|---|
| P0 | 편집 전 원본 영상, 실제 프레임 시간·프레임률, 개체·날짜·상황 ID | 동작 속도·멈춤·반응 지연 보존 | 카메라 간 시간 정합의 기반 | 시간별 모션을 다루는 MANN·Animal Avatars |
| P0 | 전신 윤곽과 관절이 보이는 자연스러운 장면, 촬영 방향·카메라 움직임 | 몸통·머리·다리 레이어와 변형 기준 | 시점·형상·자세를 구분하는 단서 | BITE·Animal Avatars |
| P0 | 시작 자세 → 핵심 자세 → 종료 자세, 그 사이 전환 | 앉기·눕기·기상·다가오기 클립과 연결 | 골격·중심 이동을 포함한 전이 | MANN·Local Motion Phases |
| P0 | 네 발의 바닥 접촉 시작·끝과 불확실 표시 | 발이 바닥에서 미끄러져 보이는 오류 점검 | 접지 제약·IK·지면 방향 | BITE·Local Motion Phases |
| P0 | 머리 돌림, 시선 방향 단서, 귀·꼬리의 움직임과 몸 동작의 상대 시점 | 작은 화면의 반응 표현 | 별도 관절·보조 변형의 제어 | 사용자 정의 지점 추적 연구와 개인화 목표에 따른 설계 제안 |
| P0 | 관절·꼬리·귀의 가림, 흐림, 화면 밖 여부 | 추측한 프레임을 실제 관찰과 구분 | 가려진 관절의 3D 불확실성 관리 | 자세 추정·단안 복원 전반 |
| P1 | 체형 비율과 정면·측면·후면의 참고 이미지 | 레이어 길이·두께·반대편 외형 | 체형 파라미터와 개인 메시 | SMAL·BARC·BITE |
| P1 | 2D 키포인트 좌표, 검출 신뢰도, 수동 수정 이력 | 골격 제작·모션 전이 보조 | 3D 복원·재투영 검수 | DeepLabCut·SuperAnimal |
| P1 | 몸통 기준 위치·방향·이동 궤적, 보행 주기·발 순서 | 화면 이동과 걷기 속도의 일치 | 루트 이동·회전과 관절 운동 분리 | MANN·WalkTheDog |
| P1 | 다른 날·다른 속도에서의 같은 동작, 보호자의 전형성 평가 | 우연한 한 장면과 반복되는 특성 구분 | 개인 모션의 변동 범위 추정 | 개체화 검증을 위한 연구 설계 제안 |
| P2 | 동기화·보정된 다중 카메라 또는 깊이 영상 | 2D 제작에는 필수 아님 | 정량적인 깊이·3D 관절과 가림 보완 | RGBD-Dog·DogMo·3DDogs |
| P2 | IMU·압력매트·광학 모션캡처 | 기준자료가 필요할 때 제한적으로 활용 | 접촉·회전·3D 움직임의 기준 측정 | 3DDogs·ARTEMIS |

여러 방향에서 따로 촬영한 사진은 외형 참고자료로 유용하지만, 동기화·카메라 보정된 다중 시점 모션캡처와 같지 않습니다. 일반 RGB 영상과 RGB-D 영상도 입력 조건이 다릅니다.

관절 추정값은 원본 영상과 연결해서 저장합니다. 화면 좌표는 픽셀 또는 정규화 좌표인지, 3D 좌표는 카메라·몸통·세계 중 어느 기준인지 표시합니다. 실제 측정값, 모델 추정값, 제작자가 넣은 보정값을 같은 값으로 덮어쓰지 않습니다.

초기 데이터 구조 제안: 개체 ID → 촬영 세션 ID → 상황·행동 에피소드 ID → 원본 영상 구간 → 프레임별 관찰·추정값 → 제작 모션 버전 → 보호자 검수 결과. 최소 공통 필드는 시간, 출처 구간, 관측/추정 구분, 신뢰도 또는 불확실 표시, 수정 이력입니다.

## 7. 구현 단계와 완료 기준

| 단계 | 작업 | 다음 단계로 넘어갈 근거 |
|---|---|---|
| 1. 2D 개인화 시제품 | 실제 영상에서 대표 동작과 전환을 선정하고 2D 레이어·골격·클립으로 재현. 행동 프로필로 반응 지연·순서·반복을 제어 | 원본과 비교해 주요 순서·속도·멈춤이 유지되고 보호자가 구체적으로 닮은 점과 어긋난 점을 설명 |
| 2. 추적·전이 보조 | SuperAnimal 등으로 관절 추적을 보조하고 가림·접지를 검수. 반복되는 제작 작업부터 자동화 | 수동 제작 대비 수정 시간 감소, 발 미끄러짐·왜곡 증가 없음 |
| 3. 3D 비교 시제품 | BITE·Animal Avatars 계열 또는 수작업 메시를 비교. 실제 모션을 체형에 맞게 전이하고 2D 출력과 3D 출력을 비교 | 필요한 시점·동작을 일관되게 표현하고 목표 기기의 성능 예산 충족 |
| 4. 생성형·신경 표현 확장 | 사진 기반 Gaussian, 텍스트 모션, 자동 리깅을 제작 보조로 평가 | 생성한 외형·동작을 실제 관찰자료와 구분하고 수정 가능한 자산으로 연결 |

2D와 3D의 행동 프로필은 공유하되 표시 계층은 교체 가능하게 설계하는 것이 좋습니다. 예를 들어 ‘바라보기→짧게 멈추기→다가오기’라는 행동 순서와 각 구간의 시간은 같게 두고, 해당 구간을 2D 클립 또는 3D 골격으로 실행할 수 있게 합니다.

모든 동작을 한 번에 학습시키는 범용 생성모델보다, 실제 데이터가 있는 동작부터 개별 검수하는 순서를 제안합니다. 관찰되지 않은 동작은 기본 동작 또는 생성 동작이라는 출처를 내부적으로 남겨 개인화 데이터와 섞이지 않게 합니다.

이 문서는 애니메이션 기술 검토입니다. 운영체제별 위젯·플로팅 화면의 권한과 실행 제한을 검증한 문서는 아니며, 데스크톱 또는 iPad 논문 성능으로 해당 조건을 충족했다고 가정하지 않습니다.

## 8. 검증 항목: 자연스러움과 ‘우리 개다움’을 분리

| 검증 목표 | 측정 예 | 해석 범위 |
|---|---|---|
| 추적·복원 정확도 | 수동 확인한 키포인트와의 오차, 실루엣 정합, 가려진 관절 오류, 프레임 간 형상 변동 | 영상·3D 복원이 입력자료에 얼마나 맞는지 |
| 모션 품질 | 접지 중 발 미끄러짐, 관절 뒤집힘, 몸통 떨림, 전환 시 위치·속도 불연속 | 움직임이 물리적·시각적으로 안정적인지 |
| 개인 동작 보존 | 원본 대비 반응 지연·동작 순서·지속시간·반복·보행 주기·좌우 차이 | 관찰한 개인의 움직임을 얼마나 유지했는지 |
| 보호자의 개체 인식 | 같은 외형에서 자기 개 모션 대 다른 개·일반 모션 비교, 강제선택과 닮음 평정, 확신도 | 움직임이 특정 개체 인식에 기여하는지 |
| 모바일 실행 | 목표 기기에서 프레임 시간, 입력 반응, 메모리, 장시간 배터리·발열 | 실제 앱의 실행 가능성 |

개체 인식 실험에서는 외형을 같게 둔 모션 비교와, 모션을 같게 둔 외형 비교를 분리할 수 있습니다. 자기 개의 익숙한 원본 장면을 단순히 기억해서 선택하는 효과를 줄이려면 다른 날·다른 구간의 자료를 평가에 사용합니다. 다른 개의 모션은 체형·동작 종류·평균 속도 등 비교 조건을 맞추는 것이 좋습니다. 이는 본 프로젝트를 위한 실험 설계 제안이며 기존 논문이 확정한 정답 프로토콜은 아닙니다.

[2021년 사족 모션 전이 지각 포스터](https://mig2021.inria.fr/files/2021/11/mig21_poster_fletcher.pdf)는 20명의 자연스러움 평정을 다뤘습니다. 원본과 전이 방법 사이에 유의한 주효과가 확인되지 않았다는 결과는 방법들이 동등하다는 입증이나 보호자의 자기 개 식별 성공을 의미하지 않습니다.

모션 클립을 학습·검증으로 나눌 때 같은 영상의 인접 프레임만 분리하면 평가가 쉬워질 수 있습니다. 최소한 촬영 구간·세션을 구분하고, 개인화의 반복성을 보려는 평가에는 촬영일을 달리한 자료를 포함하는 것이 적절합니다.

## 9. 채택 전에 확인할 구현 조건

논문 공개, 코드 공개, 학습된 모델 공개, 데이터 공개는 별개입니다. [BARC](https://openaccess.thecvf.com/content/CVPR2022/html/Ruegg_BARC_Learning_To_Regress_3D_Dog_Shape_From_Images_by_CVPR_2022_paper.html)와 [BITE](https://openaccess.thecvf.com/content/CVPR2023/papers/Ruegg_BITE_Beyond_Priors_for_Improved_Three-D_Dog_Pose_Estimation_CVPR_2023_paper.pdf)의 저자 자료는 연구 목적 제공을 명시합니다. [UniRig 공식 저장소](https://github.com/VAST-AI-Research/UniRig)에는 MIT 라이선스가 표시되어 있지만, 사용할 가중치·데이터·외부 의존성의 조건도 해당 자산 기준으로 확인해야 합니다. AniGauss는 확인한 프로젝트 페이지에서 코드가 아직 공개되지 않은 상태로 표시되었습니다.

실험 대상으로 고를 때는 다음 네 가지를 먼저 확인합니다.

1. 입력이 실제 보유한 자료와 맞는지: 사진 한 장, 단안 영상, RGB-D, 동기화 다중 시점을 구분합니다.

2. 출력이 필요한 자산인지: 동영상, 키포인트, 메시·골격, Gaussian, 행동 제어기를 구분합니다.

3. 개체화할 수 있는 정보가 무엇인지: 체형·털 외형·관절 자세·동작 리듬·상황별 습관을 구분합니다.

4. 모바일 실행에 필요한 변환과 비용이 무엇인지: 학습·제작 단계의 계산과 기기에서 매 프레임 수행하는 계산을 구분합니다.

현재의 우선 조사 대상은 2D 제작에 Animato·ARAP, 영상 추적에 SuperAnimal, 개 동작 제어에 MANN, 후속 3D 복원에 BITE·Animal Avatars입니다. 생성형 기법은 관찰 데이터가 부족한 부분을 메우는 후보이지만, 그 결과를 실제 반려견의 특성으로 확정하지 않습니다.

## 부록. 검색식 기록

아래 검색식의 결과와 관련 논문의 참고문헌·공식 프로젝트를 교차 확인했습니다. 검색 결과의 개수는 반환 항목 수이며 독립 논문 수가 아닙니다.

1. survey animal motion reconstruction animation quadruped dogs 2D 3D pose shape controllable motion

2. two dimensional animal character animation dog skeletal rigging image deformation single drawing

3. dog 3D reconstruction SMAL BARC BITE monocular video animatable dog shape pose

4. canine dog motion capture dataset markerless pose estimation gait reconstruction

5. quadruped dog character animation neural motion control mode adaptive neural networks physics

6. animal motion retargeting quadruped skeletal animation rigging UniRig RigAnything

7. animal image to animation 2D vector clipart dog motion transfer diffusion animation

8. dog animal animatable reconstruction motion generation 2025 2026 articulated Gaussian

9. As Rigid As Possible Shape Manipulation 2005 Image Deformation Moving Least Squares 2006 character animation

10. animal dog 2D video motion transfer sprite skeleton drawing AniClipart AnaMoDiff Monster Mash

11. SuperAnimal pretrained pose estimation 2024 dogs DeepLabCut SLEAP animal dataset AP10K StanfordExtra

12. physics based animation quadruped dog DeepMimic local motion phases DeepPhase animation control

13. animal motion generation dataset dog OmniMotionGPT DeformingThings4D Truebones 2024 2025 2026

14. dog animation individual motion style preserve body proportions retargeting foot sliding motion identity 2D 3D

15. real time mobile animal animation skeletal skinning 2D sprites dog computational performance

16. animal motion synthesis controllable animation dog quadruped 2026

17. 3D Menagerie SMAL 2017 Zuffi official project model animal shape

18. Who Left the Dogs Out 3D Animal Reconstruction StanfordExtra ECCV 2020 paper dataset

19. GART Gaussian Articulated Template Models 2024 CVPR dogs official project

20. MagicPony Learning Articulated 3D Animals in the Wild CVPR 2023 Farm3D official papers

21. DeepLabCut markerless pose estimation user defined body parts deep learning Nature Neuroscience 2018 official

22. AP-10K benchmark animal pose estimation 2021 NeurIPS dataset official paper Animal3D 2023

23. Bunraku Turning a Single Illustration into an Editable Live2D Character 2026 arxiv

24. Exploring the Perception of Quadruped Motion Retargeting Fletcher 2021 paper

25. Controlled Animation of Video Sprites Schodl Essa 2002 dog paper

26. Human perception of quadruped motion Skrba O Sullivan 2009 paper

27. LASR BANMo RAC reconstruct animatable animals video ARTEMIS furry 2021 2022 2023
