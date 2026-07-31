# ACE — AI Coordination Ecosystem | Portfolio

---

## 포트폴리오 구성 가이드 (리서치 기반)

### 개발자 포트폴리오 필수 항목 (2026 기준)
1. **Problem → Solution** 스토리 (WHY 1p → HOW 2-3p → WHAT 1p)
2. **아키텍처 다이어그램** — 데이터 흐름, 서비스 간 통신 시각화
3. **기술 스택** — 카테고리별 로고 + 버전 + 선택 이유
4. **트러블슈팅** — 문제 해결 과정 (필수!)
5. **수치/성과** — 응답시간, 테스트 수, 노드 수 등 정량 지표
6. **라이브 데모** — 배포 URL + 스크린샷/GIF
7. **코드 접근** — GitHub 레포 또는 핵심 코드 스니펫

### PM 포트폴리오 추가 항목
1. **WHY** — 왜 이 프로젝트를 시작했는가 (시장/사용자 문제)
2. **의사결정** — 기술 선택의 근거, 트레이드오프
3. **프로젝트 수** — 3개 정도가 적당 (너무 많으면 집중 안 됨)
4. **임팩트** — Before/After 비교, 정량 효과

### 나노바나나 2 프롬프트 작성 팁
- `<피사체> <동작> <장면>의 <이미지를 생성>` 기본 공식
- 최대한 구체적으로: 구도, 스타일, 비율, 색상 명시
- 다이어그램/인포그래픽 생성 가능 (정확한 정보 포함)
- 한국어 프롬프트 지원

---

## 1. Problem & Solution — 왜 만들었는가

### 문제
건축사가 토지 규제를 분석하려면:
- 국가법령정보센터에서 **20개 법률** 수동 검색
- 용도지역별 건폐율/용적률 **수작업 대조**
- 일조사선/가각전제/이격거리 **수기 계산**
- **250개 시군구** 조례까지 확인
- **1건에 2~3시간**, 법조문 200개 이상 검토

### 해결
**주소 하나 → 3초 → 42개 규제 + 8종 규제선 + 170개 법조항 자동 분석**

### 핵심 차별점
- 단순 데이터 조회가 아닌 **법률 해석 + 기하 계산 + AI 추출**의 결합
- 20개 법률 31,126개 노드 그래프에서 **하이브리드 시맨틱 검색**
- 규제 수치를 3D 지도 위에 **실시간 시각화**
- 규제 범위 안에서 **유전 알고리즘 매스 최적화** 연계

---

## 2. Architecture — 시스템 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    사용자 (브라우저)                          │
│         ARR Frontend (CF Pages)  /  AG-frontend (CF Pages)  │
└─────────┬──────────────────────────────────┬────────────────┘
          │                                  │
          ▼                                  ▼
┌──────────────────┐              ┌───────────────────────┐
│  AG-light Worker │              │  ARR Django Backend   │
│  (CF Workers)    │              │  (Railway)            │
│  242KB, 0ms cold │              │                       │
│                  │              │  - 토지 규제 분석     │
│  - 법제처 API    │◄────────────►│  - 매스 최적화 (GA)   │
│  - Jina 임베딩   │  law search  │  - 규제선 기하 계산   │
│  - Vectorize     │              │  - Vworld API 프록시  │
│  - LLM 추출     │              │  - SSE 스트리밍       │
└──────────────────┘              └───────────┬───────────┘
                                              │
                                    ┌─────────▼─────────┐
                                    │  Neo4j Graph DB   │
                                    │  20법 58법령      │
                                    │  31,126 노드      │
                                    │  12,069 임베딩    │
                                    │  7-stage search   │
                                    └───────────────────┘
