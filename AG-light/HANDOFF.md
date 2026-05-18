# AG-light HANDOFF — 미구현 7개 기능 완성 가이드

## 1. 프로젝트 개요

AG-light = 건축법규 에이전트 플랫폼. AG/ 4.7GB → 956KB (77 files).

```
AG-light/
├── worker/     Cloudflare Worker (TS, Hono) — 법제처API + 규제계산 + Vectorize
├── server/     Python FastAPI (:8200) — MCP 20도구 + MessageBus + SharedMemory
├── .claude/    하네스 (4 에이전트 + 4 스킬)
├── data/       팀 JSON 19개 + 패턴 14개
└── scripts/    임베딩 빌드
```

**Worker 엔드포인트** (이미 구현):
- `POST /law/search` — 법령명 검색 (법제처 API, 캐시 1h)
- `POST /law/text` — 조문 전문 (JO 코드 변환 포함)
- `POST /law/article` — 항/호/목 상세 (fetchApi + extraParams)
- `POST /law/ordinance` — 자치법규 검색
- `POST /search` — hybrid/keyword/semantic 3모드
- `POST /land/analyze` — 규제 계산 (11개 core)
- `POST /land/resolve` — PNU/주소 해석 (Vworld)
- `GET /land/zones` — 21개 용도지역

**검증 완료**: Worker tsc 0 errors, 법규 21zone 전수 검증 통과, 코드리뷰 5회.

---

## 2. 미구현 7개 — 전부 해야 함

### 구현 순서 (의존 관계)

```
#1 Vectorize 채우기 (독립, 즉시)
#3 Vworld Data API → #7 zones 연동 (순서 의존)
#2 Extended 규제 (독립)
#4 LLM 수치 추출 (독립)
#5 조례 override (독립)
#6 setback 규제선 (독립, 가장 복잡)
```

---

## 3. 각 기능 상세

### #1: Vectorize 벡터 채우기

**문제**: `/search` semantic 모드가 비어있음. "건폐율"로 조문 내용 검색 불가.

**해결**: `scripts/build-vectors.ts` 실행 → 18개 법 조문 임베딩 → Vectorize 업로드.

**실행 명령**:
```bash
wrangler vectorize create law-articles --dimensions=3072 --metric=cosine
LAW_OC=인증키 OPENAI_API_KEY=sk-... npx tsx scripts/build-vectors.ts > vectors.ndjson
wrangler vectorize insert law-articles --file=vectors.ndjson
```

**검증**: `POST /search {"query": "건폐율", "mode": "semantic"}` → 건축법 시행령 §84 결과 확인.

**주의**: `build-vectors.ts`는 korean-law-mcp.fly.dev를 호출 (MCP JSON-RPC). Worker가 배포된 후에는 Worker `/law/text`를 직접 호출하도록 전환 가능. MST 파싱이 텍스트 기반이라 fragile할 수 있음 — 리뷰에서 지적됨.

---

### #2: 31개 Extended 규제 포팅

**원본**: `D:\Data\25_ACE\ARR\backend\land\services\regulation_calculator_ext.py`
**대상**: `worker/src/services/regulation-calculator-ext.ts` (신규)

**구조** (원본 Python):
```python
# Group A (5): Zone-dependent — zoning_limits_extended.json에서 로드
#   용도제한, 접도의무, 대지분할제한, 공개공지(zone별), 내화구조(zone별)

# Group B (10): Scale-dependent — 면적/층수 기준 고정
_SCALE_REGULATIONS = {
    "site_safety":       { rule: "성토·절토 시 옹벽 설치", article: "건축법 §40" },
    "public_open_space": { rule: "연면적 5,000m² 이상", article: "건축법 §43" },
    "on_site_open_space": { rule: "건축선 이격", article: "건축법 §58" },
    "structural_safety": { rule: "구조안전 확인서", article: "건축법 §48" },
    "fire_safety":       { rule: "방화구획", article: "건축법 §49" },
    "energy_efficiency": { rule: "500m² 이상 에너지절약설계", article: "녹색건축법 §14" },
    "barrier_free":      { rule: "장애인편의시설", article: "장애인편의법 §7" },
    "environment_assessment": { rule: "환경영향평가", article: "환경영향평가법 §22" },
    "disaster_prevention": { rule: "재해 예방", article: "자연재해대책법 §12" },
    "development_permit":  { rule: "개발행위허가", article: "국토계획법 §56" },
}

# Group C (16): Text-only — 법조항 참조만
# 소방시설, 주차동선, 우수처리, 오수처리, 전기설비, 통신설비 등
```

