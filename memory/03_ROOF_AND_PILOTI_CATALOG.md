# Architectural Roof Topologies and Piloti Catalog

본 문서는 MassAgent 기하학 컴파일러에서 네이티브하게 지원 및 검증된 특수 지붕 토폴로지(Gable, Mansard, Butterfly) 및 필로티(Piloti) 하부 구조의 명세서입니다.

---

## 1. 지붕 토폴로지 및 필로티 명세

| 카탈로그 ID | 유형명 | 영문 명칭 | 기하학 파라미터 / 구현 방식 | 건축 법규 및 구조 특성 |
|---|---|---|---|---|
| **01** | **정통 박공 지붕** | **Gable Roof** | `ridge_along='y'`, `top_drop=0.85` | • 용마루 중심 대칭 경사면.<br>• 최상층 다락 및 고천장 공간 확보. |
| **02** | **필로티 하부 개방** | **Piloti Undercroft** | 상부 부유 매스 + 원형 기둥 6본 (`occupiable=False`) | • **건축법 시행령 제119조 제1항 제4호**: 공중 통행/주차용 필로티는 용적률 산정용 연면적에서 제외.<br>• 지상 보행 연속성 및 공공 개방성 극대화. |
| **03** | **망사르드 2단 지붕** | **Mansard Roof** | `top_profile=((0,0.2),(0.25,0.9),(0.75,0.9),(1,0.2))` | • 완경사 상부 + 급경사 하부 2단 꺾임.<br>• 정북방향 일조사선 한계선에 조형적으로 순응. |
| **04** | **버터플라이 V자 지붕** | **Butterfly Roof** | `top_profile=((0,1),(0.5,0.2),(1,1))` | • 중앙 집수형 역경사 V형태.<br>• 빗물 집수 및 양측 상부 천창(High Clerestory) 채광 확보. |

---

## 2. 시각 검증 카탈로그 및 뷰어 연동
- **렌더링 카탈로그**: `ARCHITECTURAL_ROOF_AND_PILOTI_CATALOG.png` (4개 쿼드런트 고해상도 렌더)
- **웹 뷰어 연동**: `http://localhost:8089/mass_3_proposals_presentation.html` (Tab 6 "Roof & Piloti Catalog" 탭 탑재 완료)
