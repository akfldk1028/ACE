# C173 three-language MASS checkpoint — 2026-08-10

## Verified result

- Run: `legal-mass-v31-c173-ridge-terminal-court-wing`
- PNU: `1168011800104170004`
- Mode: diagnostic target 3, Codex OAuth LLM-authored typed AST, no live VLM.
- Result: program passed `3/3`, selection pool `3`, selected `3`.
- This is a diagnostic 3/3 proof. It is **not** canonical publishable 20/20; canonical remains 0/20 until the publishable contract and required VLM run complete.
- ISO board: `ARR/docs/playwright/design-route-live-verify/legal-mass-v31-c173-ridge-terminal-court-wing/maas-book-neighborhood-3.png`
- Legal archive board: `ARR/docs/playwright/design-route-live-verify/legal-mass-v31-c173-ridge-terminal-court-wing/maas-book-neighborhood-0-legal-archive.png`

## Exact selected evidence

| Language | GFA | Feasible utilization | Renderer-authoritative phenotype |
|---|---:|---:|---|
| terminal shallow ridge/bar + west threshold | 199.392 m² | 0.6000 | voided |
| west-open U courtyard + continuous taper | 201.140 m² | 0.6053 | winged |
| branched L wing + oblique taper | 229.574 m² | 0.6908 | oblique |

Direct PNG inspection confirms that the three selected ISO masses are not three copies of the staircase fallback: one reads as a tall ridge/bar, one as an open U court, and one as an L/oblique terraced wing. The third still intentionally contains stepped/tapered expression; stepped form is one option, not the whole portfolio.

## Root causes repaired

1. The prior global Matrix4 pose was centered from the ground-floor west access point only. That point sat outside the shared upper legal core, so upper floors were repeatedly carved into the same stepped envelope. `source_bridge` now searches one global x/y Matrix4 translation against every authored and legal floor section while preserving the authored linear transform block.
2. Capacity evidence displayed rounded 0.6000 while the hard gate compared unrounded area at `1e-9`. All capacity paths now share a bounded `0.05 m²` measurement tolerance and the same hard-pass authority.
3. Portfolio selection recomputed phenotype from a proxy even when a renderer-certified final surface mesh existed. Final renderer-authoritative surfaces now own phenotype classification.
4. Certified CSG transport facets could contain tiny edges or redundant coplanar slivers. Morphology now follows the independent closed-manifold certificate rather than rejecting the certified payload through a coarser visual-only key.
5. `profiled_hall` already existed in the generic kernel but was omitted from the neighborhood LLM vocabulary. The neighborhood program profile now permits this existing operator without adding a completed form template or PNU-specific geometry.
6. `profiled_hall` is a terminal section operator. C172 failed `semantic_carrier` because the LLM AST used `profiled_hall -> notch`; C173 uses the valid `notch -> profiled_hall` order.

## Non-hardcoding boundary

- The C173 manifest is temporary LLM-authored normalized input, not production geometry code.
- It contains UnitBox-derived seed proportions, one Matrix4, normalized section/court/wing controls, and typed operators only.
- It contains no PNU coordinates, legal envelope coordinates, final mesh, or completed building template.
- Site placement, scaling, floorwise legal CSG, GFA, law, parking, exact mesh certification, and portfolio selection remain shared algorithms.

## Verification

- Focused regression suite: 11/11 pass.
- C173 production command exited 0 in 47.5 seconds.
- All three selected records pass geometry, law, capacity, parking, program, and selection stages.
- VLM stage is `not_evaluated`; do not call this a final VLM-approved or publishable portfolio.

## Next bounded step

Use C173 as the small deterministic baseline. Do not restart from C50/C52 and do not spend a large provider batch. Next, run one bounded exact-image VLM review only when credentials/cost are explicitly enabled, then scale the same generic author → typed feedback → repair loop toward 5 and 20.
