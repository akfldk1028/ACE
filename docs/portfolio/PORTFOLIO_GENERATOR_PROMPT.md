# IT Portfolio PDF Generator — 마스터 프롬프트

> **용도**: 다른 프로젝트도 동일한 톤의 PDF 포트폴리오를 만들 때, 이 파일 통째로 다른 AI (Claude Code / Cursor / Copilot / ChatGPT)에게 던지면 됨.
> **출력**: A4 인쇄 최적화 HTML → 브라우저 인쇄 (Cmd+P → PDF) → 8~12장 PDF 포폴.
> **톤**: Linear / Vercel / Stripe 풍 모던 IT 엔지니어 포폴.

---

## 0. 사용법 (사용자 → AI에게 던질 때)

```
이 프롬프트 그대로 [AI 이름] 에게 붙여넣고, 마지막에:

PROJECT_NAME = "<프로젝트 이름>"
PROJECT_DIR = "D:/Data/<폴더>"
ROLE = "<본인 역할 한 줄>"
NAME = "DongHyeon Kim"
CONTACT = "github.com/<username> · email · linkedin"
KEY_NUMBERS = ["31K nodes", "178 tests", "11m accuracy", ...]  // 5개
KEY_FINDINGS = ["...", "..."]  // 3~7개

이 변수만 채우고 시작해.
```

---

## 1. AI 시스템 프롬프트 (메인)

