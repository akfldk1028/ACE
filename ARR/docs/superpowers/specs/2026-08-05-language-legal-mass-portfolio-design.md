# Language Legal MASS Portfolio Design

Date: 2026-08-05 KST

## Objective

Extend the existing `/design/language` experience so one graph and one
20-card gallery show the complete MASS decision set: selected, legal-pass,
rejected, and not-evaluated candidates. Every status must be derived from the
exact candidate's persisted backend evidence. A pre-legal candidate must never
be presented as law-compliant merely because it compiled or rendered.

## Existing product surface

The implementation reuses `BookLanguageFlow.tsx`, `LanguageNetworkCanvas`,
the existing `CREATIVE 100` graph view, the creative gallery/filter controls,
and the executed-MASS archive. It does not create a second design page or a
parallel graph UI.

## Considered approaches

1. **Extend the existing portfolio view (selected).** Replace the narrowly
   pre-legal presentation with a typed portfolio-evaluation view while keeping
   the same graph, evidence panel, selection identity, and gallery. This has
   the least UI duplication and preserves the established language lineage.
2. Put every candidate directly into `FULL GRAPH`. This was rejected because
   twenty candidate subgraphs and all rejection branches would obscure the
   selected execution path.
3. Add a separate legal-results page. This was rejected because it would
   duplicate the MASS rail, graph interaction, filters, and evidence panel and
   could drift from `/design/language` identity rules.

## Authority and status model

Each card has independent typed stages:

- `geometry`
- `law`
- `capacity`
- `parking`
- `program`
- `vlm`
- `selection`

Each stage status is one of `pass`, `fail`, or `not_evaluated`. A candidate's
overall classification is:

- `selected`: all required deterministic hard gates passed and it was selected;
- `legal_pass`: geometry, law, capacity, parking, and program are all `pass`;
- `failed`: at least one evaluated required stage is `fail`;
- `not_evaluated`: no required stage failed, but at least one is not evaluated.

`vlm` remains independent. A candidate can be a deterministic `legal_pass`
while VLM is `not_evaluated`; the UI must not label that as VLM acceptance.
Legal status is derived only from hash-bound PNU/legal evidence, never a family
name, render, score, or frontend inference.

## Backend evidence contract

Add a versioned portfolio-evaluation manifest exposed through the existing
MAAS design API boundary. The manifest identifies the source run and PNU and
contains up to the requested 20 candidate records. Every record contains:

- stable candidate, program, geometry, and surface hashes;
- preview URL when canonical renderable geometry exists;
- BOOK principle/scope lineage;
- the seven typed stage decisions;
- overall classification;
- ordered terminal reason codes and human-readable evidence summaries;
- exact evidence references for law, capacity, parking, program, VLM, and
  selection where those stages ran.

The full BOOK benchmark owns these decisions. The frontend endpoint may adapt
persisted evidence but may not rerun law logic or synthesize PASS. Rejected
candidates remain in the evaluation ledger. Candidates rejected before a safe
canonical render use an explicit `NO RENDERABLE MASS` placeholder rather than
a borrowed image.

The existing pre-legal creative manifest remains supported. Its candidates
adapt to `not_evaluated` for every legal stage and retain the visible
`PRE-LEGAL` label.

## Frontend behavior

The current `CREATIVE 100` tab becomes `MASS PORTFOLIO`. For a 20-candidate
run, all cards appear in one gallery without pagination. Larger archives keep
the existing pagination boundary.

The portfolio header shows totals for `ALL`, `LEGAL PASS`, `FAIL`,
`NOT EVALUATED`, and `SELECTED`. Filters cover overall status and individual
stages. Every card includes a visible status badge and the first terminal
reason. Color is supplementary: labels and icons carry the same meaning.

Selecting a card highlights its candidate branch in `LanguageNetworkCanvas`
and opens the existing evidence panel. The panel shows:

- the exact MASS preview or explicit missing-preview state;
- UnitBox, Matrix4 BaseVolume, BOOK principle, and scope lineage;
- the seven-stage decision list;
- measured values and limits when present;
- every terminal reason without truncating the machine-readable record;
- links/identifiers for persisted evidence artifacts.

Graph stages remain conceptually:

`UnitBox -> Matrix4 BaseVolume -> BOOK -> Compile -> Law -> Capacity -> Parking
-> Program -> VLM -> Selected MASS`

Failed candidates branch at their actual terminal stage and remain visible.
Not-evaluated downstream nodes are visibly inactive, not failed.

## Error handling

- Missing or invalid evaluation evidence fails closed to `not_evaluated`.
- Hash mismatches reject the record from legal-pass presentation and expose an
  evidence-integrity error.
- Missing preview data never hides the candidate or substitutes another MASS.
- API/run load failures preserve the current graph and show a scoped error.
- A zero-selected run still renders every evaluated candidate and its reasons.

## Verification

Backend tests must prove classification is fail-closed, candidate hashes bind
to evidence, rejected candidates survive serialization, and pre-legal inputs
cannot become legal pass. Frontend unit tests must cover adapters, filters,
badges, reason display, all-20 rendering, selection identity, and missing
preview behavior.

Browser verification must load `/design/language`, select `MASS PORTFOLIO`,
show all 20 cards together, switch among ALL/PASS/FAIL/NOT EVALUATED, select
both a passing and failing candidate, and verify graph highlighting plus the
right evidence panel with no broken images or error overlay.

## Non-claims

This work exposes the existing full BOOK law/parking/program evidence. It does
not weaken hard gates, invent ordinance results, imply professional approval,
or treat optional VLM as a legal authority. Human professional review remains
separate from deterministic system evidence.
