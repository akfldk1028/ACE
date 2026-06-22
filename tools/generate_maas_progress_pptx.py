from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "maas-progress-report.pptx"

FONT = "Malgun Gothic"
BG = RGBColor(248, 249, 251)
INK = RGBColor(30, 35, 42)
MUTED = RGBColor(92, 101, 116)
LINE = RGBColor(220, 226, 235)
ACCENT = RGBColor(30, 103, 150)
GREEN = RGBColor(43, 128, 92)
AMBER = RGBColor(177, 118, 30)
RED = RGBColor(174, 68, 68)
DARK = RGBColor(23, 31, 42)
WHITE = RGBColor(255, 255, 255)


def set_bg(slide, color=BG):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def textbox(slide, x, y, w, h, text, size=18, color=INK, bold=False, align=None):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = True
    p = tf.paragraphs[0]
    if align:
        p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return shape


def add_title(slide, title, kicker="MAAS 진행 보고"):
    textbox(slide, 0.55, 0.32, 2.8, 0.28, kicker, 9, ACCENT, True)
    textbox(slide, 0.55, 0.62, 8.8, 0.58, title, 24, INK, True)
    line = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, Inches(0.55), Inches(1.28), Inches(8.9), Inches(0.02))
    line.fill.solid()
    line.fill.fore_color.rgb = LINE
    line.line.fill.background()


def card(slide, x, y, w, h, title, body, accent=ACCENT):
    box = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    box.fill.solid()
    box.fill.fore_color.rgb = WHITE
    box.line.color.rgb = LINE
    box.line.width = Pt(1)
    bar = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, Inches(x), Inches(y), Inches(0.06), Inches(h))
    bar.fill.solid()
    bar.fill.fore_color.rgb = accent
    bar.line.fill.background()
    textbox(slide, x + 0.22, y + 0.16, w - 0.42, 0.28, title, 12, INK, True)
    textbox(slide, x + 0.22, y + 0.52, w - 0.42, h - 0.62, body, 10.5, MUTED)
    return box


def bullets(slide, x, y, w, h, items, size=13, color=INK):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = True
    for idx, item in enumerate(items):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.text = item
        p.level = 0
        p.font.name = FONT
        p.font.size = Pt(size)
        p.font.color.rgb = color
        p.space_after = Pt(6)
    return shape


def metric(slide, x, y, label, value, color=ACCENT):
    textbox(slide, x, y, 1.8, 0.25, label, 8.5, MUTED, True, PP_ALIGN.CENTER)
    textbox(slide, x, y + 0.24, 1.8, 0.42, value, 20, color, True, PP_ALIGN.CENTER)


def footer(slide, num):
    textbox(slide, 8.75, 7.1, 0.7, 0.22, f"{num:02d}", 8, MUTED, False, PP_ALIGN.RIGHT)


def add_image(slide, rel_path, x, y, w=None, h=None):
    path = ROOT / rel_path
    if path.exists():
        return slide.shapes.add_picture(str(path), Inches(x), Inches(y), width=Inches(w) if w else None, height=Inches(h) if h else None)
    card(slide, x, y, w or 4, h or 2, "이미지 없음", rel_path, RED)


