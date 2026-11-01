# 중립적인 반려견 일상 행동 조사와 DB 확장

기준일: 2026-10-17. Exa로 8개 검색 방향에서 46개 결과 슬롯을 조회했다. 반환 46건을 URL 기준으로 정리하면 44개이며, 이는 44편의 논문을 읽었다는 뜻이 아니다. 후보 중 새 연구 10편과 기존 출처 2편의 관련 부분을 확인했다. 새 연구는 관련 본문·표를 확인한 8편, 초록·발췌 1편, 초록만 확인한 1편이다.

**중립은 감정이 없거나 정상이라는 판정이 아니라, 관찰되는 일상 동작에 감정가를 미리 부여하지 않는 조사 범위다.** 같은 동작은 긍정·부정·일상 맥락에 함께 나타날 수 있다. 개인화 적용 여부와 애니메이션 구현 상태는 별도다.

## 이번 반영

- 새 문헌 L53–L62 10편, 행동 기록 E130–E177 48건을 추가했다. 기존 L04·L05는 출처 ID를 재사용했다.
- 기존 E017–E019를 포함해 51개 기록에 일상 맥락 평가를 붙였다. 기존 긍정·부정 평가를 지우거나 반대 감정으로 재분류하지 않았다.
- 행동 분류 노드 24개(동작군 6개, 기록 가능한 행동·변형 18개), 상황 8개, 종합 결과 4건을 추가했다.
- 배뇨·배변 후 땅 긁기 두 관계를 양방향 4행으로 저장했다. 털기 전후 집단 전이표를 개별 고정 연쇄로 만들지 않았다.
- 누적 DB는 기록 280건, 분류 노드 164개, 기록 가능한 행동·변형 126개, 출처 86개다. 이 수치는 개체 수나 실제 발생 횟수가 아니다.
- [DB 안내](../../data/behavior-db/README.md), [SQLite](../../data/behavior-db/nana-behaviors.sqlite), [Excel](../../outputs/behavior-db-20261017/behavior-catalog.xlsx), [추가 자료](additions.json), [검색 기록](search-log.json).

## 행동별 결과와 개인화 활용

| 묶음 | 추가·보강한 행동 | 확인한 근거 | 적용할 때 구분할 점 |
| --- | --- | --- | --- |
| 자세·휴식 | 앉은 상태, 서 있는 상태, 가슴을 댄 누운 상태, 옆으로 눕기, 몸 말기, 배 보이기 | 유도 과제 영상, 휴식 연구 정의, 보호자 설문 | 상태와 자세 전환을 분리한다. 누워 있음을 수면으로 확정하지 않는다. |
| 머리 지지·수면 중 작은 동작 | 머리를 침대 가장자리에 받치기, 가장자리 아래로 늘어뜨리기, 다리 움찔하기 | 12개월 개의 보호자 보고 | 머리가 높아도 표면이 지지할 수 있다. 다리 움직임에서 꿈 내용·달리기를 추정하지 않는다. |
| 이동 | 걷기, 속보, 빠른 달리기 범주 | 영상·센서 검증과 보호자 유도 과제 | 속도와 보행형을 구분한다. 연구의 trot 범주에 포함된 pacing은 반복 서성거림 코드와 다르다. |
| 먹고 마시기 | 그릇에 머리를 내리고 먹기·마시기, 혀로 물을 끌어올려 마시는 주기 | 영상 코딩·고속 촬영 | 모금 사이 머리 들기는 음수와 별도 구간이다. 물 마시기를 혀에 물을 담아 떠먹는 동작으로 단순화하지 않는다. |
| 냄새 조사 | 바닥, 공중, 자기 몸의 냄새 맡기, 먹이 찾기 | 자연 산책 관찰·ethogram·유도 과제 | 바닥 탐색과 먹이 찾기를 구분한다. 공중·자기 몸 냄새 맡기는 이번 출처에서 정의만 확인했다. |
| 몸단장·전환 | 전신 털기, 머리만 털기, 기지개, 몸 긁기, 자기 몸 핥기, 하품, 구르기 | 자연 관찰, 행동 정의, 혼합 자료의 코딩 범주 | 몸 털기와 몸 떨기, 정지한 배 보이기와 구르기를 구분한다. 자기 핥기·긁기를 건강한 일상 습관으로 자동 채택하지 않는다. |
| 배설 | 뒷다리 들고 소변보기, 쪼그려 소변보기, 대변보기, 배설 후 땅 긁기 | 영상·센서 검증, 보호소 산책 관찰 | 좌우는 별도 필드다. 성별로 자세를 고정하거나 모든 배뇨를 영역 표시로 해석하지 않는다. |

