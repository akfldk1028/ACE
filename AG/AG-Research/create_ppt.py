"""
Generate Korean presentation PPT for Multi-Agent Termination Study.
NotebookLM-inspired clean, minimal design.
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ── Colors ──
BG_DARK = RGBColor(0x1A, 0x1A, 0x2E)       # dark navy
BG_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ACCENT = RGBColor(0x4E, 0x7C, 0xFF)          # bright blue
ACCENT2 = RGBColor(0x00, 0xC9, 0xA7)         # teal
ACCENT3 = RGBColor(0xFF, 0x6B, 0x6B)         # coral
ACCENT4 = RGBColor(0xFF, 0xA5, 0x00)         # orange
TEXT_DARK = RGBColor(0x2D, 0x2D, 0x2D)
TEXT_LIGHT = RGBColor(0xFF, 0xFF, 0xFF)
TEXT_MUTED = RGBColor(0x88, 0x88, 0x88)
GRAY_BG = RGBColor(0xF5, 0xF5, 0xFA)
BORDER = RGBColor(0xE0, 0xE0, 0xE8)
HIGHLIGHT_BG = RGBColor(0xEE, 0xF2, 0xFF)


def set_slide_bg(slide, color):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_shape_bg(slide, left, top, width, height, color, border_color=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1)
    else:
        shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def add_text_box(slide, left, top, width, height, text, font_size=14,
                 bold=False, color=TEXT_DARK, alignment=PP_ALIGN.LEFT,
                 font_name="맑은 고딕"):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.font.name = font_name
    p.alignment = alignment
    return txBox


def add_bullet_list(slide, left, top, width, height, items, font_size=13,
                    color=TEXT_DARK, spacing=Pt(6)):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = item
        p.font.size = Pt(font_size)
        p.font.color.rgb = color
        p.font.name = "맑은 고딕"
        p.space_after = spacing
        p.level = 0


def add_table(slide, left, top, width, height, rows, cols, data,
              col_widths=None, header_color=ACCENT, font_size=11):
    table_shape = slide.shapes.add_table(rows, cols, left, top, width, height)
    table = table_shape.table

    if col_widths:
        for i, w in enumerate(col_widths):
            table.columns[i].width = Inches(w)

    for r in range(rows):
        for c in range(cols):
            cell = table.cell(r, c)
            cell.text = str(data[r][c])
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE

            for paragraph in cell.text_frame.paragraphs:
                paragraph.font.size = Pt(font_size)
                paragraph.font.name = "맑은 고딕"
                paragraph.alignment = PP_ALIGN.CENTER

                if r == 0:
                    paragraph.font.bold = True
                    paragraph.font.color.rgb = TEXT_LIGHT
                else:
                    paragraph.font.color.rgb = TEXT_DARK

            if r == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = header_color
            elif r % 2 == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = GRAY_BG
            else:
                cell.fill.solid()
                cell.fill.fore_color.rgb = BG_WHITE

    return table_shape


def add_accent_bar(slide, left, top, width, height, color=ACCENT):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


def add_page_number(slide, num, total):
    add_text_box(slide, Inches(8.8), Inches(6.9), Inches(1), Inches(0.3),
                 f"{num}/{total}", font_size=9, color=TEXT_MUTED,
                 alignment=PP_ALIGN.RIGHT)


# ════════════════════════════════════════
# Build Presentation
# ════════════════════════════════════════

prs = Presentation()
prs.slide_width = Inches(10)
prs.slide_height = Inches(7.5)

TOTAL_SLIDES = 12

# ── Slide 1: Title ──
slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
set_slide_bg(slide, BG_DARK)

add_accent_bar(slide, Inches(0.8), Inches(1.5), Inches(0.08), Inches(2.5), ACCENT)

add_text_box(slide, Inches(1.2), Inches(1.5), Inches(7.5), Inches(1.2),
             "멀티 에이전트 팀은\n언제 멈춰야 하는가?",
             font_size=36, bold=True, color=TEXT_LIGHT)

add_text_box(slide, Inches(1.2), Inches(3.0), Inches(7.5), Inches(0.8),
             "13가지 조정 토폴로지에서의 종료 역학 체계적 연구",
             font_size=18, color=ACCENT)

add_text_box(slide, Inches(1.2), Inches(4.2), Inches(7.5), Inches(0.5),
             "When Should Multi-Agent Teams Stop?",
             font_size=13, color=TEXT_MUTED)
add_text_box(slide, Inches(1.2), Inches(4.6), Inches(7.5), Inches(0.5),
             "A Systematic Study of Termination Dynamics Across 13 Coordination Topologies",
             font_size=11, color=TEXT_MUTED)

add_text_box(slide, Inches(1.2), Inches(5.6), Inches(7.5), Inches(0.5),
             "2026.02  |  COLM 2026 / ACL Workshops 투고 예정",
             font_size=12, color=TEXT_MUTED)

add_page_number(slide, 1, TOTAL_SLIDES)


# ── Slide 2: Problem & Motivation ──
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_WHITE)

add_accent_bar(slide, Inches(0), Inches(0), Inches(10), Inches(0.06), ACCENT)
add_text_box(slide, Inches(0.8), Inches(0.4), Inches(8), Inches(0.6),
             "연구 동기: 왜 종료(Termination)가 문제인가?",
             font_size=24, bold=True, color=TEXT_DARK)

# Left column - problem
add_shape_bg(slide, Inches(0.5), Inches(1.3), Inches(4.2), Inches(2.5), HIGHLIGHT_BG, BORDER)
add_text_box(slide, Inches(0.7), Inches(1.4), Inches(3.8), Inches(0.4),
             "현재 종료 기준 (획일적 적용)", font_size=14, bold=True, color=ACCENT)
add_bullet_list(slide, Inches(0.7), Inches(1.9), Inches(3.8), Inches(1.8), [
    "• 고정 턴 수 (max_turns = 10)",
    "• 키워드 감지 (\"TERMINATE\")",
    "• 외부 타임아웃 신호",
    "",
    "→ 팀 구조와 무관하게 동일 적용",
    "→ 종료 후회(Termination Regret) 발생"
], font_size=12)

# Right column - scenarios
add_shape_bg(slide, Inches(5.1), Inches(1.3), Inches(4.4), Inches(2.5), GRAY_BG, BORDER)
add_text_box(slide, Inches(5.3), Inches(1.4), Inches(4.0), Inches(0.4),
             "3가지 실패 시나리오", font_size=14, bold=True, color=ACCENT3)

scenarios = [
    "과잉 종료: 합의 후에도 토론 계속 → 토큰 낭비",
    "과소 종료: 정제 단계 전 중단 → 품질 손실",
    "토폴로지 불일치: 잘못된 기준 적용 → 기능 손실"
]
add_bullet_list(slide, Inches(5.3), Inches(1.9), Inches(4.0), Inches(1.8),
                [f"❌ {s}" for s in scenarios], font_size=11, spacing=Pt(10))

# Gap box
add_shape_bg(slide, Inches(0.5), Inches(4.1), Inches(9.0), Inches(1.5), RGBColor(0xFF, 0xF8, 0xE1), ACCENT4)
add_text_box(slide, Inches(0.7), Inches(4.2), Inches(8.6), Inches(0.4),
             "선행 연구의 갭 (Gap)", font_size=14, bold=True, color=ACCENT4)
add_bullet_list(slide, Inches(0.7), Inches(4.7), Inches(8.6), Inches(0.8), [
    "• Hu et al. (NeurIPS 2025): debate 전용 종료만 다룸",
    "• REFRAIN (2025): 단일 에이전트 CoT 전용  |  Aegean (2025): 병렬 합의 전용",
    "→ 다양한 토폴로지를 통합 프레임워크에서 체계 비교한 연구 = 없음"
], font_size=11)

# Bottom highlight
add_shape_bg(slide, Inches(0.5), Inches(5.9), Inches(9.0), Inches(1.0), ACCENT)
add_text_box(slide, Inches(0.7), Inches(6.05), Inches(8.6), Inches(0.7),
             "핵심 통찰: 최적 종료 시점은 에이전트의 조정 방식(토폴로지)에 근본적으로 의존한다",
             font_size=15, bold=True, color=TEXT_LIGHT, alignment=PP_ALIGN.CENTER)

add_page_number(slide, 2, TOTAL_SLIDES)


# ── Slide 3: Contributions ──
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_WHITE)
add_accent_bar(slide, Inches(0), Inches(0), Inches(10), Inches(0.06), ACCENT)

add_text_box(slide, Inches(0.8), Inches(0.4), Inches(8), Inches(0.6),
             "5대 기여 (Contributions)", font_size=24, bold=True, color=TEXT_DARK)

contribs = [
    ("1", "교차 토폴로지 종료 비교", "13패턴, 4범주를 동일 프레임워크(AutoGen)·동일 모델·동일 과제로 최초 체계 비교", ACCENT),
    ("2", "종료 후회 지표", "G-Eval 턴별 품질 궤적으로 최적 vs. 실제 종료 시점 정밀 비교", ACCENT2),
    ("3", "주장 수준 수렴 감지", "Hu et al.의 KS-검정을 debate → 전체 13개 토폴로지로 확장", ACCENT4),
    ("4", "패턴별 오류 분류", "토폴로지 특성과 오류 유형(환각/불완전/불일치) 상관 규명", ACCENT3),
    ("5", "적응적 종료 메커니즘", "U(t) = Q(t) - λ·C(t)  — REFRAIN/Aegean과 차별화된 효용 기반 종료", RGBColor(0x9B, 0x59, 0xB6)),
]

for i, (num, title, desc, color) in enumerate(contribs):
    y = 1.2 + i * 1.15
    add_shape_bg(slide, Inches(0.5), Inches(y), Inches(9.0), Inches(1.0), BG_WHITE, BORDER)
    # Number circle
    circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.7), Inches(y + 0.15), Inches(0.55), Inches(0.55))
    circle.fill.solid()
    circle.fill.fore_color.rgb = color
    circle.line.fill.background()
    tf = circle.text_frame
    tf.paragraphs[0].text = num
    tf.paragraphs[0].font.size = Pt(18)
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.color.rgb = TEXT_LIGHT
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER

    add_text_box(slide, Inches(1.5), Inches(y + 0.08), Inches(7.8), Inches(0.4),
                 title, font_size=15, bold=True, color=TEXT_DARK)
    add_text_box(slide, Inches(1.5), Inches(y + 0.5), Inches(7.8), Inches(0.4),
                 desc, font_size=11, color=TEXT_MUTED)

add_page_number(slide, 3, TOTAL_SLIDES)


# ── Slide 4: Experimental Design ──
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_WHITE)
add_accent_bar(slide, Inches(0), Inches(0), Inches(10), Inches(0.06), ACCENT)

add_text_box(slide, Inches(0.8), Inches(0.4), Inches(8), Inches(0.6),
             "실험 설계: 13 패턴 × 4 범주", font_size=24, bold=True, color=TEXT_DARK)

# Category boxes
cats = [
    ("A. 고정 순차", "RR-2, RR-3, RR-4", "라운드 로빈\n고정 순서 순환", ACCENT),
    ("B. 동적 라우팅", "Sel-3/4, Swm-3/4", "조정자가 다음\n에이전트 선택", ACCENT2),
    ("C. 구조화 피드백", "Refl-2/3, Deb-3/4", "반성(생성+비평)\n토론(논거 교환)", ACCENT4),
    ("D. 복합/중첩", "Pipe, MoA", "파이프라인\n병렬 집약", ACCENT3),
]

for i, (cat, patterns, desc, color) in enumerate(cats):
    x = 0.5 + i * 2.35
    box = add_shape_bg(slide, Inches(x), Inches(1.3), Inches(2.15), Inches(2.5), BG_WHITE, color)
    # Header bar
    add_shape_bg(slide, Inches(x), Inches(1.3), Inches(2.15), Inches(0.45), color)
    add_text_box(slide, Inches(x + 0.1), Inches(1.32), Inches(1.95), Inches(0.4),
                 cat, font_size=13, bold=True, color=TEXT_LIGHT, alignment=PP_ALIGN.CENTER)
    add_text_box(slide, Inches(x + 0.1), Inches(1.9), Inches(1.95), Inches(0.5),
                 patterns, font_size=12, bold=True, color=TEXT_DARK, alignment=PP_ALIGN.CENTER)
    add_text_box(slide, Inches(x + 0.1), Inches(2.5), Inches(1.95), Inches(1.0),
                 desc, font_size=10, color=TEXT_MUTED, alignment=PP_ALIGN.CENTER)

# Experiment table
add_text_box(slide, Inches(0.8), Inches(4.1), Inches(8), Inches(0.4),
             "5개 실험 (총 ~1,760회 실행)", font_size=16, bold=True, color=TEXT_DARK)

exp_data = [
    ["실험", "목표", "실행 수", "상태"],
    ["01: 패턴 효율", "토폴로지별 비용 비교", "780", "98% 완료"],
    ["02: 종료 품질", "G-Eval 턴별 품질 궤적", "260", "대기"],
    ["03: 수렴 감지", "KS-검정 안정성", "분석", "Cat A 완료"],
    ["04: 오류 귀인", "패턴별 오류 분류", "분석", "Cat A 완료"],
    ["05: 적응적 종료", "U(t)=Q(t)-λC(t) 검증", "720", "대기"],
]
add_table(slide, Inches(0.5), Inches(4.6), Inches(9.0), Inches(2.4),
          len(exp_data), 4, exp_data, col_widths=[2.0, 3.0, 1.5, 2.5], font_size=11)

add_page_number(slide, 4, TOTAL_SLIDES)


# ── Slide 5: Progress Status ──
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_WHITE)
add_accent_bar(slide, Inches(0), Inches(0), Inches(10), Inches(0.06), ACCENT)

add_text_box(slide, Inches(0.8), Inches(0.4), Inches(8), Inches(0.6),
             "실험 01 진행 현황 (764/780 완료)", font_size=24, bold=True, color=TEXT_DARK)

prog_data = [
    ["범주", "패턴", "실행 수", "에러율", "상태"],
    ["A (고정 순차)", "rr2, rr3, rr4", "180/180", "rr2:8.3% rr3:23.3%*", "✅ 완료"],
    ["B (동적 라우팅)", "sel3, sel4, swm3, swm4", "240/240", "0%", "✅ 완료"],
    ["C (구조화 피드백)", "refl2, refl3, deb3, deb4", "240/240", "0%", "✅ 완료"],
    ["D (복합) pipe", "pipe", "60/60", "0%", "✅ 완료"],
    ["D (복합) moa", "moa", "44/60 진행중", "0%", "🔄 실행중"],
]
add_table(slide, Inches(0.5), Inches(1.3), Inches(9.0), Inches(2.5),
          len(prog_data), 5, prog_data, col_widths=[2.0, 2.5, 1.5, 2.0, 1.0], font_size=11)

add_text_box(slide, Inches(0.5), Inches(4.0), Inches(9.0), Inches(0.4),
             "*Cat A 에러는 인프라 버그(prompt truncation)로 과대평가. Cat B 이후 코드 수정으로 0% 에러 달성.",
             font_size=10, color=TEXT_MUTED)

# Infrastructure box
add_shape_bg(slide, Inches(0.5), Inches(4.6), Inches(9.0), Inches(2.5), GRAY_BG, BORDER)
add_text_box(slide, Inches(0.7), Inches(4.7), Inches(8.6), Inches(0.4),
             "실험 인프라", font_size=15, bold=True, color=TEXT_DARK)
add_bullet_list(slide, Inches(0.7), Inches(5.2), Inches(4.0), Inches(1.8), [
    "• 프레임워크: AutoGen + 커스텀 ChatCompletionClient",
    "• 기반 모델: Claude Haiku 4.5 (일관성)",
    "• 평가 모델: Claude Sonnet 4.5 (G-Eval judge)",
], font_size=11)
add_bullet_list(slide, Inches(5.0), Inches(5.2), Inches(4.0), Inches(1.8), [
    "• 과제: 20개 (사실5/창의5/분석5/기술5) × 3반복",
    "• 지표: 지속시간, 턴수, 토큰(in/out), 오류율",
    "• 체크포인트: 패턴별 자동 저장 (장애 복구)",
], font_size=11)

add_page_number(slide, 5, TOTAL_SLIDES)


# ── Slide 6: Category A Results ──
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_WHITE)
add_accent_bar(slide, Inches(0), Inches(0), Inches(10), Inches(0.06), ACCENT)

add_text_box(slide, Inches(0.8), Inches(0.4), Inches(8), Inches(0.6),
             "범주 A: 고정 순차 (Round-Robin)", font_size=24, bold=True, color=TEXT_DARK)

cat_a_data = [
    ["패턴", "에이전트", "시간(초)", "총 토큰", "출력/턴", "에러율"],
    ["RR-2", "2명", "52.4", "4,759", "1,583", "8.3%"],
    ["RR-3", "3명", "96.6", "10,121", "1,711", "23.3%"],
    ["RR-4", "4명", "118.8", "12,040", "1,942", "71.7%*"],
]
add_table(slide, Inches(0.5), Inches(1.2), Inches(9.0), Inches(1.6),
          len(cat_a_data), 6, cat_a_data, col_widths=[1.2, 1.2, 1.3, 1.5, 1.5, 1.3])

# Finding boxes
findings_a = [
    ("발견 1", "협력적 증폭 (Collaborative Amplification)",
     "호출당 출력 토큰 증가: rr2=930 → rr3=1,189 → rr4=1,544\n에이전트가 더 풍부한 컨텍스트에서 더 풍부한 응답 생성", ACCENT),
    ("발견 2", "입력 토큰 초선형 증가",
     "입력 2.59배 증가 vs LLM호출 1.75배\n비용의 주 동인 = 각 에이전트가 전체 대화 이력을 읽는 것", ACCENT2),
    ("발견 3", "오류율 초선형 증가",
     "rr2: 기술형만(8.3%) → rr3: 3개 범주(23.3%) → rr4: 전면 실패(71.7%)\n컨텍스트 축적이 팀 규모에 따라 한계 초과", ACCENT3),
]

for i, (label, title, desc, color) in enumerate(findings_a):
    y = 3.1 + i * 1.4
    add_accent_bar(slide, Inches(0.5), Inches(y), Inches(0.08), Inches(1.2), color)
    add_text_box(slide, Inches(0.8), Inches(y), Inches(1.2), Inches(0.3),
                 label, font_size=10, bold=True, color=color)
    add_text_box(slide, Inches(2.0), Inches(y), Inches(7.3), Inches(0.3),
                 title, font_size=13, bold=True, color=TEXT_DARK)
    add_text_box(slide, Inches(2.0), Inches(y + 0.4), Inches(7.3), Inches(0.9),
                 desc, font_size=11, color=TEXT_MUTED)

add_page_number(slide, 6, TOTAL_SLIDES)


# ── Slide 7: Category B Results ──
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_WHITE)
add_accent_bar(slide, Inches(0), Inches(0), Inches(10), Inches(0.06), ACCENT2)

add_text_box(slide, Inches(0.8), Inches(0.4), Inches(8), Inches(0.6),
             "범주 B: 동적 라우팅 (Selector / Swarm)", font_size=24, bold=True, color=TEXT_DARK)

cat_b_data = [
    ["패턴", "시간(초)", "총 토큰", "턴 수", "출력/턴", "특징"],
    ["Sel-3", "115.2", "7,851", "3.5", "2,114", "적은 턴 + 긴 독백"],
    ["Sel-4", "161.9", "11,595", "4.1", "2,616", "서브리니어 (1.48x)"],
    ["Swm-3", "75.2", "4,196 ★", "10.2", "337", "최고 효율!"],
    ["Swm-4", "185.0", "13,321", "25.0", "330", "턴 폭발 (3.17x)"],
]
add_table(slide, Inches(0.5), Inches(1.2), Inches(9.0), Inches(2.0),
          len(cat_b_data), 6, cat_b_data, col_widths=[1.2, 1.3, 1.5, 1.2, 1.3, 2.5])

findings_b = [
    ("발견 5", "두 라우팅 전략 = 완전히 다른 행동",
     "Selector: 적은 턴(3.5) + 긴 독백(2,100tok/턴) vs Swarm: 많은 턴(10) + 짧은 핸드오프(330tok/턴)", ACCENT2),
    ("발견 6", "스케일링 방향이 정반대",
     "Selector: 서브-리니어(1.48x/+1agent) vs Swarm: 슈퍼-리니어(3.17x/+1agent, 턴 폭발)", ACCENT4),
    ("발견 7", "Swm-3 = 전체 최고 토큰 효율",
     "3에이전트(4,196tok)가 2에이전트 RR-2(4,759tok)보다 12% 저렴! → 지능적 라우팅이 에이전트 추가 오버헤드를 상쇄", ACCENT),
]

for i, (label, title, desc, color) in enumerate(findings_b):
    y = 3.5 + i * 1.2
    add_accent_bar(slide, Inches(0.5), Inches(y), Inches(0.08), Inches(1.0), color)
    add_text_box(slide, Inches(0.8), Inches(y), Inches(1.2), Inches(0.3),
                 label, font_size=10, bold=True, color=color)
    add_text_box(slide, Inches(2.0), Inches(y), Inches(7.3), Inches(0.3),
                 title, font_size=13, bold=True, color=TEXT_DARK)
    add_text_box(slide, Inches(2.0), Inches(y + 0.35), Inches(7.3), Inches(0.7),
                 desc, font_size=11, color=TEXT_MUTED)

add_page_number(slide, 7, TOTAL_SLIDES)


# ── Slide 8: Category C Results ──
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_WHITE)
add_accent_bar(slide, Inches(0), Inches(0), Inches(10), Inches(0.06), ACCENT4)

add_text_box(slide, Inches(0.8), Inches(0.4), Inches(8), Inches(0.6),
             "범주 C: 구조화 피드백 (Reflection / Debate)", font_size=24, bold=True, color=TEXT_DARK)

cat_c_data = [
    ["패턴", "시간(초)", "총 토큰", "턴 수", "출력/턴", "특징"],
    ["Refl-2", "60.2", "5,237", "3.2", "1,732", "2위 효율 + 품질검증"],
    ["Refl-3", "120.2", "12,095", "4.5", "2,537", "슈퍼리니어 (2.31x)"],
    ["Deb-3", "156.6", "9,313", "4.5", "1,691", "토론 → 서브리니어"],
    ["Deb-4", "180.9", "11,637", "5.4", "1,448 ↓", "수확체감"],
]
add_table(slide, Inches(0.5), Inches(1.2), Inches(9.0), Inches(2.0),
          len(cat_c_data), 6, cat_c_data, col_widths=[1.2, 1.3, 1.5, 1.2, 1.3, 2.5])

findings_c = [
    ("발견 8", "반성과 토론의 스케일링이 정반대",
     "반성: 슈퍼-리니어(2.31x) — 비평이 전체 이력 리뷰  |  토론: 서브-리니어(1.25x) — 중재자가 오버헤드 흡수", ACCENT4),
    ("발견 9", "Refl-2 = 최소 비용으로 품질 검증",
     "RR-2(4,759)보다 10%만 비쌈(5,237). 하지만 비평가의 구조화된 품질 검증 루프를 포함 → 품질 보증이 필요할 때 최적", ACCENT2),
    ("발견 11", "Debate에서 팀 성장 시 에이전트당 출력 감소",
     "deb3=1,691 → deb4=1,448 (0.86x). Cat A의 '협력적 증폭'과 정반대 → 토론 구조가 발언량을 자연적으로 제약", ACCENT3),
]

for i, (label, title, desc, color) in enumerate(findings_c):
    y = 3.5 + i * 1.2
    add_accent_bar(slide, Inches(0.5), Inches(y), Inches(0.08), Inches(1.0), color)
    add_text_box(slide, Inches(0.8), Inches(y), Inches(1.2), Inches(0.3),
                 label, font_size=10, bold=True, color=color)
    add_text_box(slide, Inches(2.0), Inches(y), Inches(7.3), Inches(0.3),
                 title, font_size=13, bold=True, color=TEXT_DARK)
    add_text_box(slide, Inches(2.0), Inches(y + 0.35), Inches(7.3), Inches(0.7),
                 desc, font_size=11, color=TEXT_MUTED)

add_page_number(slide, 8, TOTAL_SLIDES)


# ── Slide 9: Category D + Cross-Category ──
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_WHITE)
add_accent_bar(slide, Inches(0), Inches(0), Inches(10), Inches(0.06), ACCENT3)

add_text_box(slide, Inches(0.8), Inches(0.4), Inches(8), Inches(0.6),
             "범주 D + 교차 범주 효율 랭킹", font_size=24, bold=True, color=TEXT_DARK)

# Cat D box
add_shape_bg(slide, Inches(0.5), Inches(1.2), Inches(4.2), Inches(2.0), GRAY_BG, BORDER)
add_text_box(slide, Inches(0.7), Inches(1.3), Inches(3.8), Inches(0.4),
             "범주 D: 복합/중첩", font_size=15, bold=True, color=ACCENT3)
add_bullet_list(slide, Inches(0.7), Inches(1.8), Inches(3.8), Inches(1.3), [
    "• Pipe: 129.6초, 13,856 토큰, 2,325 out/턴",
    "  → 턴당 출력 최고, 가장 비쌈",
    "  → tech 과제 19,223 tok (극단적 비용)",
    "• MoA: 3명 병렬 제안 → 1명 집약",
    "  → 현재 실행 중 (에러 0%)"
], font_size=11)

# Ranking
add_text_box(slide, Inches(5.0), Inches(1.2), Inches(4.5), Inches(0.4),
             "토큰 효율 랭킹 (TOP 5)", font_size=15, bold=True, color=TEXT_DARK)

rank_data = [
    ["순위", "패턴", "범주", "토큰"],
    ["1위", "Swm-3", "B (동적)", "4,196"],
    ["2위", "RR-2", "A (순차)", "4,759"],
    ["3위", "Refl-2", "C (피드백)", "5,237"],
    ["4위", "Sel-3", "B (동적)", "7,851"],
    ["5위", "Deb-3", "C (피드백)", "9,313"],
]
add_table(slide, Inches(5.0), Inches(1.7), Inches(4.5), Inches(2.2),
          len(rank_data), 4, rank_data, col_widths=[0.8, 1.2, 1.2, 1.3], font_size=11)

# Key insight box
add_shape_bg(slide, Inches(0.5), Inches(3.5), Inches(9.0), Inches(1.2), HIGHLIGHT_BG, ACCENT)
add_text_box(slide, Inches(0.7), Inches(3.6), Inches(8.6), Inches(0.4),
             "핵심 인사이트", font_size=15, bold=True, color=ACCENT)
add_bullet_list(slide, Inches(0.7), Inches(4.1), Inches(8.6), Inches(0.5), [
    "• 토폴로지 선택이 에이전트 수보다 효율에 더 큰 영향 — Swm-3(3명)이 RR-2(2명)보다 저렴",
    "• 동일 에이전트 수에서도 라우팅 전략에 따라 3배 이상 비용 차이 (swm3=4,196 vs refl3=12,095)"
], font_size=12)

# Scaling comparison box
add_shape_bg(slide, Inches(0.5), Inches(5.0), Inches(9.0), Inches(2.0), GRAY_BG, BORDER)
add_text_box(slide, Inches(0.7), Inches(5.1), Inches(8.6), Inches(0.4),
             "스케일링 행동 요약 (+1 에이전트 추가 시)", font_size=14, bold=True, color=TEXT_DARK)

scale_data = [
    ["토폴로지", "스케일링", "배수", "원인"],
    ["RR (순차)", "준선형", "~2.0x", "전체 이력 복사"],
    ["Selector", "서브-리니어", "1.48x", "라우팅 효율화"],
    ["Swarm", "슈퍼-리니어", "3.17x", "턴 수 폭발"],
    ["Reflection", "슈퍼-리니어", "2.31x", "이력 누적 리뷰"],
    ["Debate", "서브-리니어", "1.25x", "중재자 흡수"],
]
add_table(slide, Inches(0.5), Inches(5.5), Inches(9.0), Inches(1.5),
          len(scale_data), 4, scale_data, col_widths=[2.0, 2.0, 1.5, 3.5], font_size=10)

add_page_number(slide, 9, TOTAL_SLIDES)


# ── Slide 10: Adaptive Termination (Original Contribution) ──
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_WHITE)
add_accent_bar(slide, Inches(0), Inches(0), Inches(10), Inches(0.06), RGBColor(0x9B, 0x59, 0xB6))

add_text_box(slide, Inches(0.8), Inches(0.4), Inches(8), Inches(0.6),
             "오리지널 기여: 효용 기반 적응적 종료", font_size=24, bold=True, color=TEXT_DARK)

# Formula box
add_shape_bg(slide, Inches(1.5), Inches(1.2), Inches(7.0), Inches(1.4), BG_DARK)
add_text_box(slide, Inches(1.7), Inches(1.35), Inches(6.6), Inches(0.6),
             "U(t) = Q(t) - λ · C(t)", font_size=32, bold=True, color=ACCENT,
             alignment=PP_ALIGN.CENTER)
add_text_box(slide, Inches(1.7), Inches(2.0), Inches(6.6), Inches(0.5),
             "종료 조건:  U(t) < U(t-1)  →  한계비용 > 한계품질이득  →  멈춤",
             font_size=13, color=TEXT_LIGHT, alignment=PP_ALIGN.CENTER)

# Variable explanation
add_bullet_list(slide, Inches(0.7), Inches(2.9), Inches(4.0), Inches(1.5), [
    "Q(t) : 턴 t에서의 품질 (G-Eval 5차원)",
    "C(t) : 누적 토큰 비용 (정규화)",
    "λ    : 품질-비용 트레이드오프 계수",
    "       → 토폴로지별 다르게 튜닝 (핵심!)"
], font_size=12)

# Comparison table
comp_data = [
    ["", "REFRAIN", "Aegean", "본 연구"],
    ["대상", "단일 에이전트 CoT", "병렬 합의", "13개 토폴로지"],
    ["방법", "판별기 + UCB", "쿼럼 감지", "효용함수 U(t)"],
    ["λ 처리", "고정", "해당없음", "토폴로지 인식"],
    ["실험 규모", "1 설정", "1 설정", "13 패턴 × 5λ"],
]
add_table(slide, Inches(5.0), Inches(2.9), Inches(4.5), Inches(2.0),
          len(comp_data), 4, comp_data, col_widths=[1.0, 1.2, 1.1, 1.2], font_size=10,
          header_color=RGBColor(0x9B, 0x59, 0xB6))

# Lambda insight
add_shape_bg(slide, Inches(0.5), Inches(5.2), Inches(9.0), Inches(1.8), HIGHLIGHT_BG, RGBColor(0x9B, 0x59, 0xB6))
add_text_box(slide, Inches(0.7), Inches(5.3), Inches(8.6), Inches(0.4),
             "토폴로지 인식 λ 튜닝 — 왜 중요한가?", font_size=14, bold=True, color=RGBColor(0x9B, 0x59, 0xB6))
add_bullet_list(slide, Inches(0.7), Inches(5.8), Inches(8.6), Inches(1.0), [
    "• 피드백 패턴 (Cat C): 높은 λ 허용 → 자연 수렴 신호가 있어 일찍 멈춰도 품질 유지",
    "• 순차 패턴 (Cat A): 낮은 λ 필요 → 수렴 신호 없어 조기 종료 시 품질 손실",
    "• 동적 라우팅 (Cat B): 중간 λ → 조정자 오버헤드를 비용에 포함해야 공정",
    "→ 하나의 λ로 모든 토폴로지를 커버할 수 없음 = 토폴로지 인식의 필요성"
], font_size=11)

add_page_number(slide, 10, TOTAL_SLIDES)


# ── Slide 11: Timeline & Venue ──
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_WHITE)
add_accent_bar(slide, Inches(0), Inches(0), Inches(10), Inches(0.06), ACCENT)

add_text_box(slide, Inches(0.8), Inches(0.4), Inches(8), Inches(0.6),
             "투고 전략 & 향후 일정", font_size=24, bold=True, color=TEXT_DARK)

# Venue boxes
add_shape_bg(slide, Inches(0.5), Inches(1.2), Inches(4.2), Inches(2.0), HIGHLIGHT_BG, ACCENT)
add_text_box(slide, Inches(0.7), Inches(1.3), Inches(3.8), Inches(0.4),
             "1순위: COLM 2026", font_size=16, bold=True, color=ACCENT)
add_bullet_list(slide, Inches(0.7), Inches(1.8), Inches(3.8), Inches(1.3), [
    "• Abstract 마감: 2026-03-26",
    "• Full paper 마감: 2026-03-31",
    "• ML 시스템 특화 학회",
    "• 멀티에이전트 논문 수용적"
], font_size=11)

add_shape_bg(slide, Inches(5.3), Inches(1.2), Inches(4.2), Inches(2.0), GRAY_BG, BORDER)
add_text_box(slide, Inches(5.5), Inches(1.3), Inches(3.8), Inches(0.4),
             "보험: ACL 2026 Workshops", font_size=16, bold=True, color=TEXT_DARK)
add_bullet_list(slide, Inches(5.5), Inches(1.8), Inches(3.8), Inches(1.3), [
    "• Direct submission: 2026-03-05",
    "• 빠른 1차 발표 기회 확보",
    "• 워크숍 = 진행중 연구 수용",
    "• 국내 학회 동시 투고 가능?"
], font_size=11)

# Timeline
add_text_box(slide, Inches(0.8), Inches(3.5), Inches(8), Inches(0.4),
             "예상 일정 (COLM 기준)", font_size=16, bold=True, color=TEXT_DARK)

timeline_data = [
    ["기간", "작업", "상태"],
    ["2/11-14", "exp01 완료 (moa) + 전체 merge + 분석", "진행중"],
    ["2/15-18", "exp02 (품질 궤적) + exp05 (적응적 종료)", "대기"],
    ["2/19-25", "전체 분석 + 그래프 + 논문 수정", "대기"],
    ["2/26-3/5", "ACL Workshop 제출 가능", "대기"],
    ["3/6-25", "추가 실험 + 논문 정제", "대기"],
    ["3/26", "COLM Abstract 제출", "목표"],
    ["3/31", "COLM Full Paper 제출", "목표"],
]
add_table(slide, Inches(0.5), Inches(4.0), Inches(9.0), Inches(3.0),
          len(timeline_data), 3, timeline_data, col_widths=[2.0, 5.0, 2.0], font_size=11)

add_page_number(slide, 11, TOTAL_SLIDES)


# ── Slide 12: Discussion Points ──
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide, BG_DARK)

add_accent_bar(slide, Inches(0.8), Inches(0.8), Inches(0.08), Inches(1.0), ACCENT)
add_text_box(slide, Inches(1.2), Inches(0.8), Inches(7.5), Inches(0.6),
             "논의 포인트", font_size=28, bold=True, color=TEXT_LIGHT)
add_text_box(slide, Inches(1.2), Inches(1.4), Inches(7.5), Inches(0.4),
             "교수님과 함께 결정해야 할 사항", font_size=14, color=TEXT_MUTED)

questions = [
    ("Q1", "투고처 우선순위", "COLM 2026 (메인) vs ACL Workshop (보험) — 어디를 우선할까요?", ACCENT),
    ("Q2", "실험 범위", "5개 실험 중 COLM 제출 최소 필수는 exp01+exp02+exp05.\nexp03/04는 부록으로 가능. 범위 축소 의견은?", ACCENT2),
    ("Q3", "품질 평가기", "G-Eval (Claude Sonnet 4.5 judge) 단독 vs 2차 평가기 추가?\n비용 2배이지만 로버스트니스 확보", ACCENT4),
    ("Q4", "교차 모델 일반화", "Claude Haiku 단독 vs GPT-4o-mini 추가 비교?\n일반화 주장 강화 but 비용+시간 2배", ACCENT3),
    ("Q5", "국내 학회", "한국정보과학회/한국소프트웨어공학회 동시 투고 가능성?\n한글 논문 초안 이미 완성", RGBColor(0x9B, 0x59, 0xB6)),
]

for i, (label, title, desc, color) in enumerate(questions):
    y = 2.2 + i * 1.0
    circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(1.0), Inches(y + 0.05), Inches(0.45), Inches(0.45))
    circle.fill.solid()
    circle.fill.fore_color.rgb = color
    circle.line.fill.background()
    tf = circle.text_frame
    tf.paragraphs[0].text = label
    tf.paragraphs[0].font.size = Pt(9)
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.color.rgb = TEXT_LIGHT
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER

    add_text_box(slide, Inches(1.7), Inches(y), Inches(2.0), Inches(0.35),
                 title, font_size=13, bold=True, color=TEXT_LIGHT)
    add_text_box(slide, Inches(3.7), Inches(y), Inches(5.5), Inches(0.5),
                 desc, font_size=10, color=TEXT_MUTED)

add_page_number(slide, 12, TOTAL_SLIDES)


# ── Save ──
output_path = "presentation_kr.pptx"
prs.save(output_path)
print(f"PPT saved: {output_path}")
print(f"Total slides: {TOTAL_SLIDES}")