def make_deck():
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    # 1
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, DARK)
    textbox(slide, 0.75, 0.85, 8.4, 0.4, "ARR / MAAS", 13, RGBColor(168, 203, 224), True)
    textbox(slide, 0.75, 1.35, 8.4, 1.15, "법규 엔벨로프 기반\n매스 생성 진행 보고", 32, WHITE, True)
    textbox(slide, 0.78, 2.85, 8.1, 0.62, "PPTX 산출물 · 2026-06-09 기준 메모리 반영", 15, RGBColor(214, 224, 234))
    card(slide, 0.78, 4.35, 2.65, 1.15, "기준 경로", "ARR /design\nsource of truth", ACCENT)
    card(slide, 3.68, 4.35, 2.65, 1.15, "검증 PNU", "1168011800104170004\n대지 264.13 m²", GREEN)
    card(slide, 6.58, 4.35, 2.65, 1.15, "현재 표현", "강한 프로토타입\n완성 법규검토 아님", AMBER)
    footer(slide, 1)

    # 2
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "현재 결론")
    card(slide, 0.7, 1.65, 8.6, 1.25, "핵심 판단", "LLM/Agent가 geometry를 발명하는 구조가 아니라, legal envelope와 deterministic validator가 geometry source of truth가 되는 구조가 맞다.", ACCENT)
    card(slide, 0.7, 3.12, 4.12, 1.55, "검증된 부분", "site-boundary → auto-constraints → jobs → run → results 흐름이 동작한다. MAAS legal envelope가 후보 18개를 반환하고, evidence bundle 초안까지 연결됐다.", GREEN)
    card(slide, 5.18, 3.12, 4.12, 1.55, "아직 말하면 안 되는 것", "전체 법규 검토 완료, VWorld 3D 픽셀 검증 완료, 채광사선 최종 적합 판정, Flexity급 검토 제품이라는 표현은 부정확하다.", RED)
    footer(slide, 2)

    # 3
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "시스템 위치")
    card(slide, 0.62, 1.65, 2.75, 3.65, "ARR", "/design의 기준 구현.\nDjango backend가 필지, 법규, datum, setback, envelope를 계산하고 React/VWorld가 렌더링한다.", ACCENT)
    card(slide, 3.62, 1.65, 2.75, 3.65, "AG-light", "경량 legal-agent/MCP 실험 대상.\nARR datum, setback, VWorld 시각화와 동등하지 않다.", AMBER)
    card(slide, 6.62, 1.65, 2.75, 3.65, "gateway / Hermes", "agent/tool 경로.\n현재 /design 시각화 디버깅의 시작점이 아니라 land analysis 도구 경로다.", MUTED)
    footer(slide, 3)

    # 4
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "데이터 흐름")
    bullets(slide, 0.82, 1.7, 8.25, 4.3, [
        "ARR frontend /design",
        "POST /design/site-boundary/ : 주소/PNU 해석, VWorld cadastral geometry 수집",
        "POST /design/auto-constraints/ : zoning, regulation, setback, road frontage, datum 계산",
        "POST /design/jobs/ → run → results : MAAS legal envelope 후보 생성",
        "frontend SiteMapPanel : VWorld/Cesium 또는 2D SVG fallback 렌더링",
        "agent/review layer : evidence bundle을 읽고 PASS/FAIL/needs_evidence를 판단"
    ], 14)
    footer(slide, 4)

    # 5
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "현재 검증 결과")
    metric(slide, 0.85, 1.68, "대지면적", "264.13m²")
    metric(slide, 2.65, 1.68, "후보", "18")
    metric(slide, 4.45, 1.68, "Pareto", "18")
    metric(slide, 6.25, 1.68, "API 오류", "0", GREEN)
    card(slide, 0.72, 2.65, 4.15, 2.0, "Live /design 확인", "조회와 최적화 API 호출이 HTTP 200/202/200으로 반환됐다. 화면 텍스트는 MAAS Legal Morphology Search, 법규 산정 근거, BUILDING MASS, MAAS Agent Workspace를 포함한다.", GREEN)
    card(slide, 5.12, 2.65, 4.15, 2.0, "선택 후보 예시", "legal_layered_max, height 17.5m, 5 floors, BCR 38.97%, FAR 136.78%, floor plates [102.93, 102.93, 74.99, 51.47, 28.96].", ACCENT)
    footer(slide, 5)

    # 6
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "화면 캡처")
    add_image(slide, "docs/playwright/design-captures/design_optimize_result_with_2d_fallback_1168011800104170004.png", 0.62, 1.52, w=5.72)
    card(slide, 6.55, 1.52, 2.82, 1.25, "2D fallback", "Headless WebGL 비활성 환경에서도 mass_geojson 기반 2D MASS PREVIEW가 표시된다.", GREEN)
    card(slide, 6.55, 2.98, 2.82, 1.25, "주의", "이 캡처는 Cesium 3D 픽셀 검증이 아니다. 실제 VWorld 위치 검증은 브라우저 확인이 필요하다.", AMBER)
    card(slide, 6.55, 4.44, 2.82, 1.25, "UI 신호", "법규 산정 근거, datum, 정북일조 단면, 후보 리스트, BUILDING MASS 패널이 렌더링됨.", ACCENT)
    footer(slide, 6)

    # 7
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "법규와 Datum 상태")
    card(slide, 0.7, 1.58, 4.15, 1.42, "구현된 검증 축", "VWorld 필지 경계, NGII local DEM datum, 인접대지 이격선, 도로/building-line fallback, 정북일조 envelope, 공동주택 채광사선 reference.", GREEN)
    card(slide, 5.12, 1.58, 4.15, 1.42, "핵심 기준", "datum_result가 있어야 하며, DEM covered Seoul case에서는 elevation_source가 ngii_local_dem이어야 한다.", ACCENT)
    card(slide, 0.7, 3.28, 4.15, 1.55, "불완전한 부분", "§119 3m 초과 지반 분할은 true contour/area polygon partition이 아직 아니다. split_bands는 메타데이터 수준이다.", AMBER)
    card(slide, 5.12, 3.28, 4.15, 1.55, "채광사선 주의", "현재 daylight plane은 site-boundary reference다. 실제 매스 창면, 수직거리 ray, same-site facing logic이 필요하다.", RED)
    footer(slide, 7)

    # 8
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "Evidence Bundle")
    bullets(slide, 0.78, 1.6, 4.4, 4.8, [
        "schema_version: arr.maas.evidence.v0",
        "bundle_id: maas-evidence:<job>:<candidate>",
        "top-level: project, site, candidate, geometry, legal, program, mobility, life_safety, environment",
        "checks[]: 모든 pass/fail/unknown 판단의 flat index",
        "assets/provenance/agent_reviews/final_decision: 검토 추적 근거"
    ], 12.8)
    card(slide, 5.55, 1.65, 3.75, 1.2, "현재 상태", "example과 schema가 존재하고, live evidence API가 HTTP 200으로 arr.maas.evidence.v0를 반환했다.", GREEN)
    card(slide, 5.55, 3.05, 3.75, 1.2, "최종 상태", "unknown은 pass가 아니다. 부족한 도메인은 needs_evidence 또는 text_only로 남겨야 한다.", AMBER)
    card(slide, 5.55, 4.45, 3.75, 1.2, "Agent 역할", "geometry를 직접 만들지 않고, evidence를 읽고 검토/설명/재생성 요청을 수행한다.", ACCENT)
    footer(slide, 8)

    # 9
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "Aesthetic Pipeline")
    add_image(slide, "docs/playwright/design-route-verify/aesthetic-reference/62e70d5c89fd8b59.png", 0.75, 1.65, w=3.9)
    card(slide, 5.05, 1.62, 4.15, 1.2, "원칙", "이미지 생성은 legal mass 이후 단계다. facade/material/window rhythm은 바꿀 수 있지만 mass geometry는 바꾸면 안 된다.", ACCENT)
    card(slide, 5.05, 3.02, 4.15, 1.2, "구현", "build_aesthetic_image_job → locked_geometry snapshot → reference PNG → provider adapter → validation → evidence asset attachment.", GREEN)
    card(slide, 5.05, 4.42, 4.15, 1.2, "Provider", "placeholder, OpenAI gpt-image-2, Gemini 2.5 Flash Image preview, UniTEX 별도 GPU worker 후보.", AMBER)
    footer(slide, 9)

    # 10
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "한계와 리스크")
    card(slide, 0.72, 1.58, 4.15, 1.3, "VWorld 검증", "Headless Playwright는 WebGL이 비활성화되거나 screenshot path가 timeout될 수 있다. 최종 3D 위치 검증은 실제 브라우저가 필요하다.", AMBER)
    card(slide, 5.12, 1.58, 4.15, 1.3, "복잡 필지", "concave parcel, multi-road parcel은 buildable footprint half-plane clipping의 안정성 검증이 더 필요하다.", AMBER)
    card(slide, 0.72, 3.12, 4.15, 1.3, "프로그램 검토", "tiny FAR remainder floor는 막았지만, building type별 core/corridor/egress/usable depth rule은 아직 1차 수준이다.", RED)
    card(slide, 5.12, 3.12, 4.15, 1.3, "법규 범위", "front-road diagonal, district-unit building line, multi-zone area-ratio, full daylight pass/fail은 완성 검토가 아니다.", RED)
    footer(slide, 10)

    # 11
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "다음 순서")
    bullets(slide, 0.85, 1.65, 8.1, 4.8, [
        "1. §119 3m 초과 지반을 DEM/contour 기반 true area polygon partition으로 구현",
        "2. 9개 대표 PNU를 API, plan PNG, section PNG, VWorld capture까지 묶은 visual gate로 승격",
        "3. mass-aware daylight: 창면 후보, 수직거리 ray, facing-building logic, pass/fail section 구현",
        "4. road datum/road width/opposite boundary가 신뢰된 뒤 front-road/가로구역 height envelope 구현",
        "5. VWorld를 검토 제품으로 정리: layer toggle, compact legend, sparse default, debug opt-in",
        "6. AG-light MCP와 evidence bundle을 연결해 review agent가 structured PASS/FAIL을 반환"
    ], 13.3)
    footer(slide, 11)

    # 12
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, DARK)
    textbox(slide, 0.8, 0.8, 8.3, 0.45, "정리", 16, RGBColor(168, 203, 224), True)
    textbox(slide, 0.8, 1.35, 8.3, 0.9, "MAAS는 현재 법규 엔벨로프 기반\n매스 생성 프로토타입으로 검증 중", 29, WHITE, True)
    textbox(slide, 0.82, 2.72, 8.0, 0.72, "핵심 성과는 live /design flow, 18개 후보 생성, evidence bundle, 2D fallback 검증이다.", 15, RGBColor(224, 231, 239))
    textbox(slide, 0.82, 3.62, 8.0, 0.72, "핵심 리스크는 datum 완전성, mass-aware daylight, complex parcel, VWorld real-browser 검증이다.", 15, RGBColor(224, 231, 239))
    card(slide, 0.82, 5.1, 8.15, 0.9, "보고 기준", "docs/ai-session-memory 및 ARR/backend/design/maas/HANDOFF.md 반영 · 2026-06-09", ACCENT)
    footer(slide, 12)

    prs.save(OUT)


