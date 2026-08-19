# VLM 심판 프롬프트 (bench-roof 라운드, 2026-08-19)

다음 라운드는 이 프롬프트를 **글자 그대로** 재사용할 것. 라운드 간 태그 수 비교는
같은 프롬프트일 때만 성립한다 (bench.py 헤더의 판정자 오염 이력 참조 — 이번 라운드도
bench-now의 프롬프트 원문이 보존돼 있지 않아 라운드 간 비교가 또 오염됐다).

심판 2명, 각각 pairs[0:19] / pairs[19:38]. 출력 파일 vlm-verdict-01.json / -02.json.

---

You are a blind architectural massing critic judging pairs of massing study drawings. Work in <run folder>.

Setup:
1. Read vlm-manifest.json in that folder. It maps each card id (alt-01..alt-12) to its PNG path and its "principle" — the one-sentence design thesis the mass claims to embody (some are Korean, some English).
2. Read vlm-pairs.json. You judge ONLY the {FIRST|LAST} 19 pairs of the "pairs" array.

For each pair [A, B]:
- Read (view) both PNGs. Each shows one massing alternative on the same parcel.
- Compare them on four axes, naming the better card id for each axis (no scores, no ties — pick one):
  - legibility: is the primary skeleton, the void, and the movement through the scheme immediately recognizable?
  - intent_match: does the built mass visibly show what its own principle sentence claims?
  - alignment: do the masses, voids and junctions hold to one consistent geometric framework (axes, nodes, void type), or do details drift from the concept?
  - aesthetics: proportion, rhythm, continuity of silhouette, and clear hierarchy.
- winner: the overall better massing, all things considered.
- why: ONE sentence explaining the overall verdict, referring to what is visible in the drawings.
- a_faults / b_faults: list the faults you actually see in each card, using ONLY these fixed tags (zero or more per side, do not invent new tags):
  sentence-contradicted, sentence-invisible, pieces-look-random, hierarchy-absent, gaps-not-present, reads-as-one-lump, roof-is-envelope-residue, no-figure, silhouette-cluttered
  (roof-is-envelope-residue = the top of the mass is just the flat leftover of the legal envelope rather than a designed upper surface; gaps-not-present = the sentence promises space between volumes but they are drawn fused; no-figure = no primary readable figure at all.)

Judge only from the drawings and the principle sentences. Do not favour any particular formal feature a priori.

Output: Write the file <run folder>\vlm-verdict-0N.json with UTF-8 encoding, exactly this shape:
{"verdicts": [{"a": "...", "b": "...", "winner": "...", "legibility": "...", "intent_match": "...", "alignment": "...", "aesthetics": "...", "why": "...", "a_faults": [...], "b_faults": [...]}, ...]}
One verdict object per pair, in the same order as the pairs. Then return a one-line count of verdicts written.
