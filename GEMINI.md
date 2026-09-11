# GEMINI.md - AI Agent Context File (MassAgent & 25_ACE)

## 1. 개요 (Overview)
본 문서는 **25_ACE / MassAgent / ARR** 생태계에서 작동하는 모든 AI 코딩 에이전트(**Claude Code, Codex, Google DeepMind Gemini**)가 공유하는 **단일 진실 원천(Single Source of Truth, SSOT)** 컨텍스트 파일입니다.
대지 분석(Land), 건축법규(Law), 마스터플랜(MasterPlan), 3D 매스 조형(MAAS Geometry), 구조 자립성 검증(Structural Verification) 파이프라인의 핵심 원칙과 기하학적 수식을 정의합니다.

---

## 2. 건축법규 및 대지배치(Siting/Massing) 절대 원칙 (10대 핵심 규칙)
1. **정밀 안착(Siting) 및 매스 배치(Massing)**: 단순 보고서 요약에 그치지 않고, 모든 대지마다 정확한 건축법규를 적용하여 건물이 대지 위에 오차 없이 정확히 안착 및 매스 배치되어야 함.
2. **도로 소요너비 및 모퉁이 가각전제 산정**: 일반도로 4m 미달 시 중심선 후퇴, 막다른 도로(10m/35m) 기준 폭원 확보, 모퉁이 가각전제(2~4m 코너 절단)를 산정하여 공부상 대지면적에서 공제한 '유효 대지면적' 기준 건폐율/용적률 계산.
3. **최신 정북방향 일조사선 (시행령 제86조)**: 높이 10m 이하 1.5m 이격, 10m 초과 시 H <= 2D 적용. 북측 도로/공원 접할 시 반대편 경계선 기산선 이동 완화 반영.
4. **연면적 산정용 지상/지하 제외 (시행령 제119조)**: 지하층 면적과 지상 주차장 면적은 용적률 산정용 연면적에서 엄격히 제외하며, 지자체 조례 상한을 국토계획법 상한보다 우선 적용.
5. **층별 건축한계선(Buildable Envelope) 슬라이스 연동**: 대지경계선 이격 및 층별 일조사선을 슬라이스한 3D Envelope 데이터를 매스 배치에 직접 연동.
6. **공동주택 채광창 이격 및 인동거리 산정**: 채광창 방향 대지경계선 이격거리(D >= 0.5H, 다세대 0.25H) 및 동간 인동거리(남측동 0.5H, 측벽 4m/8m) 완벽 확보.
7. **전국 17개 광역시도 자치조례 우선 적용**: 지자체 건축/도시계획조례(BCR, FAR, 조경, 주차)를 주소로부터 자동 매칭하여 국토계획법 상한보다 최우선 적용.
8. **토지이용계획확인원 기반 중첩 규제 전수 검토**: 지목 전용, 고도지구 캡핑, 방화지구 내화, 경관지구 후퇴, 교육환경 50m 보호구역, 공개공지 5~10% 의무 및 1.2배 완화 전수 검토.
9. **LawAgent 24/7 오프라인 무중단 Fallback**: 외부 마이크로서비스(8001)나 Neo4j 유무와 무관하게 src/legal/ 내장 엔진으로 즉시 자동 전환되어 100% 무중단 보고서 및 Envelope 산출.
10. **크로스 AI(Codex, Claude, Gemini) 공통 동기화 원칙**: GEMINI.md, GEMINI.md에 정의된 대지 안착/Envelope 수식을 단일 진실 원천으로 공유하며, 3대 핵심 테스트(종합법규, 대지별 Envelope, 사이트 클릭 중첩규제) 100% 통과 유지.

---

## 3. BOOK Language 및 BaseVolume 표준 문법

### 1) 69-page BOOK p.3 Cell Grammar
건축가 오리지널 저작인 69페이지 BOOK의 p.3에 정의된 6대 기본 볼륨(BaseVolume)을 사용합니다:
- **1/1 (whole_cube)**: 1.0 x 1.0 x 1.0, 전체 큐브 기준체
- **3/8 (connected_three_octant_l)**: 2 x 2 x 2 격자 중 3개 옥탄트가 결합된 L자형 볼륨 (단순 슬라이스 방지)
- **1/2 (half_cube)**: 1.0 x 1.0 x 0.5, 수평 분할 기단/매스
- **1/4 (half_section_bar)**: 1.0 x 0.5 x 0.5, 세장한 갤러리 바/캔틸레버 매스
- **1/8 (single_octant)**: 0.5 x 0.5 x 0.5, 단일 큐브 파빌리온
- **1/16 (quarter_section_bar)**: 1.0 x 0.25 x 0.25, 브릿지/필로티/포털 요소

### 2) BaseVolume Affine Normalization Matrix4
- 모든 원시 볼륨은 BaseVolume Matrix4 선형 변환 행렬을 통해 실제 대지의 미터 단위(x, y, z)와 도로 정렬 회전각(theta)으로 사영됩니다.
- 임의의 박스 돌출(Extrude) 대신 
ormalize_affine_basevolume_program()을 거쳐 Canonical UnitBox와의 정합성을 보장합니다.

---

## 4. 대지 안착(Siting) 기하학 및 모서리 절단(Clipping) 방지 원칙

