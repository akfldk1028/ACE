# Open Validation Gaps

## P0 — visual architectural order

- Add a measured visual-order audit for layered/floating-read silhouettes,
  over-carved bodies, excessive micro-terraces and weak primary/secondary
  hierarchy. Do not hardcode one candidate's dimensions.
- Produce stable multi-view evidence per selected MASS. A single isometric crop
  can hide connecting cores and mislead both humans and VLM.
- Keep component/manifold checks, but do not treat them as visual-quality proof.

## P0 — VLM truth

- r182 has not been VLM reviewed.
- r184 performed a bounded 24-call paid review of actual MASS renders plus small
  relevant reference sets and selected 0/20. Preserve that failure; do not
  relabel r182 as VLM-approved.
- A future paid test must record exact submitted MASS/reference hashes, model
  response IDs and cost. Start with a very small representative set rather than
  sending the full archive.
- Only after the passport contains `used_by_vlm=true`, response/model IDs and a
  materialized critique may reference edges become active.

## P0 — approval-grade legal authority

- Verify Seoul/강남구 parking and building-rule sources against current official
  ordinance text, including effective dates and exceptions.
- Add source URL, ordinance/article/appendix, effective date and parsed-text hash
  to each legal rule. `official_pdf_text_extracted_manual_review` alone is not a
  complete authority chain.
- Check road/building-line constraints, district-unit plans, fire access,
  evacuation, accessibility, landscape calculation, use-specific restrictions
  and any parcel overlays not present in the current four-rule summary.
- Keep the current result labelled massing preflight, never permit approval.

## P1 — site conditioning semantics

- Rename or document `parcel_coordinates_used` so it cannot be misread. The
  current flow uses the actual parcel-derived polygon as compile host while the
  universal program avoids absolute-coordinate memorization.
- Add an explicit evidence field pair:
  `parcel_geometry_used_for_fit` and `absolute_coordinates_used_for_authoring`.

## P1 — runtime efficiency

- r182 needed 4,649 seconds and seven pages. Persist page-level compiled/GATE
  artifacts keyed by parcel/legal/program/form-page hashes so later runs do not
  recompute unchanged pages.

## P1 — remaining module seams

- `portfolio_benchmark.py` is down from roughly 4,000 lines to 1,781 lines and
  now delegates generation, analysis, selection, replenishment, capacity,
  lineage, references and VLM review.
- Continue splitting the remaining large policy modules by stable contracts,
  not by adding parallel implementations: `portfolio_selection.py` (1,823
  lines), `vlm_review.py` (1,633 lines), `candidate_generation.py` (1,552
  lines), and `candidate_analysis.py` (1,249 lines).
- Keep one public orchestration path and one canonical AST/compiler. New agent
  repositories may wrap these contracts but must not fork geometry truth.
