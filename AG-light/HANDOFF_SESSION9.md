# Session 9 HANDOFF — 다음 AI가 바로 이어서 작업

## 이 세션에서 한 것

1. HANDOFF.md 7개 미구현 기능 전부 포팅 (7개 TS 파일)
2. 코드 검토 → 3개 버그 수정 (llm content, ordinance 연결, sigungu 5자리)
3. Vworld WFS 도로 자동 탐지 → Data API로 전환
4. 필지 폴리곤 자동 조회 (`LP_PA_CBND_BUBUN` by PNU)
5. flat services/ → 4개 도메인 폴더 (land/regulation/geometry/law) + barrel export
6. **AG-light Worker 배포** → `https://law-light-api.clickaround8.workers.dev`
7. **AG-frontend Pages 배포** → `https://ag-frontend-5s3.pages.dev`
8. Pages Functions 프록시 (`/arr/*` → Worker)
9. Vworld 해외 IP 이슈 해결 (Referer 헤더)
10. E2E 테스트 성공: "강남구 역삼동 677" → 일반상업, BCR 80%, FAR 1300%, 497m²

## 현재 배포 상태

```
✅ AG-light Worker     https://law-light-api.clickaround8.workers.dev
✅ AG-frontend Pages   https://ag-frontend-5s3.pages.dev
✅ Vectorize Index     law-articles (1536dim, 비어있음)
✅ Secrets             VWORLD_API_KEY, LAW_OC, OPENAI_API_KEY
❌ ARR Backend         미배포 (Dockerfile 작성 완료, Railway 인증 필요)
❌ Vectorize 데이터     build-vectors.ts 실행 필요
❌ Design 게이트웨이     constraint-bridge.ts 작성 필요
```

## 남은 작업 순서

### 작업 1: Railway 로그인 + ARR 배포

Railway CLI 설치됨 (`npm install -g @railway/cli`), 인증만 필요.

```bash
# 1. 로그인 (브라우저 열림)
npx @railway/cli login

# 2. 프로젝트 생성
cd D:\Data\25_ACE\ARR\backend
npx @railway/cli init --name arr-backend

# 3. 배포 (Dockerfile 자동 감지)
npx @railway/cli up

# 4. 환경변수
npx @railway/cli variables set ALLOWED_HOSTS=*.up.railway.app
npx @railway/cli variables set SECRET_KEY=$(openssl rand -hex 32)
npx @railway/cli variables set VWORLD_API_KEY=C3D740E9-C1CC-3DEC-A56D-C6960DF6BD1C
npx @railway/cli variables set DEBUG=False

# 5. 도메인 생성
npx @railway/cli domain

# 6. AG-light Worker에 ARR URL 등록
cd D:\Data\25_ACE\AG-light\worker
echo "https://arr-backend-xxx.up.railway.app" | npx wrangler secret put ARR_BACKEND_URL
```

**Dockerfile** (`ARR/backend/Dockerfile`):
```dockerfile
FROM python:3.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgeos-dev libproj-dev gcc g++
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput 2>/dev/null || true
RUN python manage.py migrate --run-syncdb 2>/dev/null || true
EXPOSE 8000
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "300"]
```

**requirements.txt** (`ARR/backend/requirements.txt`):
```
Django>=6.0,<7.0
channels>=4.0
gunicorn>=23.0
uvicorn>=0.34
httpx>=0.28
httpx-sse>=0.4
openai>=1.50
shapely>=2.0
pyproj>=3.6
scipy>=1.14
numpy>=2.0
whitenoise>=6.7
```

**settings.py 변경**: whitenoise middleware 추가됨 (line 66).

### 작업 2: Vectorize 벡터 채우기

`scripts/build-vectors.ts`에서 dimensions 수정:
- Vectorize 인덱스: 1536 dim (CF 최대)
- build-vectors.ts: `dimensions: 3072` → `1536`으로 수정 필요

```bash
cd D:\Data\25_ACE\AG-light
# build-vectors.ts 수정 후
LAW_OC=hanvit4303 OPENAI_API_KEY=sk-proj-... npx tsx scripts/build-vectors.ts > vectors.ndjson
cd worker
npx wrangler vectorize insert law-articles --file=../vectors.ndjson
```

### 작업 3: Design 게이트웨이

ARR 배포 후 AG-light Worker에 추가:

**1) `regulation/constraint-bridge.ts`** — Python→TS 포팅
- 원본: `ARR/backend/design/services/constraint_bridge.py` (445줄)
- 포팅 범위: `regulationsToConstraints()` + `buildDefaultJobSpec()` + 10종 알고리즘 input builders
- 포팅 불필요: `compute_setback_geometry()` (이미 있음), `build_floor_plan_spec()` (ARR 전용)

