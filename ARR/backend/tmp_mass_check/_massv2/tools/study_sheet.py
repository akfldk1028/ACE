"""Three schemes, each with its name, its argument, and how it was made.

The contact sheet is a workbench. Every convention this project is measured
against publishes the other thing: AIA B101 and RIBA Stage 2 both pair the
volume with drawings; a Korean 매스 다이어그램 is ONE scheme carrying its
operation sequence rather than a grid of alternatives; Seattle's design
review asks for exactly three, each with its reasoning written out; OMA's
options are named ("Donkey Kong", "Mixing Chamber") because an option you
cannot name is not an option. A sheet of forty is one option sampled forty
times, and the architect reading it says so every time.

So this tool ships what the sheet was always supposed to be: three schemes,
each with the sentence that argues it, the frames that made it, the mass as
delivered, its legal numbers, and one of them recommended.

    python tools/study_sheet.py <run> [out-name]

Picks by jury score when the run has been judged, and by the run's own
selection order when it has not.
"""

import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from band_probe import corpus  # noqa: E402
from finalists import BUILDING_TYPE, PNU, rebuild  # noqa: E402
from design.maas.massv2 import composition as composition_module  # noqa: E402
from design.maas.massv2.legal import load_legal_site  # noqa: E402
from design.maas.massv2.measure import gross_floor_area_m2  # noqa: E402
from design.maas.massv2.render import render_masses  # noqa: E402
from design.maas.massv2.siting import open_side_direction  # noqa: E402
from vlm_shortlist import certified_caption  # noqa: E402

STYLE = """<title>매스 스터디 3안</title>
<style>
:root { --ink:#1a1a18; --muted:#84847c; --line:#e0e0da; --bg:#fcfcfa; --pick:#a8501a; }
body { background:var(--bg); color:var(--ink); margin:0;
  font-family:"Inter","Pretendard",-apple-system,"Malgun Gothic",sans-serif;
  line-height:1.6; }
main { max-width:1180px; margin:0 auto; padding:44px 28px 100px; }
header { border-bottom:1px solid var(--ink); padding-bottom:14px; margin-bottom:34px; }
h1 { font-size:19px; font-weight:600; margin:0 0 4px; letter-spacing:-0.01em; }
header p { margin:0; color:var(--muted); font-size:12.5px; }
section { border-bottom:1px solid var(--line); padding:30px 0 34px; }
.head { display:flex; align-items:baseline; gap:12px; flex-wrap:wrap; margin-bottom:6px; }
h2 { font-size:17px; font-weight:600; margin:0; }
.tag { font-size:11px; letter-spacing:0.08em; text-transform:uppercase;
  color:var(--muted); border:1px solid var(--line); padding:2px 8px; border-radius:2px; }
.pick { color:var(--pick); border-color:var(--pick); }
.thesis { font-size:14px; max-width:74ch; margin:0 0 18px; }
.mass { display:grid; grid-template-columns:minmax(280px,1fr) minmax(280px,1.1fr); gap:22px;
  align-items:start; }
img { display:block; width:100%; height:auto; border:1px solid var(--line); background:#fff; }
.facts { font-size:12.5px; color:var(--muted); margin:14px 0 0; }
.facts b { color:var(--ink); font-weight:600; }
.seq { margin-top:20px; }
.seq h3 { font-size:11px; letter-spacing:0.1em; text-transform:uppercase;
  color:var(--muted); margin:0 0 8px; font-weight:600; }
footer { margin-top:36px; color:var(--muted); font-size:12px; }
h2.rest { font-size:12px; letter-spacing:0.12em; text-transform:uppercase;
  color:var(--muted); margin:40px 0 10px; font-weight:600; }
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); gap:0;
  border-left:1px solid var(--line); border-top:1px solid var(--line); }
.grid figure { margin:0; border-right:1px solid var(--line);
  border-bottom:1px solid var(--line); background:#fff; }
.grid img { border:0; }
.grid figcaption { padding:6px 10px 9px; font-size:11px; color:var(--muted);
  border-top:1px solid var(--line); }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { --bg:#141413; --ink:#f0efe9; --line:#33322e;
    --muted:#8a8a84; --pick:#e0a06a; }
}
:root[data-theme="dark"] { --bg:#141413; --ink:#f0efe9; --line:#33322e;
  --muted:#8a8a84; --pick:#e0a06a; }
</style>
"""