```

### 서비스 토폴로지
| 서비스 | 플랫폼 | 역할 |
|--------|--------|------|
| ARR Frontend | CF Pages | Law+Land+Design UI, 3D Vworld 지도 |
| AG-frontend | CF Pages | SaaS UI (에이전트 빌더, 플레이그라운드) |
| AG-light Worker | CF Workers (242KB) | 유일한 public API, 법제처+Vectorize |
| ARR Backend | Railway | Django, 규제계산+GA+기하+프록시 |
| Neo4j | 로컬/Aura | 법률 그래프 DB, 벡터 인덱스 |
| Vectorize | CF Vectorize | 2,051 벡터 (Jina v3, 1024-dim) |

---

## 3. Tech Stack — 기술 스택

### Frontend
| 기술 | 버전 | 선택 이유 |
|------|------|-----------|
| React | 19.2 | 최신 Concurrent Mode + Server Components 지원 |
| TypeScript | 5.9 | erasableSyntaxOnly, 타입 안전성 |
| Vite | 7.2 | 3초 빌드, HMR, proxy 설정 간편 |
| Tailwind | 4.1 | v4 새 엔진, 시맨틱 토큰 |
| Zustand | 5.0 | Redux 대비 보일러플레이트 90% 감소 |
| OpenLayers | 10.8 | Vworld 2D 타일 + WMS 지적도 |
| Cesium (Vworld 3D) | WebGL 3.0 | 3D 건물 + 규제선 ground-clamp |
| Playwright | 1.58 | E2E 235 tests, 31초 완주 |

### Backend
| 기술 | 버전 | 선택 이유 |
|------|------|-----------|
| Django | 6.0 | 빠른 프로토타이핑, ORM, admin |
| Python | 3.13 | 최신 성능 개선 |
| Shapely | 2.0 | 규제선 polygon 클리핑/버퍼/PIP |
| PyProj | 3.6 | WGS84↔UTM 투영 (일조사선 정밀 계산) |
| SciPy | 1.14 | NSGA-II 다목적 유전 알고리즘 |

### AI/ML
| 기술 | 용도 |
|------|------|
| OpenAI text-embedding-3-large (3072d) | Neo4j 법조항 벡터 임베딩 |
| Jina jina-embeddings-v3 (1024d) | Worker 실시간 의미 검색 |
| GPT-4o-mini | 조례 수치 LLM 추출 (3-tier) |
| AutoGen Studio | 6-agent SelectorGroupChat |
| NSGA-II | 10종 매스 × 다목적 최적화 |

### Infrastructure
| 기술 | 선택 이유 |
|------|-----------|
| CF Workers | 엣지 배포, 0ms cold start, 242KB |
| CF Vectorize | 서버리스 벡터 DB, Workers 바인딩 |
| Railway | Django + scipy 무중단 배포 |
| Neo4j | 법률 계층 그래프 (JO→HANG→HO→MOK) |

### 프로토콜
| 프로토콜 | 용도 |
|----------|------|
| A2A (Google/LF) | 에이전트 간 JSON-RPC 2.0 통신 |
| MCP (Anthropic) | 57개 도구 통합 |
| SSE | 실시간 분석 진행률 6단계 |
| WebSocket | AutoGen 에이전트 실행 스트림 |

---

## 4. Data Flow — 데이터 흐름 (7단계)

```
① 주소 입력: "강남구 역삼동 677"
   ↓
② Vworld Geocoding → 좌표 + PNU 자동 추출
   ↓
③ 병렬 조회 (Vworld Data API ×4)
   ├── 용도지역 → ["일반상업지역"]
   ├── 면적 330.5m², 지목 대
   ├── 공시지가 5,120,000원/m²
   └── 필지 폴리곤 GeoJSON
   ↓
④ 규제 계산 (3-tier override)
   ├── Static: 국법 21 zone → BCR 80%, FAR 1300%
   ├── Ordinance: 시군구 조례 override
   └── LLM: 법조항에서 수치 추출 (GPT-4o-mini)
   ↓
⑤ 법조항 매칭 (Hybrid Search)
   ├── Vectorize 의미검색 (Jina)
   ├── Neo4j 키워드+벡터+PageRank
   └── RRF 병합 → 170건
   ↓
⑥ 규제선 기하 계산
   ├── 정북일조 4단계 (UTM 투영 + 법선 벡터)
   ├── 건축가능영역 (inward buffer)
   ├── 가각전제 (corner clip)
   └── 3D 일조사선 경사면 (Wall entity)
   ↓
⑦ 3D 시각화 + GA 매스 최적화
   ├── Cesium 규제선 ground-clamp
   ├── 10종 알고리즘 × NSGA-II
   └── Pareto front 결과