위 표는 구현 후보를 고르기 위한 연구 정리다. 행동 빈도·개체 안정성·작은 픽셀 화면의 식별 효과가 검증됐다는 뜻은 아니다.

## 중요한 해석

### 휴식 자세는 사진으로 확인하기 좋은 후보다

Kinsman 등의 12개월 설문에서는 옆으로 누운 자세, 몸을 만 자세, 등을 바닥에 댄 자세, 머리를 받친 자세를 복수 선택으로 보고했다. Table 2는 수면 문항 참여 1,091마리 중 해당 문항 결측 49건을 제외한 1,042응답을 분모로 사용한다. 같은 개가 여러 자세를 선택할 수 있다. 자유 서술에는 앞뒤 발을 뻗고 엎드린 자세 4건과 머리를 가장자리 아래로 늘어뜨린 자세 5건이 있었다. 낮은 건수의 자유 서술을 일반적인 빈도 순위로 사용하지 않는다. [Kinsman et al., 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7401528/)

Ladha와 Hoffman은 머리를 목으로 들고 있는 상태와 표면에 맡긴 상태를 구별했다. 침대 가장자리처럼 높은 곳에 머리를 받쳐도 후자에 해당할 수 있다. 따라서 ‘머리 높음=깨어 있음’ 또는 ‘머리 낮음=수면’이라는 규칙은 부적절하다. 기존 E017–E019에 재확인 근거를 연결하고 새 관찰로 중복 계수하지 않았다. [Ladha & Hoffman, 2018](https://www.mdpi.com/1424-8220/18/8/2649)

### 몸 털기는 활동 전환의 후보지만 고정 순서는 아니다

Bryce 등의 자연 관찰에서는 96마리에서 120회 털기를 수집했고, 전신 100회·머리만 20회로 구분했다. 털기 전후 각각 10초의 창에서 활동을 비교했을 때 107회에 행동 차이가 있었다. 그러나 연구는 감정 관련 자세 변화와의 연결을 확인하지 못했다. 각 관찰창에는 여러 행동이 들어갈 수 있어 전이표의 행 합이 1이 되지 않을 수 있다. 따라서 이 표를 게임의 개인별 전이 확률이나 ‘기상→기지개→털기’ 필수 순서로 옮기지 않았다. [Bryce et al., 2024](https://www.mdpi.com/2076-2615/14/22/3248)

같은 논문의 ethogram에는 기지개·하품·자기 몸 냄새 맡기 등이 있으나 항목별 실제 발생량은 이번에 확인하지 못했다. 이 여섯 기록은 `literature_definition / DEFINITION_ONLY`로 남겼다. 기지개 자체를 놀이 절하기나 통증 자세와 동일시하지 않는다.

### 배설 뒤 땅 긁기는 선택적인 후속 행동이다

McGuire의 보호소 개 500마리 산책 연구는 배뇨 후와 배변 후 땅 긁기를 구별했다. 이를 두 상황별 기록과 이전·후속 관계로 연결했다. 모든 개가 매번 하는 행동은 아니며, 성별·나이의 집단 차이가 개인의 동작을 결정하지 않는다. 영상 검증 연구도 좌우 뒷다리 들기와 쪼그린 배뇨를 구별하며, 암컷의 다리 들기도 포함한다. [McGuire, 2016](https://www.sciencedirect.com/science/article/abs/pii/S0168159116301794), [Bidder et al., 2020](https://www.nature.com/articles/s41598-019-57198-w)

### 자연 관찰·유도 과제·행동 정의를 나눴다

- den Uijl 등의 51마리 검증은 활동 수행을 유도한 구간이 있다. 자연 행동 빈도나 개인 선호로 사용하지 않는다. 속보 범주에 포함된 측대보를 부정 맥락의 반복 서성거림으로 연결하지 않았다. [den Uijl et al., 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5706712/)
- Vehkaoja 등의 45마리 데이터는 보호자가 자세·이동 과제를 유도하고 보상한 조건이다. 과제의 약 3분을 개별 행동 지속시간 칸에 넣지 않았다. 누운 상태를 ‘몸을 낮춰 눕는 전환’으로 바꾸지 않았다. [Vehkaoja et al., 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC8777071/)
- Chambers 등의 자기 핥기·긁기는 병원과 가정의 혼합 자료이며 건강 관련 행동 촬영이 우선됐다. 동작 형태를 참고할 수 있지만 정상 일상 빈도는 이 자료로 정할 수 없다. [Chambers et al., 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8228965/)
- Westgarth 등의 산책 자료는 286개 관찰이며 반복 관찰이 포함된다. 냄새 맡기·배뇨·배변·구르기·먹기를 기록했지만 단순 연관을 ‘냄새 맡기→배뇨’의 필수 순서로 저장하지 않았다. 산책 중 섭취물의 안전성·선호도도 확인되지 않았다. [Westgarth et al., 2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC7132425/)
- 일상 외출 중 개 77마리를 관찰한 연구는 이번에 초록만 확인했다. 낮은 활동량을 수면이나 편안함으로 변환하지 않고 종합 결과 F14로 보존했다. [Stephan et al., 2021](https://doi.org/10.1016/j.applanim.2021.105463)

## DB의 추가 항목과 결측 원칙

기존 행동 위계와 상황·이전/후속/동시/대안 필드를 유지했다. `neutral_assessments`는 일상 맥락 영역, 근거 방식, 해석 상태, 근거 내용, 혼동 요인, 적용 주의를 기록한다. `v_neutral_contexts`는 이 평가가 붙은 51건을 조회한다.

| 해석 상태 | 의미 |
| --- | --- |
| routine_observation | 일상 형태의 관찰이며 감정 중립을 검증한 것은 아님 |
| elicited_observation | 실험자·보호자가 유도한 동작의 관찰 |
| owner_reported | 논문에 실린 보호자 보고 |
| definition_only | ethogram의 행동 정의만 추출 |
| mixed_context | 건강·일상 등이 섞인 자료에서 형태 참고 |

모든 새 기록의 개별 지속시간·반응 지연·반복 횟수는 NULL이다. 논문 표본 수, 집단 사건 수, 설문 응답 비율, 실험 과제 시간은 설명 칸에만 남겼다. 연구 원영상이나 개별 원자료를 내려받아 재분석하지 않았으므로 실제 개체 ID도 만들지 않았다. 이전 자료의 source ID와 232개 기록, 원수집 23행, 긍정·부정 평가를 보존한다.

## 입력 부담을 줄이는 활용 제안

다음은 연구 결과에서 도출한 **제품 검토안**이며 아직 제작·A/B 검증되지 않았다.

1. 쉬는 모습은 사진과 소수의 자세 그림을 함께 보여주고 대표 자세·가끔 하는 자세를 선택하게 한다. 머리를 목으로 드는지, 물체에 받치는지도 묻는다.
2. 몸 털기·기지개·몸 긁기·구르기는 짧은 시안 중 닮은 형태를 고르게 한다. ‘모름·해당 없음’을 허용하고 발생 상황과 빈도는 분리한다.
3. 배설 동작은 제품 장면에 필요할 때 선택적으로 수집한다. 뒷다리를 드는지, 좌우가 일정한지, 이후 땅을 긁는지를 묻는다.
4. 물 마시기는 혀·머리의 리듬과 중간 멈춤을 시안으로 비교하되, 고속 동작의 모든 생체역학 단계를 8fps에 그대로 재현할 수 있다고 가정하지 않는다. [음수 동작 원 연구](https://pmc.ncbi.nlm.nih.gov/articles/PMC4703018/)
5. 중간점검 A/B에서는 외형·자산 품질·노출 시간을 맞추고, 자세 차이 또는 전환 차이가 ‘자기 개다움’에 기여하는지 분리해 본다. 이번 문헌 수집은 선호·구매 검증을 대신하지 않는다.

## 출처와 확인 범위

| ID | 출처 | 표본·단위 | 확인 범위 |
| --- | --- | --- | --- |
| L53 | [den Uijl et al. (2017)](https://pmc.ncbi.nlm.nih.gov/articles/PMC5706712/) | 건강한 개 51마리, 6개월–13세, 10kg 초과; 행동별 분석 표본은 다름 | 관련 본문·Table 1·3 확인 |
| L54 | [Gart et al. (2015)](https://pmc.ncbi.nlm.nih.gov/articles/PMC4703018/) | 19마리의 물 핥아 마시기 고속 촬영 및 물리 모형 | 관련 본문·동작 설명 확인 |
| L55 | [Bryce, Nurkin & Horowitz (2024)](https://www.mdpi.com/2076-2615/14/22/3248) | 96마리, 120회 털기(전신 100·머리만 20); 뉴욕 도그런·데이케어 | 관련 본문·Table 1–3 확인 |
| L56 | [Bidder et al. (2020)](https://www.nature.com/articles/s41598-019-57198-w) | 검증 모집 62마리, 분석 31마리(수컷 19·암컷 12); 별도 경비견 적용 분석 3마리 | 관련 방법·결과·배뇨 자세 확인 |
| L57 | [Chambers et al. (2021)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8228965/) | 정제 후 crowd 2,217마리·5,063영상; eat/drink 149마리·262영상 | 관련 방법·Table 2–3·결과 확인 |
| L58 | [Westgarth et al. (2010)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7132425/) | 연구 1 산책 관찰 286건(반복 관찰 포함); 연구 2 개 10마리 | 관련 방법·결과·Table 3 확인 |
| L59 | [McGuire (2016)](https://www.sciencedirect.com/science/article/abs/pii/S0168159116301794) | 두 보호소 개 500마리, 각 1회 산책; 4개월–14세 | 초록·서론·section snippets 확인 |
| L60 | [Stephan, Leidhold & Hammerschmidt (2021)](https://doi.org/10.1016/j.applanim.2021.105463) | 한 마리 가정 32마리·여러 마리 가정 45마리; 평소 외출 중 영상 | 초록 확인 |
| L61 | [Vehkaoja et al. (2022)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8777071/) | 중대형 반려견 45마리, 17마리 반복; 보호자 유도 7개 과제 | 관련 본문·2.2–2.3 확인 |
| L62 | [Kinsman et al. (2020)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7401528/) | 12개월 수면 문항 1,091마리; Table 2 문항 결측 49, 응답 1,042; 복수 선택 | 관련 본문·Table 2·각주 확인 |
| L04 재사용 | [Redmond et al., 2024](https://www.mdpi.com/1424-8220/24/18/5955) | 6마리 | Table 2·관련 본문 재확인; 자기 몸단장·휴식 세부 정의 추가 |
| L05 재사용 | [Ladha & Hoffman, 2018](https://www.mdpi.com/1424-8220/18/8/2649) | 가정 12마리 | 3.4 Annotations 재확인; 기존 세 기록의 평가와 종합 결과 추가 |

검색 결과의 날짜·저자는 본문과 대조했다. L55의 투고일을 발행일로 사용하지 않았고, L59의 검색 저자 오표기를 교정했다. 이번 조사는 범위를 넓힌 자료 탐색으로, 체계적 문헌고찰 또는 모든 일상 행동의 완전한 목록은 아니다. 기상 직후 기지개·털기의 고정 순서, 배설 전 돌기, 잠자리 파기·빙글 돌기, 앞뒤 다리 기지개의 개체별 반복 패턴은 이번 확인 범위에서 확정할 근거가 부족해 새 관찰로 만들지 않았다.

## 추가 기록 목록

| 기록 | 출처 | 행동 코드 | 근거 유형 | 요약 |
| --- | --- | --- | --- | --- |
| E130 | L53 | WALK | literature_observation | 유도·자유 활동 영상에서 걷기를 구분해 검증했다. |
| E131 | L53 | TROT | literature_observation | 속보 범주를 영상으로 코딩했다. 원 연구는 측대보도 이 범주에 포함했다. |
| E132 | L53 | RUN | literature_observation | canter/gallop을 한 범주로 관찰·검증했다. |
| E133 | L53 | EAT | literature_observation | 그릇을 향해 머리를 내린 음식 섭취를 코딩했다. 머리를 들거나 주위를 보는 구간은 분리했다. |
| E134 | L53 | DRINK | literature_observation | 그릇을 향해 머리를 내린 음수를 코딩했다. 모금 사이 머리 든 구간은 제외했다. |
| E135 | L53 | HEAD_SHAKE | literature_observation | 머리를 좌우·회전 방향으로 털어 귀가 반복 움직이는 구간을 코딩했다. |
| E136 | L54 | DRINK | literature_observation | 혀가 뒤로 말린 상태로 물에 닿고 회수될 때 물기둥이 생기며, 입을 닫아 물을 받아들이는 주기를 분석했다. |
| E137 | L55 | SHAKE | literature_observation | 96마리에서 수집한 120회 털기 중 전신 털기는 100회였다. 전후 관찰창에서 활동 변화를 분석했다. |
| E138 | L55 | STRETCH | literature_definition | 기지개를 몸통과 다리를 서로 멀어지게 펴는 형태로 ethogram에 정의했다. |
| E139 | L55 | SNIFF_SELF | literature_definition | 자기 몸 쪽으로 코를 가져가는 냄새 조사 항목이 있다. |
| E140 | L55 | SNIFF_AIR | literature_definition | 공중으로 코를 드는 냄새 조사 항목이 있다. |
| E141 | L55 | SCRATCH_SELF | literature_definition | 자기 몸을 발로 빠르게 반복 문지르는 항목이 있다. |
| E142 | L55 | ROLL_GROUND | literature_definition | 바닥에 누워 몸을 좌우로 회전하는 항목이 있다. |
| E143 | L55 | YAWN | literature_definition | 입을 크게 벌려 늘리는 하품 항목이 있다. |
| E144 | L56 | URINATE_LEG | literature_observation | 왼쪽 뒷다리를 든 배뇨를 영상·센서 분류에서 구별했다. |
| E145 | L56 | URINATE_LEG | literature_observation | 오른쪽 뒷다리를 든 배뇨를 영상·센서 분류에서 구별했다. |
| E146 | L56 | URINATE_SQUAT | literature_observation | 쪼그린 배뇨 자세를 별도 관찰 범주로 구별했다. |
| E147 | L56 | DEFECATE | literature_observation | 배변을 쪼그린 배뇨와 구별하는 영상 참조 범주로 사용했다. |
| E148 | L57 | SELF_LICK | literature_definition | 자기 몸 핥기를 외부 물체 핥기와 분리해 정의했다. |
| E149 | L57 | SCRATCH_SELF | literature_definition | 뒷발로 몸·목·머리를 긁는 동작을 정의했다. |
| E150 | L58 | SNIFF_GROUND | literature_observation | 산책 중 지면 냄새 맡기를 관찰·계량했다. |
| E151 | L58 | ROLL_GROUND | literature_observation | 산책 중 몸 구르기가 8개 관찰에서 기록됐다. |
| E152 | L58 | EAT | literature_observation | 산책 중 먹는 행동이 6개 관찰에서 기록됐다. |
| E153 | L58 | URINATE | literature_observation | 산책 중 배뇨 발생을 기록했다. |
| E154 | L58 | DEFECATE | literature_observation | 산책 중 배변 발생을 기록했다. |
| E155 | L59 | URINATE | literature_observation | 소변 횟수와 환경 대상에 향한 배뇨를 구분해 기록했다. |
| E156 | L59 | DEFECATE | literature_observation | 산책 중 대변보기와 배변 뒤 땅 긁기 여부를 기록했다. |
| E157 | L59 | GROUND_SCRAPE | literature_observation | 일부 개에서 소변을 본 뒤 발로 땅을 뒤로 긁는 행동을 보고했다. |
| E158 | L59 | GROUND_SCRAPE | literature_observation | 일부 개에서 대변을 본 뒤 땅 긁기를 보고했다. |
| E159 | L61 | SIT | literature_observation | 정지해 앉은 자세를 코딩했다. |
| E160 | L61 | STAND | literature_observation | 정지해 서 있는 자세를 코딩했다. |
| E161 | L61 | LIE_PRONE | literature_observation | 가슴을 바닥에 댄 누운 상태를 코딩했다. 눕는 전환 동작의 측정이 아니다. |
| E162 | L61 | WALK | literature_observation | 보호자 유도 보행에서 분명하고 연속된 걷기 구간을 코딩했다. |
| E163 | L61 | TROT | literature_observation | 보호자 유도 보행에서 분명하고 연속된 속보 구간을 코딩했다. |
| E164 | L61 | SCENT_SEARCH | literature_observation | 바닥의 사료 조각을 냄새로 찾는 과제를 코딩했다. |
| E165 | L62 | LIE_SIDE | published_owner_report | 보호자가 옆으로 길게 누운 수면 자세를 보고했다. |
| E166 | L62 | LIE_CURL | published_owner_report | 보호자가 몸을 말고 자는 자세를 보고했다. |
| E167 | L62 | LIE_BELLY | published_owner_report | 보호자가 등을 바닥에 대고 자는 자세를 보고했다. |
| E168 | L62 | REST_HEAD_SUPPORTED | published_owner_report | 보호자가 침대 가장자리 등에 머리를 받치고 자는 자세를 보고했다. |
| E169 | L62 | HOLD_OBJECT | published_owner_report | 보호자가 장난감·물체를 입에 문 채 자는 모습을 보고했다. |
| E170 | L62 | LIMB_TWITCH | published_owner_report | 보호자가 수면 중 다리의 작은 움찔거림을 보고했다. |
| E171 | L62 | LIE_PRONE | published_owner_report | 자유 서술에서 배를 바닥에 대고 앞뒤 발을 뻗는 수면 자세가 보고됐다. |
| E172 | L62 | REST_HEAD_DANGLE | published_owner_report | 자유 서술에서 머리를 침대·의자 가장자리 아래로 늘어뜨린 자세가 보고됐다. |
| E173 | L04 | SELF_GROOM | literature_definition | 핥기·자기 몸 깨물기·긁기를 포함하는 자기 몸단장 범주를 정의했다. |
| E174 | L04 | LIE_SIDE | literature_definition | 옆구리를 바닥에 대고 머리도 옆으로 지지하는 형태를 정의했다. |
| E175 | L04 | REST_HEAD_UP | literature_definition | 배를 대고 눕거나 뒷다리를 한쪽으로 둔 채 머리를 든 휴식 형태를 정의했다. |
| E176 | L04 | REST_HEAD_DOWN | literature_definition | 같은 누운 형태에서 앞발이나 바닥에 머리를 내린 휴식 형태를 정의했다. |
| E177 | L55 | HEAD_SHAKE | literature_observation | 120회 털기 중 머리만 터는 행동은 20회였다. |