**포팅 방법**:
1. `zoning_limits_extended.json` 복사: `ARR/backend/land/data/zoning_limits_extended.json` → `worker/src/data/`
2. Python → TS: 구조가 간단 (JSON lookup + 조건 체크)
3. `routes/land.ts`에서 `/land/analyze` 응답에 `extended_regulations` 필드 추가

**주의**: Group B의 `applies_when` 판단에 면적/층수 정보 필요 → `land_info` (Vworld Data API, #3) 필요.

---

### #3: Vworld Data API 포팅

**원본**: `D:\Data\25_ACE\ARR\backend\land\services\land_api.py` (291줄)
**대상**: `worker/src/services/land-api.ts` (신규)

**3개 API** (모두 `https://api.vworld.kr/ned/data/` base):

| API | 엔드포인트 | 반환 | 필드 |
|-----|----------|------|------|
| getLandUseAttr | `getLandUseAttr?key=&pnu=&format=json` | 용도지역 목록 | `landUses.field[].prposAreaDstrcCodeNm` |
| ladfrlList | `ladfrlList?key=&pnu=&format=json` | 면적(m2), 지목 | `ladfrlVOList.ladfrlVOList[].lndpclAr` / `lndcgrCodeNm` |
| getIndvdLandPriceAttr | `getIndvdLandPriceAttr?key=&pnu=&stdrYear=&format=json` | 공시지가 원/m2 | `indvdLandPrices.field[].pblntfPclnd` |

**핵심 로직** (반드시 유지):
```python
# getLandUseAttr에서 zones 필터링
# cnflcAtNm이 "포함" 또는 "저촉"인 것만 포함 (해당 필지에 적용)
# "접함"은 제외 (인접한 것이지 적용되는 게 아님)
if item.get("cnflcAtNm") not in ("포함", "저촉", None):
    continue

# zone name 정규화
# Vworld가 "일반상업"만 반환할 수 있음 → "일반상업지역"으로 변환
def _normalize_zone_name(name):
    if name.endswith("지역"): return name
    candidate = name + "지역"
    if zoning_mapper.lookup(candidate): return candidate
    return name
```

**공시지가**: 올해 → 작년 fallback.

**반환 형태**:
```json
{
  "success": true,
  "pnu": "1168010100106770003",
  "zones": ["제1종일반주거지역", "제3종일반주거지역"],
  "land_area_m2": 330.5,
  "official_land_price": 5120000,
  "land_use_situation": "대",
  "source": "vworld"
}
```

**환경변수**: `VWORLD_API_KEY` (이미 Worker env에 있음).
**Vworld Data Base URL**: `https://api.vworld.kr/ned/data` (pnu_resolver의 geocode URL과 다름!).

---

### #4: LLM 수치 추출

**원본**:
- `D:\Data\25_ACE\ARR\backend\land\services\law_enricher.py` 의 `extract_regulation_values()` (200~343줄)
- `D:\Data\25_ACE\ARR\backend\land\data\regulation_prompts.py` (프롬프트 정의)

**대상**: `worker/src/services/llm-extractor.ts` (신규)

**흐름**:
```
1. zone_names + regulation_type 입력 (e.g., ["제3종일반주거지역"], "sunlight")
2. Worker /law/search로 관련 조문 텍스트 수집 (상위 3~5개)
3. regulation_prompts의 프롬프트 + 조문 텍스트 → OpenAI gpt-4o-mini
4. JSON 응답 파싱 → regulation_calculator 호환 dict
5. 실패 시 zoning_limits.json fallback (현재 동작 유지)
```

**프롬프트 5종** (regulation_prompts.py에 정의):
| type | 추출 대상 | 프롬프트 |
|------|----------|---------|
| sunlight | 정북 일조사선 거리 | "건축법 시행령 제86조... H<=Xm → Y, H>Xm → H*Z" |
| adjacent_setback | 인접대지 이격거리 | "건축법 제58조... N미터 이상" |
| building_designation | 건축지정선 | "국토계획법 §49-52... 지구단위계획" |
| bcr_far | 건폐율/용적률 | "시행령 §84, §85... 조례 완화 포함" |
| height | 높이제한 | "시행령 §80... N층 이하, Nm 이하" |

**OpenAI 호출** (Workers에서 fetch로 직접):
```typescript
const resp = await fetch("https://api.openai.com/v1/chat/completions", {
  method: "POST",
  headers: { Authorization: `Bearer ${env.OPENAI_API_KEY}`, "Content-Type": "application/json" },
  body: JSON.stringify({
    model: "gpt-4o-mini",
    messages: [{ role: "system", content: SYSTEM_PROMPT }, { role: "user", content: prompt }],
    temperature: 0,
    response_format: { type: "json_object" },
  }),
});
```

**검증 로직** (원본에서 반드시 유지):
```python
# LLM 응답 타입 검증 — LLM이 잘못된 타입 반환 시 reject
for key in ("sunlight_applies",):
    if key in parsed and not isinstance(parsed[key], bool): return None
for key in ("adjacent_setback_m", "bcr_pct", "far_pct"):
    if key in parsed and parsed[key] is not None:
        if not isinstance(parsed[key], (int, float)): return None
```

**regulation-calculator.ts 연동**:
- `_resolve_sunlight()`, `_resolve_adjacent_setback()`, `_resolve_building_designation()`에서 LLM 결과로 override
- 단, `sunlight_applies`는 LLM이 False→True로 뒤집을 수 없음 (zone applicability는 static fact)

---

### #5: 조례 Override

**원본**: `regulation_calculator.py`의 `_apply_ordinance_overrides()` (320~365줄)

**구조**:
```python
# ordinance_overrides/{시군구코드}.json 파일에서 zone별 override 로드
# 1-level merge: zone_data에 override 값 덮어쓰기
def _apply_ordinance_overrides(zones_data, sigungu_code):
    ordinance = _load_ordinance(sigungu_code)  # JSON file
    overrides = ordinance.get("overrides", {})
    for z in zones_data:
        if z["zone_name"] in overrides:
            merged = {**z, **overrides[z["zone_name"]]}  # shallow merge
```

**AG-light에서의 접근**:
- `worker/src/data/ordinance_overrides/` 디렉토리에 JSON 파일 → Workers에선 static import 어려움
- **대안**: `/law/ordinance`로 조례 텍스트 검색 → LLM (#4)로 수치 추출 → override
- 또는 KV에 조례 데이터 저장 → lookup

**현재**: `regulation-calculator.ts`의 `_sigunguCode` 파라미터는 받지만 사용 안 함 (의도적).

---

### #6: Setback 규제선 (가장 복잡)

**원본**: `D:\Data\25_ACE\ARR\backend\land\services\setback_geometry.py` (~800줄, Shapely)
**대상**: `worker/src/services/setback-geometry.ts` (신규)

**7종 규제선**:
| 규제선 | 로직 | Shapely 함수 |
|--------|------|-------------|
| 건축선 | 도로경계선에서 후퇴 | `parallel_offset()`, `intersection()` |
| 인접대지 이격 | 경계선에서 N미터 내측 | `buffer(-N)` |
| 정북일조 4단계 | 10/20/30/40m 높이별 사선 | `LineString`, `intersection()` |
| 채광사선 | 인동간격 H*2 (공동주택) | `parallel_offset()` |
| 가각전제 | 교차로 모서리 컷 | `shared_vertex`, `arc()` |
| 인동간격 | 건물간 최소 이격 | `distance()` |
| 건축지정선 | 지구단위계획 지정 | `parallel_offset()` |

**TS 포팅 방법**: Shapely → `@turf/turf` (npm)

| Shapely | Turf.js |
|---------|---------|
| `Polygon.buffer(-N)` | `turf.buffer(polygon, -N, {units: 'meters'})` |
| `parallel_offset(line, d)` | `turf.lineOffset(line, d, {units: 'meters'})` |
| `line.intersection(polygon)` | `turf.lineIntersect(line, polygon)` 또는 `turf.booleanIntersects` |
| `unary_union()` | `turf.union()` |
| `shapely.affinity.rotate()` | `turf.transformRotate()` |

**주의사항** (리뷰에서 확인된 것):
- 정북일조 4단계: 필지 클리핑 필수 (`line.intersection(parcel_utm)`)
- 3D depth 클리핑: `min(parcel_span*0.4, 30m)`
- 가각전제: 교차각별 차등 (90°미만→3~4m, 90~120°→2~3m, 120°이상→불필요)
- 도로사선: **삭제됨** (multiplier=null, 시행령 §82 개정)

**GeoJSON 출력 형태**:
```json
{
  "type": "FeatureCollection",
  "features": [
    { "type": "Feature", "geometry": { "type": "LineString", "coordinates": [...] },
      "properties": { "type": "building_line", "setback_m": 2.0, "article": "건축법 §46" } },
    { "type": "Feature", "geometry": { "type": "Polygon", "coordinates": [...] },
      "properties": { "type": "sunlight_10m", "height_m": 10, "setback_m": 1.5 } }
  ]
}
```

---

### #7: Zones 자동 연동

**원본 위치**: `ARR/backend/land/views.py` 131-135줄
**대상**: `worker/src/routes/land.ts` 수정

**현재 문제**: 주소만 주면 `resolvedZones`가 비어있어서 규제 계산 불가.

**수정 (간단)**:
```typescript
// land.ts의 POST /land/analyze에서
// PNU 해석 후, zones가 비어있으면 Vworld Data API 호출
if (resolvedZones.length === 0 && pnuData?.pnu) {
  const landInfo = await getLandUseInfo(pnuData.pnu, c.env.VWORLD_API_KEY);
  if (landInfo.success && landInfo.zones.length > 0) {
    resolvedZones = landInfo.zones;
  }
}
```

**#3 (Vworld Data API) 완료 후에만 가능.**

---

## 4. 공통 주의사항

- **Worker는 Cloudflare Workers 런타임**: Node.js API 사용 불가 (fs, path, process.env 불가). fetch(), AbortSignal.timeout() 사용.
- **환경변수**: `LAW_OC`, `VWORLD_API_KEY`, `OPENAI_API_KEY` — 모두 `wrangler secret put`으로 설정.
- **원본 Python 파일 위치**: `D:\Data\25_ACE\ARR\backend\land\services\` (규제 관련), `D:\Data\25_ACE\ARR\backend\land\data\` (JSON 데이터)
- **코드 복사 원칙**: 원본 그대로 가져오고 Workers 비호환만 최소 수정. 간소화하면 리뷰에서 걸림.
- **테스트**: 포팅 후 기존 Python 테스트의 assertion 값으로 TS에서도 검증 (`ARR/backend/land/tests.py` 128 tests)
- **`@turf/turf`**: setback용. `npm install @turf/turf` 필요 (worker/package.json에 추가)

## 5. 검증 기준

모든 7개 완료 후 E2E:
```
입력: "강남구 역삼동 677"
  → PNU 자동 해석 (Vworld geocode)
  → 용도지역 자동 조회 (#3+#7: Vworld getLandUseAttr)
  → BCR=60%, FAR=200% (core 11개)
  → extended 31개 규제 (#2)
  → LLM 수치 추출 (#4: 조문에서 정밀값)
  → 조례 override (#5: 강남구 조례)
  → setback 규제선 GeoJSON (#6: 7종)
  → /search "건폐율" → 시행령 §84 (#1: Vectorize)
```

## 6. 메모리

`D:\DevCache\claude-data\projects\D--Data-25-ACE\memory\ag-light\`:
- `overview.md` — 전체 구조
- `code-reviews.md` — 5회 리뷰 이력
- `code-origins.md` — 파일 출처 매핑
- `korean-law-mcp-integration.md` — lib 흡수 상세

## 7. 실행

```bash
# Worker 로컬 실행
cd worker && npm install && npm run dev  # localhost:8787

# Server 로컬 실행
cd server && pip install -r requirements.txt && uvicorn main:app --port 8200

# 배포
npm run deploy:all
```