def _trimmed(text: str, limit: int = 165) -> str:
    """Cut a thesis at a word, not mid-syllable.

    The tile caption is a fixed width and the sentence was sliced at a
    character count, so a scheme's argument ended "the court is not a". The
    whole sentence is on the page below; the tile carries as much of it as
    fits and says so with an ellipsis.
    """

    text = str(text or "").strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    space = cut.rfind(" ")
    return (cut[:space] if space > limit // 2 else cut).rstrip(",;: ") + "…"


def _uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def _picks(run: str, book: dict) -> list[tuple[str, float | None]]:
    """Three schemes, best first, one per sentence.

    A jury score if the round was judged, the run's own selection order if it
    was not. One scheme per sentence, because two sizes of one idea are one
    option - which is the whole complaint this sheet answers.
    """

    scored = ROOT / "runs" / f"vlm-{run}" / "vlm-shortlist.json"
    rows: list[tuple[str, float | None]] = []
    if scored.exists():
        entries = json.loads(scored.read_text(encoding="utf-8"))
        entries.sort(key=lambda row: -(row.get("corrected") or row.get("score") or 0.0))
        rows = [(row["name"], float(row.get("corrected") or row.get("score") or 0.0))
                for row in entries if not row.get("anchor")]
    else:
        summary = json.loads((ROOT / "runs" / run / "massv2-summary.json")
                             .read_text(encoding="utf-8"))
        rows = [(record["name"], None) for record in summary["records"]
                if record.get("status") == "compiled"]
    seen: set[str] = set()
    picks: list[tuple[str, float | None]] = []
    for name, score in rows:
        sentence = name.split("~")[0].split("^")[0]
        if sentence in seen or sentence not in book:
            continue
        seen.add(sentence)
        picks.append((name, score))
        if len(picks) == 3:
            break
    return picks


def main(run: str, out_name: str = "") -> int:
    book = corpus()
    site = load_legal_site(PNU, building_type=BUILDING_TYPE)
    buildable = site.plan_at(0.0)
    axis = open_side_direction(buildable, site.shared_edges) or (1.0, 0.0)
    base = site.floor_height_m * max(
        1, int(site.far_capacity_m2 // max(1.0, site.ground_capacity_m2)))
    parcel = float(site.parcel_area_m2)

    out = ROOT / "runs" / (out_name or f"study-{run}")
    out.mkdir(parents=True, exist_ok=True)

    blocks = []
    for order, (name, score) in enumerate(_picks(run, book)):
        sentence = name.split("~")[0].split("^")[0]
        record = book[sentence]
        asked = max((float(op.get("storeys") or 0) for op in record["ops"]), default=0.0)
        source = rebuild(name, book, site, buildable, axis,
                         max(base, asked * site.floor_height_m))
        if source is None:
            continue
        tile = out / f"{order + 1}-{sentence}.png"
        gross = gross_floor_area_m2(source, floor_height_m=site.floor_height_m)
        # 건폐율 has one owner - the same certified caption every jury tile
        # carries. Read off `source.metadata` here it came back empty and the
        # sheet printed a dash where the number the architect checks first
        # belongs.
        caption = certified_caption(
            source, site, _trimmed(record.get("formal_principle", "")))
        render_masses(
            [(sentence.replace("_", " "), source, caption)],
            tile, site_ring=list(buildable.exterior.coords),
            columns=1, tile=(900, 800), style="massing")
        reading = composition_module.read(source)
        sequence = ROOT / "runs" / run / f"parti-{sentence}.png"
        blocks.append({
            "name": sentence.replace("_", " "),
            "thesis": record.get("formal_principle", ""),
            "moves": " → ".join(op["op"] for op in record["ops"]),
            "score": score,
            "reading": reading,
            "gross": gross,
            "tile": tile,
            "sequence": sequence if sequence.exists() else None,
            "recommended": order == 0,
        })
        print(f"  {order + 1}. {sentence}", flush=True)

    if not blocks:
        print("nothing to draw")
        return 1

    sections = []
    for block in blocks:
        reading = block["reading"]
        tag = ('<span class="tag pick">추천안</span>' if block["recommended"]
               else '<span class="tag">대안</span>')
        score = (f' · 심사 {block["score"]:.2f}/5' if block["score"] is not None else "")
        sequence = ""
        if block["sequence"] is not None:
            sequence = (
                '<div class="seq"><h3>이 안이 만들어진 순서</h3>'
                f'<img src="{_uri(block["sequence"])}" alt="operation sequence"></div>')
        sections.append(
            f'<section><div class="head">{tag}<h2>{block["name"]}</h2>'
            f'<span class="tag">{block["moves"]}</span></div>'
            f'<p class="thesis">{block["thesis"]}</p>'
            f'<div class="mass"><img src="{_uri(block["tile"])}" alt="{block["name"]}">'
            f'<div><p class="facts">'
            f'<b>연면적</b> {block["gross"]:,.0f}㎡ · 용적률 {block["gross"] / parcel * 100:.0f}%'
            f'{score}<br>'
            f'<b>구성</b> {composition_module.band_id(reading)} · '
            f'부분 {reading.parts}개를 규제선 {reading.elements}개가 설명 · '
            f'지배 {reading.dominance:.0%}'
            f'{" · 지면에서 들림" if reading.lifted else ""}'
            f'{f" · {reading.tiers}단" if reading.tiers > 1 else ""}'
            f'</p></div></div>{sequence}</section>')

    # The rest of the shortlist under the three, so one address carries the
    # whole answer. The architect asked why a selection board, a sweep sheet
    # and a study were three separate links; there is no good answer - the
    # study is the deliverable and the board is what it was chosen from.
    board = ROOT / "runs" / "board" / "board-key.json"
    rest = ""
    if board.exists():
        chosen = {block["name"].replace(" ", "_") for block in blocks}
        cards = []
        for row in json.loads(board.read_text(encoding="utf-8")):
            label = str(row.get("label") or "")
            if not label.startswith("O"):
                continue
            if str(row.get("name") or "").split("~")[0].split("^")[0] in chosen:
                continue
            png = board.parent / f"{label}.png"
            if not png.exists():
                continue
            score = row.get("score")
            mark = f" · {float(score):.2f}" if score else ""
            cards.append(
                f'<figure><img src="{_uri(png)}" alt="{label}">'
                f'<figcaption>{label}{mark}</figcaption></figure>')
        if cards:
            rest = ('<h2 class="rest">심사를 통과한 나머지 안</h2>'
                    f'<div class="grid">{"".join(cards)}</div>')

    html = STYLE + (
        '<main>\n<header><h1>매스 스터디 3안</h1>'
        f'<p>효돈동 {parcel:,.0f}㎡ · 건폐율 60% · 용적률 250% · '
        '각 안은 이름, 논지, 조작 순서, 배달된 매스와 법정 수치를 가진다. '
        '첫 안이 추천안이다.</p></header>\n'
        + "\n".join(sections)
        + rest
        + '\n<footer>백색 모형 액소노메트릭과 배치도는 법규선으로 잘린 배달 상태다. '
        '순서 띠의 마지막 프레임이 그 상태이며, 그 앞의 프레임들은 문장의 단어 하나씩이다.'
        '</footer>\n</main>')

    page = out / "study.html"
    page.write_text(html, encoding="utf-8")
    print(f"wrote {page} ({page.stat().st_size // 1024} KB, {len(blocks)} schemes)")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(*sys.argv[1:]))