### 1) 전면도로 정렬 로컬 좌표계 (Local-to-Global Alignment)
- 부채꼴 지적 등 비정형 대지에서 남측 도로 접면 벡터의 각도(theta_road ≈ -28.0°)를 기준으로 주동의 주축을 일치시킵니다.
  x_global = cx + (x_local * cos(theta) - y_local * sin(theta))
  y_global = cy + (x_local * sin(theta) + y_local * cos(theta))

### 2) 건축한계선 내부 완충 마진 (>= 1.4m) 및 Overhang 0.00㎡ 원칙
- compile_matrix_form() 시 매스가 건축한계선(buildable)을 0.1m라도 벗어나면 다각형 교차 연산으로 인해 매스 모서리가 사선으로 잘리는(Chamfer) 훼손이 발생합니다.
- 따라서 주동 중심점(cx, cy)과 폭/길이를 사전에 계산하여 대지경계선으로부터 최소 1.4m 이상의 안전 이격을 확보하고, overhang == 0.0000 ㎡를 필수 충족하여 매스의 날카롭고 순수한 비례를 유지합니다.

---

## 5. 건폐율 협의점(Sweet Spot: 28% ~ 35%) 원칙
- **법적 상한(60%) 과밀 방지**: 법정 건폐율을 60%까지 무리하게 채우면 지상 여유가 사라져 답답한 과밀 단지가 됩니다.
- **최적 협의점**:
  - **수평투영 건폐율**: 28.0% ~ 35.0% (대지 2,499.7㎡ 기준 건축면적 694㎡~863㎡)
  - **1층 접지 건폐율**: 15.0% ~ 33.0% (OMA 15.6%, BIG 32.8%, SANAA 32.8%)
  - **지상 오픈스페이스**: 67.0% ~ 84.4% (1,680㎡ ~ 2,110㎡를 시민 광장, 조경 녹지, 법정 주차 P01~P08로 전면 개방)

---

## 6. 3대 건축 거장 정품 매스 조형 원칙

1. **대안 1 : OMA (Rem Koolhaas) - Asymmetric Cantilever Bar & Piloti Undercroft**
   - **조형 언어**: 18m 접지 앵커 코어(후면)와 40m 부유 갤러리 바(전면)의 비대칭 길이 대비.
   - **하부 필로티**: 1.2m×1.2m 메가필로티 기둥 4본 + 14° 경사 V-브레이스로 18m 캔틸레버 지지.
   - **지표**: 지상 건폐율 15.6%, 투영 건폐율 27.8%, 용적률 95.8%, 지상 광장 84.4% 개방, 구조 자립 통과(Stands: True, Cantilever Ratio 0.04).
2. **대안 2 : BIG (Bjarke Ingels) - Continuous Mountain Terrace Loop & Passage**
   - **조형 언어**: 남측 4.5m 진입부에서 8.5m, 12.5m, 북측 16.0m까지 연속 상승하는 30~35% 경사 마운틴 루프(Sloped Wedge Roof).
   - **중정 및 포털**: 18m×12m 중앙 침상 시민중정 + 남측 도로 직결 8m 그랜드 관통 포털.
   - **지표**: 건폐율 32.8%, 용적률 121.6%, 공원 녹지율 67.2%, 정북일조 순응 테라스, 구조 자립 통과(Stands: True).
3. **대안 3 : SANAA (Kazuyo Sejima & Ryue Nishizawa) - Porous Glass Plinth & Shifting Pavilions**
   - **조형 언어**: 38m×23m 경량 투명 유리 기단(Porous Plinth) + 직사일광을 유입시키는 3개 원형 채광 마이크로 중정(Lightwell, Ø 4.5~5.0m).
   - **부유 큐브**: 상부에 독립 회전각(-23° ~ -34°)을 지닌 4개 화이트 큐브 클러스터 배치 및 옥상 정원 테라스 형성.
   - **지표**: 지상 건폐율 32.8%, 투영 건폐율 34.5%, 용적률 105.7%, 잔디 공원 67.2%, 구조 자립 통과(Stands: True).

---

## 7. 크로스 AI 9단계 통합 실행 파이프라인 (The 9-Step Full Flow)

1. **PNU / GIS 지적 수치지형도 연동**: VWorld 지적도 + NGII DEM EL.37.8m 수치지형 표고 취득.
2. **지자체 조례 및 건축법규 엔진**: 제1종일반주거 상한(BCR 60%, FAR 200%), 건축법 제46조(도로후퇴), 제86조(정북일조) 반영.
3. **MasterPlanAgent 대지 및 주차계획**: 남측 도로 -28° 정렬, P01~P08 법정 8면 표준 자주식(2.5m×5.0m) 완비, 330.2㎡ 코어 정착.
4. **BOOK Language & BaseVolume 사영**: BOOK p.3 1/1, 3/8, 1/4 원시 볼륨 + Matrix4 Affine 정규화.
5. **3대 거장 매스 조형 변환**: OMA 비대칭 캔틸레버 / BIG 경사 마운틴 / SANAA 다공성 기단 조형.
6. **건축한계선 검증 & 1.4m 안전 마진**: Overhang 0.00㎡, 무절단 정형 직방체 바 형태 보존.
7. **구조 자립성 & 법규 지표 검증**: Stands == True, 건폐율 28~35% 협의점 달성.
8. **클레이 팔레트 3D 렌더링 & 보드 합성**: style='clay', 테라코타/앰버/그린 2460x3192 고해상도 시트 생성.
9. **웹 인터랙티브 뷰어 서빙 & 피드백**: http://localhost:8089/mass_3_proposals_presentation.html 서빙.