**2) `routes/design.ts`** — 새 라우트
```typescript
// POST /design/optimize
// 1. regulations → constraints 변환 (Worker 내부)
// 2. job spec 생성 (Worker 내부)
// 3. fetch(ARR_BACKEND_URL + "/design/jobs/", { method: "POST" })
// 4. SSE 스트림 릴레이 (ReadableStream)

// GET /design/pareto/:id
// → fetch(ARR_BACKEND_URL + "/design/pareto/:id") 프록시
```

**3) `index.ts`** — design route 등록
```typescript
import { designRoutes } from "./routes/design";
app.route("/design", designRoutes);
```

**4) `wrangler.toml`** — Env 타입에 ARR_BACKEND_URL 추가
```typescript
// index.ts
export type Env = {
  VWORLD_API_KEY: string;
  LAW_OC: string;
  OPENAI_API_KEY: string;
  LAW_VECTORS: VectorizeIndex;
  ARR_BACKEND_URL: string;  // 추가
};
```

## 파일 구조 (현재 최종)

```
AG-light/worker/src/           21 TS files, 242KB
├── index.ts                   Env 타입 + Hono 앱
├── land/                      🏗️ 토지
│   ├── index.ts               barrel
│   ├── pnu-resolver.ts        PNU + Vworld geocode (Referer fix)
│   ├── land-api.ts            Data API 4개 (zones+면적+가격+필지폴리곤)
│   ├── road-detector.ts       Data API BBOX → 지목="도" → 도로폭
│   └── zoning-mapper.ts       21 zone
├── regulation/                📋 규제
│   ├── index.ts               barrel
│   ├── calculator.ts          core 11 + 조례
│   ├── calculator-ext.ts      extended 31
│   ├── ordinance.ts           강남구 11680
│   └── llm-extractor.ts      5프롬프트 + enhanceWithLlm
├── geometry/                  📐 규제선
│   ├── index.ts               barrel
│   ├── setback.ts            8종 + 도로폭 차등
│   └── geo-math.ts           투영+법선+클리핑
├── law/                       ⚖️ 법률
│   ├── index.ts               barrel
│   ├── enricher.ts            법제처 API
│   └── vector-search.ts      Vectorize (1536dim)
├── lib/                       외부 (7파일)
├── data/                      JSON (2파일)
└── routes/
    ├── land.ts               자동 파이프라인 (주소→규제→필지→도로→규제선)
    ├── law.ts
    ├── search.ts
    └── health.ts

AG-frontend/
├── dist/                      빌드됨, Pages 배포됨
├── functions/arr/[[path]].ts  Pages Functions 프록시
└── src/                       소스 (수정 없음)

ARR/backend/
├── Dockerfile                 신규
├── requirements.txt           신규
├── .dockerignore              신규
└── backend/settings.py        whitenoise 추가
```

## Cloudflare 계정

- **계정**: clickaround8@gmail.com
- **Account ID**: 2c1b8299e2d8cec3f82a016fa88368aa
- **Worker**: law-light-api
- **Pages**: ag-frontend (ag-frontend-5s3.pages.dev)
- **Vectorize**: law-articles (1536dim)
- **wrangler 인증**: OAuth 토큰 저장됨

## 핵심 E2E 테스트 (검증 완료)

```bash
# 주소 → 규제 전체 (Worker 직접)
curl -X POST https://law-light-api.clickaround8.workers.dev/land/analyze \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-binary '{"input":"서울특별시 강남구 역삼동 677","include_law":false}'

# 응답: PNU + zones(7개) + BCR 80% + FAR 1300% + 면적 497m² + extended 31개

# Pages 프록시 (프론트엔드에서의 호출 패턴)
curl https://ag-frontend-5s3.pages.dev/arr/land/zones
# 응답: 21개 zone

# PNU 직접 + zones 수동 (Vworld 우회)
curl -X POST https://law-light-api.clickaround8.workers.dev/land/analyze \
  -H "Content-Type: application/json" \
  -d '{"input":"1168010100106770000","input_type":"pnu","zones":["제3종일반주거지역"]}'
# 응답: BCR 50% + FAR 300% + 조례 override(인접 1.0m) + extended 31개
```

## 메모리 위치

`D:\DevCache\claude-data\projects\D--Data-25-ACE\memory\ag-light/`:
- `overview.md` — 사용자 시나리오 + 전체 구조
- `session9-porting.md` — Session 9 전체 이력
- `deployment-status.md` — 배포 현황 + URL + 잔여 작업
- `design-gateway.md` — 매스 게이트웨이 아키텍처
- `code-origins.md` — 21파일 원본 매핑