def _ensure_crops() -> None:
    """Create focused images from the Playwright body capture for the deck."""
    try:
        from PIL import Image
    except Exception:
        return
    src = ROOT / "docs/playwright/design-captures/design_optimize_result_with_2d_fallback_1168011800104170004.png"
    if not src.exists():
        return
    out = ROOT / "docs/playwright/design-captures/crops"
    out.mkdir(exist_ok=True)
    im = Image.open(src)
    crops = {
        "maas_input_legal_panel.png": (0, 0, 410, 1000),
        "maas_2d_mass_preview.png": (410, 0, 1040, 1000),
        "maas_building_mass_card.png": (800, 20, 1025, 245),
        "maas_legal_basis_panel.png": (0, 520, 410, 905),
        "maas_controls_panel.png": (0, 0, 410, 520),
    }
    for name, box in crops.items():
        target = out / name
        im.crop(box).save(target)


def mini_table(slide, x, y, w, h, headers, rows, widths=None, font_size=8.5):
    widths = widths or [1 / len(headers)] * len(headers)
    table_shape = slide.shapes.add_table(len(rows) + 1, len(headers), Inches(x), Inches(y), Inches(w), Inches(h))
    table = table_shape.table
    for i, width in enumerate(widths):
        table.columns[i].width = Inches(w * width)
    for c, head in enumerate(headers):
        cell = table.cell(0, c)
        cell.text = head
        cell.fill.solid()
        cell.fill.fore_color.rgb = DARK
        for p in cell.text_frame.paragraphs:
            p.font.name = FONT
            p.font.size = Pt(font_size)
            p.font.bold = True
            p.font.color.rgb = WHITE
    for r, row in enumerate(rows, start=1):
        for c, value in enumerate(row):
            cell = table.cell(r, c)
            cell.text = str(value)
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if r % 2 else RGBColor(242, 245, 249)
            for p in cell.text_frame.paragraphs:
                p.font.name = FONT
                p.font.size = Pt(font_size)
                p.font.color.rgb = INK
    return table_shape


