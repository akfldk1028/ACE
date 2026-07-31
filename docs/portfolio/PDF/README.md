# Portfolio PDF — DongHyeon Kim

12페이지 통합 IT 포트폴리오 (25_ACE + AG-Research). HTML → A4 PDF.

---

## 빠른 변환 (3가지 방법)

### 방법 1 — Edge headless (Windows 가장 빠름, 추천)

```bash
start msedge --headless --disable-gpu --print-to-pdf="D:/Data/25_ACE/docs/portfolio/PDF/portfolio.pdf" --print-to-pdf-no-header --no-pdf-header-footer "file:///D:/Data/25_ACE/docs/portfolio/PDF/portfolio.html"
```

또는 Chrome:
```bash
start chrome --headless --disable-gpu --print-to-pdf="D:/Data/25_ACE/docs/portfolio/PDF/portfolio.pdf" --no-pdf-header-footer "file:///D:/Data/25_ACE/docs/portfolio/PDF/portfolio.html"
```

### 방법 2 — Playwright Python (모든 OS)

```bash
pip install playwright
playwright install chromium

python D:/Data/25_ACE/docs/portfolio/PDF/render.py
```

`render.py` 코드는 아래 참조.

### 방법 3 — 브라우저 수동 (가장 간단)

1. `portfolio.html`을 Chrome 또는 Edge에서 열기
2. **Ctrl+P** (Mac: Cmd+P)
3. 설정:
   - Destination: **Save as PDF**
   - Layout: **Portrait**
   - Paper size: **A4**
   - Margins: **None** (또는 Default)
   - Background graphics: **✅ ON** (필수!)
   - Headers and footers: **OFF**
4. **Save** → `portfolio.pdf`

---

## 페이지 구성 (12장)

| # | 섹션 | 핵심 |
|---|---|---|
| 1 | Cover | 거대 hero + indigo blob |
| 2 | About + 핵심 메트릭 5개 | 본인 소개 + 4 스킬 카드 |
| 3 | 25_ACE Hero | 프로젝트 한 줄 + 6 메트릭 |
| 4 | 25_ACE Architecture | drawio 시스템 다이어그램 (3 layer) |
| 5 | 25_ACE Data Flow | 8 step + 표 + 기술/지연 |
| 6 | 25_ACE Algorithms | 4 알고리즘 카드 + 10 매스 + 4 평면 |
| 7 | 25_ACE Live + Validation | 4 service ($28/월) + 178 tests |
| 8 | AG-Research Hero | 14 patterns + 6 metrics + taxonomy |
| 9 | AG-Research Findings | 6 finding 카드 + ΔU formula |
| 10 | Tech Stack | 16 tech grid + statistics + 5 LLMs |
| 11 | Roadmap | Q1-Q4 timeline + 3 next-step |
| 12 | Closing | "Let's build..." + contact |

---

## 디자인 시스템

- **배경**: #FFFFFF (pure white)
- **본문**: #0A0A0A / #525252
- **액센트**: #4F46E5 (indigo, 단일)
- **보더**: #E5E7EB (1px)
- **타이포**: Inter (영어) + Pretendard (한글) + JetBrains Mono (숫자/코드)
- **사이즈**: A4 (210 × 297 mm), 18mm 상하 / 20mm 좌우 마진

---

## 트러블슈팅

### "PDF가 흑백으로 나와요"
→ Background graphics ON 필수. headless 명령에 `--print-to-pdf`는 자동 ON.

### "페이지가 잘려요"
→ 인쇄 다이얼로그에서 "Margins: None" + "Scale: Default" 또는 "Fit to page" 끄기.

### "한글이 안 이뻐요"
→ Pretendard CDN이 로드 실패. `<head>`의 link 태그 확인. 오프라인이면 다음 추가:
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css">
```

### "페이지 번호가 추가됐어요"
→ Edge/Chrome 인쇄 다이얼로그에서 "Headers and footers: OFF". headless면 `--no-pdf-header-footer` 플래그.

---

## render.py (Python 자동 변환 스크립트)

`D:/Data/25_ACE/docs/portfolio/PDF/render.py`로 저장:

```python
"""Portfolio HTML → PDF renderer.

사용법:
    pip install playwright
    playwright install chromium
    python render.py
"""
from playwright.sync_api import sync_playwright
import os
import sys

HTML = os.path.abspath(os.path.join(os.path.dirname(__file__), "portfolio.html"))
PDF = os.path.abspath(os.path.join(os.path.dirname(__file__), "portfolio.pdf"))

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(f"file://{HTML}")
    page.wait_for_load_state("networkidle")
    # 폰트 로드 보장
    page.wait_for_timeout(1500)
    page.pdf(
        path=PDF,
        format="A4",
        print_background=True,
        margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        prefer_css_page_size=True,
    )
    browser.close()

print(f"OK -> {PDF}")
print(f"   size: {os.path.getsize(PDF) / 1024:.1f} KB")
```

---

## 다른 프로젝트도 같은 톤으로 만드려면

`D:/Data/25_ACE/docs/portfolio/PORTFOLIO_GENERATOR_PROMPT.md` 통째로 다른 AI에게 던지면 됨. 변수 표만 채우면 자동 생성.