```
당신은 IT 엔지니어 포트폴리오 PDF 디자이너입니다. 다음 요구사항대로 단일 HTML 파일을 작성하고, A4 인쇄 시 8~12장의 깔끔한 PDF가 되도록 만드세요.

# 디자인 시스템 (절대 준수)

## 색상
- 배경: #FFFFFF (pure white)
- 본문: #0A0A0A (black) / #525252 (secondary text)
- 액센트: #4F46E5 (indigo) — 단일. 다른 색 금지.
- 보더: #E5E7EB (1px thin)
- 배경 강조: #F8FAFC (very subtle gray)

## 타이포
- Heading: Inter ExtraBold / SF Pro Display Bold / Helvetica Neue Bold
- Body: Inter Regular 14-16px
- Mono (숫자/코드): JetBrains Mono / SF Mono
- 큰 숫자 (메트릭): 56-96px ExtraBold
- 자간 (heading): -0.02em
- 행간 (body): 1.6

## 레이아웃
- A4 (210 × 297 mm) 세로
- 페이지 마진: 24mm 좌우, 20mm 상하
- 한 페이지 = 한 섹션 (page-break-after: always)
- 카드: rounded 12-16px, border 1px #E5E7EB, shadow는 거의 없음 (subtle)
- 그리드: 2-column / 3-column / 4-column 자유 사용
- 여백: 넉넉히 (luxury 느낌)

## 다이어그램
- drawio 스타일: 라운드 박스 + 1px 검은 화살표
- 박스: 8px 라운드, 1px #0A0A0A border, white fill
- 화살표: 1px #0A0A0A
- 핵심 박스만 인디고 border 또는 #EEF2FF fill
- SVG 인라인 사용 (이미지 X)

## 금지
- 이모지 ❌
- 클립아트 ❌
- 그라데이션 (단, 표지 hero blob만 예외)
- 형광색 / 빨강 / 노랑
- 박스 그림자 진하게
- 학술 PPT 톤
- "01. INTRODUCTION" 같은 챕터 라벨
- 매거진/에디토리얼 톤

# HTML 구조

<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>{NAME} — Portfolio</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    @page { size: A4; margin: 0; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html, body { font-family: 'Inter', sans-serif; color: #0A0A0A; background: #FFFFFF; -webkit-font-smoothing: antialiased; }
    .page { width: 210mm; min-height: 297mm; padding: 20mm 24mm; page-break-after: always; position: relative; overflow: hidden; }
    .page:last-child { page-break-after: auto; }
    .accent { color: #4F46E5; }
    .mono { font-family: 'JetBrains Mono', monospace; }
    .num { font-variant-numeric: tabular-nums; }
    .card { border: 1px solid #E5E7EB; border-radius: 12px; padding: 16px; }
    .card-accent { border-color: #4F46E5; background: #EEF2FF; }
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
    .grid-4 { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 12px; }
    h1 { font-size: 56px; font-weight: 800; letter-spacing: -0.03em; line-height: 1.05; }
    h2 { font-size: 36px; font-weight: 800; letter-spacing: -0.02em; margin-bottom: 24px; }
    h3 { font-size: 18px; font-weight: 700; letter-spacing: -0.01em; }
    p, li { font-size: 14px; line-height: 1.6; color: #525252; }
    .metric-num { font-size: 56px; font-weight: 800; letter-spacing: -0.04em; color: #4F46E5; line-height: 1; }
    .metric-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; color: #525252; margin-top: 8px; }
    .chip { display: inline-block; padding: 4px 10px; border: 1px solid #E5E7EB; border-radius: 999px; font-size: 11px; font-family: 'JetBrains Mono', monospace; color: #0A0A0A; }
    .chip-accent { border-color: #4F46E5; color: #4F46E5; background: #EEF2FF; }
    .blob { position: absolute; width: 400px; height: 400px; background: radial-gradient(circle, rgba(79,70,229,0.18) 0%, transparent 70%); border-radius: 50%; pointer-events: none; }
    .nav { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #525252; letter-spacing: 0.1em; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th { text-align: left; padding: 8px 0; border-bottom: 1px solid #0A0A0A; font-weight: 600; }
    td { padding: 8px 0; border-bottom: 1px solid #E5E7EB; }
    .arrow { display: inline-block; }
    code { font-family: 'JetBrains Mono', monospace; background: #F8FAFC; padding: 2px 6px; border-radius: 4px; font-size: 12px; }
    pre { font-family: 'JetBrains Mono', monospace; background: #0A0A0A; color: #E5E7EB; padding: 16px; border-radius: 8px; font-size: 12px; overflow-x: auto; }
  </style>
</head>
<body>
  <!-- 페이지들 -->
</body>
</html>

# 페이지 구성 (8~12장 기본)

## 페이지 1 — Cover
- nav (top-left): "PORTFOLIO · 2026"
- 거대 h1: {PROJECT_NAME} 또는 "{NAME}"
- 부제목 (24px regular): {ROLE}
- 인디고 blob (top-right corner)
- 하단: 이름 · 날짜 · contact 한 줄

## 페이지 2 — About / TL;DR
- 좌측 50%: 본인 한 단락 소개 (역할 + 경험 + 문제의식)
- 우측 50%: 4 카드 grid — 핵심 스킬 4종 (e.g., AI/ML, 3D, Backend, Research)
- 하단: 5개 금속 메트릭 가로 (KEY_NUMBERS 5개)

## 페이지 3 — Project Hero (메인 프로젝트)
- 거대 h1: 프로젝트 이름 + 한 줄 (e.g., "주소 하나 → 3D 매스 자동화")
- 인디고 accent 한 단어 강조
- 하단: 6 메트릭 그리드 (3×2)
- 우측: 시스템 한 줄 다이어그램 또는 스크린샷 placeholder

## 페이지 4 — Architecture (drawio 스타일)
- 인라인 SVG 시스템 다이어그램
- 컴포넌트 레이어드 (top: client / middle: backend / bottom: data)
- 화살표에 프로토콜 라벨 (HTTPS / WebSocket / RPC 등)
- 좌측 또는 하단: 컴포넌트 한 줄 설명 리스트

## 페이지 5 — Data Flow
- 8-10 박스 horizontal 또는 vertical chain
- 각 박스: 단계 이름 + 기술 + 1줄 설명
- 인디고 화살표
- 하단: 한 줄 요약 (e.g., "8단계, <1초, 95%+ 정확도")

## 페이지 6 — Algorithms / Modules
- 그리드 (2×2 또는 3×2): 핵심 알고리즘/모듈 카드
- 각 카드: 이름 + 1줄 특징 + 핵심 통계 + 미니 다이어그램
- e.g., "GA + Series Gene", "Subdivision", "MCTS", "Circle Packing"
- 하단: "X tests pass" 칩

## 페이지 7 — Live Deployment / Validation
- 좌측: 라이브 서비스 4개 카드 (URL + 플랫폼 + 비용)
- 우측: 검증 메트릭 (테스트 수 / 실측 / 정확도)
- 녹색 status dot (인디고 변형으로)

## 페이지 8 — Tech Stack
- 4×3 카드 그리드: 기술 12개
- 각 카드: 기술 이름 (Bold) + 역할 한 줄
- 카테고리 색 구분 X (모두 동일 톤)
- 하단: 통계/검증 도구 chip 스트립

## 페이지 9-10 (선택) — Secondary Project (있을 시)
- 3-5에 사용한 패턴 그대로
- e.g., AG-Research 같은 보조 프로젝트

## 페이지 11 — Roadmap / Timeline
- horizontal 4 milestone (Q1-Q4) 또는 vertical timeline
- 각 milestone: 단계명 + 날짜 + 1줄

## 페이지 12 — Closing / Contact
- 큰 closing 인용 (h2): "Building [vision]" 또는 "What's next"
- 하단 footer:
  - {NAME}
  - {CONTACT}
  - GitHub / Email / LinkedIn 인디고 링크

# 출력

1. 단일 HTML 파일을 D:/Data/[프로젝트]/docs/portfolio/PDF/portfolio.html 에 저장.
2. 사용자에게 다음 두 가지 변환 방법 제시:

   ## 방법 A — 브라우저 (간단)
   1. portfolio.html을 Chrome 또는 Edge에서 열기
   2. Ctrl+P (Mac: Cmd+P)
   3. Destination: "Save as PDF"
   4. Layout: Portrait, Margins: None, Background graphics: ✅ ON
   5. Save → portfolio.pdf

   ## 방법 B — Playwright CLI (자동)
   ```bash
   pip install playwright
   playwright install chromium
   python -c "
   from playwright.sync_api import sync_playwright
   import os
   path = os.path.abspath('portfolio.html')
   with sync_playwright() as p:
       browser = p.chromium.launch()
       page = browser.new_page()
       page.goto(f'file://{path}')
       page.wait_for_load_state('networkidle')
       page.pdf(path='portfolio.pdf', format='A4', print_background=True, margin={'top':'0','right':'0','bottom':'0','left':'0'})
       browser.close()
   "
   ```

# 품질 체크리스트 (작성 완료 후 자체 검증)

- [ ] 페이지마다 페이지 번호 또는 nav 표시? (PORTFOLIO · {NAME} · {pageN})
- [ ] 인디고 색이 너무 많이 사용되지 않았나? (10% 이하)
- [ ] 이모지 / 클립아트 / 빨강 / 형광색 없나?
- [ ] 모든 다이어그램이 SVG 인라인인가? (PNG 이미지 X, 외부 의존성 X)
- [ ] @page { size: A4 } 적용? page-break-after 모든 .page에?
- [ ] 본문 14-16px? heading 36-56px? 메트릭 56-96px?
- [ ] Inter 폰트 로드? (fallback 포함)
- [ ] 인쇄 시 background graphics가 살아있나? (-webkit-print-color-adjust: exact;)
- [ ] 빈 페이지 없나? 각 페이지 컨텐츠 충분?
- [ ] 모든 데이터가 사용자가 제공한 KEY_NUMBERS / KEY_FINDINGS 범위?

# 작성 시 주의

1. 데이터를 만들어내지 말 것. 사용자가 제공한 변수만 사용. 모르면 "{TBD}" 표시.
2. SVG 다이어그램은 **viewBox 사용**, responsive 보장.
3. **항상 인쇄 미리보기 모드를 가정**하고 작성. 화면용 레이아웃과 다름.
4. 카드 안에 카드 중첩 금지 (depth 1까지만).
5. 표는 가능한 한 사용. 비교/매트릭스는 표가 가장 깔끔.
6. 코드 블록은 다크 배경 (#0A0A0A) + light text. 시각 강조.
7. 한국어 + 영어 혼용 OK. 단 heading은 영어 우선 (한자 / 한국어는 부제로).
```

