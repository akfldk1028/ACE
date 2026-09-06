"""Assemble an author brief from its owners - no hand-typed numbers, no
hand-picked exemplars.

The brief is derived, per the one-owner rule: trap numbers come from
trap_ledger (which reads the gate constants), the vocabulary and canon are
included verbatim from their files, and the board section lists the current
board's sentences from the curator's own key - so the "differ from all of
these at the level of formal principle" demand (NoveltyBench's best-in-class
regeneration, canon §10) always names today's board, not a remembered one.

    python tools/make_brief.py <track> <out.md> [assignment-text-file]
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parents[1]


def board_section(track: str) -> str:
    key_path = ROOT / "runs" / "board" / "board-key.json"
    # A new era archives its key before the first author brief is made.
    # There are no currently evaluated seats until that era's first bake.
    key = json.loads(key_path.read_text(encoding="utf-8")) if key_path.exists() else []
    book = {}
    for path in sorted((ROOT / "inputs").glob("gen-*.json")):
        for scheme in json.loads(path.read_text(encoding="utf-8"))["schemes"]:
            book[scheme["name"]] = scheme
    lines = ["## Current board: differ from every entry at the level of formal principle",
             "The common curator reserves one seat per family, not per renamed parameter variation.", ""]
    if not key:
        lines.append("No judged and baked seats exist in the current era yet.")
    for row in key:
        if not row["label"].startswith(track):
            continue
        family = row["name"].split("~")[0].split("^")[0]
        scheme = book.get(family) or {}
        line = (scheme.get("secondary_language")
                or scheme.get("formal_principle") or family)
        lines.append(f"- {row['label']} ({row['score']:.2f}): {line}")
    return "\n".join(lines)


def champion_section() -> str:
    """Developments that beat their parent in front of a blind jury.

    The development loop's one real output is a champion, and champion.json
    was read by nothing - so a mutation a jury had already preferred was
    invisible to the next author, who could propose the parent's value again
    with no way of knowing it had been tried and beaten. Read from the
    develop runs' own files, never typed here, and it names the juror count
    because a one-juror round is one opinion, not a consensus.
    """

    lines = []
    for path in sorted(ROOT.glob("runs/develop-*/champion.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        # A champion.json written before the scorer counted jurors cannot say
        # how many voted, and the brief must not claim a consensus it has no
        # evidence for. Re-score that round and it appears.
        if not record.get("champion") or "jurors" not in record:
            continue
        lines.append(
            f"- **{record['champion']}** — {record.get('champion_change', '-')}"
            f" : all {record.get('jurors', 0)} independent juror sessions preferred this variant"
            f" to parent {record['parent']} in a blind pairwise comparison")
    if not lines:
        return ""
    return "\n".join(
        ["## Development champions already carried into the corpus",
         "These comparisons were judged. Treat them as specific evidence, not a guarantee for a different design.",
         ""] + lines)


def main(track: str, out_path: str, assignment: str = "") -> int:
    from trap_ledger import ledger  # django setup inside
    from design.maas.massv2.parcel_policy import policy_for
    from finalists import PNU

    count = os.environ.get("MASS_AUTHOR_COUNT")
    count_instruction = f"Exactly {int(count)} schemes." if count else "Use the scheme count requested by this cycle."

    parts = [
        "# Architectural massing author brief - assembled from canonical owners",
        "",
        f"Return only one {{\"schemes\":[...]}} JSON object. {count_instruction} Required scheme keys: name,",
        "primary_language, secondary_language, formal_principle (one Korean sentence for the final sheet),",
        "dominant_gesture, reference_basis (verified facts or original authorship), floor_height_m,",
        "ops (each with op, supported parameters, and a concise why: input -> operation -> visible change -> function -> limitation).",
        "Use the live grammar's parameter units and ranges. Start with extrude|loop|aggregate|stack.",
        "Operational authoring instructions are in English; user-facing sheet descriptions may be Korean.",
        "Design architectural masses: positive-volume hierarchy, section, articulation, joining/separation and carved voids.",
        "A courtyard is a void organizing building volumes; planting or landscape composition does not substitute for a massing proposition.",
        "",
        "## Programme first; compare density as a design decision",
        "Legal upper bounds are hard limits, not automatic design targets.",
        "Meet explicit required programme and area using the supplied definitions and tolerances; disclose infeasibility instead of silently reducing the brief.",
        "If required programme or target area is absent, keep it unknown; do not invent a maximum-FAR target or claim programme compliance.",
        "Compare distinct height, density and solid-void organizations that address the same supplied requirements; do not reduce alternatives to scaled copies.",
        "Lower FAR needs a visible spatial benefit in delivered mass, plan or section; prose alone is not evidence and lower density is not automatically superior.",
        "Initial authored height is revisable when the spatial proposition benefits, while explicit per-alternative growth constraints remain meaningful and must not be silently overridden.",
        "Do not invent rooms, circulation or structural proof from an attractive silhouette. State what the supplied geometry establishes and what remains unverified.",
        "Choose only the supported principles and operations needed for each proposition; operator count is not a quality target.",
        "",
        "## Brief design rationale required for each scheme",
        "1) State one conflict supported by the supplied site/programme evidence; label a provisional question when that evidence is missing.",
        "2) State one architectural massing principle that addresses it.",
        "3) Explain how that principle differs from the current board entries below.",
        "4) Express it with supported operators and state the resulting limitations.",
        "Provide concise decisions and evidence, not hidden deliberation.",
        "",
    ]
    policy = policy_for(PNU)
    if policy:
        parts += ["## Confirmed parcel planning constraints derived from the code owner",
                  "Storey count and metric height are different constraints. Do not mark unverified items as passed.",
                  "```json", json.dumps(policy, ensure_ascii=False, indent=2), "```", ""]
    if assignment:
        parts += ["## Assigned authoring territory", assignment.strip(), ""]
    verdicts = ROOT / "runs" / "board" / "verdict-ledger.md"
    if verdicts.exists():
        # What the juries keep refusing, in their own clauses - generated by
        # verdict_ledger.py from every judged round, never typed here.
        parts += [verdicts.read_text(encoding="utf-8"), ""]
    champions = champion_section()
    if champions:
        parts += [champions, ""]
    parts += ["## Canonical reference material (original source language preserved)",
              ledger(), "", board_section(track), "",
              "---", "",
              (ROOT / "inputs" / "VOCABULARY.md").read_text(encoding="utf-8"),
              "", "---", "",
              (ROOT / "inputs" / "AUTHORING-CANON.md").read_text(encoding="utf-8")]
    Path(out_path).write_text("\n".join(parts), encoding="utf-8")
    print(f"brief -> {out_path} ({Path(out_path).stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    track = sys.argv[1] if len(sys.argv) > 1 else "O"
    out = sys.argv[2] if len(sys.argv) > 2 else "brief.md"
    text = Path(sys.argv[3]).read_text(encoding="utf-8") if len(sys.argv) > 3 else ""
    sys.exit(main(track, out, text))