def make_deck_v2():
    _ensure_crops()
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    candidates = [
        ("1", "법규엔벨로프", "legal_layered_max", "463", "61.0", "OK"),
        ("2", "포디움/타워", "lift_overlap_slabs", "429", "62.4", "OK"),
        ("3", "다단 일조스텝", "grammar_sunlight_multi_step", "463", "61.0", "OK"),
        ("4", "포디움+타워오프셋", "grammar_podium_tower_offset", "309", "61.0", "OK"),
        ("5", "오버랩+시프트+테라스", "grammar_overlap_shift_terrace", "287", "67.9", "OK"),
        ("6", "코너/오픈코트", "court_open", "309", "61.0", "OK"),
        ("15", "테라스", "grade_terrace", "448", "61.0", "OK"),
        ("18", "분절+브릿지+계단", "grammar_split_lift_stepback", "265", "69.6", "OK"),
    ]

    # 1
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, DARK)
    textbox(slide, 0.75, 0.78, 8.5, 0.35, "ARR / MAAS / Playwright DOM Evidence", 12, RGBColor(158, 205, 235), True)
    textbox(slide, 0.75, 1.28, 8.4, 1.05, "법규 기반 매스 생성\n진행 보고", 32, WHITE, True)
    textbox(slide, 0.78, 2.65, 8.1, 0.42, "PNU 1168011800104170004 · /design DOM/API capture · VWorld 3D 미검증", 15, RGBColor(220, 230, 240))
    add_image(slide, "docs/playwright/design-captures/design_optimize_result_with_2d_fallback_1168011800104170004.png", 0.75, 3.55, w=8.5)
    footer(slide, 1)

    # 2
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "Playwright DOM/API 캡처 기준")
    add_image(slide, "docs/playwright/design-captures/crops/maas_controls_panel.png", 0.58, 1.55, w=3.05)
    add_image(slide, "docs/playwright/design-captures/crops/maas_2d_mass_preview.png", 3.86, 1.55, w=3.45)
    card(slide, 7.55, 1.55, 1.85, 1.05, "검증 PNU", "1168011800104170004\n264.13 m²", ACCENT)
    card(slide, 7.55, 2.78, 1.85, 1.05, "API flow", "site-boundary\nconstraints\njobs/results", GREEN)
    card(slide, 7.55, 4.01, 1.85, 1.05, "결과", "18 candidates\n18 pareto\n0 errors", GREEN)
    card(slide, 7.55, 5.24, 1.85, 1.05, "주의", "WebGL fallback\n2D preview", AMBER)
    footer(slide, 2)

    # 3
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "법규 산정 근거 화면")
    add_image(slide, "docs/playwright/design-captures/crops/maas_legal_basis_panel.png", 0.7, 1.5, w=3.2)
    card(slide, 4.25, 1.55, 2.35, 1.25, "Datum", "NGII local DEM\n대지 14개 샘플\n도로 3개 샘플\n인접대지 13개 샘플", ACCENT)
    card(slide, 6.88, 1.55, 2.35, 1.25, "법규 기준", "§119 대지 기준면\n§86 평균수평면\n정북일조 기준면\n채광사선 참고면", GREEN)
    card(slide, 4.25, 3.12, 2.35, 1.25, "도로/인접", "검출 도로폭 37.5m\n전면도로 후보 1개\n인접대지 후보 4개", AMBER)
    card(slide, 6.88, 3.12, 2.35, 1.25, "해석 주의", "채광사선은 reference.\n최종 pass/fail은 매스 창면 기반 ray 검토 필요.", RED)
    bullets(slide, 4.3, 4.82, 4.8, 1.25, [
        "PPT에 넣은 법규 값은 Playwright capture-result-with-fallback.json의 화면 텍스트 기준",
        "완성 법규검토가 아니라 datum/envelope/후보 생성 검증 상태"
    ], 11.5, MUTED)
    footer(slide, 3)

    # 4
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "Constraint / Datum / Section")
    add_image(slide, "docs/screenshots/design_1168011800104170004_04_full.png", 0.55, 1.5, w=5.8)
    card(slide, 6.65, 1.5, 2.75, 1.2, "화면상 법규 패널", "건폐율 ≤ 60%\n용적률 ≤ 250%\n인접대지 ≥ 0.5m\n조경면적 ≥ 15%", GREEN)
    card(slide, 6.65, 2.9, 2.75, 1.2, "단면 표기", "정북일조 H/2는 H = 2x.\n라벨은 2:1이 맞다.", ACCENT)
    card(slide, 6.65, 4.3, 2.75, 1.2, "품질 기준", "plan PNG, section PNG, VWorld/Cesium이 서로 맞아야 최종 검증으로 볼 수 있다.", AMBER)
    footer(slide, 4)

    # 5
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "2D Mass Preview와 Building Mass")
    add_image(slide, "docs/playwright/design-captures/crops/maas_2d_mass_preview.png", 0.62, 1.45, w=5.25)
    add_image(slide, "docs/playwright/design-captures/crops/maas_building_mass_card.png", 6.12, 1.55, w=2.3)
    card(slide, 6.12, 4.05, 2.75, 1.25, "화면 지표", "형태 maas_legal_envelope\n높이 16.8m\n층수 6F\nBCR 39.0%\nFAR 175.5%\n연면적 463m²", ACCENT)
    card(slide, 6.12, 5.55, 2.75, 0.95, "의미", "WebGL이 꺼져도 mass_geojson 기반 fallback으로 후보 형상을 확인.", GREEN)
    footer(slide, 5)

    # 6
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "후보 리스트: 계단/스텝 매스 포함")
    mini_table(slide, 0.55, 1.52, 8.95, 3.35,
               ["#", "화면명", "operator / mass_shape", "연면적", "일조", "상태"],
               candidates,
               widths=[0.07, 0.22, 0.36, 0.11, 0.11, 0.13],
               font_size=8.1)
    card(slide, 0.72, 5.25, 2.75, 1.05, "계단 mass", "다단 일조스텝\n분절+브릿지+계단\n테라스/stepback 계열", ACCENT)
    card(slide, 3.72, 5.25, 2.75, 1.05, "화면 근거", "Playwright capture text에 18개 후보명과 OK 상태가 기록됨.", GREEN)
    card(slide, 6.72, 5.25, 2.75, 1.05, "주의", "화면상 6F/16.8m 지표와 evidence sample의 5F/17.5m dry-run은 서로 다른 검증 산출 시점.", AMBER)
    footer(slide, 6)

    # 7
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "바뀐 MAAS 로직")
    bullets(slide, 0.82, 1.55, 4.25, 4.9, [
        "legacy 10종은 더 이상 capacity source가 아니다.",
        "legal envelope가 capacity anchor이고, legal_layered_max가 먼저 들어간다.",
        "grammar/morphology seed가 생성된다: notch, court, split, branch, pinch, interlock, overlap, terrace, tower, taper, grade.",
        "각 후보는 repair_design과 legal metrics를 통과해야 리스트에 남는다.",
        "후보 선택은 점수만이 아니라 concept family diversity를 보존한다."
    ], 12.3)
    mini_table(slide, 5.35, 1.65, 3.9, 2.55,
               ["단계", "역할"],
               [
                   ("legal envelope", "층별 허용 footprint"),
                   ("floor plates", "FAR/BCR/height 기반 stack"),
                   ("seed grammar", "계단/분절/테라스 등 생성"),
                   ("repair/check", "법규 실패 후보 제거"),
                   ("rank/select", "capacity + diversity"),
               ],
               widths=[0.42, 0.58],
               font_size=8.3)
    card(slide, 5.35, 4.55, 3.9, 1.25, "코드 기준", "legal_mesh_optimizer.py\nseed_library.py\ngrammar/sequence_library.py", ACCENT)
    footer(slide, 7)

    # 8
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "계단/스텝 생성 방식")
    card(slide, 0.75, 1.55, 2.65, 1.35, "grammar_sunlight_multi_step", "base(site)\nstep_envelope(bands=4)\n층별 법규 envelope 추종", ACCENT)
    card(slide, 3.68, 1.55, 2.65, 1.35, "grammar_split_lift_stepback", "split(x)\nlift(upper 0.66)\ngrade(north)\n분절+후퇴 상층부", GREEN)
    card(slide, 6.62, 1.55, 2.65, 1.35, "compact visual volumes", "step/terrace/grade/tower는 volume band를 4단계까지 분할 표시", AMBER)
    bullets(slide, 0.9, 3.35, 8.1, 2.4, [
        "계단 mass는 단순 라벨이 아니라 grammar sequence가 geometry로 해석되고 legal repair/check를 지난다.",
        "wants_stepped_display가 켜진 후보는 floor plate stack을 band로 묶어 사용자-facing mass volume으로 만든다.",
        "높은 footprint IoU라도 section/volume profile이 다르면 sectional alternative로 유지된다."
    ], 13)
    footer(slide, 8)

    # 9
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "Diversity Review 결과")
    mini_table(slide, 0.62, 1.55, 8.8, 3.25,
               ["rank", "mass_shape", "concept", "height", "BCR", "FAR", "vol", "plates"],
               [
                   ("1", "legal_layered_max", "법규엔벨로프", "14.0", "59.4", "249.88", "2", "5"),
                   ("2", "lift_overlap_slabs_layered", "포디움/타워", "14.0", "58.81", "249.85", "4", "5"),
                   ("3", "grammar_sunlight_multi_step_layered", "다단 일조스텝", "14.0", "58.81", "249.85", "4", "5"),
                   ("4", "grammar_podium_tower_offset_layered", "포디움+타워오프셋", "14.0", "58.81", "249.85", "2", "5"),
                   ("8", "slender_bar_east", "바형", "8.4", "45.73", "137.2", "1", "0"),
               ],
               widths=[0.08, 0.30, 0.20, 0.09, 0.08, 0.10, 0.07, 0.08],
               font_size=7.7)
    card(slide, 0.82, 5.18, 2.6, 1.05, "결과", "8 candidates\n8 unique mass_shape\n8 unique concepts", GREEN)
    card(slide, 3.7, 5.18, 2.6, 1.05, "판단", "하나의 legal box가 아니라 plan/section concept가 분리됨.", ACCENT)
    card(slide, 6.58, 5.18, 2.6, 1.05, "남은 gate", "3D diversity validator를 validators.runs[]에 넣어야 함.", AMBER)
    footer(slide, 9)

    # 10
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "Evidence Bundle 상태")
    bullets(slide, 0.82, 1.52, 4.15, 4.65, [
        "schema_version: arr.maas.evidence.v0",
        "bundle: maas-evidence:6ee6...:900000",
        "candidate: maas_01 / legal_layered_max",
        "checks: 7",
        "final decision: needs_evidence",
        "missing evidence: 4",
        "diversity class: plan_diverse"
    ], 12.2)
    card(slide, 5.35, 1.65, 3.8, 1.25, "왜 필요?", "Agent가 말로 판단하지 않고 site/candidate/geometry/legal/program/assets/provenance/checks를 근거로 리뷰.", ACCENT)
    card(slide, 5.35, 3.15, 3.8, 1.25, "법규 완성 아님", "unknown은 pass가 아니며, parking/fire/energy/structural 등은 needs_evidence로 남는다.", AMBER)
    card(slide, 5.35, 4.65, 3.8, 1.25, "Graph DB 방향", "geometry는 GeoJSON/assets에 두고 Neo4j는 법규/근거/후보 lineage provenance에 사용.", GREEN)
    footer(slide, 10)

    # 11
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "Nano Banana / Aesthetic Pipeline")
    add_image(slide, "docs/playwright/design-route-verify/aesthetic-reference/62e70d5c89fd8b59.png", 0.75, 1.58, w=3.25)
    card(slide, 4.35, 1.58, 4.85, 1.08, "구현된 adapter", "nano-banana provider는 Gemini API 우선. GEMINI_API_KEY 또는 GOOGLE_API_KEY 사용, 기본 모델 gemini-2.5-flash-image-preview.", ACCENT)
    card(slide, 4.35, 2.92, 4.85, 1.08, "현재 dry-run", "locked reference PNG까지 생성됨. provider key/endpoint가 없으면 needs_provider로 반환하고 생성 성공처럼 꾸미지 않는다.", AMBER)
    card(slide, 4.35, 4.26, 4.85, 1.08, "안전 계약", "이미지 모델은 facade/material/window rhythm만 변경. silhouette, footprint, roofline, height, floor count, massing steps, setbacks 변경 금지.", GREEN)
    footer(slide, 11)

    # 12
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "Aesthetic은 법규 대체가 아님")
    bullets(slide, 0.82, 1.55, 8.0, 4.7, [
        "MAAS evidence bundle → locked reference render spec → facade/material prompt → image backend → silhouette/geometry validation → evidence asset reference",
        "OpenAI adapter는 gpt-image-2 기본값으로 수정됨.",
        "Nano Banana adapter는 Gemini 2.5 Flash Image preview 기본값과 generic HTTP fallback을 같이 지원.",
        "UniTEX는 Apache-2.0 repo를 체크아웃했지만, ARR Django venv에 설치하지 않고 별도 CUDA worker 후보로 둔다.",
        "어떤 이미지 backend도 legal checks를 pass로 만들 수 없다."
    ], 13)
    footer(slide, 12)

    # 13
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "현재 한계")
    card(slide, 0.7, 1.55, 4.15, 1.2, "Playwright 한계", "Headless Chromium에서 Cesium/WebGL 픽셀 검증은 불안정. VWorld가 아니라 API/DOM/2D fallback 검증까지만 확실.", AMBER)
    card(slide, 5.12, 1.55, 4.15, 1.2, "법규 한계", "§119 >3m true area partition, mass-aware daylight, front-road height envelope는 미완성.", RED)
    card(slide, 0.7, 3.05, 4.15, 1.2, "매스 한계", "program/core/corridor/egress/depth rule은 1차 수준. single-volume 후보는 floor plate reviewability가 낮음.", AMBER)
    card(slide, 5.12, 3.05, 4.15, 1.2, "복잡 필지", "concave/multi-road parcel은 buildable footprint clipping과 road datum 신뢰성 보강 필요.", RED)
    footer(slide, 13)

    # 14
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "다음 구현 순서")
    bullets(slide, 0.88, 1.6, 8.0, 4.9, [
        "1. Playwright/real-browser 캡처 세트를 후보 선택별로 더 늘린다: legal_layered, multi_step, split_lift_stepback.",
        "2. §119 3m 초과 지반을 DEM/contour 기반 true area polygon partition으로 구현한다.",
        "3. mass-aware daylight: selected mass wall/window candidates → perpendicular distance rays → pass/fail section.",
        "4. 3D diversity validator를 evidence validators.runs[]에 추가한다.",
        "5. Nano Banana 실제 provider key 연결 시 생성 asset을 evidence.assets.aesthetic에 붙이고 silhouette validation을 통과시킨다.",
        "6. VWorld layer controller/legend를 제품 검토 화면으로 정리한다."
    ], 13)
    footer(slide, 14)

    # 15
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "LLM이 하는 것과 하지 않는 것")
    card(slide, 0.72, 1.55, 4.15, 1.35, "LLM이 하지 않는 것", "LLM은 mass 좌표, mesh, floor plate, legal envelope를 직접 생성하지 않는다. Geometry source of truth는 ARR/backend/design/maas 코드다.", RED)
    card(slide, 5.12, 1.55, 4.15, 1.35, "LLM이 하는 것", "후보 설명, evidence 요약, 부족한 근거 지적, 재생성/수정 방향 제안, agent review orchestration을 담당한다.", ACCENT)
    card(slide, 0.72, 3.25, 4.15, 1.35, "왜 이 방식인가", "법규, datum, 일조, 면적은 재현성과 추적성이 중요하다. LLM 직접 geometry는 그럴듯해도 검증과 디버깅이 어렵다.", AMBER)
    card(slide, 5.12, 3.25, 4.15, 1.35, "현재 최선의 방향", "deterministic legal geometry + grammar/operator diversity + repair/check + evidence bundle + LLM review가 안전한 구조다.", GREEN)
    footer(slide, 15)

    # 16
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "최종 목표 Flow")
    bullets(slide, 0.88, 1.55, 8.05, 4.95, [
        "1. deterministic legal envelope",
        "2. floor-by-floor legal plate generation",
        "3. grammar/operator seed generation",
        "4. evolutionary 또는 multi-objective search",
        "5. program/core/parking/egress viability check",
        "6. daylight/window-wall validation",
        "7. evidence bundle",
        "8. LLM/agent review",
        "9. human selection/edit",
        "10. image model은 마지막 facade/aesthetic 단계만 담당"
    ], 13)
    footer(slide, 16)

    # 17
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "메싱 Flow 1: 입력에서 기준 매스까지")
    bullets(slide, 0.78, 1.5, 8.45, 5.0, [
        "1. PNU 입력: 예 1168011800104170004",
        "2. ARR backend가 대지 정보 수집: 필지 경계, 대지면적, 용도지역, 도로/인접대지, DEM 기반 datum",
        "3. 법규 constraint 계산: 건폐율, 용적률, 높이, 인접대지 이격, 정북일조 envelope, 채광사선 reference",
        "4. legal envelope 생성: 이 대지에서 법적으로 매스가 들어갈 수 있는 3D 한계공간",
        "5. floor plate stack 생성: legal envelope 안에서 층별 바닥판 생성",
        "   예: 1F 102.93m², 2F 102.93m², 3F 74.99m², 4F 51.47m², 5F 28.96m²",
        "6. 기준 후보 생성: legal_layered_max = 법규 envelope를 최대한 채우는 기준 매스"
    ], 11.8)
    card(slide, 0.9, 6.25, 8.1, 0.55, "핵심", "여기까지는 LLM이 아니라 ARR/MAAS 코드가 deterministic geometry로 계산한다.", ACCENT)
    footer(slide, 17)

    # 18
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_title(slide, "메싱 Flow 2: 후보 다양화에서 LLM Review까지")
    bullets(slide, 0.78, 1.42, 8.45, 5.15, [
        "7. 형태 seed/operator 적용: 다단 일조스텝, 포디움/타워, 분절+브릿지+계단, 테라스, 중정형, 바형, 코너/오픈코트",
        "8. 각 후보를 법규 안으로 repair/check: 법규 밖으로 나간 후보는 자르거나 수정하고, 그래도 실패하면 버림",
        "9. 점수화/선택: FAR/BCR 활용도, 높이, 일조 여유, 형태 다양성, plan diversity, section diversity",
        "10. frontend에 후보 전달: mass_geojson, floor_plates, mass_volumes, metrics가 UI로 전달됨",
        "11. agent/LLM review: 후보 설명, 부족 evidence 지적, needs_evidence 판단, 재생성/수정 요청",
        "LLM이 직접 좌표를 찍어서 '이런 매스 만들자' 하는 구조가 아니다."
    ], 12.0)
    card(slide, 0.9, 6.28, 2.55, 0.65, "LLM", "리뷰어 / 설명자 / 오케스트레이터", AMBER)
    card(slide, 3.72, 6.28, 2.55, 0.65, "MAAS 코드", "실제 매스 생성기", GREEN)
    card(slide, 6.55, 6.28, 2.55, 0.65, "법규 envelope", "geometry 기준선", ACCENT)
    footer(slide, 18)

    # 19
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, DARK)
    textbox(slide, 0.78, 0.82, 8.4, 0.35, "정리", 15, RGBColor(158, 205, 235), True)
    textbox(slide, 0.78, 1.3, 8.4, 1.05, "지금 보여줄 핵심은\nVWorld가 아니라 DOM/API와 MAAS 근거다", 30, WHITE, True)
    card(slide, 0.82, 3.05, 2.65, 1.35, "화면", "Playwright DOM 캡처\n법규 패널\n2D fallback preview", ACCENT)
    card(slide, 3.68, 3.05, 2.65, 1.35, "로직", "legal envelope first\nseed/operator diversity\n계단/스텝 grammar", GREEN)
    card(slide, 6.55, 3.05, 2.65, 1.35, "이미지", "Nano Banana adapter\nlocked reference PNG\nneeds_provider 정직 처리", AMBER)
    textbox(slide, 0.84, 5.4, 8.0, 0.5, "산출 파일: docs/maas-progress-report-vworld-corrected.pptx", 14, RGBColor(220, 230, 240))
    footer(slide, 19)

    prs.save(OUT)


if __name__ == "__main__":
    make_deck_v2()
    print(OUT)