```

---

## 5. Troubleshooting — 문제 해결 사례

### 5.1 법제처 API 불안정 (522/525)
**문제**: law.go.kr API가 간헐적 다운 → 조문 조회 실패
**해결**: 3중 fallback 구조
1. Neo4j (로컬, 항상 가용)
2. AG-light Worker (Vectorize 의미검색)
3. 법제처 API (최종 fallback)

### 5.2 Vectorize ID ↔ Neo4j full_id 불일치
**문제**: Worker 검색 결과 ID(`건축법_제60조`)와 Neo4j ID(`건축법(법률)::제6장::제60조::1`) 형식 불일치 → 조문 상세 400 에러
**해결**: Django에서 자동 매핑 함수 구현 — 법명+조번호 추출 → Neo4j JO 검색 (법률>시행령>시행규칙 우선순위)

### 5.3 Vworld 3D 위성→다이어그램 전환
**문제**: Vworld 3D SDK에 basemap 변경 API 없음
**해결**: Cesium imagery provider 직접 교체 — `ws3dInitCallBack`에서 `removeAll()` + `UrlTemplateImageryProvider(Vworld Base 타일)` 추가

### 5.4 일조사선 2023 개정 반영
**문제**: 건축법 시행령 제86조 2023.9.12 개정 — 기존 9m → 10m 기준 변경
**해결**: `setback_geometry.py`에서 H≤10m → 1.5m, H>10m → H×0.5 정확 구현. 전용/일반주거만 적용, 준주거/상업/공업 제외.

---

## 6. Key Metrics — 주요 지표

| 지표 | 수치 |
|------|------|
| 법률 수 | 20개 (58 법령) |
| Neo4j 노드 | 31,126개 |
| 벡터 임베딩 | 12,069 + 2,051 |
| 규제 항목 | 42개 (11 core + 31 ext) |
| 중첩지역 유형 | 30+ |
| 규제선 | 8종 (2D + 3D) |
| 매스 알고리즘 | 10종 |
| MCP 도구 | 57개 |
| E2E 테스트 | 235개 |
| 단위 테스트 | 93개 (land) |
| 응답 시간 | ~3초 |
| Worker 크기 | 242KB (gzip 47KB) |
| 분석→규제선 | 실시간 3D 렌더링 |

---

## 7. Live Demo

| 서비스 | URL |
|--------|-----|
| ARR Frontend (Law+Land+Design) | https://arr-frontend.pages.dev |
| AG-frontend (SaaS) | https://ag-frontend-5s3.pages.dev |
| AG-light Worker API | https://law-light-api.clickaround8.workers.dev/health |

---

## 8. 나노바나나 2 (Gemini) 이미지 프롬프트

### Prompt 1: 히어로 이미지 (메인 배너)
```
어두운 네이비(#0a0a12) 배경의 미래지향적 대시보드 UI.
서울 도심 3D 건물 모델 위에 홀로그램처럼 규제선이 투영되어 있다.
초록색 점선은 건축가능영역, 빨간색 그라데이션 선은 일조사선 4단계(10m, 20m, 30m, 40m),
파란색 선은 도로 건축선. 왼쪽에 유리모피즘 사이드바가 있고
"건폐율 80%" "용적률 1300%" 숫자가 크게 표시. 시안(#22d3ee)과 에메랄드(#34d399)
발광 악센트. 항공 시점, 포토리얼리스틱 3D 렌더링.
가로세로 비율 21:9, 4K 해상도.
```

### Prompt 2: 시스템 아키텍처 다이어그램
```
깔끔한 테크니컬 아키텍처 다이어그램. 어두운 배경.
상단: 브라우저 아이콘 (React 로고 포함).
왼쪽: 육각형 "CF Workers" 노드 (시안 발광, "242KB" 라벨).
오른쪽: 둥근 "Django" 노드 (에메랄드 발광, "Railway" 라벨).
하단: 원형 "Neo4j" 데이터베이스 노드 (보라 발광, "31K nodes" 라벨).
노드 사이를 연결하는 화살표에 "law search", "land analyze", "3D map" 라벨.
미니멀 플랫 디자인, 고급스러운 어두운 테마. 가로세로 16:9.
```

### Prompt 3: 데이터 파이프라인 흐름도
```
왼쪽에서 오른쪽으로 흐르는 수평 파이프라인 다이어그램.
1단계: 검색바에 "강남구 역삼동 677" 한국어 주소 입력.
2단계: 지오코딩 아이콘 (지구본+핀).
3단계: 병렬 API 호출 4갈래 화살표 (용도지역, 면적, 공시지가, 폴리곤).
4단계: 법률 책 아이콘 + "42개 규제" 계산.
5단계: 3D 지도 위에 색깔 규제선 오버레이 결과.
각 단계는 유리 카드, 1~5 번호 표시, 진행 인디케이터.
아이소메트릭 시점. 어두운 테마, 모던 SaaS 일러스트레이션 스타일.
가로세로 21:9.
```

### Prompt 4: 법률 그래프 네트워크
```
어두운 배경에 포스-다이렉티드 그래프 시각화.
중앙 큰 노드 "건축법" (파란색).
5개 위성 클러스터: 주황 "주차장법", 빨강 "소방시설법",
초록 "국토계획법", 보라 "장애인편의법", 노랑 "경관법".
각 클러스터에서 작은 노드들이 가지치기 (조, 항, 호 계층).
엣지는 클러스터 색상으로 발광. "31,126 nodes" 숫자 크게 표시.
Neo4j 그래프 시각화 스타일, 다크 모드. 정사각형 1:1.
```

### Prompt 5: 3D 규제선 시각화 (건축 도면 스타일)
```
조감도 시점의 3D 도시 블록 모델.
중앙에 하이라이트된 건축 필지 위에 규제선이 오버레이.
초록 점선: 건축가능영역 경계. 빨간 그라데이션 4줄: 정북일조
사선 (10m, 20m, 30m, 40m 거리 표기). 주황 선: 인접대지 이격.
파란 선: 도로 건축선. 노란 삼각형 컷오프: 가각전제.
측정 주석(한국어)이 달린 깔끔한 다이어그램 스타일.
어두운 배경, 건축 시각화 퀄리티. 가로세로 16:9.
```

### Prompt 6: Before/After 비교
```
좌우 분할 화면.
왼쪽 (붉은 톤, 라벨 "기존 2~3시간"):
건축사가 책상에서 법률 서적 더미, 여러 브라우저 탭, 계산기,
한국어 법률 문서 종이에 둘러싸여 지친 표정.
오른쪽 (초록 톤, 라벨 "자동 3초"):
같은 건축사가 깔끔한 다크 대시보드 앞에서 미소.
화면에 "42개 규제 분석 완료" 3D 지도와 색깔 규제선 표시.
모던 일러스트레이션, 깔끔한 벡터 아트 스타일. 가로세로 16:9.
```

### Prompt 7: 기술 스택 그리드
```
어두운 그리드 레이아웃에 기술 로고 배치. 4행.
1행 (Frontend): React, TypeScript, Vite, Tailwind CSS, Three.js 아이콘.
2행 (Backend): Django, Python, Neo4j, OpenAI 아이콘.
3행 (Infrastructure): Cloudflare, Railway, Vectorize 아이콘.
4행 (Protocol): A2A, MCP, SSE, WebSocket 텍스트 뱃지.
각 아이콘은 브랜드 색상으로 은은한 발광 효과.
네이비 배경, 그리드 라인. 깔끔하고 프로페셔널. 가로세로 16:9.
```

### Prompt 8: 멀티에이전트 팀 (6 에이전트)
```
6개 AI 에이전트 아이콘이 원형으로 배치.
각각 역할 라벨: "토지 분석", "법규 검색", "규제 계산",
"기하 계산", "LLM 추출", "결과 종합".
중앙에 발광하는 오케스트레이터 노드 (SelectorGroupChat).
연결선이 데이터 흐름으로 펄스. 각 에이전트는 서로 다른
색상 아바타 (시안, 에메랄드, 앰버, 보라, 빨강, 파랑).
어두운 미래지향적 테마, 홀로그램 효과.
모던 AI 제품 일러스트레이션 스타일. 정사각형 1:1.
```