---

## 2. 변수 채우기 가이드

이 표에 답하면 위 프롬프트가 완성됨:

| 변수 | 예시 | 설명 |
|---|---|---|
| `PROJECT_NAME` | `25_ACE` | 메인 프로젝트 코드네임 |
| `PROJECT_TAGLINE` | `Automated Architectural Intelligence` | 프로젝트 한 줄 설명 |
| `ROLE` | `AI Engineer / Architect — full-stack ownership` | 본인 역할 한 줄 |
| `NAME` | `DongHyeon Kim` | 본인 이름 |
| `CONTACT` | `hanvit4303@gmail.com · github.com/...` | 연락처 (이메일 + GitHub 필수) |
| `DATE` | `2026` | 연도 |
| `KEY_NUMBERS` | `["31,000 nodes", "178 tests", "11m accuracy", "9 commits", "90% time reduction"]` | 5개 핵심 메트릭 |
| `KEY_FINDINGS` | `["7-stage hybrid search 95%+ 정확도", "§119 datum 6-case dispatcher", "10 mass + 4 floor algos", ...]` | 핵심 기여 3-7개 |
| `STACK` | `["React 19", "TypeScript", "Vite 7", "Tailwind v4", "Django", "Python 3.13", "Neo4j", "Cesium 3D", "NSGA-II", "Cloudflare Workers", "Railway"]` | 12개 기술 |
| `LIVE_URLS` | `[{name:"AG-frontend", url:"...", platform:"CF Pages", cost:"$0"}, ...]` | 라이브 서비스 4개 |
| `MILESTONES` | `["Q1: MVP", "Q2: B2B Pilot", "Q3: Public Beta", "Q4: B2G Enterprise"]` | 4개 마일스톤 |

