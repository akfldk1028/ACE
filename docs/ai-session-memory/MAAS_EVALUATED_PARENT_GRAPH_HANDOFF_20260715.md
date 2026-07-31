# MAAS evaluated-parent graph handoff

Updated: 2026-07-15

Read this before changing ARR Mass-Brain ingestion, GRL relations, the
activation UI, or claiming that the v102 board is competition-grade.

> Superseding generative-impact verdict: read
> `MAAS_GRL_ON_OFF_ABLATION_20260715.md`. A corrected v104 OFF / v105 ON paired
> run produced the exact same 19 selected sequences, review rows and
> accepted-only PNG bytes. The connectivity work below is valid, but it has
> not improved final mass generation while rollout remains shadow/slots=0.

## What was fixed

The previous bridge sent raw seed labels, built a complete 64-node graph with
2,016 relations, lost typed node constraints/schema at the service boundary,
and could reject a whole ingest when a previously compiled LLM parent used a
legacy parameter value. Concrete names such as `offset twin bar with shared
court` also appeared too early in the presentation hierarchy.

The current flow is:

```text
BOOK (pending) / ArchDaily / PNU+program
        -> abstract formal principle
        -> evaluated typed component graph
        -> Mass-Brain proposal
        -> exact compile / VLM / legal / parking outcome
```

ARR now exact-compiles sources on the real parcel before ingestion. The first
non-base operation is the primary language node; later operations remain typed
support/void/connector nodes. The bridge preserves parent links, relations,
constraints, structured control points and parameter schemas. Previously
verified legacy values extend only their exported compatibility schema; this
preserves exact source geometry and is not a parcel-form template.

GRL edges are sparse evidence/navigation links with bounded degree. Mass-Brain
computes compatibility from typed payloads; it no longer needs a meaningless
complete graph in order to recombine.

## Real-PNU v102 evidence

PNU: `1168011800104170004`

- parent features: 44
- eligible evaluated parents: 34
- sparse relations: 160 (previously 2,016)
- proposals generated: 20
- exact proposal compiles: 15
- VLM-evaluated proposals: 6
- recorded outcomes: 15
- rollout: `shadow`, slots 0
- final ARR board: 19/20
- visual status: `automatic_visual_floor_failed`
- legal/parking projection: `not_run`

Artifacts:

- `docs/playwright/design-route-live-verify/maas-neighborhood-vlm-a2a-v102-connected-graph.json`
- `docs/playwright/design-route-live-verify/maas-neighborhood-vlm-a2a-v102-connected-graph.png`
- `docs/playwright/design-route-live-verify/maas-neighborhood-vlm-a2a-v102-connected-graph-accepted-only.png`
- `docs/mass-brain-v102-full-activation-20260715.png`
- `docs/mass-brain-v102-grl-all-nodes-20260715.png`

## Honest visual review

The accepted-only PNG is clean enough to inspect and is materially more varied
than the old box-only regressions: roof-section, faceted taper, courtyard,
connector/interlock, ribbon and step families are all visible. It is not a new
aesthetic win over v101. Several stepped slab and arched/roof-section solutions
remain close in architectural language, the branched-field quota is missing,
and no Mass-Brain proposal can enter final selection while rollout slots are 0.

Do not report `15 compiled` or `6 VLM evaluated` as 15/20 visual success. Do
not report geometry pass as legal or parking pass.

## Presentation behavior

`http://127.0.0.1:5210` opens the layered activation view. It renders all 20
latest proposal nodes and all 20 result nodes. BOOK is dashed because its 69
pages have not been distilled into reviewed relation cards. The `GRL 원본`
tab renders all 44 parents and 160 relations.

## Verification

- `D:\Data\Mass-Brain`: `npm run verify` passed (12 unit tests, builds,
  dist smoke and Playwright smoke).
- `D:\Data\Mass-Brain`: `npm audit --audit-level=high` found 0 vulnerabilities.
- `D:\Data\25_ACE\ARR\backend`: `python manage.py test design.test_mass_brain`
  passed 7 tests.
- Browser activation: 20 proposal nodes, 20 result nodes, 0 page/HTTP errors.
- Browser GRL: 44 nodes, 320 visible circuit/relation edges, 44 evidence, 160
  relations.

## Next work

1. Distill BOOK page evidence into architect-reviewed coordinate-free relation
   cards and only then activate BOOK-derived typed graph mutations.
2. Diagnose the five v102 proposal compile failures and fourteen proposals that
   did not reach VLM evaluation without weakening hard gates.
3. Restore a genuine branched continuous field and close the 20th accepted
   candidate without duplicating roof/step families.
4. Run identical legal/FAR/parking projection and paired blind VLM comparison
   before considering any Mass-Brain active slot.