---

## 3. 빠른 명령어 모음 (사용자 → AI)

### 3.1 Claude Code / Cursor / Copilot CLI
```
이 프로젝트의 PDF 포트폴리오를 만들어줘.

레퍼런스: D:/Data/25_ACE/docs/portfolio/PORTFOLIO_GENERATOR_PROMPT.md 참고.
이 파일의 디자인 시스템 + HTML 구조 + 페이지 구성을 그대로 따라.

이번 프로젝트 변수:
- PROJECT_NAME: <이름>
- ROLE: <역할>
- KEY_NUMBERS: [...]
- KEY_FINDINGS: [...]
- STACK: [...]

산출물: docs/portfolio/PDF/portfolio.html (10페이지) + 변환 instruction.

작성 후 자체 품질 체크리스트 통과 확인.
```

### 3.2 ChatGPT / Gemini (외부 챗봇)
```
첨부한 프롬프트 파일 (PORTFOLIO_GENERATOR_PROMPT.md) 그대로 따라줘.

내 프로젝트 정보:
[변수 표 채워서 붙여넣기]

HTML 한 파일로 출력해줘. 다른 파일 의존성 X. Tailwind CDN OK.
```

### 3.3 빠른 PDF 변환 (이미 HTML 있을 때)
```bash
# Python 3 + Playwright 설치
pip install playwright
playwright install chromium

# 변환 스크립트 (Bash 1줄)
python -c "from playwright.sync_api import sync_playwright; import os; p = sync_playwright().start(); b = p.chromium.launch(); pg = b.new_page(); pg.goto(f'file://{os.path.abspath(\"portfolio.html\")}'); pg.wait_for_load_state('networkidle'); pg.pdf(path='portfolio.pdf', format='A4', print_background=True, margin={'top':'0','right':'0','bottom':'0','left':'0'}); b.close(); p.stop()"

# 또는 Chrome headless로
chrome --headless --disable-gpu --print-to-pdf=portfolio.pdf --no-margins file://$(pwd)/portfolio.html
```

### 3.4 Microsoft Edge (Windows 가장 빠름)
```bash
# Edge로 직접
start msedge --headless --disable-gpu --print-to-pdf="portfolio.pdf" --print-to-pdf-no-header "file:///D:/Data/<프로젝트>/docs/portfolio/PDF/portfolio.html"
```

---

## 4. 디자인 톤 레퍼런스 (영감)

좋은 예시 (이런 톤):
- linear.app
- vercel.com
- stripe.com/atlas
- supabase.com
- nat.org/posts (개인 블로그 미니멀)
- resend.com
- railway.app

피할 예시:
- 학술 학회 PPT
- LinkedIn slideshare
- Behance 디자이너 포폴 (너무 비주얼 헤비)
- Canva 템플릿
- 매거진 / 에디토리얼

---

## 5. 자주 묻는 질문 (사용자 셀프 디버그)

**Q1. 인쇄하니까 background 색이 다 빠져요**
→ 인쇄 다이얼로그에서 "Background graphics" 옵션 ON. 또는 CSS에 `-webkit-print-color-adjust: exact; print-color-adjust: exact;` 추가.

**Q2. 페이지가 잘려요**
→ 각 `.page` 안 컨텐츠가 297mm - 40mm = 257mm를 넘으면 잘림. h2 크기 줄이거나 카드 padding 줄이기.

**Q3. SVG 다이어그램이 안 나와요**
→ viewBox 속성 확인. `<svg viewBox="0 0 800 400" xmlns="http://www.w3.org/2000/svg">` 형식.

**Q4. 한글 폰트가 안 이쁘게 나와요**
→ Inter는 한글 미지원. Pretendard 추가:
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css">
```
그리고 CSS:
```css
font-family: 'Pretendard', 'Inter', sans-serif;
```

**Q5. PDF 크기가 너무 커요**
→ Playwright 옵션 `prefer_css_page_size: True`. 또는 SVG 최적화 (svgo).

---

## 6. 진화 / 추가 변형

**한 페이지 짧은 버전** (이력서 첨부용 1-pager):
- 표지 + 핵심 메트릭 + 간단 다이어그램만
- 3페이지 max

**비즈니스 / 투자자 버전**:
- 페이지 1 추가: Market & Problem
- 페이지 11 변경: Roadmap → Business Model
- 색상 액센트는 유지

**연구 / 학술 버전**:
- Findings 페이지 강조 (페이지 늘림)
- 통계 (effect size / p-value) 강조
- References 페이지 추가
